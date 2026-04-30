# Testing Strategy

## Overview

This document outlines the testing strategy for the Bayesian Nonparametrics Anomaly Detection system. All tests are required per spec.md Independent Test scenarios.

## Test Categories

### 1. Contract Tests (tests/contract/)

Contract tests validate that outputs conform to expected schemas.

| Test File | Validates |
|-------------|-----------|
| `test_dp_gmm_schema.py` | DPGMMModel output schema |
| `test_metrics_schema.py` | EvaluationMetrics schema |
| `test_threshold_schema.py` | ThresholdResult schema |

**Requirements**:
- Run before implementation (tests should fail initially)
- Validate dataclass field types and required fields
- Run independently per user story

### 2. Integration Tests (tests/integration/)

Integration tests validate end-to-end functionality across components.

| Test File | Validates |
|-------------|-----------|
| `test_streaming_update.py` | Streaming observation processing pipeline |
| `test_baseline_comparison.py` | Full baseline comparison workflow |
| `test_threshold_calibration.py` | Unlabeled threshold calibration |

**Requirements**:
- Test complete user story workflows
- Verify data flows correctly between components
- Run after contract tests pass

### 3. Unit Tests (tests/unit/)

Unit tests validate individual functions and edge cases.

| Test File | Validates |
|-------------|-----------|
| `test_memory_profile.py` | <7GB RAM constraint |
| `test_edge_cases.py` | Low-variance, missing values, etc. |
| `test_concentration.py` | Adaptive concentration tuning |

**Requirements**:
- Test edge cases per user story
- Verify performance constraints
- Run as part of CI pipeline

## Test Execution Order

```bash
# 1. Contract tests (schema validation)
pytest tests/contract/ -v

# 2. Integration tests (end-to-end)
pytest tests/integration/ -v

# 3. Unit tests (individual components)
pytest tests/unit/ -v

# 4. All tests together
pytest tests/ -v --tb=short
```

## User Story Test Mapping

### User Story 1: Core DPGMM

| Test | File | Purpose |
|------|------|---------|
| T013 | tests/contract/test_dp_gmm_schema.py | Output schema validation |
| T014 | tests/integration/test_streaming_update.py | Streaming update verification |
| T015 | tests/unit/test_memory_profile.py | Memory constraint verification |

**Independent Test**: Process synthetic time series with known anomalies and verify anomaly scores are produced without batch retraining.

### User Story 2: Baseline Comparison

| Test | File | Purpose |
|------|------|---------|
| T027 | tests/contract/test_metrics_schema.py | Metrics schema validation |
| T028 | tests/integration/test_baseline_comparison.py | Full comparison pipeline |

**Independent Test**: Run DPGMM, ARIMA, and moving average on UCI dataset and generate precision-recall curves with F1-score measurements.

### User Story 3: Threshold Calibration

| Test | File | Purpose |
|------|------|---------|
| T042 | tests/contract/test_threshold_schema.py | Threshold schema validation |
| T043 | tests/integration/test_threshold_calibration.py | Unlabeled calibration |

**Independent Test**: Run model on unlabeled data and verify adaptive threshold produces reasonable anomaly rates.

## Test Fixtures

### Synthetic Data Fixtures

```python
# tests/conftest.py
import pytest
from data.synthetic_generator import generate_synthetic_timeseries

@pytest.fixture
def synthetic_dataset():
    return generate_synthetic_timeseries(
        signal_config=SignalConfig(length=1000),
        anomaly_config=AnomalyConfig(anomaly_rate=0.05)
    )

@pytest.fixture
def known_anomaly_indices():
    return [100, 250, 500, 750]  # Known ground truth
```

### Model Fixtures

```python
@pytest.fixture
def dp_gmm_model():
    return DPGMMModel(config={
        "concentration_prior": 1.0,
        "max_components": 100
    })

@pytest.fixture
def arima_baseline():
    return ARIMABaseline(config=ARIMAConfig(order=(1, 1, 1)))
```

## Performance Constraints Testing

### Memory Constraint (<7GB)

```python
def test_memory_usage_under_limit(dp_gmm_model, synthetic_dataset):
    profile = profile_memory_usage(
        operation=lambda: process_dataset(dp_gmm_model, synthetic_dataset),
        max_memory_gb=7.0
    )
    assert profile.max_memory_gb < 7.0
```

### Runtime Constraint (<30 minutes)

```python
def test_runtime_under_budget(dataset):
    result = monitor_runtime(
        operation=lambda: run_full_pipeline(dataset),
        budget_seconds=1800
    )
    assert result.total_seconds < 1800
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r code/requirements.txt
      - name: Run contract tests
        run: pytest tests/contract/ -v
      - name: Run integration tests
        run: pytest tests/integration/ -v
      - name: Run unit tests
        run: pytest tests/unit/ -v
      - name: Verify memory constraint
        run: python code/scripts/profile_memory_1000_obs.py
        timeout-minutes: 30
```

## Test Coverage Requirements

| Component | Minimum Coverage |
|-------------|-----------------|
| DPGMMModel | 85% |
| Baselines | 90% |
| Evaluation | 95% |
| Utilities | 80% |

## Edge Cases to Test

1. **Low-Variance Time Series**: May cause numerical instability
2. **Missing Values**: Should handle via imputation or skip
3. **Clustered Anomalies**: Collective anomaly detection
4. **Large Component Counts**: Concentration parameter tuning
5. **Empty Datasets**: Graceful handling
6. **Single Observation**: Edge case for streaming

## Test Data Requirements

### Required Datasets

1. **Synthetic**: Generated with known ground truth
2. **UCI Electricity**: Real-world power consumption
3. **UCI Traffic**: Traffic sensor data
4. **PEMS-SF**: Bay Area traffic data

### Ground Truth Requirements

- Synthetic datasets: Known anomaly indices
- Real datasets: Annotated anomaly periods where available

## Regression Testing

When modifying core components:

1. Run all contract tests first
2. Run integration tests for affected user stories
3. Verify performance constraints still met
4. Update test data if schemas change

## Test Maintenance

- Update contract tests when dataclass schemas change
- Add new unit tests for each edge case discovered
- Keep integration tests independent per user story
- Document test failures with reproduction steps
