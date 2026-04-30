# Data Model Specification

## Entity Definitions

### TimeSeries

Primary entity representing a time-ordered sequence of observations.

```python
@dataclass
class TimeSeries:
    values: np.ndarray           # Shape: (n_observations,)
    timestamps: Optional[np.ndarray]  # Shape: (n_observations,)
    metadata: Dict[str, Any]     # Dataset source, preprocessing info
```

### StreamingObservation

Single observation for streaming processing.

```python
@dataclass
class StreamingObservation:
    value: float
    timestamp: datetime
    is_missing: bool = False
```

### AnomalyScore

Output of anomaly scoring function.

```python
@dataclass
class AnomalyScore:
    score: float                 # Negative log posterior
    timestamp: datetime
    uncertainty: float           # Posterior variance estimate
    component_id: Optional[int]  # Most likely component
```

### DPGMMModel

The Dirichlet Process Gaussian Mixture Model.

```python
@dataclass
class DPGMMModel:
    config: DPGMMConfig
    components: List[GaussianComponent]
    stick_weights: np.ndarray
    concentration: float
```

## Schema Specifications

### Input Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| values | float[] | Yes | Time series observations |
| timestamps | datetime[] | No | Observation timestamps |
| metadata | object | No | Source information |

### Output Schema

| Field | Type | Description |
|-------|------|-------------|
| scores | AnomalyScore[] | Per-observation anomaly scores |
| components | int | Number of active mixture components |
| elbo_history | float[] | ELBO convergence history |

### Configuration Schema (config.yaml)

```yaml
hyperparameters:
  concentration: 1.0          # Dirichlet process concentration
  truncation_level: 100       # Maximum mixture components
  learning_rate: 0.01         # ADVI step size
  random_seed: 42             # Reproducibility

paths:
  raw_data: data/raw/
  processed_data: data/processed/
  models: models/
  logs: logs/

thresholds:
  anomaly_percentile: 95      # Adaptive threshold
  min_observations: 100       # Minimum before scoring
```

## Temporal Split Methodology

### Train/Test Split

To prevent temporal data leakage:

1. **Chronological ordering**: All datasets sorted by timestamp
2. **80/20 split**: First 80% for training, last 20% for testing
3. **No shuffling**: Time order preserved
4. **Gap handling**: Optional 1-observation gap to prevent boundary leakage

### Dataset-Specific Splits

| Dataset | Train Start | Train End | Test Start | Test End |
|---------|-------------|-----------|------------|----------|
| NYC Taxi | 2016-01-01 | 2017-10-31 | 2017-11-01 | 2018-02-28 |
| Electricity | 2011-07-01 | 2014-06-30 | 2014-07-01 | 2014-12-31 |
| Synthetic | 0-800 | 800-1000 | 1000-1200 | 1200-1500 |

### Streaming Deployment

For production streaming:
- **Warm-up period**: First 100 observations (no scoring)
- **Adaptive threshold**: Computed from warm-up scores
- **Continuous update**: Model updates on each observation

## Data Quality Requirements

1. **Missing values**: Handled via imputation or skip (configurable)
2. **Outliers in input**: Pre-filtered via z-score > 10
3. **Timestamp gaps**: Logged but not blocking
4. **Non-numeric values**: Rejected with validation error

## State Management

All data artifacts tracked in `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`:

```yaml
artifacts:
  - path: data/raw/nyc_taxi.csv
    checksum: sha256:abc123...
    created: 2024-01-15T10:30:00Z
    observations: 17256
```

Checksums verified before model training to ensure reproducibility.
