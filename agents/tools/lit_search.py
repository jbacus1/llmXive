"""Lit-Search tool (T041) — queries Semantic Scholar / arXiv / OpenAlex.

Used by the Flesh-Out Agent to ground its `Related work` section in
real primary sources, by the Paper-Specifier to identify the paper's
prior-art landscape, and by the Writing-Agent to find references
during paper drafting.

Per Constitution Principle II, every record returned here MUST be a
real result from a real upstream API — no fabricated entries. The
caller (Reference-Validator Agent) re-verifies each cited paper
before review points are awarded.

The tool is intentionally tolerant of upstream outages: if all three
providers fail, it returns an empty list rather than raising, so the
Flesh-Out Agent can decide whether to proceed (a fleshed-out idea
with zero related-work bullets is rejected by the Idea-Selector).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT_S = 10.0
DEFAULT_USER_AGENT = "llmxive-lit-search/0.1 (+https://github.com/ContextLab/llmXive)"


@dataclass
class Paper:
    """Structured paper record returned by every provider."""

    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    source_url: str = ""
    abstract: str = ""
    provider: str = ""
    external_id: str = ""  # arXiv id / DOI / OpenAlex id, depending on provider

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "source_url": self.source_url,
            "abstract": self.abstract,
            "provider": self.provider,
            "external_id": self.external_id,
        }


def _semantic_scholar(
    query: str, max_results: int, timeout: float, client: httpx.Client | None = None
) -> list[Paper]:
    """Query Semantic Scholar with simple retry-and-backoff for 429s.

    Unauthenticated S2 rate-limits very aggressively: a single search
    burst yields 429 even at 1 RPS. Two retries with 2s+4s backoff
    typically clear the rate-limit window so biology queries (where
    S2 has best coverage) actually return results.
    """
    import time

    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params: dict[str, str | int] = {
        "query": query,
        "limit": max_results,
        "fields": "title,authors,year,externalIds,abstract,url",
    }
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    data: list[dict] | None = None
    backoffs = (0.0, 2.0, 4.0)
    last_exc: Exception | None = None
    for delay in backoffs:
        if delay:
            time.sleep(delay)
        try:
            if client is None:
                with httpx.Client(timeout=timeout, headers=headers) as inner:
                    resp = inner.get(url, params=params)
            else:
                resp = client.get(url, params=params, headers=headers)
            if resp.status_code == 429:
                last_exc = httpx.HTTPStatusError(
                    "429 too many requests", request=resp.request, response=resp
                )
                continue
            resp.raise_for_status()
            data = resp.json().get("data", [])
            break
        except httpx.HTTPError as exc:
            last_exc = exc
            continue
    if data is None:
        LOGGER.warning("semantic_scholar query failed: %s", last_exc)
        return []

    papers: list[Paper] = []
    for item in data:
        title = (item.get("title") or "").strip()
        if not title:
            continue
        authors = [a.get("name", "") for a in item.get("authors") or [] if a.get("name")]
        ext_ids = item.get("externalIds") or {}
        external_id = ext_ids.get("DOI") or ext_ids.get("ArXiv") or ext_ids.get("CorpusId", "")
        papers.append(
            Paper(
                title=title,
                authors=authors,
                year=item.get("year"),
                source_url=item.get("url") or "",
                abstract=(item.get("abstract") or "").strip(),
                provider="semantic_scholar",
                external_id=str(external_id),
            )
        )
    return papers


def _arxiv(query: str, max_results: int, timeout: float) -> list[Paper]:
    try:
        import arxiv  # lazy import — arxiv is in optional deps for this tool
    except ImportError:
        LOGGER.warning("arxiv package not installed; skipping arxiv provider")
        return []
    try:
        search = arxiv.Search(query=query, max_results=max_results)
        results = list(search.results())
    except Exception as exc:  # arxiv raises a variety of errors
        LOGGER.warning("arxiv query failed: %s", exc)
        return []

    papers: list[Paper] = []
    for r in results:
        papers.append(
            Paper(
                title=(r.title or "").strip(),
                authors=[a.name for a in r.authors],
                year=r.published.year if r.published else None,
                source_url=r.entry_id or "",
                abstract=(r.summary or "").strip(),
                provider="arxiv",
                external_id=r.entry_id.rsplit("/", 1)[-1] if r.entry_id else "",
            )
        )
    return papers


def _openalex(
    query: str, max_results: int, timeout: float, client: httpx.Client | None = None
) -> list[Paper]:
    url = "https://api.openalex.org/works"
    params: dict[str, str | int] = {
        "search": query,
        "per-page": max_results,
        "select": "id,title,authorships,publication_year,doi,abstract_inverted_index",
    }
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    try:
        if client is None:
            with httpx.Client(timeout=timeout, headers=headers) as inner:
                resp = inner.get(url, params=params)
        else:
            resp = client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json().get("results", [])
    except httpx.HTTPError as exc:
        LOGGER.warning("openalex query failed: %s", exc)
        return []

    papers: list[Paper] = []
    for item in data:
        title = (item.get("title") or "").strip()
        if not title:
            continue
        authors = [
            a.get("author", {}).get("display_name", "")
            for a in item.get("authorships") or []
            if a.get("author")
        ]
        # OpenAlex returns abstracts as inverted indexes; reconstruct loosely.
        abstract = ""
        inv = item.get("abstract_inverted_index") or {}
        if isinstance(inv, dict) and inv:
            tokens: list[tuple[int, str]] = []
            for word, positions in inv.items():
                for p in positions:
                    tokens.append((p, word))
            abstract = " ".join(w for _, w in sorted(tokens))
        papers.append(
            Paper(
                title=title,
                authors=[a for a in authors if a],
                year=item.get("publication_year"),
                source_url=item.get("doi") or item.get("id") or "",
                abstract=abstract,
                provider="openalex",
                external_id=item.get("id", ""),
            )
        )
    return papers


def _dedupe(papers: list[Paper]) -> list[Paper]:
    """Drop duplicate hits (same title, case-insensitive)."""
    seen: set[str] = set()
    out: list[Paper] = []
    for p in papers:
        key = p.title.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


_LITSEARCH_STOPWORDS: set[str] = {
    "the", "and", "for", "with", "from", "this", "that", "these", "those",
    "into", "using", "based", "study", "studies", "between", "across",
    "research", "analysis", "approach", "biology", "general", "novel", "modern",
    "framework",
    # task-related verbs that show up in titles but don't carry topic
    "exploring", "investigating", "developing", "evaluating", "improving",
    "understanding", "assessing", "characterizing",
}


def _relevance_score(paper: Paper, query: str) -> float:
    """Lexical overlap between paper title/abstract and informative query terms.

    Rationale: arXiv broad-keyword search will happily return any paper
    that matches ONE word of the query (e.g., "evolutionary"). We need
    multiple specific topic words to match before counting a hit. Words
    in the stoplist are excluded so generic stems don't inflate the
    score.
    """
    if not query.strip():
        return 0.0
    qtoks = {
        t for t in (query.lower().replace("/", " ").split())
        if len(t) > 3 and t not in _LITSEARCH_STOPWORDS
    }
    if not qtoks:
        return 0.0
    text = (paper.title + " " + paper.abstract).lower()
    hits = sum(1 for t in qtoks if t in text)
    return hits / len(qtoks)


def lit_search(
    query: str,
    *,
    max_results: int = 8,
    timeout: float = DEFAULT_TIMEOUT_S,
    providers: list[str] | None = None,
) -> list[Paper]:
    """Search ALL configured providers, dedupe, rank by topical relevance, trim.

    Default providers: semantic_scholar, arxiv, openalex. We always
    query all three (each has different coverage gaps; arXiv has weak
    bio coverage, OpenAlex covers it; semantic_scholar rate-limits
    aggressively) and rank the merged set by lexical overlap with the
    query so off-topic filler doesn't crowd out real hits.
    """
    if not query.strip():
        return []
    providers = providers or ["semantic_scholar", "arxiv", "openalex"]

    collected: list[Paper] = []
    for prov in providers:
        if prov == "semantic_scholar":
            collected.extend(_semantic_scholar(query, max_results, timeout))
        elif prov == "arxiv":
            collected.extend(_arxiv(query, max_results, timeout))
        elif prov == "openalex":
            collected.extend(_openalex(query, max_results, timeout))
        else:
            LOGGER.warning("unknown provider: %s", prov)

    deduped = _dedupe(collected)
    # Rank by topical relevance (ties broken by year recency).
    deduped.sort(
        key=lambda p: (-_relevance_score(p, query), -(p.year or 0)),
    )
    # Drop hits that share fewer than 3 informative tokens with the query
    # — they are off-topic filler. (Two-token coincidences are common
    # because words like "evolutionary" + "pressure" or "alternative" +
    # "biology" occur in unrelated CS/physics papers.)
    n_tokens = len({
        t for t in (query.lower().split())
        if len(t) > 3 and t not in _LITSEARCH_STOPWORDS
    })
    if n_tokens >= 5:
        threshold = 3.0 / n_tokens
    elif n_tokens >= 3:
        threshold = 2.0 / n_tokens
    else:
        threshold = 0.0  # too few informative tokens to filter sensibly
    relevant = [p for p in deduped if _relevance_score(p, query) >= threshold]
    return relevant[:max_results]


__all__ = ["Paper", "lit_search"]
