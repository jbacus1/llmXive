"""
Contract test for assessment schema validation.

This test ensures that assessment data conforms to the
contracts/assessment.schema.yaml definition, testing both
valid data acceptance and invalid data rejection.

Related tasks:
  - T006: Create assessment.schema.yaml contract
  - T009: Implement validation utilities
  - T012: Participant schema contract test (reference)
"""

import pytest
import yaml
import json
from pathlib import Path

# Import validation utilities from the project
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from lib.validators import validate_against_schema
from models.data_models import Assessment


@pytest.fixture
def assessment_schema():
    """Load the assessment schema from contracts directory."""
    schema_path = Path(__file__).parent.parent.parent / 'contracts' / 'assessment.schema.yaml'
    assert schema_path.exists(), f"Assessment schema not found at {schema_path}"
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def valid_assessment_data():
    """Return valid assessment data for testing."""
    return {
        "participant_id": "P001",
        "assessment_type": "social_skills",
        "timepoint": "baseline",
        "timestamp": "2025-01-15T10:30:00Z",
        "score": 45.5,
        "assessor_id": "A001",
        "notes": "Initial baseline assessment"
    }


@pytest.fixture
def valid_assessment_with_optional():
    """Return valid assessment data including optional fields."""
    return {
        "participant_id": "P002",
        "assessment_type": "mindfulness",
        "timepoint": "post_intervention",
        "timestamp": "2025-02-20T14:00:00Z",
        "score": 52.3,
        "assessor_id": "A002",
        "notes": "Post-intervention measurement",
        "session_adherence": 0.95,
        "follow_up_scheduled": True
    }


class TestAssessmentSchemaValidation:
    """Contract tests for assessment schema validation."""
    
    def test_schema_file_exists(self, assessment_schema):
        """Verify the assessment schema file loads correctly."""
        assert assessment_schema is not None
        assert '$schema' in assessment_schema or 'type' in assessment_schema
    
    def test_valid_assessment_accepted(self, assessment_schema, valid_assessment_data):
        """Valid assessment data should pass schema validation."""
        result = validate_against_schema(
            data=valid_assessment_data,
            schema=assessment_schema,
            schema_name='assessment'
        )
        assert result['valid'] is True
        assert 'errors' not in result or len(result.get('errors', [])) == 0
    
    def test_valid_assessment_with_optional_fields(self, assessment_schema, valid_assessment_with_optional):
        """Valid assessment with optional fields should pass validation."""
        result = validate_against_schema(
            data=valid_assessment_with_optional,
            schema=assessment_schema,
            schema_name='assessment'
        )
        assert result['valid'] is True
    
    def test_invalid_assessment_missing_required_field(self, assessment_schema):
        """Assessment missing required field should fail validation."""
        invalid_data = {
            "assessment_type": "social_skills",
            "timepoint": "baseline",
            "score": 45.5
            # Missing participant_id (required)
        }
        result = validate_against_schema(
            data=invalid_data,
            schema=assessment_schema,
            schema_name='assessment'
        )
        assert result['valid'] is False
        assert 'errors' in result
        assert len(result['errors']) > 0
    
    def test_invalid_assessment_wrong_type(self, assessment_schema):
        """Assessment with wrong data types should fail validation."""
        invalid_data = {
            "participant_id": 12345,  # Should be string
            "assessment_type": "social_skills",
            "timepoint": "baseline",
            "timestamp": "2025-01-15T10:30:00Z",
            "score": "not_a_number",  # Should be numeric
            "assessor_id": "A001"
        }
        result = validate_against_schema(
            data=invalid_data,
            schema=assessment_schema,
            schema_name='assessment'
        )
        assert result['valid'] is False
    
    def test_invalid_timepoint_value(self, assessment_schema, valid_assessment_data):
        """Assessment with invalid timepoint should fail validation."""
        invalid_data = valid_assessment_data.copy()
        invalid_data['timepoint'] = 'invalid_timepoint'  # Not in enum
        result = validate_against_schema(
            data=invalid_data,
            schema=assessment_schema,
            schema_name='assessment'
        )
        assert result['valid'] is False
    
    def test_assessment_pydantic_model_creation(self, valid_assessment_data):
        """Valid data should create Assessment Pydantic model."""
        assessment = Assessment(**valid_assessment_data)
        assert assessment.participant_id == "P001"
        assert assessment.assessment_type == "social_skills"
        assert assessment.score == 45.5
    
    def test_assessment_pydantic_model_validation_fails(self):
        """Invalid data should raise validation error in Pydantic model."""
        invalid_data = {
            "participant_id": "P001",
            "assessment_type": "social_skills",
            "timepoint": "baseline",
            "score": "invalid"  # Should be numeric
        }
        with pytest.raises(Exception):  # Pydantic ValidationError
            Assessment(**invalid_data)
    
    def test_json_serialization(self, valid_assessment_data):
        """Assessment data should serialize to JSON."""
        json_str = json.dumps(valid_assessment_data)
        assert json_str is not None
        loaded = json.loads(json_str)
        assert loaded == valid_assessment_data
    
    def test_schema_completeness(self, assessment_schema):
        """Verify schema has expected structure for contract testing."""
        # Check for key schema properties
        assert 'properties' in assessment_schema or 'required' in assessment_schema
        # Verify participant_id is defined (required field)
        if 'properties' in assessment_schema:
            assert 'participant_id' in assessment_schema['properties']