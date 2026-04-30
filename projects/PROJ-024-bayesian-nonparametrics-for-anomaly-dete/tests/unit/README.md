# Unit Tests

## Purpose

Unit tests validate individual components in isolation. These tests ensure that:

1. Functions produce correct outputs for given inputs
2. Edge cases are handled correctly
3. Component-level requirements are met

## Test Files

### Memory Profiling
- `test_memory_profile.py` - Validates memory usage constraints
  - Tests <7GB RAM limit during processing
  - Checks memory profiling utilities
  - Validates garbage collection behavior

### Edge Cases (T052)
- Additional unit tests for edge cases including:
  - Low-variance time series handling
  - Missing value processing
  - Concentration parameter tuning
  - Cluster anomaly detection

## Running Unit Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific unit test
pytest tests/unit/test_memory_profile.py -v

# Run memory tests with profiling
pytest tests/unit/test_memory_profile.py -v --profile-memory
```

## Test Requirements

Each unit test must:
1. Test a single component/function
2. Use minimal dependencies
3. Provide clear failure messages
4. Cover edge cases and error conditions

## Test Markers

Unit tests are marked with `@pytest.mark.unit` for selective execution.
Memory tests are additionally marked with `@pytest.mark.memory`.
