"""
Contract tests for dataset schema validation (User Story 1).

These tests verify that the dataset schema defined in
contracts/dataset.schema.yaml is properly validated.

Tests should FAIL before implementation to verify test-driven approach.
"""

import pytest
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.schemas import DatasetSchemaValidator


@pytest.fixture
def schema_path() -> Path:
    """Return path to dataset schema file."""
    return Path("contracts/dataset.schema.yaml")

@pytest.fixture
def schema(schema_path: Path) -> Dict[str, Any]:
    """Load the dataset schema from YAML file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def validator(schema: Dict[str, Any]) -> DatasetSchemaValidator:
    """Create a schema validator instance."""
    return DatasetSchemaValidator(schema)

class TestDatasetSchemaContract:
    """Contract tests for dataset schema validation."""

    def test_schema_file_exists(self, schema_path: Path):
        """Verify schema file exists at expected location."""
        assert schema_path.exists(), "Dataset schema file must exist"

    def test_schema_has_required_fields(self, schema: Dict[str, Any]):
        """Verify schema contains required top-level fields."""
        assert "type" in schema, "Schema must have 'type' field"
        assert "properties" in schema, "Schema must have 'properties' field"

    def test_valid_dataset_record(self, validator: DatasetSchemaValidator):
        """Test validation passes for a valid dataset record."""
        valid_record = {
            "record_id": "REC001",
            "source": "survey",
            "timestamp": "2025-01-15T10:30:00Z",
            "location": {
                "latitude": 45.5,
                "longitude": -122.7,
                "region": "Pacific Northwest"
            },
            "data": {
                "crop_yield": 150.5,
                "weather_temp": 22.3,
                "soil_moisture": 45.0
            }
        }
        result = validator.validate(valid_record)
        assert result.get("valid", False) is True

    def test_missing_required_field_fails(self, validator: DatasetSchemaValidator):
        """Test validation fails when required field is missing."""
        invalid_record = {
            "record_id": "REC002",
            "source": "survey",
            # Missing 'timestamp' - required field
            "location": {
                "latitude": 45.5,
                "longitude": -122.7
            }
        }
        result = validator.validate(invalid_record)
        assert result.get("valid", False) is False

    def test_invalid_data_type_fails(self, validator: DatasetSchemaValidator):
        """Test validation fails when data type is incorrect."""
        invalid_record = {
            "record_id": "REC003",
            "source": "survey",
            "timestamp": "2025-01-15T10:30:00Z",
            "location": {
                "latitude": "not_a_number",  # Should be float
                "longitude": -122.7
            }
        }
        result = validator.validate(invalid_record)
        assert result.get("valid", False) is False

    def test_boundary_values_pass(self, validator: DatasetSchemaValidator):
        """Test validation accepts boundary/edge case values."""
        boundary_record = {
            "record_id": "REC004",
            "source": "survey",
            "timestamp": "2025-12-31T23:59:59Z",
            "location": {
                "latitude": -90.0,  # Minimum valid latitude
                "longitude": 180.0,  # Maximum valid longitude
                "region": ""  # Empty string if allowed
            },
            "data": {
                "crop_yield": 0.0,  # Minimum yield
                "weather_temp": -50.0,  # Extreme temp
                "soil_moisture": 100.0  # Maximum moisture
            }
        }
        result = validator.validate(boundary_record)
        assert result.get("valid", False) is True

    def test_schema_compliance_report(self, validator: DatasetSchemaValidator):
        """Test that validator returns detailed compliance report."""
        invalid_record = {
            "record_id": "REC005",
            "source": "invalid_source"
        }
        result = validator.validate(invalid_record)
        
        # Contract: validation result must include error details
        assert "errors" in result or "error_messages" in result, \
            "Validation result must include error details"

    def test_all_sources_validated(self, validator: DatasetSchemaValidator):
        """Test validation for all supported data sources."""
        sources = ["survey", "climate", "remote_sensing"]
        
        for source in sources:
            record = {
                "record_id": f"REC_{source}",
                "source": source,
                "timestamp": "2025-01-15T10:30:00Z",
                "location": {
                    "latitude": 45.5,
                    "longitude": -122.7
                },
                "data": {}
            }
            result = validator.validate(record)
            assert result.get("valid", False) is True, \
                f"Source '{source}' should be valid"

    def test_nested_validation(self, validator: DatasetSchemaValidator):
        """Test that nested objects are validated correctly."""
        record_with_invalid_nested = {
            "record_id": "REC006",
            "source": "survey",
            "timestamp": "2025-01-15T10:30:00Z",
            "location": {
                # Missing required nested fields
                "latitude": 45.5
            }
        }
        result = validator.validate(record_with_invalid_nested)
        assert result.get("valid", False) is False


class TestSchemaFileStructure:
    """Tests for schema file structure and format."""

    def test_schema_is_valid_yaml(self, schema_path: Path):
        """Verify schema file is valid YAML."""
        with open(schema_path, 'r') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Schema file is not valid YAML: {e}")

    def test_schema_has_version_info(self, schema: Dict[str, Any]):
        """Verify schema includes version information."""
        assert "version" in schema or "schema_version" in schema, \
            "Schema should include version information"

    def test_schema_documentation_present(self, schema: Dict[str, Any]):
        """Verify schema includes documentation/description."""
        assert "description" in schema or "title" in schema, \
            "Schema should include description or title"

    def test_property_definitions_complete(self, schema: Dict[str, Any]):
        """Verify all properties have type definitions."""
        for prop_name, prop_def in schema.get("properties", {}).items():
            assert "type" in prop_def, \
                f"Property '{prop_name}' must have a 'type' definition"

    def test_required_fields_listed(self, schema: Dict[str, Any]):
        """Verify schema lists required fields."""
        assert "required" in schema, \
            "Schema must have 'required' field listing mandatory properties"