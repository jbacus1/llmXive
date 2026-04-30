# Integration Tests

## Purpose

Integration tests validate end-to-end workflows across multiple components.
These tests ensure that:

1. Components work correctly when combined
2. Data flows correctly through the pipeline
3. System-level requirements are met

## Test Files

### User Story 1 (Streaming DPGMM)
- `test_streaming_update.py` - Validates streaming observation processing
  - Tests incremental posterior updates
  - Verifies memory usage during streaming
  - Checks anomaly scoring in real-time

### User Story 2 (Baseline Comparison)
- `test_baseline_comparison.py` - Validates end-to-end comparison pipeline
  - Tests data loading and preprocessing
  - Validates model training and evaluation
  - Checks statistical significance testing

### User Story 3 (Threshold Calibration)
- `test_threshold_calibration.py` - Validates threshold calibration workflow
  - Tests unlabeled data calibration
  - Verifies anomaly rate validation
  - Checks multi-dataset calibration

## Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific integration test
pytest tests/integration/test_streaming_update.py -v

# Run with timeout
pytest tests/integration/ --timeout=300
```

## Test Requirements

Each integration test must:
1. Use realistic data sizes
2. Validate end-to-end data flow
3. Check system-level metrics (memory, time)
4. Provide clear failure diagnostics

## Test Markers

Integration tests are marked with `@pytest.mark.integration` for selective execution.
