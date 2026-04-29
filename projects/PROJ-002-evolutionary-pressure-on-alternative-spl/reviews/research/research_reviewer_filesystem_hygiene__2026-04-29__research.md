---
artifact_hash: 2160977a67c773f0fd9bc73a632f777b1efa924bfe2828c8ac12d265304ce048
artifact_path: projects/PROJ-002-evolutionary-pressure-on-alternative-spl/specs/001-evolutionary-pressure-on-alternative-spl/tasks.md
backend: dartmouth
feedback: ''
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-04-29T17:12:03.856717Z'
reviewer_kind: llm
reviewer_name: research_reviewer_filesystem_hygiene
score: 0.0
verdict: minor_revision
---

## Filesystem Hygiene Review

### Critical Violations Per Constitution Principle V

The current repository structure violates plan.md specifications and Constitution Principle V in multiple ways:

**1. Root-Level Code Artifacts (T066, T067)**
- `pyproject.toml` exists at root but should be `code/pyproject.toml`
- `requirements.txt` exists at root but should be `code/requirements.txt`
These files must be relocated per Phase 8 revision tasks.

**2. Source Code Location (T068)**
- `src/` directory exists at root level
- Per plan.md, all source code must be under `code/src/`
- Current paths like `src/acquisition/sra_downloader.py` violate the specification

**3. Documentation Location (T069)**
- `docs/` exists at root with `docs/API.md`, `docs/README.md`, etc.
- Should be relocated to `code/docs/` per plan.md structure

**4. Configuration Location (T070)**
- `config/logging.yaml` at root should move to `code/config/`

**5. Contract Specification Location (T071, T072)**
- `specs/contracts/*.py` files exist but should be:
  - Relocated to `specs/001-evolutionary-pressure-alternative-splicing/contracts/`
  - Renamed from `.py` to `.schema.yaml` per plan.md specification

**6. Data Directory Structure (T073, T074, T075)**
- `metadata.yaml` location unclear (should be `data/metadata.yaml` or `code/data/metadata.yaml`)
- `data/raw/example.csv` exists but `data/raw/` directory structure needs explicit creation
- `data/results/psi_stats.json` exists but `data/processed/` directory should be created

### Documentation Currency Issues

- `docs/README.md` (2686 bytes) at root should be moved and potentially consolidated
- `paper/results.md` referenced in T087 but not present in file listing
- `paper/figures/` directory structure referenced but not created

### Recommendation

Complete Phase 8 revision tasks (T066-T075) before proceeding. The filesystem structure currently blocks proper version control, reproducibility, and compliance with Constitution Principle V. After relocation, verify all import paths in code update accordingly.
