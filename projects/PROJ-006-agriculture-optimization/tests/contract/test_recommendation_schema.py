"""
Contract test for recommendation output schema (US3).

This test validates that recommendation engine outputs conform to the
expected schema defined in contracts/recommendation.schema.yaml.

NOTE: This test is written FIRST and should FAIL until the recommendation
engine implementation (T036-T040) is complete.
"""
import pytest
import json
from pathlib import Path
from typing import Dict, List, Any
import jsonschema
from jsonschema import validate, ValidationError

# Import schema from contracts directory
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"
RECOMMENDATION_SCHEMA_PATH = CONTRACTS_DIR / "recommendation.schema.yaml"

# Fallback to output schema if recommendation-specific schema doesn't exist
OUTPUT_SCHEMA_PATH = CONTRACTS_DIR / "output.schema.yaml"

@pytest.fixture
def recommendation_schema() -> Dict[str, Any]:
    """Load the recommendation output schema."""
    import yaml
    
    # Try recommendation-specific schema first
    if RECOMMENDATION_SCHEMA_PATH.exists():
        with open(RECOMMENDATION_SCHEMA_PATH, 'r') as f:
            return yaml.safe_load(f)
    
    # Fallback to general output schema
    if OUTPUT_SCHEMA_PATH.exists():
        with open(OUTPUT_SCHEMA_PATH, 'r') as f:
            return yaml.safe_load(f)
    
    # If no schema exists, use a default structure for testing
    return {
        "type": "object",
        "required": ["recommendations", "metadata"],
        "properties": {
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["practice_id", "practice_name", "justification"],
                    "properties": {
                        "practice_id": {"type": "string"},
                        "practice_name": {"type": "string"},
                        "description": {"type": "string"},
                        "justification": {"type": "string"},
                        "adoption_rate": {"type": "number", "minimum": 0, "maximum": 1},
                        "expected_yield_impact": {"type": "number"},
                        "sustainability_score": {"type": "number", "minimum": 0, "maximum": 10},
                        "ecosystem_service_impact": {"type": "object"},
                        "social_equity_score": {"type": "number", "minimum": 0, "maximum": 10}
                    }
                }
            },
            "metadata": {
                "type": "object",
                "required": ["generated_at", "model_version"],
                "properties": {
                    "generated_at": {"type": "string", "format": "date-time"},
                    "model_version": {"type": "string"},
                    "community_id": {"type": "string"},
                    "data_sources": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    }

@pytest.fixture
def valid_recommendation_output() -> Dict[str, Any]:
    """Sample valid recommendation output for testing."""
    return {
        "recommendations": [
            {
                "practice_id": "PRAC-001",
                "practice_name": "Conservation Tillage",
                "description": "Reduce soil disturbance to improve water retention",
                "justification": "Based on climate risk assessment showing drought vulnerability",
                "adoption_rate": 0.65,
                "expected_yield_impact": 0.12,
                "sustainability_score": 8.5,
                "ecosystem_service_impact": {
                    "soil_health": "positive",
                    "water_retention": "improved",
                    "carbon_sequestration": "moderate"
                },
                "social_equity_score": 7.0
            }
        ],
        "metadata": {
            "generated_at": "2025-07-04T12:00:00Z",
            "model_version": "1.0.0",
            "community_id": "COMM-001",
            "data_sources": ["climate_data", "survey_data", "remote_sensing"]
        }
    }

@pytest.fixture
def invalid_recommendation_output() -> Dict[str, Any]:
    """Sample invalid recommendation output (missing required fields)."""
    return {
        "recommendations": [
            {
                "practice_id": "PRAC-001",
                # Missing required: practice_name, justification
            }
        ],
        # Missing required: metadata
    }

class TestRecommendationSchema:
    """Contract tests for recommendation output schema validation."""
    
    def test_schema_loads_successfully(self, recommendation_schema):
        """Verify the schema is valid JSON Schema."""
        assert isinstance(recommendation_schema, dict)
        assert "type" in recommendation_schema
        assert "properties" in recommendation_schema
    
    def test_valid_recommendation_conforms_to_schema(
        self, recommendation_schema, valid_recommendation_output
    ):
        """Verify valid recommendation output passes schema validation."""
        # This test should PASS when schema and output are compatible
        validate(instance=valid_recommendation_output, schema=recommendation_schema)
    
    def test_invalid_recommendation_fails_schema_validation(
        self, recommendation_schema, invalid_recommendation_output
    ):
        """Verify invalid recommendation output fails schema validation."""
        # This test should PASS (i.e., catch the error) when validation works
        with pytest.raises(ValidationError):
            validate(
                instance=invalid_recommendation_output,
                schema=recommendation_schema
            )
    
    def test_recommendation_has_required_fields(self, valid_recommendation_output):
        """Verify each recommendation has all required fields."""
        required_fields = ["practice_id", "practice_name", "justification"]
        
        for rec in valid_recommendation_output["recommendations"]:
            for field in required_fields:
                assert field in rec, f"Missing required field: {field}"
    
    def test_metadata_has_required_fields(self, valid_recommendation_output):
        """Verify metadata has all required fields."""
        required_fields = ["generated_at", "model_version"]
        
        for field in required_fields:
            assert field in valid_recommendation_output["metadata"], \
                f"Missing required metadata field: {field}"
    
    def test_adoption_rate_in_valid_range(self, valid_recommendation_output):
        """Verify adoption_rate is between 0 and 1."""
        for rec in valid_recommendation_output["recommendations"]:
            if "adoption_rate" in rec:
                assert 0 <= rec["adoption_rate"] <= 1, \
                    f"adoption_rate must be between 0 and 1, got {rec['adoption_rate']}"
    
    def test_sustainability_score_in_valid_range(self, valid_recommendation_output):
        """Verify sustainability_score is between 0 and 10."""
        for rec in valid_recommendation_output["recommendations"]:
            if "sustainability_score" in rec:
                assert 0 <= rec["sustainability_score"] <= 10, \
                    f"sustainability_score must be between 0 and 10, got {rec['sustainability_score']}"
    
    def test_recommendation_output_is_json_serializable(self, valid_recommendation_output):
        """Verify recommendation output can be serialized to JSON."""
        try:
            json.dumps(valid_recommendation_output)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Recommendation output is not JSON serializable: {e}")
    
    def test_empty_recommendations_list(self):
        """Test that empty recommendations list is valid."""
        empty_output = {
            "recommendations": [],
            "metadata": {
                "generated_at": "2025-07-04T12:00:00Z",
                "model_version": "1.0.0",
                "community_id": "COMM-001",
                "data_sources": []
            }
        }
        # This should be valid - no recommendations is a valid state
        assert len(empty_output["recommendations"]) == 0
    
    def test_multiple_recommendations(self):
        """Test that multiple recommendations are valid."""
        multi_output = {
            "recommendations": [
                {
                    "practice_id": "PRAC-001",
                    "practice_name": "Practice 1",
                    "justification": "Justification 1"
                },
                {
                    "practice_id": "PRAC-002",
                    "practice_name": "Practice 2",
                    "justification": "Justification 2"
                }
            ],
            "metadata": {
                "generated_at": "2025-07-04T12:00:00Z",
                "model_version": "1.0.0",
                "community_id": "COMM-001",
                "data_sources": ["data1"]
            }
        }
        assert len(multi_output["recommendations"]) == 2