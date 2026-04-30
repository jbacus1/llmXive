# Data Model: Bayesian Nonparametrics for Anomaly Detection

## Overview

This document defines the core data entities used throughout the anomaly detection pipeline.

## TimeSeries Entity

### Definition

```python
class TimeSeries:
    """Represents a univariate time series with metadata."""
    
    def __init__(
        self,
        values: np.ndarray,           # Shape (n_observations,)
        timestamps: Optional[np.ndarray] = None,
        metadata: Dict[str, Any] = None,
        source: str = "synthetic"
    ):
        pass
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| values | np.ndarray | Raw time series values |
| timestamps | np.ndarray | Optional timestamps (Unix or datetime) |
| metadata | Dict | Additional metadata (dataset name, etc.) |
| source | str | Data source identifier |

### Validation Rules

1. values must be 1D array of floats
2. timestamps must align with values length if provided
3. No NaN values allowed (must be imputed first)
4. Minimum 10 observations required

## DPGMMModel Entity

### Definition

```python
class DPGMMModel:
    """Dirichlet Process Gaussian Mixture Model for streaming inference."""
    
    def __init__(
        self,
        concentration: float = 1.0,
        mean_prior: float = 0.0,
        variance_prior: float = 1.0,
        max_components: int = 100,
        random_seed: int = 42
    ):
        pass
    
    def update(self, observation: float) -> None:
        """Incremental posterior update for streaming data."""
        pass
    
    def get_anomaly_score(self, observation: float) -> float:
        """Compute negative log posterior probability."""
        pass
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| concentration | float | Dirichlet process concentration parameter (α) |
| mean_prior | float | Prior mean for cluster means |
| variance_prior | float | Prior variance for cluster variances |
| max_components | int | Maximum number of mixture components |
| random_seed | int | Random seed for reproducibility |

### State

The model maintains:
- Cluster means (μ_k)
- Cluster variances (σ²_k)
- Cluster weights (π_k) via stick-breaking
- Total observations processed
- ELBO value for convergence monitoring

## AnomalyScore Entity

### Definition

```python
class AnomalyScore:
    """Anomaly score for a single observation with uncertainty."""
    
    def __init__(
        self,
        value: float,              # The observed value
        score: float,              # Negative log posterior probability
        threshold: float,          # Adaptive threshold
        is_anomaly: bool,          # Binary flag
        uncertainty: float,        # Posterior uncertainty estimate
        timestamp: Optional[float] = None
    ):
        pass
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| value | float | The original observation value |
| score | float | Computed anomaly score |
| threshold | float | Current adaptive threshold |
| is_anomaly | bool | Whether score exceeds threshold |
| uncertainty | float | Variational posterior uncertainty |
| timestamp | float | Optional timestamp |

### Contract Schema

Validated against `specs/001-bayesian-nonparametrics-anomaly-detection/contracts/anomaly_score.schema.yaml`

## EvaluationMetrics Entity

### Definition

```python
class EvaluationMetrics:
    """Comprehensive evaluation metrics for anomaly detection."""
    
    def __init__(
        self,
        precision: float,
        recall: float,
        f1_score: float,
        auc_roc: float,
        auc_pr: float,
        confusion_matrix: np.ndarray,
        threshold_used: float
    ):
        pass
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| precision | float | True positives / (True positives + False positives) |
| recall | float | True positives / (True positives + False negatives) |
| f1_score | float | Harmonic mean of precision and recall |
| auc_roc | float | Area under ROC curve |
| auc_pr | float | Area under Precision-Recall curve |
| confusion_matrix | np.ndarray | 2x2 confusion matrix |
| threshold_used | float | Threshold that produced these metrics |

### Contract Schema

Validated against `specs/001-bayesian-nonparametrics-anomaly-detection/contracts/evaluation_metrics.schema.yaml`

## Data Flow

```
TimeSeries (raw)
    ↓
DPGMMModel.update() (streaming inference)
    ↓
DPGMMModel.get_anomaly_score() (scoring)
    ↓
AnomalyScore (per-observation)
    ↓
EvaluationMetrics (aggregate on test set)
```

## File Locations

| Entity | Implementation Path |
|--------|-------------------|
| TimeSeries | code/models/timeseries.py |
| DPGMMModel | code/models/dpgmm.py |
| AnomalyScore | code/models/anomaly_score.py |
| EvaluationMetrics | code/models/evaluation_metrics.py |

## Version

- Schema version: 1.0.0
- Last updated: Implementation complete - Phase 6 polish
