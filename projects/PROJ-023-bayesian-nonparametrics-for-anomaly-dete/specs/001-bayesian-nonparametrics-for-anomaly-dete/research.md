# Research: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Objective

Investigate the efficacy of Bayesian Nonparametric models, specifically Gaussian Processes (GP) with Dirichlet Process (DP) mixtures, for detecting distributional shifts in univariate time series data compared to traditional Statistical Process Control (SPC) and deep learning baselines.

## Background & Methodology

### Bayesian Nonparametrics for Time Series
Traditional parametric models assume a fixed number of parameters, which may not capture complex, evolving dynamics in time series. Bayesian Nonparametrics allows the model complexity to grow with the data.
*   **Gaussian Process (GP) Prior**: Provides a flexible prior over functions, capturing temporal correlations without specifying a fixed functional form.
*   **Dirichlet Process (DP) Mixture**: Allows for an infinite mixture of components, enabling the model to infer the number of distinct regimes (normal vs. anomalous) automatically.
*   **Sparse Variational Inference (SVI)**: Selected for computational efficiency. Full MCMC is often too slow for large time series windows. SVI approximates the posterior using a variational distribution optimized via ELBO (Evidence Lower Bound).

### Implementation Choice: NumPyro (JAX)
Per Functional Requirement FR-004, NumPyro is selected over PyMC.
*   **Rationale**: NumPyro leverages JAX for automatic differentiation and XLA compilation, offering superior CPU performance for Sparse Variational Inference. This aligns with the <7GB memory constraint and 6-hour compute limit specified in the feature spec.
*   **Compatibility**: JAX backend ensures efficient sparse GP approximations commonly used in time series Bayesian nonparametrics.

### Baselines
To validate the Bayesian approach, two baselines are required (FR-006):
1.  **Shewhart Control Charts**: Traditional SPC method. Detects shifts when data points fall outside control limits (typically ±3σ). Simple, interpretable, but assumes normality and independence.
2.  **Variational Auto-Encoder (VAE)**: A lightweight deep learning approach. Learns a latent representation of normal data; high reconstruction error indicates anomalies.

## Data Strategy

### Datasets
Three representative UCR Time Series Archive datasets will be used (FR-008):
1.  **ECGFiveDays**: Electrocardiogram data (Medical).
2.  **PowerConsumption**: Energy monitoring (Industrial).
3.  **SyntheticControl**: Manufacturing process control.

### Ground Truth Generation
Since real-world anomaly labels are often unavailable or noisy, synthetic anomalies will be injected (FR-003):
*   **Mean Shift**: 2.5 standard deviations from baseline mean.
*   **Variance Spike**: 3x baseline variance.
*   **Duration**: 5-15 consecutive time points (5-10% of window length).
*   **Rationale**: These magnitudes follow standard practice in anomaly detection research where anomalies must be detectable but not trivial.

## Edge Case Handling

*   **Missing Values (NaNs)**: Preprocessing script will interpolate linearly or forward-fill based on window context, logging all imputations.
*   **High Variance/Memory**: Data will be processed in chunks/windows. If a single dataset exceeds 7GB, subsampling or windowing strategies will be applied to ensure memory constraints are met.
*   **Non-Detectable Shifts**: If synthetic anomalies are too subtle, the model will output low anomaly scores. This will be recorded as a False Negative in evaluation metrics.

## Validation & Metrics

*   **Primary Metrics**: Precision, Recall, F1-Score, AUC-ROC (FR-007).
*   **Statistical Significance**: Paired t-test across datasets to determine if Bayesian method outperforms baselines with p < 0.05 (User Story 3).
*   **Convergence Diagnostics**: R-hat, Effective Sample Size (ESS), ELBO stability must be reported for all Bayesian runs (Constitution Principle VI).
