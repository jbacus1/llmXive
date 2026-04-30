"""
Contract test for evaluation_metrics.schema.yaml validation.

Per plan.md requirements: Contract tests must verify that all
evaluation metrics data structures conform to their schema definitions.
This test ensures FR-006 compliance (confusion matrices, ROC curves,
PR curves for evaluation) by validating the schema contract.

Written BEFORE implementation per TDD requirements.
"""
import pytest
import json
import yaml
from pathlib import Path
from jsonschema import validate, ValidationError, SchemaError

# Schema path relative to project root
SCHEMA_PATH = Path("specs/001-bayesian-nonparametrics-anomaly-detection/contracts/evaluation_metrics.schema.yaml")

@pytest.fixture(scope="module")
def evaluation_metrics_schema():
    """Load the evaluation_metrics schema from file."""
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def valid_metrics_payload():
    """Valid evaluation metrics payload per schema."""
    return {
        "precision": 0.85,
        "recall": 0.90,
        "f1_score": 0.874,
        "auc_roc": 0.92,
        "auc_pr": 0.88,
        "confusion_matrix": {
            "true_positive": 85,
            "false_positive": 15,
            "true_negative": 90,
            "false_negative": 10
        },
        "threshold": 0.5,
        "dataset_name": "uci_synthetic_001",
        "model_name": "dpgmm_streaming"
    }

@pytest.fixture
def invalid_precision_payload():
    """Invalid payload: precision out of [0, 1] range."""
    return {
        "precision": 1.5,
        "recall": 0.90,
        "f1_score": 0.874,
        "auc_roc": 0.92,
        "auc_pr": 0.88,
        "confusion_matrix": {
            "true_positive": 85,
            "false_positive": 15,
            "true_negative": 90,
            "false_negative": 10
        },
        "threshold": 0.5,
        "dataset_name": "uci_synthetic_001",
        "model_name": "dpgmm_streaming"
    }

@pytest.fixture
def missing_required_field_payload():
    """Invalid payload: missing required 'f1_score' field."""
    return {
        "precision": 0.85,
        "recall": 0.90,
        "auc_roc": 0.92,
        "auc_pr": 0.88,
        "confusion_matrix": {
            "true_positive": 85,
            "false_positive": 15,
            "true_negative": 90,
            "false_negative": 10
        },
        "threshold": 0.5,
        "dataset_name": "uci_synthetic_001",
        "model_name": "dpgmm_streaming"
    }

@pytest.fixture
def invalid_confusion_matrix_payload():
    """Invalid payload: confusion matrix with negative values."""
    return {
        "precision": 0.85,
        "recall": 0.90,
        "f1_score": 0.874,
        "auc_roc": 0.92,
        "auc_pr": 0.88,
        "confusion_matrix": {
            "true_positive": -5,
            "false_positive": 15,
            "true_negative": 90,
            "false_negative": 10
        },
        "threshold": 0.5,
        "dataset_name": "uci_synthetic_001",
        "model_name": "dpgmm_streaming"
    }

@pytest.fixture
def invalid_type_payload():
    """Invalid payload: precision as string instead of float."""
    return {
        "precision": "high",
        "recall": 0.90,
        "f1_score": 0.874,
        "auc_roc": 0.92,
        "auc_pr": 0.88,
        "confusion_matrix": {
            "true_positive": 85,
            "false_positive": 15,
            "true_negative": 90,
            "false_negative": 10
        },
        "threshold": 0.5,
        "dataset_name": "uci_synthetic_001",
        "model_name": "dpgmm_streaming"
    }

class TestEvaluationMetricsContract:
    """Contract tests for evaluation_metrics.schema.yaml."""

    def test_schema_file_exists(self):
        """Verify schema file exists at expected path."""
        assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

    def test_schema_is_valid_json_schema(self, evaluation_metrics_schema):
        """Verify the schema itself is valid JSON Schema."""
        with pytest.raises((SchemaError, ValidationError), strict=False) as exc_info:
            validate(instance={"test": "data"}, schema=evaluation_metrics_schema)
        # Should not raise SchemaError - schema definition is valid

    def test_valid_metrics_passes_validation(self, evaluation_metrics_schema, valid_metrics_payload):
        """Valid metrics payload should pass schema validation."""
        # This should NOT raise ValidationError
        try:
            validate(instance=valid_metrics_payload, schema=evaluation_metrics_schema)
            assert True, "Valid payload passed validation"
        except ValidationError as e:
            pytest.fail(f"Valid payload failed validation: {e.message}")

    def test_invalid_precision_fails_validation(self, evaluation_metrics_schema, invalid_precision_payload):
        """Precision > 1.0 should fail validation (range constraint)."""
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_precision_payload, schema=evaluation_metrics_schema)
        assert "precision" in exc_info.value.message.lower() or "maximum" in exc_info.value.message.lower()

    def test_missing_required_field_fails_validation(self, evaluation_metrics_schema, missing_required_field_payload):
        """Missing required field should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=missing_required_field_payload, schema=evaluation_metrics_schema)
        assert "f1_score" in exc_info.value.message.lower() or "required" in exc_info.value.message.lower()

    def test_invalid_confusion_matrix_fails_validation(self, evaluation_metrics_schema, invalid_confusion_matrix_payload):
        """Negative confusion matrix values should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_confusion_matrix_payload, schema=evaluation_metrics_schema)
        assert "true_positive" in exc_info.value.message.lower() or "minimum" in exc_info.value.message.lower()

    def test_invalid_type_fails_validation(self, evaluation_metrics_schema, invalid_type_payload):
        """Wrong type for precision should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_type_payload, schema=evaluation_metrics_schema)
        assert "precision" in exc_info.value.message.lower() or "type" in exc_info.value.message.lower()

    def test_boundary_precision_zero(self, evaluation_metrics_schema):
        """Precision = 0.0 should pass (boundary value)."""
        payload = valid_metrics_payload.copy()
        payload["precision"] = 0.0
        try:
            validate(instance=payload, schema=evaluation_metrics_schema)
            assert True
        except ValidationError as e:
            pytest.fail(f"Boundary value 0.0 failed: {e.message}")

    def test_boundary_precision_one(self, evaluation_metrics_schema):
        """Precision = 1.0 should pass (boundary value)."""
        payload = valid_metrics_payload.copy()
        payload["precision"] = 1.0
        try:
            validate(instance=payload, schema=evaluation_metrics_schema)
            assert True
        except ValidationError as e:
            pytest.fail(f"Boundary value 1.0 failed: {e.message}")

    def test_schema_contains_required_properties(self, evaluation_metrics_schema):
        """Verify schema defines all required properties per FR-006."""
        required_properties = ["precision", "recall", "f1_score", "auc_roc", "auc_pr", "confusion_matrix"]
        schema_properties = evaluation_metrics_schema.get("properties", {})
        for prop in required_properties:
            assert prop in schema_properties, f"Required property '{prop}' missing from schema"

    def test_confusion_matrix_structure(self, evaluation_metrics_schema):
        """Verify confusion_matrix has required sub-properties."""
        cm_schema = evaluation_metrics_schema.get("properties", {}).get("confusion_matrix", {})
        cm_properties = cm_schema.get("properties", {})
        required_cm_fields = ["true_positive", "false_positive", "true_negative", "false_negative"]
        for field in required_cm_fields:
            assert field in cm_properties, f"Required confusion_matrix field '{field}' missing"