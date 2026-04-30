# Implementation Plan: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Branch**: `001-bayesian-nonparametrics-anomaly-detection` | **Date**: 2024-01-15 | **Spec**: `specs/001-bayesian-nonparametrics-anomaly-detection/spec.md`
**Input**: Feature specification from `specs/001-bayesian-nonparametrics-anomaly-detection/spec.md`

## Summary

Implement an incremental Dirichlet Process Gaussian Mixture Model (DPGMM) for streaming anomaly detection in univariate time series. The model uses stick-breaking construction with ADVI variational inference to maintain memory under 7GB while processing observations sequentially. Performance will be validated against ARIMA and moving average baselines on UCI Machine Learning Repository datasets, with F1-scores, ROC curves, and PR curves generated for evaluation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pymc>=5.0.0, numpy>=1.24.0, pandas>=2.0.0, scikit-learn>=1.3.0, statsmodels>=0.14.0, matplotlib>=3.7.0, pyyaml>=6.0  
**Storage**: Local filesystem (`data/` for datasets, `code/` for scripts)  
**Testing**: pytest>=7.4.0 with contract tests against YAML schemas  
**Target Platform**: Linux server (GitHub Actions runner)  
**Project Type**: computational research library  
**Performance Goals**: <30 minutes runtime per dataset, <7GB memory during processing  
**Constraints**: Streaming update without batch retraining, no labeled data required for threshold calibration  
**Scale/Scope**: 3-5 univariate time series datasets, 1000+ observations per dataset

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | PASS | Seeds pinned in `config.yaml`; datasets fetched from UCI via wget/curl scripts; `requirements.txt` pins all dependencies |
| II. Verified Accuracy | PASS | All citations from spec.md copied verbatim; no fabricated URLs; Reference-Validator will verify at artifact write time |
| III. Data Hygiene | PASS | Checksums recorded in `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`; raw data preserved unchanged |
| IV. Single Source of Truth | PASS | Figures/statistics trace to `data/` rows and `code/` blocks; no hand-typed numbers in paper |
| V. Versioning Discipline | PASS | Content hashes for artifacts; `updated_at` timestamp updates on changes |
| VI. Numerical Stability & Convergence | PASS | ADVI convergence diagnostics (ELBO) will be logged; models failing criteria marked invalid |
| VII. Prior Sensitivity Analysis | PASS | Concentration parameter will be varied across [0.1, 1.0, 10.0]; results documented in paper |

## Project Structure

### Documentation (this feature)

```text
specs/001-bayesian-nonparametrics-anomaly-detection/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/
├── data/
│   ├── raw/                    # Downloaded UCI datasets (checksummed)
│   └── processed/              # Transformed data (derived files)
├── code/
│   ├── requirements.txt        # Pinned dependencies
│   ├── config.yaml             # Hyperparameters and seeds
│   ├── download_datasets.py    # UCI dataset fetcher
│   ├── models/
│   │   └── dp_gmm.py           # DPGMM implementation
│   ├── baselines/
│   │   ├── arima.py            # ARIMA baseline
│   │   └── moving_average.py   # Moving average z-score baseline
│   ├── evaluation/
│   │   ├── metrics.py          # F1, precision, recall, AUC
│   │   └── plots.py            # ROC/PR curve generators
│   └── utils/
│       ├── streaming.py        # Streaming update utilities
│       └── threshold.py        # Adaptive threshold calibration
├── tests/
│   ├── contract/               # Schema validation tests
│   ├── integration/            # End-to-end pipeline tests
│   └── unit/                   # Model component tests
└── state/
    └── projects/
        └── PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml  # Artifact hashes
```

**Structure Decision**: Single computational research project structure. All code lives under `code/` with clear separation between models, baselines, evaluation, and utilities. Contract tests validate output schemas before evaluation results are accepted.

## Complexity Tracking

> No violations requiring justification. All complexity is necessary for streaming DPGMM implementation and baseline comparison requirements.

## Computational Task Ordering

1. **Phase 0 - Data Acquisition**: Download UCI datasets via `download_datasets.py` (before any modeling)
2. **Phase 1 - Model Training**: Fit DPGMM and baselines on training splits (before evaluation)
3. **Phase 2 - Evaluation**: Compute anomaly scores, F1-scores, ROC/PR metrics (before figure generation)
4. **Phase 3 - Figure Generation**: Save PNG files for ROC/PR curves (before paper inclusion)
5. **Phase 4 - Sensitivity Analysis**: Vary concentration parameter across specified ranges
