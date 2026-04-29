---
artifact_hash: ca3860d497f97ae4db973147b309aa663ae91da71386597c32dafccc6ecc1a17
artifact_path: projects/PROJ-002-evolutionary-pressure-on-alternative-spl/paper/specs/001-paper/tasks.md
backend: dartmouth
feedback: ''
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-04-29T17:38:11.204848Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: full_revision
---

## Data Quality Review

This manuscript has fundamental data quality issues that prevent acceptance in its current state.

### 1. Data Provenance Mismatch (Critical)
Section 2 (Methods, lines 21-24) explicitly states the dataset is "scikit-learn iris.csv as a stand-in for splice-junction PSI values." However, the title (lines 1-8) claims "Evolutionary Pressure on Alternative Splicing in Primates" — a biological claim unsupported by the actual data used. The iris dataset is a generic ML benchmark with no biological relationship to primate splicing. This represents a critical provenance failure: the data does not match the scientific question posed.

### 2. Missing Dataset Citation and License (Lines 49-53)
Section 5 (References) states "None at this stage." The iris dataset has a well-known source and license (typically CC0 or BSD), but neither is documented. Per data quality standards, all datasets must include:
- Source URL/DOI
- License information
- Access date

### 3. Schema Documentation Absent
No schema is documented for the proxy data. While statistics are reported (n=150, mean=3.758), there is no column definition, data type specification, or validation of the PSI proxy mapping. Lines 31-33 report descriptive statistics without explaining how iris features map to PSI values.

### 4. No Missing-Data Handling Protocol
The Methods section (lines 21-27) describes data download and analysis but omits any missing-data handling procedures. For reproducibility, this must be documented.

### 5. External Source Link Rot Risk
Figure references (lines 35-45) point to `../figures/fig1_psi_hist.png` and `../figures/fig2_psi_vs_coverage.png` with no versioning or archival information. No DOI or persistent identifier is provided for these artifacts.

### Required Revisions
1. Either replace iris.csv with actual biological splicing data (GTEx, SRA, etc.) with proper provenance, OR
2. Revise title/abstract to accurately reflect the methodological validation nature and explicitly state the proxy dataset limitation

Until data provenance and licensing are properly documented, this review cannot proceed further.
