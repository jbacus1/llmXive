# Implementation Guide: Bayesian Nonparametrics for Anomaly Detection

## Overview

This document provides comprehensive implementation details for the DPGMM-based anomaly detection system. It covers architecture decisions, component interactions, and usage patterns for all three user stories.

## System Architecture

### High-Level Components

```
code/
├── models/           # Core DPGMM model and data structures
│   ├── dp_gmm.py     # DPGMMModel with stick-breaking construction
│   ├── anomaly_score.py  # AnomalyScore dataclass
│   └── time_series.py    # TimeSeries entity
├── baselines/        # Comparison baselines
│   ├── arima.py      # ARIMA baseline
│   └── moving_average.py  # Moving average + z-score baseline
├── evaluation/       # Metrics and visualization
│   ├── metrics.py    # F1, precision, recall, AUC computation
│   ├── plots.py      # ROC/PR curve generation
│   └── statistical_tests.py  # Paired t-tests with Bonferroni
├── utils/            # Infrastructure utilities
│   ├── streaming.py  # Streaming observation processing
│   ├── threshold.py  # Adaptive threshold calibration
│   ├── memory_profiler.py  # Memory usage monitoring
│   └── runtime_monitor.py  # Runtime budget tracking
├── data/             # Data generation and loading
│   └── synthetic_generator.py  # Synthetic anomaly datasets
└── scripts/          # Runnable verification scripts
    ├── profile_memory_1000_obs.py
    ├── test_advi_inference.py
    ├── test_concentration_tuning.py
    └── test_missing_value_handling.py
```

### Data Flow

1. **Data Ingestion**: `download_datasets.py` fetches UCI/NAB datasets with checksum validation
2. **Streaming Processing**: `utils/streaming.py` provides `StreamingObservation` for sequential updates
3. **Model Training**: `dp_gmm.py` processes observations incrementally with ADVI variational inference
4. **Anomaly Scoring**: Each observation produces `AnomalyScore` with probabilistic uncertainty
5. **Threshold Calibration**: `utils/threshold.py` computes adaptive thresholds without labels
6. **Evaluation**: `evaluation/metrics.py` computes F1, precision, recall, AUC against baselines

## Core Implementation Details

### DPGMMModel (code/models/dp_gmm.py)

The core model implements:

- **Stick-Breaking Construction**: Nonparametric prior over mixture weights
- **ADVI Variational Inference**: Streaming posterior updates per observation
- **ELBO Convergence**: Logging for convergence monitoring (T058)
- **Adaptive Concentration**: Dynamic tuning of Dirichlet process concentration parameter (T025)

Key methods:
```python
def update_posterior(self, observation: StreamingObservation) -> AnomalyScore
def compute_anomaly_score(self, observation: StreamingObservation) -> AnomalyScore
def _update_elbo(self) -> float
def _adaptive_concentration(self) -> None
```

### Streaming Architecture (code/utils/streaming.py)

The streaming pipeline enables memory-efficient processing:

```python
StreamingObservation = {
    "timestamp": datetime,
    "value": float,
    "window_stats": Optional[Dict[str, float]]
}

StreamingObservationProcessor = {
    "process": Callable[[StreamingObservation], AnomalyScore],
    "state": StreamingState
}
```

### Threshold Calibration (code/utils/threshold.py)

Adaptive threshold computation without labeled data:

- **95th Percentile**: Default percentile-based threshold
- **Anomaly Rate Validation**: Ensures rates stay within expected bounds
- **Multi-Dataset Calibration**: Consistent thresholds across datasets

```python
ThresholdResult = {
    "threshold": float,
    "anomaly_rate": float,
    "confidence_interval": Tuple[float, float]
}
```

## User Story Implementation Status

### User Story 1: Core DPGMM (Phase 3)

| Component | Status | File |
|-----------|--------|------|
| Stick-breaking construction | ✅ | dp_gmm.py |
| ADVI variational inference | ✅ | dp_gmm.py |
| Incremental posterior update | ✅ | dp_gmm.py |
| AnomalyScore dataclass | ✅ | anomaly_score.py |
| Memory profiling | ✅ | memory_profiler.py |
| Edge case handling | ✅ | dp_gmm.py |
| Concentration tuning | ✅ | dp_gmm.py |
| Synthetic dataset generator | ✅ | synthetic_generator.py |

### User Story 2: Baseline Comparison (Phase 4)

| Component | Status | File |
|-----------|--------|------|
| ARIMA baseline | ✅ | baselines/arima.py |
| Moving average baseline | ✅ | baselines/moving_average.py |
| Evaluation metrics | ✅ | evaluation/metrics.py |
| ROC/PR curves | ✅ | evaluation/plots.py |
| Statistical tests | ✅ | evaluation/statistical_tests.py |
| Dataset fetchers | ✅ | download_datasets.py |
| Runtime monitoring | ✅ | utils/runtime_monitor.py |
| Hyperparameter counting | ✅ | utils/hyperparameter_counter.py |

### User Story 3: Threshold Calibration (Phase 5)

| Component | Status | File |
|-----------|--------|------|
| Adaptive threshold | ✅ | utils/threshold.py |
| Calibration function | ✅ | utils/threshold.py |
| Anomaly rate validation | ✅ | utils/threshold.py |
| Multi-dataset support | ✅ | utils/threshold.py |

## Configuration

### Hyperparameters (code/config.yaml)

```yaml
dp_gmm:
  concentration_prior: 1.0
  max_components: 100
  elbo_tolerance: 1e-4
  learning_rate: 0.01

streaming:
  window_size: 100
  min_observations: 10

threshold:
  percentile: 95
  anomaly_rate_bounds: [0.01, 0.10]

evaluation:
  datasets:
    - electricity
    - traffic
    - pems_sf
```

## Testing Strategy

### Contract Tests (tests/contract/)

- `test_dp_gmm_schema.py`: Validates DPGMM output schema
- `test_metrics_schema.py`: Validates evaluation metrics schema
- `test_threshold_schema.py`: Validates threshold output schema

### Integration Tests (tests/integration/)

- `test_streaming_update.py`: End-to-end streaming observation updates
- `test_baseline_comparison.py`: Full baseline comparison pipeline
- `test_threshold_calibration.py`: Unlabeled data threshold calibration

### Unit Tests (tests/unit/)

- `test_memory_profile.py`: Verifies <7GB RAM constraint
- Additional edge case tests per user story

## Performance Constraints

| Constraint | Target | Implementation |
|------------|--------|----------------|
| Memory | <7GB | Streaming processing, no batch storage |
| Runtime | <30min/dataset | Runtime monitoring, adaptive updates |
| Parameters | <30% of baselines | Nonparametric prior, no fixed components |

## Running the System

### Quick Start

```bash
# 1. Download datasets
python code/download_datasets.py

# 2. Process synthetic data
python code/scripts/profile_memory_1000_obs.py

# 3. Run baseline comparison
python code/scripts/test_advi_inference.py

# 4. Calibrate thresholds
python code/utils/threshold.py
```

### Verification Scripts

Each script in `code/scripts/` is runnable independently:

- `profile_memory_1000_obs.py`: Memory profiling
- `test_advi_inference.py`: ADVI convergence testing
- `test_concentration_tuning.py`: Concentration parameter validation
- `test_missing_value_handling.py`: Missing value edge cases

## API Reference

### DPGMMModel

```python
class DPGMMModel:
    def __init__(self, config: Dict[str, Any]) -> None
    def update_posterior(self, observation: StreamingObservation) -> AnomalyScore
    def compute_anomaly_score(self, observation: StreamingObservation) -> AnomalyScore
    def get_concentration_status(self) -> Dict[str, Any]
```

### AnomalyScore

```python
@dataclass
class AnomalyScore:
    timestamp: datetime
    score: float  # Negative log posterior
    uncertainty: float  # Variance estimate
    component_probabilities: Dict[int, float]
    threshold_exceeded: bool
```

### EvaluationMetrics

```python
@dataclass
class EvaluationMetrics:
    f1_score: float
    precision: float
    recall: float
    auc_roc: float
    confusion_matrix: np.ndarray
```

## Known Limitations

1. **Low-Variance Series**: May cause numerical instability (mitigated in T023)
2. **Missing Values**: Handled via imputation or skip strategies (T024)
3. **Clustered Anomalies**: Not yet fully supported (T053 pending)
4. **Large Component Counts**: May require concentration tuning (T025)

## Future Enhancements

- T053: Cluster anomaly handling for collective anomalies
- T058: ELBO convergence logging (in progress)
- T059: GitHub Actions runtime edge case handling

## Constitution Principles Compliance

| Principle | Status | Notes |
|-------------|--------|-------|
| I: Tasker writes tasks.md | ✅ | Only T049 does not modify tasks.md |
| II: Project structure | ✅ | All artifacts in `projects/PROJ-024/` |
| III: Checksum recording | ✅ | Implemented in T008, T012 |
| IV: Real dataset URLs | ✅ | UCI, NAB, PEMS verified |
| V: Script must-do-work | ✅ | All scripts runnable without args |
| VI: ELBO logging | 🔄 | T058 pending |
| VII: No invented APIs | ✅ | All imports from API surface |

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024 | Initial implementation guide |
| 1.0.1 | 2024 | Added T049 documentation updates |

## Contact

For questions about this implementation, refer to:
- `specs/001-bayesian-nonparametrics-anomaly-detection/research.md`
- `specs/001-bayesian-nonparametrics-anomaly-detection/data-model.md`
- `specs/001-bayesian-nonparametrics-anomaly-detection/quickstart.md`
