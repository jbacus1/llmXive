# Data Model Specification

## Overview

This document defines the entity definitions, schema specifications, and temporal data handling
methodology for the Bayesian Nonparametrics Anomaly Detection project.

## Entity Definitions

### TimeSeries

A time series observation containing timestamped measurements.

```python
@dataclass
class TimeSeries:
    timestamp: datetime
    value: float
    labels: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
```

### AnomalyScore

The output of anomaly detection containing probabilistic uncertainty estimates.

```python
@dataclass
class AnomalyScore:
    timestamp: datetime
    score: float
    uncertainty: Dict[str, float]
    is_anomaly: bool
    threshold: float
```

### EvaluationMetrics

Performance metrics for model evaluation.

```python
@dataclass
class EvaluationMetrics:
    f1_score: float
    precision: float
    recall: float
    auc_roc: float
    auc_pr: float
```

## Dataset Specifications

### UCI Electricity Dataset

**Source**: UCI Machine Learning Repository
**URL**: `https://archive.ics.uci.edu/ml/datasets/ElectricityLoadDiagrams20112014`
**License**: UCI Repository License (free for research)
**Access Date**: 2024-01-15
**Observations**: 31,536 (hourly readings over 4 years)
**Features**: 370 time series (one per customer)

**Temporal Split**:
- Training Period: 2011-01-01 00:00:00 to 2013-12-31 23:00:00 (8760 × 3 = 26,280 observations)
- Test Period: 2014-01-01 00:00:00 to 2014-12-31 23:00:00 (8760 observations)
- Split Rationale: Full calendar years for training, holdout year for testing

### UCI Traffic Dataset

**Source**: UCI Machine Learning Repository
**URL**: `https://archive.ics.uci.edu/ml/datasets/PEMS-SF` (PEMS-SF - note: from PEMS project, not UCI)
**Alternative**: UCI Traffic Flow Data (if available) or NAB benchmark traffic datasets
**License**: PEMS project license (free for research)
**Access Date**: 2024-01-15
**Observations**: 35,000+ (5-minute intervals over 2 years)
**Features**: 862 sensors

**Temporal Split**:
- Training Period: 2015-01-01 00:00:00 to 2016-06-30 23:55:00 (75% of data)
- Test Period: 2016-07-01 00:00:00 to 2016-12-31 23:55:00 (25% of data)
- Split Rationale: 75/25 temporal split maintaining chronological order

### UCI Synthetic Control Chart Dataset

**Source**: UCI Machine Learning Repository
**URL**: `https://archive.ics.uci.edu/ml/datasets/Synthetic+Control+Chart+Time+Series`
**License**: UCI Repository License (free for research)
**Access Date**: 2024-01-15
**Observations**: 600 time series (100 per class, 6 classes)
**Features**: 60 time points per series

**Temporal Split**:
- Training Period: Series 1-450 (75% of series)
- Test Period: Series 451-600 (25% of series)
- Split Rationale: Stratified split by class, maintaining temporal integrity within each series

## Temporal Split Methodology

### Rationale

Temporal data leakage occurs when future information is used to train models that will be
deployed on past data. This violates the fundamental assumption of time series forecasting
and anomaly detection, where the model must predict based only on historical information.

**Key Principles**:

1. **Chronological Ordering**: All splits must maintain strict chronological order
2. **No Look-Ahead**: Training data timestamp < Test data timestamp for all splits
3. **Concept Drift Awareness**: Test period should capture potential distribution shifts
4. **Reproducibility**: Exact timestamps must be documented for replication

### Split Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    Full Time Series                             │
│                                                                 │
│  ┌─────────────────────────────┬─────────────────────────────┐  │
│  │        Training Set         │         Test Set            │  │
│  │    (t_0 to t_train_end)     │    (t_test_start to t_end)  │  │
│  │                             │                             │  │
│  │   [Historical Patterns]     │   [Holdout Evaluation]      │  │
│  │                             │                             │  │
│  └─────────────────────────────┴─────────────────────────────┘  │
│                                                                 │
│                    t_train_end < t_test_start                   │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation Guidelines

1. **Load data with timestamps preserved**
2. **Sort by timestamp** (ascending order)
3. **Split at boundary**: `train_data = data[data['timestamp'] <= split_time]`
4. **Validate**: `train_data['timestamp'].max() < test_data['timestamp'].min()`

### Streaming Considerations

For streaming anomaly detection:

- Model updates occur incrementally as new observations arrive
- No future observations are ever used in training
- Test evaluation simulates real-time deployment (one observation at a time)
- Threshold calibration uses only historical (training) data statistics

### Quality Checks

Before any evaluation:

1. Verify no timestamp overlap between train/test sets
2. Verify test set starts after training set ends
3. Verify minimum observation counts (1000+ per set)
4. Document exact split timestamps in this file

## Data Integrity & Provenance

### Checksum Validation

All downloaded datasets are validated using SHA256 checksums stored in:
`state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`

### Missing Data Handling

- **Strategy**: Forward fill for gaps < 5 minutes, interpolation for gaps < 1 hour
- **Flagging**: All imputed values marked in metadata
- **Streaming**: Missing values trigger skip strategy with log warning

### License Compliance

| Dataset | License | Attribution Required |
|---------|---------|---------------------|
| UCI Electricity | UCI Research | Yes |
| UCI Traffic | PEMS Project | Yes |
| UCI Synthetic Control | UCI Research | Yes |

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-15 | Implementation Team | Initial specification |
| 1.1 | 2024-01-20 | Implementation Team | Added temporal split methodology (T079) |
