# PROJ-024 end-to-end pipeline verification — session log

**Date:** 2026-04-29 → 2026-04-30
**Project:** PROJ-024-bayesian-nonparametrics-for-anomaly-dete
**Goal:** Push ONE backlog project end-to-end at top quality, no shortcuts, find structural bugs

## Verified stage-by-stage

| Stage | Outcome | Critical findings |
|-|-|-|
| brainstormed → flesh_out_complete | ✅ pass | flesh_out produced GHA-feasible methodology, real arxiv refs (after lit_search relevance fix) |
| flesh_out_complete → project_initialized | ✅ pass | scaffold + domain-adapted constitution (added Numerical Stability + Prior Sensitivity principles) |
| project_initialized → specified | ✅ pass | spec.md with 8 FRs, 5 SCs, 3 user stories, 5 edge cases, 3 [NEEDS CLARIFICATION] markers (capped) |
| specified → clarified | ✅ pass (after fix) | Clarifier produced substantive answers (95th-percentile threshold, UCI Electricity+Traffic+Synthetic, F1 within 5%) |
| clarified → planned | ✅ pass | plan.md, research.md, data-model.md, quickstart.md, contracts/{anomaly_score,config,evaluation_metrics}.schema.yaml |
| planned → tasked | ⚠️ partial | 78 quality tasks, but Mode-B analyze loop hit JSON parse failures on rounds 3-5 (multi-line strings) |
| tasked → analyzed | (skipped — redundant pass) | |
| analyzed → in_progress → research_complete | ⚠️ 17/78 FAILED | Real bugs: fabricated dataset URLs, API mismatches across LLM-written sibling files, missing data → no model could run |
| research_complete → research_review | ✅ pass | 8 specialist reviewers wrote substantive review records; 6×full_revision, 2×minor_revision |
| research_review → research_full_revision | ✅ pass (after weakest-link fix) | Correctly routed to revision based on most-severe verdict |

## Structural shortcuts caught and fixed (9 total)

1. **Dartmouth backend creds resolution** — was env-var-only; now reads `~/.config/llmxive/credentials.toml`
2. **Dartmouth empty-content detection** — Qwen returned `''` with `finish_reason=length` silently; now raises `TransientBackendError`
3. **Backend router retry** — was 1 attempt per backend; now 3 with exponential backoff, surfaces all errors
4. **Lit_search relevance** — was first-success short-circuit; now queries all 3 providers, ranks by topical-token overlap, drops off-topic filler
5. **Lit_search S2 retry** — now retries 429 with exp backoff
6. **Clarifier YAML→JSON output** — citation-colons broke YAML mapping parser; switched to JSON; multi-line-string-aware parser
7. **Clarifier hard gate** — was silently stubbing every unresolved marker as `_(Resolved by default)_`; now raises if patches < markers
8. **Tasker Mode-B YAML→JSON output + parser** — same multi-line-aware fix; analyze loop now catches BackendError per round (one bad round doesn't kill stage)
9. **Implementer slug-canonicalization** — LLMs invented wrong feature-dir slugs creating ghost specs/ dirs; now (a) `_feature_dir` prefers dirs with tasks.md, (b) `write_artifacts` rewrites `specs/<wrong>/...` → `specs/<canonical>/...`
10. **Sandbox `ensure_venv`** — was no-op when venv created lazily before requirements.txt; now re-runs pip install whenever requirements.txt mtime > last sync
11. **Review-record schema** — was missing `github_authenticated` field; every LLM review was being silently rejected by schema validator
12. **Advancement evaluator** — (a) missing `ReviewerKind` import broke forged-review-blocking path; (b) score-weighted-max routed 6×full_revision + 2×minor_revision to `minor_revision` due to alphabetical tie-break — replaced with weakest-link rule

## What still needs to happen for an actual POSTED paper

1. **Revision loop** (~2 hours per cycle, likely 2-3 cycles needed):
   - research_full_revision → CLARIFIED (auto)
   - Re-Planner (incorporates review feedback)
   - Re-Tasker (analyze loop)
   - Re-Implementer (fixes the 17 broken scripts; needs to read sibling files for API consistency, use real dataset URLs)
   - Re-Reviewers (8 specialists)
   - Repeat until all-accept + threshold met

2. **Paper pipeline** (~3-4 hours):
   - paper_initializer → paper_specifier → paper_clarifier → paper_planner → paper_tasker → paper_implementer → paper_complete
   - paper_implementer dispatches to writing/figure/statistics/lit-search/reference-validator/proofreader/latex-build sub-agents
   - 12 paper specialists must all accept

## Open known issues (not blockers, but improvement areas)

- **Implementer cross-file API consistency** — implementer doesn't read sibling files when writing each task, causing API mismatches. Needs prompt redesign to include relevant existing code in context.
- **Sandbox script path-traversal** — execute:true scripts can write outside project_dir (T005's setup_project.py created a recursive `projects/<wrong-slug>/` ghost dir before the canonicalization fix). Real defense needs Docker chroot.
- **Mode-B analyze loop convergence rate** — 0/5 prior tasker runs converged in <5 rounds. Either reduce TASKER_MAX_REVISION_ROUNDS or accept that "polish loop" is best-effort.
- **Bio query lit_search starvation** — Semantic Scholar 429s aggressively for unauthenticated queries; arxiv has weak bio coverage. PROJ-002 (alt splicing) couldn't get on-topic refs.

## Final commit

`ef0a996` (rebased to `71c2469` on origin/main) — "pipeline: fix 7 structural shortcuts caught by end-to-end PROJ-024 verification"

