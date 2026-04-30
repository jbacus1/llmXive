---
artifact_hash: bce6e5aeb10b03c90dc630149075c9976cf4c010ed6426f962e73b36bf7bbc69
artifact_path: projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/specs/001-bayesian-nonparametrics-for-anomaly-dete/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-04-30T18:01:38.218573Z'
reviewer_kind: llm
reviewer_name: research_reviewer_data_quality_research
score: 0.0
verdict: full_revision
---

## Data Quality Review — Critical Provenance and Hygiene Deficits

This review identifies unresolved data quality issues that prevent acceptance. The current state fails to meet the Constitution Principles regarding Data Hygiene (III) and Reproducibility (I), as evidenced by unchecked Phase 7 tasks in `tasks.md`.

### 1. Dataset Provenance & Compliance (T066, T067, T083)
The specification requires three UCI Machine Learning Repository datasets (SC-001). However, `data summary` lists `raw/pems_sf_synthetic.csv`. PEMS-SF is not a UCI dataset (as noted in T066), and the suffix `_synthetic` suggests a workaround rather than a canonical source. Tasks T066 (source third UCI dataset), T067 (document provenance with URLs/access dates), and T083 (document data licenses) remain unchecked (`[ ]`). Without verified UCI sources and explicit license documentation, reproducibility and legal compliance cannot be validated.

### 2. Checksums & Version Control (T068)
Constitution Principle III mandates that every file under `data/` be checksummed. Task T068 (generate and record SHA256 checksums in `state/`) is incomplete. The `state/projects/PROJ-024-...yaml` file must contain hashes for `raw/electricity.csv`, `raw/traffic.csv`, and the third dataset. Currently, the `data/` directory contains raw and processed files without corresponding integrity records in the state artifact.

### 3. Configuration Hygiene (T073)
Task T073 requires reducing `config.yaml` from 11KB to under 2KB. The `code summary` shows `config.yaml` is 11,449 bytes. Derived statistics must be moved to state files; `config.yaml` should only hold hyperparameters, seeds, and paths. This violation impacts reproducibility and violates the code quality/data quality intersection.

### 4. Missing Data Handling (T070)
Edge cases regarding missing values in time series are flagged in `spec.md`. Task T070 (implement missing data handling for streaming updates) is unchecked. Streaming anomaly detection is brittle with missing timestamps; without documented imputation or skip logic, the model may crash or produce biased anomaly scores.

### Required Actions
1.  **Replace PEMS-SF:** Acquire a true UCI dataset (e.g., Synthetic Control Chart) and update `download_datasets.py`.
2.  **Document Provenance:** Create `data-dictionary.md` with exact URLs, licenses, and access dates (T067, T083).
3.  **Record Checksums:** Update `state/` YAML with SHA256 hashes for all `data/raw` files (T068).
4.  **Trim Config:** Move derived stats out of `config.yaml` to meet the 2KB limit (T073).
5.  **Handle Missing Data:** Implement logic for gaps in streaming input (T070).

Until these data hygiene tasks are marked complete and verified, the project cannot proceed to analysis or acceptance.
