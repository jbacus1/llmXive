"""
Contract test for config.yaml threshold parameters (US3).

Validates that the config.yaml file conforms to the schema defined in
specs/001-bayesian-nonparametrics-anomaly-detection/contracts/config.schema.yaml
with specific focus on threshold calibration parameters for User Story 3.

Per plan.md requirements: Tests MUST fail before implementation.
"""

import os
import yaml
import pytest
from pathlib import Path

# Import schema validation utilities
try:
    from jsonschema import validate, ValidationError, SchemaError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# Project root path (relative to code/tests/contract/)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
SCHEMA_PATH = (
    PROJECT_ROOT / "specs" / "001-bayesian-nonparametrics-anomaly-detection"
    / "contracts" / "config.schema.yaml"
)

# Threshold-specific parameter names for US3
THRESHOLD_PARAMS = [
    "threshold_percentile",
    "threshold_method",
    "adaptive_threshold_enabled",
    "min_anomaly_rate",
    "max_anomaly_rate",
    "threshold_calibration_window",
]

REQUIRED_THRESHOLD_FIELDS = {
    "threshold_percentile": (0.0, 1.0),  # Must be between 0 and 1
    "threshold_method": ["percentile", "adaptive", "fixed"],
    "adaptive_threshold_enabled": [True, False],
    "min_anomaly_rate": (0.0, 1.0),
    "max_anomaly_rate": (0.0, 1.0),
    "threshold_calibration_window": (10, 10000),  # Min/max observations
}

@pytest.mark.contract
@pytest.mark.us3
class TestConfigThresholdContract:
    """Contract tests for config.yaml threshold parameters."""

    @pytest.fixture(scope="class")
    def config(self):
        """Load config.yaml for testing."""
        assert CONFIG_PATH.exists(), f"config.yaml not found at {CONFIG_PATH}"
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    
    @pytest.fixture(scope="class")
    def schema(self):
        """Load config.schema.yaml for validation."""
        assert SCHEMA_PATH.exists(), f"Schema not found at {SCHEMA_PATH}"
        with open(SCHEMA_PATH, "r") as f:
            return yaml.safe_load(f)

    def test_config_file_exists(self):
        """Verify config.yaml exists in project root."""
        assert CONFIG_PATH.exists(), (
            "config.yaml must exist at project root for threshold calibration"
        )

    def test_config_schema_exists(self):
        """Verify config.schema.yaml exists for contract validation."""
        assert SCHEMA_PATH.exists(), (
            "config.schema.yaml must exist for contract testing"
        )

    def test_config_is_valid_yaml(self):
        """Verify config.yaml is valid YAML."""
        with open(CONFIG_PATH, "r") as f:
            try:
                config = yaml.safe_load(f)
                assert isinstance(config, dict), "config.yaml must be a YAML dictionary"
            except yaml.YAMLError as e:
                pytest.fail(f"config.yaml is not valid YAML: {e}")

    @pytest.mark.skipif(
        not HAS_JSONSCHEMA,
        reason="jsonschema package required for schema validation"
    )
    def test_config_matches_schema(self, config, schema):
        """Validate config.yaml against config.schema.yaml."""
        try:
            validate(instance=config, schema=schema)
        except ValidationError as e:
            pytest.fail(f"config.yaml does not match schema: {e.message}")
        except SchemaError as e:
            pytest.fail(f"config.schema.yaml is invalid: {e.message}")

    def test_threshold_section_exists(self, config):
        """Verify threshold section exists in config for US3."""
        assert "threshold" in config, (
            "threshold section required in config.yaml for anomaly flagging"
        )
        assert isinstance(config["threshold"], dict), (
            "threshold section must be a dictionary"
        )

    def test_threshold_percentile_valid_range(self, config):
        """Verify threshold_percentile is within valid range [0, 1]."""
        threshold = config.get("threshold", {})
        percentile = threshold.get("threshold_percentile")
        
        assert percentile is not None, (
            "threshold_percentile is required for US3 threshold calibration"
        )
        assert isinstance(percentile, (int, float)), (
            "threshold_percentile must be numeric"
        )
        assert 0.0 <= percentile <= 1.0, (
            f"threshold_percentile must be between 0 and 1, got {percentile}"
        )

    def test_threshold_method_valid(self, config):
        """Verify threshold_method is one of the allowed values."""
        threshold = config.get("threshold", {})
        method = threshold.get("threshold_method")
        
        assert method is not None, (
            "threshold_method is required for US3"
        )
        assert method in REQUIRED_THRESHOLD_FIELDS["threshold_method"], (
            f"threshold_method must be one of "
            f"{REQUIRED_THRESHOLD_FIELDS['threshold_method']}, got {method}"
        )

    def test_adaptive_threshold_enabled_type(self, config):
        """Verify adaptive_threshold_enabled is boolean."""
        threshold = config.get("threshold", {})
        enabled = threshold.get("adaptive_threshold_enabled")
        
        assert enabled is not None, (
            "adaptive_threshold_enabled is required for US3"
        )
        assert isinstance(enabled, bool), (
            f"adaptive_threshold_enabled must be boolean, got {type(enabled)}"
        )

    def test_min_anomaly_rate_valid(self, config):
        """Verify min_anomaly_rate is within valid range."""
        threshold = config.get("threshold", {})
        min_rate = threshold.get("min_anomaly_rate")
        
        assert min_rate is not None, (
            "min_anomaly_rate is required for anomaly rate bounds"
        )
        assert isinstance(min_rate, (int, float)), (
            "min_anomaly_rate must be numeric"
        )
        assert 0.0 <= min_rate <= 1.0, (
            f"min_anomaly_rate must be between 0 and 1, got {min_rate}"
        )

    def test_max_anomaly_rate_valid(self, config):
        """Verify max_anomaly_rate is within valid range."""
        threshold = config.get("threshold", {})
        max_rate = threshold.get("max_anomaly_rate")
        
        assert max_rate is not None, (
            "max_anomaly_rate is required for anomaly rate bounds"
        )
        assert isinstance(max_rate, (int, float)), (
            "max_anomaly_rate must be numeric"
        )
        assert 0.0 <= max_rate <= 1.0, (
            f"max_anomaly_rate must be between 0 and 1, got {max_rate}"
        )

    def test_min_max_anomaly_rate_consistency(self, config):
        """Verify min_anomaly_rate <= max_anomaly_rate."""
        threshold = config.get("threshold", {})
        min_rate = threshold.get("min_anomaly_rate", 0)
        max_rate = threshold.get("max_anomaly_rate", 1)
        
        assert min_rate <= max_rate, (
            f"min_anomaly_rate ({min_rate}) must be <= "
            f"max_anomaly_rate ({max_rate})"
        )

    def test_threshold_calibration_window_valid(self, config):
        """Verify threshold_calibration_window is within valid range."""
        threshold = config.get("threshold", {})
        window = threshold.get("threshold_calibration_window")
        
        assert window is not None, (
            "threshold_calibration_window is required for adaptive threshold"
        )
        assert isinstance(window, int), (
            "threshold_calibration_window must be integer"
        )
        assert 10 <= window <= 10000, (
            f"threshold_calibration_window must be between 10 and 10000, got {window}"
        )

    def test_threshold_section_contains_all_required_fields(self, config):
        """Verify all required threshold fields are present."""
        threshold = config.get("threshold", {})
        required = list(REQUIRED_THRESHOLD_FIELDS.keys())
        
        missing = [field for field in required if field not in threshold]
        assert not missing, (
            f"Missing required threshold fields: {missing}"
        )

    def test_threshold_parameters_are_documented(self, config):
        """Verify threshold parameters match US3 documentation requirements."""
        threshold = config.get("threshold", {})
        
        # FR-004 requires decision boundary to be documented in config
        assert "threshold_percentile" in threshold, (
            "FR-004: threshold_percentile must be documented in config.yaml"
        )
        assert "threshold_method" in threshold, (
            "FR-004: threshold_method must be documented in config.yaml"
        )

    def test_threshold_defaults_are_reasonable(self, config):
        """Verify threshold defaults are within reasonable bounds for anomaly detection."""
        threshold = config.get("threshold", {})
        
        # Default 95th percentile is standard for anomaly detection
        default_percentile = 0.95
        percentile = threshold.get("threshold_percentile", default_percentile)
        assert 0.90 <= percentile <= 0.99, (
            f"threshold_percentile should be between 0.90 and 0.99 for anomaly detection, "
            f"got {percentile}"
        )

    def test_threshold_config_is_replicable(self, config):
        """Verify threshold config supports reproducibility (Constitution Principle)."""
        threshold = config.get("threshold", {})
        
        # All threshold parameters should be explicitly set for reproducibility
        for param in REQUIRED_THRESHOLD_FIELDS.keys():
            assert param in threshold, (
                f"Threshold parameter '{param}' must be explicitly set for reproducibility"
            )

# Run with: pytest code/tests/contract/test_config.py -v -m contract
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "contract"])
