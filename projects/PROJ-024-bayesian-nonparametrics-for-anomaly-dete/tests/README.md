# Test Suite Documentation

## Overview

This test suite validates the Bayesian Nonparametrics Anomaly Detection
project across three levels:

1. **Contract Tests** (`tests/contract/`) - Validate API schemas and outputs
2. **Integration Tests** (`tests/integration/`) - Validate end-to-end workflows
3. **Unit Tests** (`tests/unit/`) - Validate individual components

## Running Tests

### Run All Tests
```bash
cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete
pytest
```

### Run Specific Test Category
```bash
# Contract tests only
pytest -m contract

# Integration tests only
pytest -m integration

# Unit tests only
pytest -m unit
```

### Run with Coverage
```bash
pytest --cov=code --cov-report=html
```

### Run with Verbose Output
```bash
pytest -v --tb=long
```

## Test Organization

### Contract Tests (tests/contract/)
- `test_dp_gmm_schema.py` - DPGMM model output schema validation (T013)
- `test_metrics_schema.py` - Evaluation metrics output schema validation (T027)
- `test_threshold_schema.py` - Threshold calibration output schema validation (T042)

### Integration Tests (tests/integration/)
- `test_streaming_update.py` - Streaming observation update workflow (T014)
- `test_baseline_comparison.py` - End-to-end baseline comparison pipeline (T028)
- `test_threshold_calibration.py` - Unlabeled data threshold calibration (T043)

### Unit Tests (tests/unit/)
- `test_memory_profile.py` - Memory usage validation <7GB RAM (T015)
- Additional unit tests for edge cases (T052)

## Shared Fixtures

Common test fixtures are defined in `tests/conftest.py`:
- `sample_timeseries_data` - Synthetic time series with known anomalies
- `sample_anomaly_labels` - Ground truth anomaly labels
- `test_config` - Test configuration dictionary
- `temp_data_dir` - Temporary data directory
- `temp_output_dir` - Temporary output directory
- `contract_test_schema` - Schema for contract validation
- `baseline_comparison_data` - Data for baseline comparison tests
- `threshold_calibration_data` - Data for threshold calibration tests
- `memory_profile_config` - Configuration for memory profiling

## Markers

Tests can be marked with pytest markers:
- `@pytest.mark.contract` - Contract tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.memory` - Memory profiling tests
- `@pytest.mark.baseline` - Baseline comparison tests

## CI Integration

Tests are configured for GitHub Actions CI:
- JSON report generation for test result parsing
- Timeout limits (300 seconds per test)
- Parallel execution support with pytest-xdist
- Coverage reporting for code quality

## Requirements

Install test dependencies:
```bash
pip install -r requirements-test.txt
```

## Test Data

Test data is generated using fixtures to ensure reproducibility:
- Random seeds are set in fixtures
- Synthetic data is used for most tests
- Real dataset tests use the download_datasets.py utilities

## Troubleshooting

### Import Errors
If you encounter import errors, ensure the code directory is in PATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/code"
```

### Test Discovery Issues
Ensure test files follow the naming convention `test_*.py`

### Fixture Not Found
Check that fixtures are defined in `tests/conftest.py` or the test file itself
