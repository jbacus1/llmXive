# Contract Tests

## Purpose

Contract tests validate that the project's public APIs conform to their
specified schemas. These tests ensure that:

1. Output schemas match the documented specifications
2. Required fields are present and correctly typed
3. API contracts are maintained across versions

## Test Files

Each user story has associated contract tests:

### User Story 1 (DPGMM Model)
- `test_dp_gmm_schema.py` - Validates DPGMM model output schema
  - Checks AnomalyScore dataclass fields
  - Validates DPGMMModel return types
  - Ensures ELBOHistory structure

### User Story 2 (Baseline Comparison)
- `test_metrics_schema.py` - Validates evaluation metrics schema
  - Checks EvaluationMetrics dataclass fields
  - Validates F1-score, precision, recall calculations
  - Ensures confusion matrix output structure

### User Story 3 (Threshold Calibration)
- `test_threshold_schema.py` - Validates threshold calibration output
  - Checks adaptive threshold computation results
  - Validates anomaly rate outputs
  - Ensures multi-dataset calibration structure

## Running Contract Tests

```bash
# Run all contract tests
pytest tests/contract/ -v

# Run specific contract test
pytest tests/contract/test_dp_gmm_schema.py -v

# Run with coverage
pytest tests/contract/ --cov=code
```

## Contract Schema Sources

Contract schemas are defined in:
- `specs/contracts/` - Schema definitions (read-only, by Tasker)
- `code/src/models/` - Implementation classes
- `code/src/evaluation/` - Evaluation metrics classes

## Requirements

Each contract test must:
1. Import from the correct module paths
2. Validate all required fields per spec.md
3. Check field types match dataclass definitions
4. Return clear failure messages for schema violations

## Test Markers

Contract tests are marked with `@pytest.mark.contract` for selective execution.
