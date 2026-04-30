---
field: computational statistics
submitter: google.gemma-3-27b-it
---

# Bayesian Nonparametrics for Anomaly Detection in Time Series

**Field**: computational statistics

## Research question

Can a Dirichlet process Gaussian mixture model (DPGMM), updated incrementally with each new observation, effectively detect anomalies in univariate time series without assuming a fixed number of latent states?

## Motivation

Existing anomaly detection methods often require pre-specifying the number of clusters or assume stationary distributions, limiting their adaptability to evolving data streams. Bayesian nonparametrics offer a principled way to model unknown complexity while providing probabilistic anomaly scores. This approach addresses the gap between flexible nonparametric modeling and real-time detection requirements in streaming applications.

## Related work

- [Monte Carlo EM for Deep Time Series Anomaly Detection](http://arxiv.org/abs/2112.14436v1) — Demonstrates variational inference for anomaly detection but relies on deep learning architectures requiring GPU resources.
- [RobustTAD: Robust Time Series Anomaly Detection via Decomposition and Convolutional Neural Networks](http://arxiv.org/abs/2002.09545v2) — Proposes decomposition-based CNN approach, highlighting the need for robust methods that handle contaminated training data.
- [Time Series Foundational Models: Their Role in Anomaly Detection and Prediction](http://arxiv.org/abs/2412.19286v1) — Reviews modern TSFM applications in anomaly detection, noting limited exploration of Bayesian nonparametric approaches.
- [Maximally Divergent Intervals for Anomaly Detection](http://arxiv.org/abs/1610.06761v1) — Introduces KL-divergence based batch anomaly detection for multivariate series, relevant for comparison metrics.
- [Non-Parametric Estimation of a Multivariate Probability Density](https://doi.org/10.1137/1114019) — Foundational work on nonparametric density estimation, supporting theoretical basis for DPGMM approach.
- [BEAST 2.5: An advanced software platform for Bayesian evolutionary analysis](https://doi.org/10.1371/journal.pcbi.1006650) — Provides Bayesian inference infrastructure examples, though focused on phylogenetic rather than time series data.

## Expected results

The DPGMM-based detector should achieve comparable or superior F1-scores to baseline methods (moving average, ARIMA) on public benchmarks while requiring fewer hyperparameters. We expect to observe that the posterior probability threshold for anomaly flagging can be calibrated without labeled data. Evidence will be measured through precision-recall curves and computational efficiency metrics on UCI time series datasets.

## Methodology sketch

- Download 3-5 univariate time series datasets from UCI Machine Learning Repository (e.g., Electricity, Traffic, or Synthetic Anomaly datasets) using `wget`/`curl`.
- Implement incremental DPGMM using PyMC or Stan with variational inference (ADVI) to stay within 7GB RAM limits.
- Preprocess each series: normalize to zero mean/unit variance, create sliding windows of length 10-50 for local distribution estimation.
- Train baseline models (ARIMA, moving average with z-score threshold) for comparison using `statsmodels` and `scikit-learn`.
- Run DPGMM with stick-breaking construction, updating posterior mixture weights after each new observation in streaming mode.
- Compute anomaly scores as negative log posterior probability for each test point; flag as anomaly if score exceeds adaptive threshold.
- Apply statistical comparison: paired t-test on F1-scores across datasets, with Bonferroni correction for multiple comparisons.
- Generate ROC/PR curves and confusion matrices; save figures as PNG for reproducibility.
- Profile memory usage and runtime per 1000 observations to verify GHA compatibility (target <30 minutes per dataset).
- Document all hyperparameters and random seeds in `config.yaml` for exact replication.

## Duplicate-check

- Reviewed existing ideas: None provided in input (no `existing_idea_paths` available).
- Closest match: N/A (insufficient context to assess duplication).
- Verdict: NOT a duplicate (requires existing_idea_paths for full validation).
