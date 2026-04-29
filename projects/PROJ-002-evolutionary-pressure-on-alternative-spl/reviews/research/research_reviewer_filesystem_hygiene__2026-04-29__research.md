---
artifact_hash: f2eb4ef2c0528b40a1e794527debea07675dfa225b7e0f203aaa02004972c56e
artifact_path: projects/PROJ-002-evolutionary-pressure-on-alternative-spl/specs/001-evolutionary-pressure-on-alternative-spl/tasks.md
backend: dartmouth
feedback: ''
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-04-29T16:04:50.704384Z'
reviewer_kind: llm
reviewer_name: research_reviewer_filesystem_hygiene
score: 0.0
verdict: minor_revision
---

## Filesystem Hygiene Review

### Structure Violations

**Constitution Principle V (Versioning)** - The current file layout deviates from `plan.md`'s Project Structure specification:

1. **Root-level files vs. `projects/PROJ-002-.../code/`**: Per plan.md, all source code should be under `projects/PROJ-002-evolutionary-pressure-on-alternative-spl/code/`. The code summary shows files at apparent repository root:
   - `pyproject.toml`, `requirements.txt` should be in `code/`
   - `src/` should be `code/src/`
   - `docs/` should be `code/docs/`
   - `config/` should be `code/config/`

2. **Spec location**: plan.md specifies `specs/001-evolutionary-pressure-alternative-splicing/` should contain `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/`. The code summary shows `specs/contracts/` at root level, not nested under the feature directory.

3. **Data directory inconsistency**: data summary reports "(no files)" but code summary lists `data/metadata.yaml` (6604 bytes). This needs reconciliation per Constitution Principle III (Data Hygiene).

### Naming Convention Issues

- Task T008 references `code/specs/contracts/` but plan.md shows `specs/001-evolutionary-pressure-alternative-splicing/contracts/`
- Contract files use `.py` extension (e.g., `alignment_result_contract.py`) but plan.md's contracts section shows `.schema.yaml` convention

### Documentation Currency

- `docs/README.md` exists at root but plan.md specifies documentation should be in `code/docs/`
- Quickstart validation (T053) failed - verify `quickstart.md` location matches plan.md

### Required Actions

1. Restructure to match plan.md: `projects/PROJ-002-.../code/{src,tests,docs,config}`
2. Move `specs/001-evolutionary-pressure-alternative-splicing/` to proper location under `specs/`
3. Reconcile data directory: ensure `data/raw/`, `data/processed/`, `data/metadata.yaml` structure exists
4. Update contract file naming to `.schema.yaml` per plan.md specification

These are structural corrections that do not affect functionality but are required for Constitution Principle compliance.
