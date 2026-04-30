# Implementation Plan: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Branch**: `001-bayesian-nonparametrics-anomaly-detection` | **Date**: 2024-01-15 | **Spec**: specs/001-bayesian-nonparametrics-anomaly-detection/spec.md

**Input**: Feature specification from `specs/001-bayesian-nonparametrics-anomaly-detection/spec.md`

## Summary

Implement an incremental Dirichlet Process Gaussian Mixture Model (DPGMM) for streaming anomaly detection in univariate time series. The core innovation is the stick-breaking construction with ADVI variational inference, enabling anomaly scoring without batch retraining. The system compares against ARIMA and moving average baselines on UCI benchmark datasets, with adaptive threshold calibration for unlabeled deployment scenarios.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyMC 5.9.0, NumPy 1.24.0, pandas 2.0.0, scikit-learn 1.3.0, statsmodels 0.14.0, ucimlrepo 0.0.7  
**Storage**: Local filesystem (data/raw, data/processed), config.yaml for hyperparameters  
**Testing**: pytest 7.4.0 with contract tests against YAML schemas  
**Target Platform**: Linux server (GitHub Actions runners)  
**Project Type**: computational research library  
**Performance Goals**: <30 minutes per dataset on CI, <7GB RAM during processing  
**Constraints**: Univariate time series only, no multivariate extensions, streaming update after each observation  
**Scale/Scope**: 3-5 UCI datasets, 1000+ observations per dataset, F1-score within 5% of baselines

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Notes |
|-----------|-------------------|---------------------|
| I. Reproducibility (NON-NEGOTIABLE) | COMPLIANT | Random seeds pinned in config.yaml. External datasets fetched via ucimlrepo package from canonical UCI sources on every run. requirements.txt pins all dependencies. |
| II. Verified Accuracy | COMPLIANT | All citations in research.md and paper artifacts will be verified by Reference-Validator Agent before review points are awarded. Title-token-overlap threshold ≥ 0.7 enforced. |
| III. Data Hygiene | COMPLIANT | Every file under data/ is checksummed in state artifact_hashes map. Raw data preserved unchanged; derivations written to new filenames. PII scan enforced. |
| IV. Single Source of Truth | COMPLIANT | Every figure, statistic, or interpretation in paper traces to exactly one row in data/ and one block in code/. Derived numbers NOT hand-typed. |
| V. Versioning Discipline | COMPLIANT | Every artifact carries content hash. State updated_at timestamp refreshed on artifact changes. |
| VI. Numerical Stability & Convergence | COMPLIANT | ADVI convergence diagnostics (ELBO convergence) reported in code/. Models failing convergence criteria within iteration limits marked invalid for review. |
| VII. Prior Sensitivity Analysis | COMPLIANT | Dirichlet process concentration parameter varied in sensitivity analysis. Results claimed as robust hold across reasonable prior specifications documented in paper/. |

## Project Structure

### Documentation (this feature)

```text
specs/001-bayesian-nonparametrics-anomaly-detection/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── dataset.schema.yaml
│   ├── anomaly_score.schema.yaml
│   └── evaluation_metrics.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/
├── code/
│   ├── requirements.txt
│   ├── config.yaml
│   ├── src/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── dpgmm.py
│   │   │   └── baselines.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── anomaly_detector.py
│   │   │   └── threshold_calibrator.py
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   └── downloaders.py
│   │   └── evaluation/
│   │       ├── __init__.py
│   │       ├── metrics.py
│   │       └── visualizations.py
│   └── tests/
│       ├── contract/
│       │   ├── test_dataset_schema.py
│       │   ├── test_anomaly_score_schema.py
│       │   └── test_evaluation_metrics_schema.py
│       ├── unit/
│       │   ├── test_dpgmm.py
│       │   └── test_threshold_calibrator.py
│       └── integration/
│           └── test_full_pipeline.py
├── data/
│   ├── raw/
│   │   ├── electricity/
│   │   ├── traffic/
│   │   └── pems_sf/
│   └── processed/
│       └── [dataset_name]_processed.csv
└── state/
    └── projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml
```

**Structure Decision**: Single project structure (Option 1) selected because this is a computational research library with no frontend/backend separation. All code under `code/src/` follows standard Python package layout with clear separation between models, services, data, and evaluation. Tests organized by type (contract, unit, integration) to support the contract validation requirements.

## Complexity Tracking

> **No violations requiring justification**

All seven constitution principles are satisfied without requiring additional complexity. The single-project structure minimizes overhead while maintaining clear separation of concerns. ADVI variational inference chosen over MCMC for memory efficiency (FR-005 constraint).
