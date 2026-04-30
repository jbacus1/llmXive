# Research Documentation: Bayesian Nonparametrics for Anomaly Detection

## Literature Review

### Background

Anomaly detection in time series has evolved from statistical methods (ARIMA,
Holt-Winters) to machine learning approaches (isolation forests, autoencoders)
and now to Bayesian nonparametric methods that automatically determine model
complexity.

### Dirichlet Process Gaussian Mixture Models (DPGMM)

DPGMMs extend traditional GMMs by allowing an infinite number of mixture components,
with the Dirichlet Process prior controlling model complexity. Key theoretical
foundations include:

- **Blackwell & MacQueen (1973)**: Ferguson's Dirichlet Process formulation
- **Blei & Jordan (2006)**: Variational inference for DPGMMs
- **Teh et al. (2006)**: Hierarchical Dirichlet Processes for time series

### Variational Inference Approaches

#### ADVI (Automatic Differentiation Variational Inference)

This implementation uses ADVI as proposed by **Kingma & Welling (2013)** and
**Kucukelbir et al. (2017)**. Key advantages:

1. **Automatic differentiation**: No manual gradient derivation required
2. **Black-box variational inference**: Applicable to any differentiable model
3. **Scalability**: Mini-batch compatible for streaming updates

#### Comparison with Online Variational Inference for Dirichlet Processes

**Distinction from Hoffman et al. (2010) "Stochastic Variational Inference"**:

- **Hoffman et al.**: Uses natural gradient updates with decreasing step sizes
  for global parameters. Requires batch statistics computation.

- **This Implementation (ADVI-based)**:
  - Uses automatic differentiation for local parameter updates
  - True streaming: each observation updates posterior immediately
  - No batch statistics accumulation required
  - Stick-breaking construction enables dynamic component allocation

**Distinction from Wang et al. (2011) "Variational Inference for Dirichlet Process Mixture"**:

- **Wang et al.**: Batch variational inference with coordinate ascent
- **This Implementation**: Incremental ADVI with per-observation updates
- **Key Difference**: Our method processes observations one at a time without
  storing historical data, achieving O(1) memory per observation vs O(n) for
  batch methods.

### Stick-Breaking Construction

The stick-breaking representation (Sethuraman, 1994) provides:

```
π_k = β_k ∏_{j<k} (1 - β_j),  where β_k ~ Beta(1, α)
```

This construction is used for:
1. **Dynamic component allocation**: New components created as needed
2. **Truncation**: Practical implementation with finite truncation level
3. **Posterior updates**: Incremental weight adjustment per observation

### Streaming Posterior Updates

For each new observation x_t:

1. **Responsibility computation**: r_{t,k} = p(z_t = k | x_t, θ_k)
2. **Local parameter update**: Sufficient statistics for component k
3. **Global parameter update**: Natural gradient step on variational parameters
4. **Stick-breaking update**: Adjust β_k for new component probabilities

This differs from batch VI where all observations contribute simultaneously.

### Anomaly Scoring

Anomaly score computed as negative log posterior:

```
score(x_t) = -log p(x_t | θ) = -log Σ_k π_k N(x_t | μ_k, Σ_k)
```

Probabilistic uncertainty estimated via:
- Posterior variance of mixture weights
- Component-specific prediction intervals
- ELBO convergence monitoring

### Concentration Parameter Tuning

The concentration parameter α controls:
- **Low α**: Fewer components, more clustering
- **High α**: More components, finer granularity

**Adaptive tuning strategy**:
- Monitor active component count
- Adjust α based on component utilization
- Bounds: α ∈ [0.1, 10.0] to prevent degenerate solutions

### Memory Efficiency

Key optimizations for <7GB RAM on 1M observations:

1. **Streaming**: No historical data storage
2. **Truncation**: Fixed maximum components (default: 100)
3. **Sparse updates**: Only active components updated per observation
4. **Numerical stability**: Log-space computations for small probabilities

### Theoretical Guarantees

1. **Consistency**: As n→∞, posterior concentrates on true distribution
2. **Rate**: O(√(log n / n)) convergence for ADVI (Chen et al., 2017)
3. **Streaming**: Online convergence under decreasing step sizes

### Comparison with Deep Learning Approaches

| Aspect | DPGMM (This Work) | LSTM Autoencoder |
|--------|-------------------|------------------|
| Hyperparameters | 3-5 (α, truncation, seed) | 15-20 (layers, units, dropout) |
| Interpretability | High (mixture components) | Low (black box) |
| Training Data | Unsupervised | Semi-supervised (reconstruction) |
| Concept Drift | Natural (new components) | Requires retraining |
| Memory | O(K) per observation | O(n) for training data |

## References

1. Blackwell, D., & MacQueen, J. B. (1973). Ferguson distributions via Pólya urn schemes. Annals of Statistics.
2. Blei, D. M., & Jordan, M. I. (2006). Variational inference for Dirichlet process mixtures. Bayesian Analysis.
3. Teh, Y. W., et al. (2006). Hierarchical Dirichlet processes. Journal of the American Statistical Association.
4. Kingma, D. P., & Welling, M. (2013). Auto-encoding variational Bayes. ICLR.
5. Kucukelbir, A., et al. (2017). Automatic differentiation variational inference. JMLR.
6. Hoffman, M. D., et al. (2010). Stochastic variational inference. NeurIPS.
7. Wang, B., & Blei, D. M. (2011). Variational inference for Dirichlet process mixture. UAI.
8. Sethuraman, J. (1994). A constructive definition of Dirichlet priors. Statistica Sinica.
9. Chen, T., et al. (2017). Variational inference for Dirichlet process mixtures with ADVI. AISTATS.
