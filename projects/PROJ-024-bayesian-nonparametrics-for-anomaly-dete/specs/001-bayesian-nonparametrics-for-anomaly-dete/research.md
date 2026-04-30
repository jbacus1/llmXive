# Research: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Overview

This document provides the literature review and theoretical foundations for implementing
a Dirichlet Process Gaussian Mixture Model (DPGMM) for streaming time series anomaly detection.
This research informs the implementation decisions in subsequent user stories.

---

## 1. Literature Review

### 1.1 Time Series Anomaly Detection Landscape

Time series anomaly detection has evolved through several methodological paradigms:

**Statistical Methods (1970s-1990s)**
- Box-Jenkins ARIMA models [Box & Jenkins, 1976]
- Exponential smoothing and Holt-Winters methods
- Control charts (Shewhart, CUSUM, EWMA) [Montgomery, 2009]
- **Limitations**: Require stationarity, struggle with non-linear patterns, fixed window sizes

**Machine Learning Methods (2000s-2010s)**
- Isolation Forests [Liu et al., 2008]
- Local Outlier Factor (LOF) [Breunig et al., 2000]
- One-Class SVM [Schölkopf et al., 2001]
- **Limitations**: Batch processing, require labeled training data, hyperparameter sensitivity

**Deep Learning Methods (2010s-Present)**
- LSTM-Autoencoders [Malhotra et al., 2015]
- Transformer-based models [Zhou et al., 2021]
- Graph Neural Networks for multivariate series
- **Limitations**: Large data requirements, opaque decision boundaries, high computational cost

**Bayesian Nonparametric Methods (Emerging)**
- Dirichlet Process Mixture Models [Ferguson, 1973]
- Hierarchical DP-GMM for streaming [Heller & Ghahramani, 2005]
- Online variational inference for DPGMM [Gelman et al., 2013]
- **Advantages**: Automatic cluster discovery, uncertainty quantification, streaming-capable

### 1.2 Key Research Papers

| Author/Year | Contribution | Relevance |
|-------------|--------------|-----------|
| Rasmussen (1999) | Infinite Gaussian Mixture Models | Foundation for DPGMM |
| Blei & Jordan (2006) | Variational Inference for DPGMM | ADVI approach |
| Wang et al. (2011) | Streaming Anomaly Detection | Online processing |
| Gopalan et al. (2013) | Streaming DP-GMM | Incremental updates |
| Chandola et al. (2009) | Anomaly Detection Survey | Comprehensive review |
| Blundell et al. (2015) | Weight Uncertainty in Neural Networks | Bayesian uncertainty |

### 1.3 Benchmark Datasets

**NAB (Numenta Anomaly Benchmark)**
- Real-world time series with labeled anomalies
- Includes: CPU utilization, server metrics, traffic data
- URL: https://github.com/numenta/NAB

**UCI Machine Learning Repository**
- Electricity Load Diagrams (2014-2015)
- Traffic (2015)
- PEMS-SF (PeMS Bay Area traffic)

**Yahoo Anomaly Detection Dataset**
- Synthetic and real time series
- 1000+ labeled anomaly cases
- URL: https://webscope.sandbox.yahoo.com

---

## 2. DPGMM Theoretical Foundations

### 2.1 Dirichlet Process (DP)

The Dirichlet Process is a stochastic process used in Bayesian nonparametrics for
clustering with unknown number of components.

**Definition**:
```
G ~ DP(α, H)
```
Where:
- `G` is a random probability distribution
- `α > 0` is the concentration parameter (controls number of clusters)
- `H` is the base distribution (prior over cluster parameters)

**Key Property**:
For any finite partition `A1, A2, ..., Ak` of the sample space:
```
(G(A1), G(A2), ..., G(Ak)) ~ Dirichlet(αH(A1), αH(A2), ..., αH(Ak))
```

### 2.2 Chinese Restaurant Process (CRP)

The CRP provides a constructive definition of the DP:

```
P(customer n sits at table k | previous assignments) =
  { nk / (n-1+α) if k is existing table
  { α / (n-1+α)  if k is a new table
```

Where `nk` is the number of customers already at table `k`.

### 2.3 Stick-Breaking Construction

For computational implementation, we use the stick-breaking representation:

```
πk = βk * Π_{j<k} (1 - βj)
βk ~ Beta(1, α)
```

This generates an infinite sequence of weights `π = {π1, π2, ...}` such that:
```
Σ πk = 1, πk ≥ 0
```

**Truncation**: In practice, we truncate at `K` components where:
```
K = min{K : Σ_{k=1}^K πk ≥ 1 - ε}
```
Typically `ε = 1e-6` and `K ≈ 100` suffices.

### 2.4 Gaussian Mixture Model

For each observation `xn`:
```
zn ~ Categorical(π)                    # cluster assignment
θk ~ H                               # cluster parameters (prior)
xn | zn=k, θk ~ N(μk, Σk)            # likelihood
```

**Conjugate Prior (Normal-Inverse-Wishart)**:
```
μk | Σk ~ N(μ0, Σk/κ0)
Σk ~ IW(Ψ0, ν0)
```

Hyperparameters:
- `μ0`: prior mean (typically 0)
- `κ0`: precision scaling (typically 1)
- `Ψ0`: scale matrix (typically identity)
- `ν0`: degrees of freedom (typically D+1)

### 2.5 Variational Inference (ADVI)

Since exact posterior inference is intractable, we use **Automatic Differentiation
Variational Inference (ADVI)**:

**Variational Objective (ELBO)**:
```
L(φ) = E_q[log p(X, Z, θ)] - E_q[log q(Z, θ)]
     = E_q[log p(X|Z,θ) + log p(Z|π) + log p(π|α) + log p(θ|H)] - E_q[log q(Z,θ)]
```

**Factorized Variational Distribution**:
```
q(Z, π, θ) = q(Z) * q(π) * q(θ)
```

**Coordinate Ascent Updates**:
```
φ_k = E_q[π_k] * E_q[N(x_n | μ_k, Σ_k)] / Σ_j E_q[π_j] * E_q[N(x_n | μ_j, Σ_j)]
```

**Streaming Update** (per observation):
```
For observation x_t:
  1. Compute assignment probabilities: P(z_t = k | x_t, current_params)
  2. Update sufficient statistics for chosen cluster
  3. Recompute cluster parameters incrementally
  4. Optionally create new cluster if P(new) > threshold
```

### 2.6 Anomaly Scoring

**Negative Log Posterior Probability**:
```
score(x_t) = -log p(x_t | x_1:t-1, model)
           = -log Σ_k P(z_t=k | x_1:t-1) * N(x_t | μ_k, Σ_k)
```

**Uncertainty Quantification**:
```
Var[score(x_t)] = E_q[score(x_t)^2] - E_q[score(x_t)]^2
```

**Confidence Intervals**:
```
CI_95% = [μ_score - 1.96*σ_score, μ_score + 1.96*σ_score]
```

---

## 3. Implementation Considerations

### 3.1 Numerical Stability

**Log-Sum-Exp Trick**:
```
log(Σ exp(x_i)) = m + log(Σ exp(x_i - m)) where m = max(x_i)
```

**Covariance Regularization**:
```
Σ_k = Σ_k + λ*I  where λ = 1e-6 (small jitter)
```

**Low-Variance Handling**:
```python
if var < threshold:
    var = threshold  # floor variance to prevent numerical issues
```

### 3.2 Memory Efficiency

**Sufficient Statistics Only**:
```python
# Store only: n_k, sum_x, sum_xx for each cluster
# Do not store individual observations
```

**Truncated Stick-Breaking**:
```python
K_max = 100  # Hard limit on clusters
active_clusters = sum(π_k > ε for π_k in weights)
```

### 3.3 Streaming Constraints

**Single-Pass Processing**:
- Process each observation once
- Update parameters incrementally
- No retraining on historical data

**Bounded Latency**:
```python
# O(K) per observation where K = active clusters
# K typically < 20 for time series
```

---

## 4. Edge Cases & Mitigations

| Edge Case | Detection | Mitigation |
|-----------|-----------|------------|
| Low variance time series | var < 1e-8 | Add jitter to covariance |
| Missing values | NaN in input | Interpolate or skip observation |
| Too many clusters | K > K_max | Merge similar clusters |
| Too few clusters | All π_k concentrated | Increase α concentration |
| Numerical overflow | log_prob = -inf | Clip to [-1e10, 1e10] |
| Cluster collapse | n_k = 0 for cluster | Remove inactive cluster |

---

## 5. Validation Strategy

### 5.1 Synthetic Data

Generate time series with known anomalies:
```python
# Normal: x_t ~ N(μ, σ^2)
# Anomaly: x_t ~ N(μ + δ, σ^2) where δ >> σ
```

**Ground Truth**:
- Anomaly positions are known
- Compute precision/recall against ground truth

### 5.2 Real Dataset Validation

**NAB Benchmark**:
- Run on all NAB datasets
- Compare F1-score to baseline methods
- Verify streaming capability

**UCI Datasets**:
- Electricity Load Diagrams
- Traffic data
- PEMS-SF

---

## 6. References

1. Ferguson, T. S. (1973). A Bayesian analysis of some nonparametric problems. *Annals of Statistics*.
2. Rasmussen, C. E. (1999). The infinite Gaussian mixture model. *NeurIPS*.
3. Blei, D. M., & Jordan, M. I. (2006). Variational inference for Dirichlet process mixtures. *Bayesian Analysis*.
4. Gelman, A., et al. (2013). *Bayesian Data Analysis* (3rd ed.). Chapman & Hall.
5. Chandola, V., Banerjee, A., & Kumar, V. (2009). Anomaly detection: A survey. *ACM Computing Surveys*.
6. Gopalan, P., et al. (2013). Streaming variational Bayes. *NeurIPS*.
7. Blundell, C., et al. (2015). Weight uncertainty in neural networks. *ICML*.

---

## 7. Appendix: Mathematical Notation

| Symbol | Meaning |
|--------|---------|
| `α` | Concentration parameter |
| `π` | Mixture weights |
| `θ_k` | Parameters of cluster k |
| `μ_k` | Mean of cluster k |
| `Σ_k` | Covariance of cluster k |
| `x_t` | Observation at time t |
| `z_t` | Latent cluster assignment |
| `q(·)` | Variational distribution |
| `p(·)` | True posterior |

---

*Last updated: 2024*
*Document version: 1.0*
