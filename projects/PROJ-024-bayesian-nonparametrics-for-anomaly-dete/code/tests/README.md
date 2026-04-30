# Testing Guide

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_stick_breaking.py

# Run tests by marker
pytest -m contract
pytest -m integration
pytest -m unit

# Run with coverage
pytest --cov=code --cov-report=html
```

## Test Organization

- **contract/**: Schema validation tests (YAML/JSON schema compliance)
- **integration/**: Tests that verify component interactions
- **unit/**: Tests for individual functions and classes

## Writing New Tests

1. Place tests in the appropriate directory
2. Use the `test_` prefix for test functions
3. Add appropriate markers: `@pytest.mark.contract`, `@pytest.mark.integration`, `@pytest.mark.unit`
4. Use fixtures from `conftest.py` for common setup

## Test Requirements

Per plan.md, tests MUST fail before implementation to verify they are meaningful.
