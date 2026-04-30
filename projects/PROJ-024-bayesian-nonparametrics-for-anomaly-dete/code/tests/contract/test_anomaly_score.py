"""
Contract tests for anomaly_score.schema.yaml validation.

These tests ensure that the AnomalyScore entity conforms to the
defined JSON schema contract. Tests must FAIL before implementation
and PASS after implementation per plan.md requirements.

Related schema: specs/001-bayesian-nonparametrics-anomaly-detection/contracts/anomaly_score.schema.yaml
"""

import pytest
import yaml
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError


# Schema path relative to project root
SCHEMA_PATH = Path("specs/001-bayesian-nonparametrics-anomaly-detection/contracts/anomaly_score.schema.yaml")


@pytest.fixture
def schema():
    """Load the anomaly_score schema."""
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def valid_anomaly_score():
    """Create a valid anomaly score instance."""
    return {
        "timestamp": "2024-01-15T10:30:00Z",
        "observation_id": "obs_001",
        "score": 0.95,
        "probability": 0.87,
        "cluster_id": "cluster_003",
        "features": {
            "mean": 1.5,
            "std": 0.3
        }
    }


@pytest.fixture
def invalid_score_not_number():
    """Invalid: score must be numeric."""
    return {
        "timestamp": "2024-01-15T10:30:00Z",
        "observation_id": "obs_001",
        "score": "high",  # Invalid: should be float
        "probability": 0.87,
        "cluster_id": "cluster_003",
        "features": {
            "mean": 1.5,
            "std": 0.3
        }
    }


@pytest.fixture
def invalid_missing_timestamp():
    """Invalid: timestamp is required."""
    return {
        "observation_id": "obs_001",
        "score": 0.95,
        "probability": 0.87,
        "cluster_id": "cluster_003",
        "features": {
            "mean": 1.5,
            "std": 0.3
        }
    }


@pytest.fixture
def invalid_timestamp_format():
    """Invalid: timestamp must be ISO8601."""
    return {
        "timestamp": "Jan 15 2024 10:30",  # Invalid format
        "observation_id": "obs_001",
        "score": 0.95,
        "probability": 0.87,
        "cluster_id": "cluster_003",
        "features": {
            "mean": 1.5,
            "std": 0.3
        }
    }


class TestAnomalyScoreSchema:
    """Contract tests for anomaly_score.schema.yaml validation."""

    def test_schema_loads_correctly(self, schema):
        """Verify the schema file loads and is valid YAML."""
        assert schema is not None
        assert isinstance(schema, dict)
        assert '$schema' in schema or 'type' in schema

    def test_valid_anomaly_score_passes_validation(self, schema, valid_anomaly_score):
        """Verify a valid anomaly score instance passes schema validation."""
        # This should NOT raise ValidationError
        validate(instance=valid_anomaly_score, schema=schema)

    def test_invalid_score_not_number_fails_validation(self, schema, invalid_score_not_number):
        """Verify non-numeric score fails validation."""
        with pytest.raises(ValidationError) as excinfo:
            validate(instance=invalid_score_not_number, schema=schema)
        assert 'score' in str(excinfo.value).lower()

    def test_missing_timestamp_fails_validation(self, schema, invalid_missing_timestamp):
        """Verify missing required timestamp fails validation."""
        with pytest.raises(ValidationError) as excinfo:
            validate(instance=invalid_missing_timestamp, schema=schema)
        assert 'timestamp' in str(excinfo.value).lower() or 'required' in str(excinfo.value).lower()

    def test_invalid_timestamp_format_fails_validation(self, schema, invalid_timestamp_format):
        """Verify invalid timestamp format fails validation."""
        with pytest.raises(ValidationError) as excinfo:
            validate(instance=invalid_timestamp_format, schema=schema)
        assert 'timestamp' in str(excinfo.value).lower()

    def test_schema_has_required_fields(self, schema):
        """Verify the schema defines required fields."""
        assert 'required' in schema
        assert 'timestamp' in schema['required']
        assert 'observation_id' in schema['required']
        assert 'score' in schema['required']

    def test_score_is_numeric_type(self, schema):
        """Verify score field is defined as numeric type."""
        properties = schema.get('properties', {})
        score_def = properties.get('score', {})
        assert score_def.get('type') in ['number', 'float', 'integer']

    def test_probability_range_validation(self, schema):
        """Verify probability has defined range constraints."""
        properties = schema.get('properties', {})
        prob_def = properties.get('probability', {})
        assert 'minimum' in prob_def
        assert 'maximum' in prob_def
        assert prob_def['minimum'] == 0.0
        assert prob_def['maximum'] == 1.0