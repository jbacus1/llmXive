# Data Model Specification

**Project**: Bayesian Nonparametrics for Anomaly Detection in Time Series
**Version**: 1.0.0
**Status**: Phase 0 Design Artifact
**Last Updated**: 2024

---

## Overview

This document defines the core data entities, their relationships, and schema specifications
for the Bayesian Nonparametrics Anomaly Detection system. It serves as the canonical reference
for all data structures used throughout the implementation.

---

## Core Entities

### 1. TimeSeries

**Purpose**: Represents a univariate or multivariate time series observation sequence.

**Location**: `code/models/time_series.py`

```python
@dataclass
class TimeSeries:
    """Core time series data structure."""
    name: str                              # Unique identifier for the series
    timestamps: np.ndarray                 # Shape: (n_observations,) float64
    values: np.ndarray                     # Shape: (n_observations, n_features) float64
    metadata: Dict[str, Any]               # Optional metadata (source, collection_method, etc.)
    is_multivariate: bool = False          # True if n_features > 1
    
    @property
    def n_observations(self) -> int:
        """Return number of observations in the series."""
        return len(self.timestamps)
    
    @property
    def n_features(self) -> int:
        """Return number of features per observation."""
        return self.values.shape[1] if len(self.values.shape) > 1 else 1
```

**Validation Rules**:
- `timestamps` must be strictly monotonically increasing
- `values` must have matching length to `timestamps`
- Missing values should be represented as `np.nan`

---

### 2. AnomalyScore

**Purpose**: Represents the anomaly score for a single observation with uncertainty estimates.

**Location**: `code/models/anomaly_score.py`

```python
@dataclass
class AnomalyScore:
    """Anomaly score with probabilistic uncertainty."""
    timestamp: float                       # Timestamp of the scored observation
    score: float                           # Negative log posterior probability
    uncertainty: float                     # Variance of the score estimate
    mixture_weights: np.ndarray            # Shape: (n_components,) - posterior weights
    component_assignments: np.ndarray      # Shape: (n_components,) - responsibility
    is_anomaly: bool                       # Flagged as anomaly based on threshold
    threshold: float                       # Threshold used for flagging
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON export."""
        return {
            'timestamp': self.timestamp,
            'score': self.score,
            'uncertainty': self.uncertainty,
            'mixture_weights': self.mixture_weights.tolist(),
            'component_assignments': self.component_assignments.tolist(),
            'is_anomaly': self.is_anomaly,
            'threshold': self.threshold
        }
```

**Validation Rules**:
- `score` must be >= 0 (negative log probability)
- `uncertainty` must be >= 0
- `mixture_weights` must sum to 1.0

---

### 3. DPGMMModel

**Purpose**: Dirichlet Process Gaussian Mixture Model with streaming inference.

**Location**: `code/models/dp_gmm.py`

```python
@dataclass
class DPGMMModel:
    """DPGMM model state for streaming anomaly detection."""
    # Core parameters
    alpha: float                           # Concentration parameter (Dirichlet process)
    n_components: int                      # Current number of active components
    max_components: int                    # Upper bound on components
    
    # Component parameters (for each component k)
    means: np.ndarray                      # Shape: (n_components, n_features)
    covariances: np.ndarray                # Shape: (n_components, n_features, n_features)
    precision_matrices: np.ndarray         # Shape: (n_components, n_features, n_features)
    
    # Mixture weights (stick-breaking construction)
    beta: np.ndarray                       # Shape: (max_components,) - stick-breaking weights
    pi: np.ndarray                         # Shape: (n_components,) - effective mixture weights
    
    # Variational inference state
    variational_params: Dict[str, np.ndarray]  # ADVI parameters
    elbo_history: List[float]              # ELBO values per iteration
    
    # Hyperparameters
    prior_mean: np.ndarray                 # Shape: (n_features,)
    prior_covariance: np.ndarray           # Shape: (n_features, n_features)
    concentration_prior: float             # Prior on alpha
    
    # State tracking
    n_observations_seen: int               # Total observations processed
    is_fitted: bool                        # Whether model has seen enough data
    
    def get_component_count(self) -> int:
        """Return current active component count."""
        return self.n_components
```

**Validation Rules**:
- `covariances` must be positive definite
- `pi` must sum to 1.0
- `alpha` must be > 0

---

### 4. EvaluationMetrics

**Purpose**: Aggregated evaluation metrics for model comparison.

**Location**: `code/evaluation/metrics.py`

```python
@dataclass
class EvaluationMetrics:
    """Evaluation metrics for anomaly detection models."""
    # Classification metrics
    precision: float
    recall: float
    f1_score: float
    auc_roc: float
    auc_pr: float
    
    # Timing metrics
    total_runtime_seconds: float
    observations_per_second: float
    peak_memory_mb: float
    
    # Model complexity
    n_parameters: int
    n_components: int
    
    # Statistical significance
    p_value_vs_baseline: Optional[float]   # From paired t-test
    significant_vs_baseline: Optional[bool]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON export."""
        return {
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'auc_roc': self.auc_roc,
            'auc_pr': self.auc_pr,
            'total_runtime_seconds': self.total_runtime_seconds,
            'observations_per_second': self.observations_per_second,
            'peak_memory_mb': self.peak_memory_mb,
            'n_parameters': self.n_parameters,
            'n_components': self.n_components,
            'p_value_vs_baseline': self.p_value_vs_baseline,
            'significant_vs_baseline': self.significant_vs_baseline
        }
```

---

### 5. ThresholdConfig

**Purpose**: Configuration for anomaly threshold calibration.

**Location**: `code/utils/threshold.py`

```python
@dataclass
class ThresholdConfig:
    """Threshold calibration configuration."""
    method: str                            # 'percentile', 'bayesian', 'adaptive'
    percentile: float                      # For percentile method (e.g., 95.0)
    min_anomaly_rate: float                # Minimum expected anomaly rate
    max_anomaly_rate: float                # Maximum expected anomaly rate
    calibration_window: int                # Number of observations for calibration
    is_labeled: bool                       # Whether calibration data has labels
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        return (0 < self.min_anomaly_rate < self.max_anomaly_rate < 1.0 and
                self.calibration_window > 0)
```

---

## Data Flow Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Raw Dataset    │────▶│ TimeSeries      │────▶│ DPGMMModel      │
│  (CSV/JSON)     │     │ (normalized)    │     │ (streaming)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Evaluation     │◀────│ Evaluation      │◀────│ AnomalyScore    │
│  Metrics        │     │ Pipeline        │     │ (per obs)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## File Storage Schema

### Directory Structure

```
projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/
├── code/
│   ├── config.yaml              # Hyperparameters and paths
│   ├── download_datasets.py     # Dataset fetchers
│   ├── models/
│   │   ├── time_series.py       # TimeSeries entity
│   │   ├── dp_gmm.py            # DPGMMModel implementation
│   │   └── anomaly_score.py     # AnomalyScore entity
│   ├── baselines/
│   │   ├── arima.py             # ARIMA baseline
│   │   └── moving_average.py    # Moving average baseline
│   ├── evaluation/
│   │   ├── metrics.py           # EvaluationMetrics entity
│   │   ├── plots.py             # ROC/PR curve generators
│   │   └── statistical_tests.py # Paired t-tests
│   └── utils/
│       ├── streaming.py         # Streaming utilities
│       ├── threshold.py         # ThresholdConfig and calibration
│       ├── memory_profiler.py   # Memory profiling
│       └── runtime_monitor.py   # Runtime monitoring
├── data/
│   ├── raw/                     # Downloaded raw datasets
│   ├── processed/               # Normalized/processed data
│   └── results/                 # Evaluation outputs
├── tests/
│   ├── contract/                # Schema contract tests
│   ├── integration/             # Integration tests
│   └── unit/                    # Unit tests
└── specs/
    └── 001-bayesian-nonparametrics-anomaly-detection/
        ├── research.md          # Literature review
        ├── data-model.md        # This file
        └── quickstart.md        # Usage examples
```

### Config Schema (`code/config.yaml`)

```yaml
# Hyperparameters
model:
  alpha: 1.0                     # Concentration parameter
  max_components: 100            # Maximum mixture components
  prior_mean: [0.0]              # Prior mean for features
  prior_covariance: [1.0]        # Prior covariance
  
training:
  random_seed: 42                # Reproducibility
  elbo_tolerance: 1e-4           # Convergence threshold
  max_iterations: 1000           # Max ADVI iterations
  
threshold:
  method: percentile             # Calibration method
  percentile: 95.0               # Percentile threshold
  min_anomaly_rate: 0.01         # Min expected anomaly rate
  max_anomaly_rate: 0.10         # Max expected anomaly rate
  
data:
  raw_dir: data/raw/             # Raw dataset storage
  processed_dir: data/processed/ # Processed data storage
  results_dir: data/results/     # Evaluation outputs
  
baselines:
  arima_order: [1, 1, 1]         # ARIMA (p,d,q)
  moving_avg_window: 20          # Window size for MA
  zscore_threshold: 3.0          # Z-score anomaly threshold
```

---

## Relationships

### Entity Relationships

| Entity A | Relationship | Entity B | Cardinality |
|----------|--------------|----------|-------------|
| TimeSeries | contains | AnomalyScore | 1:N |
| DPGMMModel | produces | AnomalyScore | 1:N |
| EvaluationMetrics | summarizes | AnomalyScore | N:1 |
| ThresholdConfig | configures | AnomalyScore | 1:1 |

### State Dependencies

```
DPGMMModel.state → depends on → n_observations_seen
AnomalyScore → depends on → DPGMMModel.state
EvaluationMetrics → depends on → AnomalyScore[]
```

---

## Validation Constraints

### Data Integrity Rules

1. **TimeSeries**:
   - No duplicate timestamps allowed
   - Missing values must be explicitly marked (np.nan)
   - Values must be finite (no inf)

2. **DPGMMModel**:
   - Covariance matrices must remain positive definite
   - Mixture weights must be normalized after each update
   - Component count must not exceed max_components

3. **AnomalyScore**:
   - Scores must be non-negative
   - Uncertainty estimates must be finite
   - is_anomaly flag must match threshold comparison

4. **EvaluationMetrics**:
   - Precision, recall, F1 must be in [0, 1]
   - AUC values must be in [0, 1]
   - Runtime must be positive

---

## Serialization Formats

### JSON Schema for AnomalyScore

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "timestamp": {"type": "number"},
    "score": {"type": "number", "minimum": 0},
    "uncertainty": {"type": "number", "minimum": 0},
    "mixture_weights": {"type": "array", "items": {"type": "number"}},
    "component_assignments": {"type": "array", "items": {"type": "number"}},
    "is_anomaly": {"type": "boolean"},
    "threshold": {"type": "number"}
  },
  "required": ["timestamp", "score", "uncertainty", "is_anomaly", "threshold"]
}
```

### CSV Schema for Results

| Column | Type | Description |
|--------|------|-------------|
| timestamp | float64 | Observation timestamp |
| value | float64 | Observed value |
| score | float64 | Anomaly score |
| is_anomaly | bool | Anomaly flag |
| component | int | Assigned mixture component |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024 | Initial data model specification |

---

## References

- FR-001: DPGMM model with stick-breaking construction
- FR-002: Streaming posterior updates
- FR-003: Anomaly scoring with uncertainty
- FR-004: Threshold calibration without labels
- FR-005: Memory constraints (<7GB RAM)
- FR-006: Evaluation metrics and statistical tests
- FR-007: Hyperparameter configuration
- FR-008: Dataset downloading with validation
- Constitution Principle III: Checksum verification for all artifacts
