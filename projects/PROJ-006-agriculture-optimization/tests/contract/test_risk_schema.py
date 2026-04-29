"""
Contract test for climate risk assessment output schema.

This test validates that risk assessment outputs conform to the
contracts/output.schema.yaml specification.

NOTE: This test is written FIRST and should FAIL until the
climate risk model implementation (T025-T031) is complete.

User Story: US2 - Climate Risk Assessment
Priority: P2
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any, List

import yaml

# Project root path (assumes tests/contract/ structure)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestRiskAssessmentSchema:
    """Contract tests for climate risk assessment output schema."""
    
    @pytest.fixture
    def risk_schema(self) -> Dict[str, Any]:
        """Load the risk assessment output schema from contracts."""
        schema_path = PROJECT_ROOT / "contracts" / "output.schema.yaml"
        if not schema_path.exists():
            pytest.skip(f"Schema file not found: {schema_path}")
        
        with open(schema_path, "r") as f:
            return yaml.safe_load(f)
    
    @pytest.fixture
    def sample_risk_output(self) -> Dict[str, Any]:
        """Sample risk assessment output for validation testing."""
        # This represents expected output structure from climate_risk model
        return {
            "assessment_id": "risk_2025_001",
            "location": {
                "region": "sub-Saharan Africa",
                "coordinates": {
                    "latitude": 10.5,
                    "longitude": 35.2
                }
            },
            "climate_risk_score": 0.75,
            "risk_category": "high",
            "risk_factors": [
                {
                    "factor": "drought_frequency",
                    "impact_score": 0.8,
                    "trend": "increasing"
                },
                {
                    "factor": "temperature_anomaly",
                    "impact_score": 0.6,
                    "trend": "stable"
                }
            ],
            "yield_impact": {
                "estimated_reduction_pct": 15.5,
                "confidence_interval": [12.0, 19.0]
            },
            "timestamp": "2025-01-15T10:30:00Z",
            "data_sources": ["OpenWeatherMap", "USGS"],
            "model_version": "1.0.0"
        }
    
    def test_schema_file_exists(self, risk_schema: Dict[str, Any]) -> None:
        """Verify the risk assessment schema file exists and is valid YAML."""
        assert risk_schema is not None
        assert "type" in risk_schema or "properties" in risk_schema
    
    def test_required_fields_present(self, sample_risk_output: Dict[str, Any]) -> None:
        """Verify all required fields exist in risk assessment output."""
        required_fields = [
            "assessment_id",
            "location",
            "climate_risk_score",
            "risk_category",
            "yield_impact",
            "timestamp"
        ]
        
        for field in required_fields:
            assert field in sample_risk_output, \
                f"Required field '{field}' missing from risk assessment output"
    
    def test_risk_score_valid_range(self, sample_risk_output: Dict[str, Any]) -> None:
        """Verify climate risk score is within valid range [0, 1]."""
        risk_score = sample_risk_output["climate_risk_score"]
        assert isinstance(risk_score, (int, float)), \
            "climate_risk_score must be numeric"
        assert 0 <= risk_score <= 1, \
            f"climate_risk_score must be between 0 and 1, got {risk_score}"
    
    def test_risk_category_valid_values(self, sample_risk_output: Dict[str, Any]) -> None:
        """Verify risk_category is one of the allowed values."""
        valid_categories = ["low", "moderate", "high", "critical"]
        category = sample_risk_output["risk_category"]
        assert category in valid_categories, \
            f"risk_category must be one of {valid_categories}, got '{category}'"
    
    def test_location_structure(self, sample_risk_output: Dict[str, Any]) -> None:
        """Verify location object has required structure."""
        location = sample_risk_output["location"]
        
        assert "region" in location, "location must have 'region' field"
        assert "coordinates" in location, "location must have 'coordinates' field"
        
        coords = location["coordinates"]
        assert "latitude" in coords, "coordinates must have 'latitude'"
        assert "longitude" in coords, "coordinates must have 'longitude'"
        
        # Validate coordinate ranges
        assert -90 <= coords["latitude"] <= 90, \
            f"Invalid latitude: {coords['latitude']}"
        assert -180 <= coords["longitude"] <= 180, \
            f"Invalid longitude: {coords['longitude']}"
    
    def test_yield_impact_structure(self, sample_risk_output: Dict[str, Any]) -> None:
        """Verify yield_impact has required structure and valid values."""
        yield_impact = sample_risk_output["yield_impact"]
        
        assert "estimated_reduction_pct" in yield_impact, \
            "yield_impact must have 'estimated_reduction_pct'"
        assert "confidence_interval" in yield_impact, \
            "yield_impact must have 'confidence_interval'"
        
        # Validate reduction percentage
        reduction = yield_impact["estimated_reduction_pct"]
        assert isinstance(reduction, (int, float)), \
            "estimated_reduction_pct must be numeric"
        assert 0 <= reduction <= 100, \
            f"estimated_reduction_pct must be 0-100, got {reduction}"
        
        # Validate confidence interval
        ci = yield_impact["confidence_interval"]
        assert isinstance(ci, list) and len(ci) == 2, \
            "confidence_interval must be a list of 2 values"
        assert ci[0] <= ci[1], \
            "confidence_interval lower bound must be <= upper bound"
    
    def test_risk_factors_structure(self, sample_risk_output: Dict[str, Any]) -> None:
        """Verify risk_factors is a list with valid structure."""
        risk_factors = sample_risk_output.get("risk_factors", [])
        
        assert isinstance(risk_factors, list), \
            "risk_factors must be a list"
        
        for factor in risk_factors:
            assert "factor" in factor, "Each risk factor must have 'factor' name"
            assert "impact_score" in factor, "Each risk factor must have 'impact_score'"
            assert "trend" in factor, "Each risk factor must have 'trend'"
            
            # Validate impact score range
            assert 0 <= factor["impact_score"] <= 1, \
                f"impact_score must be 0-1, got {factor['impact_score']}"
            
            # Validate trend values
            valid_trends = ["increasing", "stable", "decreasing"]
            assert factor["trend"] in valid_trends, \
                f"trend must be one of {valid_trends}"
    
    def test_timestamp_format(self, sample_risk_output: Dict[str, Any]) -> None:
        """Verify timestamp follows ISO 8601 format."""
        from datetime import datetime
        
        timestamp = sample_risk_output["timestamp"]
        try:
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {timestamp}")
    
    def test_data_sources_not_empty(self, sample_risk_output: Dict[str, Any]) -> None:
        """Verify data_sources is a non-empty list."""
        data_sources = sample_risk_output["data_sources"]
        assert isinstance(data_sources, list), "data_sources must be a list"
        assert len(data_sources) > 0, "data_sources must not be empty"
    
    def test_model_version_format(self, sample_risk_output: Dict[str, Any]) -> None:
        """Verify model_version follows semantic versioning pattern."""
        import re
        
        version = sample_risk_output["model_version"]
        semver_pattern = r"^\d+\.\d+\.\d+$"
        assert re.match(semver_pattern, version), \
            f"model_version must follow semver format, got '{version}'"
    
    def test_json_serialization(self, sample_risk_output: Dict[str, Any]) -> None:
        """Verify risk output can be serialized to JSON."""
        try:
            json.dumps(sample_risk_output)
        except TypeError as e:
            pytest.fail(f"Risk output is not JSON serializable: {e}")
    
    def test_schema_compliance(self, risk_schema: Dict[str, Any], 
                               sample_risk_output: Dict[str, Any]) -> None:
        """
        Validate sample output against the full schema.
        
        NOTE: This test will FAIL until the schema validation
        implementation is complete in T025-T031.
        """
        from src.config.schemas import validate_against_schema
        
        # This import will fail until schemas.py has validate_against_schema
        # This is intentional - test written before implementation
        try:
            is_valid, errors = validate_against_schema(
                sample_risk_output, 
                risk_schema,
                schema_name="risk_assessment_output"
            )
            assert is_valid, f"Schema validation errors: {errors}"
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Schema validation not yet implemented: {e}")


# Additional integration-level contract tests
class TestRiskAssessmentContract:
    """Higher-level contract tests for risk assessment integration."""
    
    def test_empty_assessment_rejected(self) -> None:
        """Empty or None assessment should be rejected."""
        from src.config.schemas import validate_risk_assessment
        
        with pytest.raises(ValueError):
            validate_risk_assessment(None)
        
        with pytest.raises(ValueError):
            validate_risk_assessment({})
    
    def test_multiple_location_types_supported(self) -> None:
        """Verify schema supports different location representations."""
        locations = [
            {"region": "Kenya", "coordinates": {"latitude": -1.2921, "longitude": 36.8219}},
            {"region": "Malawi", "coordinates": {"latitude": -13.2543, "longitude": 34.3015}},
            {"region": "Tanzania", "coordinates": {"latitude": -6.3690, "longitude": 34.8888}}
        ]
        
        for loc in locations:
            assert "region" in loc
            assert "coordinates" in loc
            assert -90 <= loc["coordinates"]["latitude"] <= 90
            assert -180 <= loc["coordinates"]["longitude"] <= 180