# Research: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Overview

This research investigates whether a Dirichlet Process Gaussian Mixture Model (DPGMM), updated incrementally with each new observation, can effectively detect anomalies in univariate time series without assuming a fixed number of latent states.

## Background

### Bayesian Nonparametrics

Bayesian nonparametric methods allow the model complexity to grow with the data. The Dirichlet Process (DP) serves as a prior over probability distributions, enabling infinite mixture models where the number of components is inferred from the data rather than fixed a priori.

### Stick-Breaking Construction

The stick-breaking construction provides a constructive representation of the Dirichlet Process. Given concentration parameter α, mixture weights are generated as:

- v_k ~ Beta(1, α) for k = 1, 2, ...
- π_k = v_k * ∏_{j<k} (1 - v_j)

This allows incremental updates as new observations arrive.

### Variational Inference (ADVI)

Automatic Differentiation Variational Inference (ADVI) approximates the posterior distribution using optimization rather than sampling. This enables:
- Streaming updates without full batch retraining
- Memory-efficient inference suitable for 7GB RAM constraint
- Faster convergence compared to MCMC for large datasets

## Dataset Strategy

| Dataset Name | Source | Fetch Method | Expected Size | Anomaly Labels |
|--------------|--------|--------------|---------------|----------------|
| UCI Electricity | UCI Machine Learning Repository | ucimlrepo package (load_dataset) | ~45,000 observations | No (unsupervised) |
| UCI Traffic | UCI Machine Learning Repository | ucimlrepo package (load_dataset) | ~17,500 observations | No (unsupervised) |
| UCI PEMS-SF | UCI Machine Learning Repository | ucimlrepo package (load_dataset) | ~35,000 observations | No (unsupervised) |
| NAB RealKnownCause | Numenta Anomaly Benchmark | https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/ | Variable | Yes (labeled) |

**Dataset Selection Rationale**: Per spec requirement for UCI datasets, we prioritize Electricity, Traffic, and PEMS-SF. The ucimlrepo Python package provides programmatic access to UCI datasets without requiring browser navigation. NAB benchmark included as fallback with stable raw URLs for labeled anomaly evaluation.

**Data Hygiene Compliance**: All downloaded datasets will be checksummed and stored in data/raw/. Processed derivatives written to data/processed/ with documented derivation in data-model.md.

## Baseline Methods

### ARIMA Baseline

- Autoregressive Integrated Moving Average model
- Configured with p, d, q parameters
- Anomaly detection via residual analysis (z-score on prediction errors)
- Hyperparameters: p, d, q (3 tunable parameters)

### Moving Average with Z-Score Baseline

- Simple moving average for trend estimation
- Z-score computed on residuals
- Threshold at 3 standard deviations (configurable)
- Hyperparameters: window_size, threshold (2 tunable parameters)

### DPGMM (Proposed Method)

- Dirichlet Process Gaussian Mixture with stick-breaking construction
- ADVI variational inference for streaming updates
- Anomaly score: negative log posterior probability
- Hyperparameters: concentration parameter α, max_components (2 tunable parameters)

**Hyperparameter Reduction Goal**: DPGMM requires at least 30% fewer tunable parameters than baselines (SC-004).

## Research Questions

1. **RQ-1**: Does the incremental DPGMM achieve comparable F1-scores to ARIMA and moving average baselines on UCI datasets? (Target: within 5% per SC-001)

2. **RQ-2**: Does the memory-efficient ADVI implementation maintain <7GB RAM usage during streaming processing? (SC-002)

3. **RQ-3**: Can adaptive threshold calibration produce reasonable anomaly rates without labeled data? (User Story 3)

4. **RQ-4**: How sensitive are results to the Dirichlet process concentration parameter prior? (Constitution Principle VII)

## Computational Task Ordering

Per computational task ordering requirements, phases MUST be ordered as follows:

1. **Phase 1**: Download all datasets (ucimlrepo or NAB raw URLs)
2. **Phase 2**: Preprocess and checksum datasets (data hygiene)
3. **Phase 3**: Fit baseline models (ARIMA, moving average)
4. **Phase 4**: Fit DPGMM with streaming updates
5. **Phase 5**: Generate anomaly scores for all methods
6. **Phase 6**: Compute evaluation metrics (F1, precision, recall, AUC)
7. **Phase 7**: Generate figures (ROC, PR curves) - MUST complete before paper inclusion
8. **Phase 8**: Write paper with figures embedded

## Edge Case Handling

| Edge Case | Mitigation Strategy |
|-----------|---------------------|
| Near-constant variance (numerical instability) | Add numerical jitter to observations; minimum variance floor in Gaussian components |
| Missing values in time series | Forward-fill for streaming assumption; flag missing data in preprocessing |
| Too many/few mixture components | Sensitivity analysis across α values; automatic component pruning based on posterior weights |
| Clustered anomalies (not isolated) | Evaluate sliding window metrics; report both point-wise and cluster-wise detection rates |
| Runtime exceeds 30 minutes | Early stopping on ELBO convergence; reduce max_components; parallelize across datasets in CI |

## Success Metrics

- **SC-001**: F1-score within 5% of baselines on ≥3 UCI datasets
- **SC-002**: Memory <7GB during 1000+ observation processing
- **SC-003**: Runtime <30 minutes per dataset on GitHub Actions
- **SC-004**: ≥30% reduction in tunable parameters vs. baselines
- **SC-005**: Precision-recall curves saved for all datasets
