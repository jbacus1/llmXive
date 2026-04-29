"""
Unit tests for src/lib/validators.py

Test-first approach: These tests verify schema compliance checks
for participant, assessment, and intervention data validation.
"""
import pytest
from datetime import datetime
from typing import Dict, Any, List
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from lib.validators import (
    validate_participant_data,
    validate_assessment_data,
    validate_intervention_data,
    validate_schema_compliance,
    ValidationError,
)


class TestValidateParticipantData:
    """Tests for participant data validation (US1 - T005 contract)"""

    def test_valid_participant_data(self):
        """Test that valid participant data passes validation"""
        valid_data = {
            "participant_id": "P001",
            "age": 8,
            "gender": "M",
            "diagnosis_confirmed": True,
            "diagnosis_date": "2024-01-15",
            "consent_given": True,
            "consent_date": "2024-02-01",
            "parent_contact": "parent@example.com",
        }
        result = validate_participant_data(valid_data)
        assert result["valid"] is True
        assert "errors" not in result or len(result.get("errors", [])) == 0

    def test_missing_required_fields(self):
        """Test that missing required fields are caught"""
        invalid_data = {
            "participant_id": "P002",
            "age": 10,
            # Missing: diagnosis_confirmed, consent_given, etc.
        }
        result = validate_participant_data(invalid_data)
        assert result["valid"] is False
        assert len(result.get("errors", [])) > 0

    def test_invalid_age_range(self):
        """Test that age outside valid range (5-17 for children) is caught"""
        invalid_data = {
            "participant_id": "P003",
            "age": 25,  # Too old for child study
            "gender": "F",
            "diagnosis_confirmed": True,
            "diagnosis_date": "2024-01-15",
            "consent_given": True,
            "consent_date": "2024-02-01",
            "parent_contact": "parent@example.com",
        }
        result = validate_participant_data(invalid_data)
        assert result["valid"] is False
        assert any("age" in str(e).lower() for e in result.get("errors", []))

    def test_negative_age(self):
        """Test that negative age is rejected"""
        invalid_data = {
            "participant_id": "P004",
            "age": -5,
            "gender": "M",
            "diagnosis_confirmed": True,
            "diagnosis_date": "2024-01-15",
            "consent_given": True,
            "consent_date": "2024-02-01",
            "parent_contact": "parent@example.com",
        }
        result = validate_participant_data(invalid_data)
        assert result["valid"] is False

    def test_invalid_date_format(self):
        """Test that invalid date formats are caught"""
        invalid_data = {
            "participant_id": "P005",
            "age": 7,
            "gender": "F",
            "diagnosis_confirmed": True,
            "diagnosis_date": "2024/01/15",  # Wrong format
            "consent_given": True,
            "consent_date": "2024-02-01",
            "parent_contact": "parent@example.com",
        }
        result = validate_participant_data(invalid_data)
        assert result["valid"] is False

    def test_missing_consent(self):
        """Test that participant without consent is rejected"""
        invalid_data = {
            "participant_id": "P006",
            "age": 9,
            "gender": "M",
            "diagnosis_confirmed": True,
            "diagnosis_date": "2024-01-15",
            "consent_given": False,  # No consent
            "consent_date": None,
            "parent_contact": "parent@example.com",
        }
        result = validate_participant_data(invalid_data)
        assert result["valid"] is False


class TestValidateAssessmentData:
    """Tests for assessment data validation (US1 - T006 contract)"""

    def test_valid_assessment_data(self):
        """Test that valid assessment data passes validation"""
        valid_data = {
            "assessment_id": "A001",
            "participant_id": "P001",
            "timepoint": "baseline",
            "assessment_date": "2024-02-15",
            "assessor_id": "R001",
            "scores": {
                "ssbs": 45,
                "ssbs_t": 55,
                "sscs": 30,
                "sscs_t": 48,
            },
            "notes": "Baseline assessment completed",
        }
        result = validate_assessment_data(valid_data)
        assert result["valid"] is True

    def test_invalid_timepoint(self):
        """Test that invalid timepoint values are caught"""
        invalid_data = {
            "assessment_id": "A002",
            "participant_id": "P001",
            "timepoint": "invalid_point",  # Not baseline, post, or followup
            "assessment_date": "2024-02-15",
            "assessor_id": "R001",
            "scores": {"ssbs": 45, "sscs": 30},
        }
        result = validate_assessment_data(invalid_data)
        assert result["valid"] is False
        assert any("timepoint" in str(e).lower() for e in result.get("errors", []))

    def test_score_out_of_range(self):
        """Test that scores outside valid range are caught"""
        invalid_data = {
            "assessment_id": "A003",
            "participant_id": "P001",
            "timepoint": "baseline",
            "assessment_date": "2024-02-15",
            "assessor_id": "R001",
            "scores": {
                "ssbs": -5,  # Negative score
                "sscs": 200,  # Above max
            },
        }
        result = validate_assessment_data(invalid_data)
        assert result["valid"] is False

    def test_missing_assessment_date(self):
        """Test that missing assessment date is caught"""
        invalid_data = {
            "assessment_id": "A004",
            "participant_id": "P001",
            "timepoint": "post",
            # Missing: assessment_date
            "assessor_id": "R001",
            "scores": {"ssbs": 45, "sscs": 30},
        }
        result = validate_assessment_data(invalid_data)
        assert result["valid"] is False

    def test_duplicate_assessment_for_timepoint(self):
        """Test that duplicate assessments for same participant/timepoint are flagged"""
        # This tests the validator's ability to detect duplicates when
        # multiple records are provided
        pass  # Tested in integration tests


class TestValidateInterventionData:
    """Tests for intervention data validation (US1 - T007 contract)"""

    def test_valid_intervention_session(self):
        """Test that valid session data passes validation"""
        valid_data = {
            "session_id": "S001",
            "participant_id": "P001",
            "session_number": 1,
            "session_date": "2024-02-20",
            "session_type": "mindfulness",
            "duration_minutes": 45,
            "adherence_score": 0.95,
            "activities_completed": ["breathing", "body_scan", "reflection"],
            "facilitator_id": "F001",
            "notes": "Session completed as planned",
        }
        result = validate_intervention_data(valid_data)
        assert result["valid"] is True

    def test_session_number_out_of_range(self):
        """Test that session numbers outside expected range are caught"""
        invalid_data = {
            "session_id": "S002",
            "participant_id": "P001",
            "session_number": 15,  # Beyond 8 or 12 session protocol
            "session_date": "2024-02-20",
            "session_type": "mindfulness",
            "duration_minutes": 45,
            "adherence_score": 0.95,
            "activities_completed": ["breathing"],
            "facilitator_id": "F001",
        }
        result = validate_intervention_data(invalid_data)
        assert result["valid"] is False

    def test_invalid_adherence_score(self):
        """Test that adherence scores outside 0-1 range are caught"""
        invalid_data = {
            "session_id": "S003",
            "participant_id": "P001",
            "session_number": 1,
            "session_date": "2024-02-20",
            "session_type": "mindfulness",
            "duration_minutes": 45,
            "adherence_score": 1.5,  # Above 1.0
            "activities_completed": ["breathing"],
            "facilitator_id": "F001",
        }
        result = validate_intervention_data(invalid_data)
        assert result["valid"] is False

    def test_missing_session_type(self):
        """Test that missing session type is caught"""
        invalid_data = {
            "session_id": "S004",
            "participant_id": "P001",
            "session_number": 1,
            "session_date": "2024-02-20",
            # Missing: session_type
            "duration_minutes": 45,
            "adherence_score": 0.95,
            "facilitator_id": "F001",
        }
        result = validate_intervention_data(invalid_data)
        assert result["valid"] is False


class TestValidateSchemaCompliance:
    """Tests for general schema compliance checking"""

    def test_compliant_schema(self):
        """Test that schema-compliant data passes"""
        data = {"name": "test", "value": 100}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"},
            },
            "required": ["name", "value"],
        }
        result = validate_schema_compliance(data, schema)
        assert result["valid"] is True

    def test_non_compliant_schema(self):
        """Test that non-compliant data is caught"""
        data = {"name": "test", "value": "not_a_number"}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"},
            },
            "required": ["name", "value"],
        }
        result = validate_schema_compliance(data, schema)
        assert result["valid"] is False

    def test_missing_required_field_schema(self):
        """Test that missing required fields in schema are caught"""
        data = {"name": "test"}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"},
            },
            "required": ["name", "value"],
        }
        result = validate_schema_compliance(data, schema)
        assert result["valid"] is False


class TestValidationErrorHandling:
    """Tests for error handling and edge cases"""

    def test_empty_data(self):
        """Test that empty data is handled gracefully"""
        result = validate_participant_data({})
        assert result["valid"] is False
        assert len(result.get("errors", [])) > 0

    def test_none_data(self):
        """Test that None data is handled gracefully"""
        with pytest.raises((TypeError, ValidationError)):
            validate_participant_data(None)

    def test_empty_string_values(self):
        """Test that empty string values are handled"""
        invalid_data = {
            "participant_id": "",  # Empty string
            "age": 8,
            "gender": "M",
            "diagnosis_confirmed": True,
            "diagnosis_date": "2024-01-15",
            "consent_given": True,
            "consent_date": "2024-02-01",
            "parent_contact": "parent@example.com",
        }
        result = validate_participant_data(invalid_data)
        assert result["valid"] is False

    def test_whitespace_only_values(self):
        """Test that whitespace-only values are handled"""
        invalid_data = {
            "participant_id": "   ",
            "age": 8,
            "gender": "M",
            "diagnosis_confirmed": True,
            "diagnosis_date": "2024-01-15",
            "consent_given": True,
            "consent_date": "2024-02-01",
            "parent_contact": "parent@example.com",
        }
        result = validate_participant_data(invalid_data)
        assert result["valid"] is False

    def test_extra_fields_ignored(self):
        """Test that extra fields don't cause validation to fail"""
        data = {
            "participant_id": "P001",
            "age": 8,
            "gender": "M",
            "diagnosis_confirmed": True,
            "diagnosis_date": "2024-01-15",
            "consent_given": True,
            "consent_date": "2024-02-01",
            "parent_contact": "parent@example.com",
            "extra_field": "should_be_ignored",
        }
        result = validate_participant_data(data)
        # Extra fields should not invalidate
        assert result["valid"] is True

    def test_case_insensitive_boolean_values(self):
        """Test that boolean-like string values are handled"""
        data = {
            "participant_id": "P001",
            "age": 8,
            "gender": "M",
            "diagnosis_confirmed": "True",  # String boolean
            "diagnosis_date": "2024-01-15",
            "consent_given": True,
            "consent_date": "2024-02-01",
            "parent_contact": "parent@example.com",
        }
        result = validate_participant_data(data)
        # Should handle string booleans gracefully
        # May be valid or invalid depending on implementation
        assert "valid" in result

    def test_special_characters_in_fields(self):
        """Test that special characters in text fields are handled"""
        data = {
            "participant_id": "P001",
            "age": 8,
            "gender": "M",
            "diagnosis_confirmed": True,
            "diagnosis_date": "2024-01-15",
            "consent_given": True,
            "consent_date": "2024-02-01",
            "parent_contact": "parent+test@example.com",
        }
        result = validate_participant_data(data)
        assert result["valid"] is True

    def test_unicode_characters(self):
        """Test that unicode characters are handled"""
        data = {
            "participant_id": "P001",
            "age": 8,
            "gender": "M",
            "diagnosis_confirmed": True,
            "diagnosis_date": "2024-01-15",
            "consent_given": True,
            "consent_date": "2024-02-01",
            "parent_contact": "parent@example.com",
            "notes": "Notes with unicode: café 日本語 🎯",
        }
        result = validate_participant_data(data)
        # Should handle unicode gracefully
        assert "valid" in result