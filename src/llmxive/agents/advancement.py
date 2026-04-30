"""Rule-based, non-LLM Advancement-Evaluator (T028).

The sole writer of Project.current_stage. Reads project state + review
records and decides each stage transition.

Acceptance gate (per user request 2026-04-29): in addition to the
points threshold, **every required specialist reviewer must have
written an accept review** before the project can advance to
RESEARCH_ACCEPTED or PAPER_ACCEPTED. The list of required specialists
is read from agents/registry.yaml at evaluation time (any agent whose
name starts with `research_reviewer_` or `paper_reviewer_`).
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from llmxive.agents import registry as registry_loader
from llmxive.agents.lifecycle import is_valid_transition
from llmxive.config import (
    PAPER_ACCEPT_THRESHOLD,
    RESEARCH_ACCEPT_THRESHOLD,
)
from llmxive.state import citations as citations_store
from llmxive.state import project as project_store
from llmxive.state import reviews as reviews_store
from llmxive.types import (
    Project,
    ReviewerKind,
    ReviewRecord,
    Stage,
    VerificationStatus,
)


def _required_specialists(prefix: str, *, repo_root: Path | None = None) -> set[str]:
    """Return every agent name in the registry that starts with `prefix`.

    Used to gate RESEARCH_ACCEPTED on all `research_reviewer_*` accepts and
    PAPER_ACCEPTED on all `paper_reviewer_*` accepts.
    """
    try:
        reg = registry_loader.load(repo_root=repo_root)
    except Exception:
        return set()
    return {a.name for a in reg.agents if a.name.startswith(prefix)}


def _all_specialists_accept(records: list[ReviewRecord], required: set[str]) -> bool:
    """True iff every required reviewer has at least one accept record."""
    if not required:
        return True  # no gate configured
    accepted_by: set[str] = {
        r.reviewer_name for r in records if r.verdict == "accept"
    }
    return required <= accepted_by


class AdvancementError(RuntimeError):
    """Raised when a requested transition is invalid."""


def _produced_by(project: Project, artifact_path: str) -> str | None:
    """Best-effort author lookup from the project's run-log; v1 stub.

    A future refinement reads state/run-log/ to find the entry that wrote
    the artifact and returns entry.agent_name. For v1 we return None so
    self-review filtering is done by reviewer-name comparison only.
    """
    return None


def _award_review_points(
    project: Project,
    records: list[ReviewRecord],
    *,
    bucket: str,
    citations: list[citations_store.Citation],
    is_paper_stage: bool,
) -> Project:
    """Sum eligible review records into the right point bucket.

    Eligibility filters:
    1. The record's artifact_hash matches the live artifact's hash
       (anti-tamper).
    2. The reviewer is not the artifact's author (self-review prohibited).
    3. The reviewed artifact has no citation in unreachable/mismatch
       status (FIX C2 — Reference-Validator gates point award).
    """
    bad_artifacts: set[str] = {
        c.artifact_path
        for c in citations
        if c.verification_status in (VerificationStatus.UNREACHABLE, VerificationStatus.MISMATCH)
    }
    awarded: float = 0.0
    for rec in records:
        if rec.artifact_path in bad_artifacts:
            continue
        live_hash = project.artifact_hashes.get(rec.artifact_path)
        if live_hash and live_hash != rec.artifact_hash:
            continue
        author = _produced_by(project, rec.artifact_path)
        if author and author == rec.reviewer_name:
            continue
        # Reject un-authenticated human reviews. Anyone could drop a
        # YAML file into reviews/ claiming reviewer_kind=human; the
        # github_authenticated flag is set only by the OAuth-backed
        # submission flow.
        if rec.reviewer_kind == ReviewerKind.HUMAN and not rec.github_authenticated:
            continue
        awarded += rec.score
    target = (
        project.points_paper if is_paper_stage else project.points_research
    )
    target = dict(target)
    target[bucket] = round(target.get(bucket, 0.0) + awarded, 2)
    if is_paper_stage:
        return project.model_copy(update={"points_paper": target})
    return project.model_copy(update={"points_research": target})


def _winning_recommendation(records: list[ReviewRecord]) -> str | None:
    """Return the verdict to act on, or None if no records.

    Strategy: **majority-vote with severity tie-break**.

    1. Count each verdict's frequency.
    2. Hard severity floor: if ≥50% of reviewers voted `reject` or
       `fundamental_flaws`, route there immediately (those are
       project-killers and a true majority is needed to terminate).
    3. Otherwise, take the verdict with the most votes. If two are
       tied, pick the more severe one (severity ladder: reject >
       fundamental_flaws > full_revision > major_revision_science >
       major_revision_writing > minor_revision > accept).

    Why not "weakest link" (any one severe verdict wins)? With 7-8
    reviewers, that rule guaranteed at least one full_revision per
    round even when 5+ reviewers said the work only needed minor
    tweaks — the pipeline would throw away the entire revision and
    restart from `clarified`, wasting hours. Majority-vote lets the
    pipeline make incremental progress when most reviewers agree the
    work is close.
    """
    if not records:
        return None

    counts: dict[str, int] = defaultdict(int)
    for rec in records:
        counts[rec.verdict] += 1
    if not counts:
        return None

    # Hard severity floor — kill the project only on true majority.
    n = len(records)
    half = (n + 1) // 2  # ceiling: 4 of 7, 5 of 8
    for kill_verdict in ("reject", "fundamental_flaws"):
        if counts.get(kill_verdict, 0) >= half:
            return kill_verdict

    # Severity ladder for tie-breaking (lower index = more severe).
    severity_order = [
        "reject",
        "fundamental_flaws",
        "full_revision",
        "major_revision_science",
        "major_revision_writing",
        "minor_revision",
        "accept",
    ]
    severity_index = {v: i for i, v in enumerate(severity_order)}

    # Pick by (highest count, then most-severe verdict for tie-break).
    return max(
        counts.items(),
        key=lambda kv: (kv[1], -severity_index.get(kv[0], 99)),
    )[0]


def evaluate(project: Project, *, repo_root: Path | None = None) -> Project:
    """Decide whether the project transitions; return updated state.

    No-op if the project is in a stable stage (e.g., specified, planned)
    that another agent advances. The Evaluator only fires for stages it
    governs: review-result transitions and citation-gated accepts.
    """
    cits = citations_store.load(project.id, repo_root=repo_root)

    # Auto-promote research_complete → research_review when at least one
    # research-stage review record has been written (T067).
    if project.current_stage == Stage.RESEARCH_COMPLETE:
        records = reviews_store.list_for(project.id, stage="research", repo_root=repo_root)
        if records:
            project = _transition(project, Stage.RESEARCH_REVIEW)
        else:
            return project

    # Auto-promote paper_complete → paper_review on the same trigger.
    if project.current_stage == Stage.PAPER_COMPLETE:
        records = reviews_store.list_for(project.id, stage="paper", repo_root=repo_root)
        if records:
            project = _transition(project, Stage.PAPER_REVIEW)
        else:
            return project

    # Research-review handling (US3 wiring; placeholder logic now).
    if project.current_stage == Stage.RESEARCH_REVIEW:
        records = reviews_store.list_for(project.id, stage="research", repo_root=repo_root)
        project = _award_review_points(
            project,
            records,
            bucket="research_review",
            citations=cits,
            is_paper_stage=False,
        )
        accept_total = sum(r.score for r in records if r.verdict == "accept")
        winning = _winning_recommendation(records)
        required = _required_specialists("research_reviewer_", repo_root=repo_root)
        all_accept = _all_specialists_accept(records, required)
        # Both gates must pass: enough points AND every specialist accepts.
        if (
            accept_total >= RESEARCH_ACCEPT_THRESHOLD
            and all_accept
            and not _has_blocking_citations(cits)
        ):
            return _transition(project, Stage.RESEARCH_ACCEPTED)
        if winning == "minor_revision":
            return _transition(project, Stage.RESEARCH_MINOR_REVISION)
        if winning == "full_revision":
            return _transition(project, Stage.RESEARCH_FULL_REVISION)
        if winning == "reject":
            return _transition(project, Stage.RESEARCH_REJECTED)
        return project  # not enough votes yet

    # Paper-review handling (US5 wiring).
    if project.current_stage == Stage.PAPER_REVIEW:
        records = reviews_store.list_for(project.id, stage="paper", repo_root=repo_root)
        project = _award_review_points(
            project,
            records,
            bucket="paper_review",
            citations=cits,
            is_paper_stage=True,
        )
        accept_total = sum(r.score for r in records if r.verdict == "accept")
        winning = _winning_recommendation(records)
        required = _required_specialists("paper_reviewer_", repo_root=repo_root)
        all_accept = _all_specialists_accept(records, required)
        if (
            accept_total >= PAPER_ACCEPT_THRESHOLD
            and all_accept
            and not _has_blocking_citations(cits)
        ):
            return _transition(project, Stage.PAPER_ACCEPTED)
        if winning == "minor_revision":
            return _transition(project, Stage.PAPER_MINOR_REVISION)
        if winning == "major_revision_writing":
            return _transition(project, Stage.PAPER_MAJOR_REVISION_WRITING)
        if winning == "major_revision_science":
            return _transition(project, Stage.PAPER_MAJOR_REVISION_SCIENCE)
        if winning == "fundamental_flaws":
            return _transition(project, Stage.PAPER_FUNDAMENTAL_FLAWS)
        return project

    return project


def _has_blocking_citations(cits: list[citations_store.Citation]) -> bool:
    return any(
        c.verification_status in (VerificationStatus.UNREACHABLE, VerificationStatus.MISMATCH)
        for c in cits
    )


def _transition(project: Project, target: Stage) -> Project:
    if not is_valid_transition(project.current_stage, target):
        raise AdvancementError(
            f"invalid transition {project.current_stage.value} -> {target.value}"
        )
    return project.model_copy(update={"current_stage": target})


def commit(project: Project, *, repo_root: Path | None = None) -> None:
    """Persist a project after evaluate(); convenience helper."""
    project_store.save(project, repo_root=repo_root)


__all__ = ["evaluate", "commit", "AdvancementError"]
