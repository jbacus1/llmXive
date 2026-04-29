---
artifact_hash: e71a494b421df34db64787e5349abe958bd6e8fd7fa3003fb797ce901e76ee79
artifact_path: projects/PROJ-008-psychology-research/specs/001-psychology-research/tasks.md
backend: dartmouth
feedback: ''
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-04-29T16:31:58.907178Z'
reviewer_kind: llm
reviewer_name: research_reviewer_data_quality_research
score: 0.0
verdict: minor_revision
---

## Data Quality Review: Critical Artifacts Missing

### Current State Assessment

**Verdict Justification**: This project cannot be evaluated for data quality because all referenced data artifacts are absent. The `data/` directory is empty, `contracts/` schema files are not present despite being defined in `tasks.md` (T005-T007), and no sample data exists for validation testing.

### Specific Data Quality Gaps

**1. Schema Definitions Missing** (`contracts/` directory)
- `contracts/participant.schema.yaml` (T005): Not created
- `contracts/assessment.schema.yaml` (T006): Not created  
- `contracts/intervention.schema.yaml` (T007): Not created

Without these schemas, I cannot verify:
- Field definitions for demographic data
- Timepoint structure (baseline, post-intervention, follow-up)
- Outcome measure specifications

**2. Sample-Size Documentation**
Plan states 60 participants with 20% oversample (72 total), but no power analysis or sample-size justification exists in `docs/` or `research.md`. Per `plan.md` Constitution Principle II (Verified Accuracy), this requires statistical justification.

**3. Missing-Data Handling Strategy**
No documentation addresses:
- Attrition handling (4 timepoints × 3 timepoints = potential missingness)
- Imputation methods for incomplete assessments
- IRB-compliant data retention policies

**4. Data Provenance & License**
- No license file for research outputs
- Data source provenance unclear (school partnerships referenced but not documented)
- HIPAA/FERPA compliance procedures not specified in `data/` directory structure

**5. Version Control for Schemas**
`plan.md` mentions "Version all contracts; pre-register analysis plan" but no versioning scheme is implemented (e.g., `contracts/v1/`, semantic versioning in filenames).

### Required Actions Before Re-evaluation

1. **Create schema files** in `contracts/` directory (T005-T007)
2. **Document sample-size justification** in `docs/protocol.md` or separate power analysis document
3. **Add missing-data handling section** to `docs/analysis-plan.md`
4. **Create sample data files** in `data/raw/` for validation testing (synthetic, de-identified)
5. **Add LICENSE file** specifying research data usage terms

Until these artifacts exist, data quality review cannot proceed. Other reviewers have already flagged implementation gaps—this data quality review is contingent on those artifacts being created first.
