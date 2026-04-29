---
artifact_hash: 2160977a67c773f0fd9bc73a632f777b1efa924bfe2828c8ac12d265304ce048
artifact_path: projects/PROJ-002-evolutionary-pressure-on-alternative-spl/specs/001-evolutionary-pressure-on-alternative-spl/tasks.md
backend: dartmouth
feedback: ''
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-04-29T17:11:36.345917Z'
reviewer_kind: llm
reviewer_name: research_reviewer_data_quality_research
score: 0.0
verdict: minor_revision
---

The current data artifacts show significant gaps regarding provenance, schema, and sample adequacy. Per `tasks.md` T088, actual RNA-seq data for four primate species must be downloaded, yet `data summary` only lists `data/raw/example.csv` (2734 bytes), which appears to be the placeholder from T083. Without the primary research dataset, sample-size adequacy and mapping rate thresholds (Spec SC-001) cannot be verified. The `data/results/psi_stats.json` (87 bytes) indicates insufficient data volume for evolutionary analysis.

Schema compliance is incomplete. `tasks.md` T072 mandates renaming contract files to `.schema.yaml`, but `code summary` shows `specs/contracts/*.py`. This hinders automated schema validation of incoming data pipelines. Additionally, `data/metadata.yaml` exists, but T073 requires reconciliation with Constitution Principle III regarding location.

Integrity controls are planned (T006 checksum utilities) but unverified. `spec.md` requires SHA-256 checksums for all artifacts. Ensure all intermediate BAM files and final results are checksummed. Reproducibility is at risk; T009 requires random seeds, and T057 requires an audit trail in `state/projects/`, yet `data summary` shows no state directory contents. Version control for data is critical. T057 mentions an audit trail, but `state/` contents are not listed. Ensure `state/projects/PROJ-002...yaml` records dataset versions and download timestamps.

Missing data handling is noted in T046 (phyloP scores), but no evidence of implementation in `src/analysis/phylo_extractor.py` is visible. Finally, data licensing for SRA downloads (T017) is not documented in `spec.md` or `data/metadata.yaml`. Ensure SRA terms of use are recorded for provenance.

To proceed, populate `data/raw/` with the 4-species RNA-seq dataset, convert contracts to YAML schemas, document license/checksums in the metadata registry, and verify the state audit trail captures data versioning. Until the actual research data is ingested and validated against the schema, data quality cannot be assured.
