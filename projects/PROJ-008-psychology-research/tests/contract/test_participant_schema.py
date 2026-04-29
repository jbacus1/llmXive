"""
Contract tests for participant schema (T005).

These tests verify that participant data validation
conforms to the schema contract defined in
contracts/participant.schema.yaml

Tests should FAIL before implementation and PASS after.
"""
import pytest
import json
from pathlib import Path
from typing import Dict, Any
from pydantic import ValidationError

# Import the models and validators
from src.models.data_models import Participant, ParticipantDemographics
from src.lib.validators import validate_schema_compliance

# Path to schema contract
SCHEMA_PATH = Path("contracts/participant.schema.yaml")

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def valid_participant_data() -> Dict[str, Any]:
    """Valid participant data for testing."""
    return {
        "participant_id": "P001",
        "demographics": {
            "age": 8,
            "sex": "M",
            "diagnosis": "ASD",
            "nonverbal_intellectual_ability": 85,
            "verbal_intellectual_ability": 90,
            "language_profile": "verbal",
            "comorbidities": []
        },
        "consent": {
            "parent_consent": True,
            "child_assent": True,
            "consent_date": "2025-01-15",
            "irb_approved": True
        },
        "site": "SITE_A",
        "enrollment_date": "2025-01-20"
    }

@pytest.fixture
def schema_contract() -> Dict[str, Any]:
    """Load the participant schema contract."""
    with open(SCHEMA_PATH, 'r') as f:
        import yaml
        return yaml.safe_load(f)

# ============================================================================
# VALID DATA TESTS
# ============================================================================

class TestValidParticipantData:
    """Test that valid participant data passes validation."""
    
    def test_valid_participant_creation(self, valid_participant_data):
        """Valid participant data should instantiate without error."""
        participant = Participant(**valid_participant_data)
        assert participant.participant_id == "P001"
        assert participant.enrollment_date is not None
    
    def test_valid_demographics_creation(self, valid_participant_data):
        """Valid demographics should instantiate without error."""
        demo = ParticipantDemographics(**valid_participant_data["demographics"])
        assert demo.age == 8
        assert demo.diagnosis == "ASD"
    
    def test_schema_compliance_valid(self, valid_participant_data, schema_contract):
        """Valid data should pass schema compliance check."""
        result = validate_schema_compliance(
            valid_participant_data,
            schema_contract,
            "participant"
        )
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    def test_required_fields_present(self, valid_participant_data):
        """All required fields should be present."""
        participant = Participant(**valid_participant_data)
        assert hasattr(participant, "participant_id")
        assert hasattr(participant, "demographics")
        assert hasattr(participant, "consent")
        assert hasattr(participant, "site")
        assert hasattr(participant, "enrollment_date")

# ============================================================================
# INVALID DATA TESTS
# ============================================================================

class TestInvalidParticipantData:
    """Test that invalid participant data fails validation."""
    
    def test_missing_required_field_participant_id(self):
        """Missing participant_id should raise validation error."""
        invalid_data = {
            "demographics": {
                "age": 8,
                "sex": "M",
                "diagnosis": "ASD",
                "nonverbal_intellectual_ability": 85,
                "verbal_intellectual_ability": 90,
                "language_profile": "verbal",
                "comorbidities": []
            },
            "consent": {
                "parent_consent": True,
                "child_assent": True,
                "consent_date": "2025-01-15",
                "irb_approved": True
            },
            "site": "SITE_A",
            "enrollment_date": "2025-01-20"
        }
        with pytest.raises(ValidationError):
            Participant(**invalid_data)
    
    def test_missing_required_field_demographics(self):
        """Missing demographics should raise validation error."""
        invalid_data = {
            "participant_id": "P002",
            "consent": {
                "parent_consent": True,
                "child_assent": True,
                "consent_date": "2025-01-15",
                "irb_approved": True
            },
            "site": "SITE_A",
            "enrollment_date": "2025-01-20"
        }
        with pytest.raises(ValidationError):
            Participant(**invalid_data)
    
    def test_invalid_age_type(self, valid_participant_data):
        """Age must be an integer, not string."""
        valid_participant_data["demographics"]["age"] = "eight"
        with pytest.raises(ValidationError):
            Participant(**valid_participant_data)
    
    def test_invalid_age_range(self, valid_participant_data):
        """Age must be within valid range (4-18)."""
        valid_participant_data["demographics"]["age"] = 25
        with pytest.raises(ValidationError):
            Participant(**valid_participant_data)
    
    def test_invalid_sex_value(self, valid_participant_data):
        """Sex must be M, F, or X."""
        valid_participant_data["demographics"]["sex"] = "invalid"
        with pytest.raises(ValidationError):
            Participant(**valid_participant_data)
    
    def test_invalid_diagnosis_value(self, valid_participant_data):
        """Diagnosis must be ASD or other valid diagnosis."""
        valid_participant_data["demographics"]["diagnosis"] = "INVALID"
        with pytest.raises(ValidationError):
            Participant(**valid_participant_data)
    
    def test_missing_consent_parent(self, valid_participant_data):
        """Parent consent is required."""
        valid_participant_data["consent"]["parent_consent"] = False
        # This should still be valid (parent consent can be False for certain cases)
        # But missing the field should fail
        del valid_participant_data["consent"]["parent_consent"]
        with pytest.raises(ValidationError):
            Participant(**valid_participant_data)
    
    def test_invalid_date_format(self, valid_participant_data):
        """Dates must be in ISO format."""
        valid_participant_data["enrollment_date"] = "01/20/2025"
        with pytest.raises(ValidationError):
            Participant(**valid_participant_data)

# ============================================================================
# SCHEMA CONTRACT TESTS
# ============================================================================

class TestSchemaContractCompliance:
    """Test that the schema contract is properly enforced."""
    
    def test_schema_exists(self):
        """Schema contract file should exist."""
        assert SCHEMA_PATH.exists(), f"Schema contract not found at {SCHEMA_PATH}"
    
    def test_schema_has_required_structure(self, schema_contract):
        """Schema contract should have required structure."""
        assert "type" in schema_contract
        assert schema_contract["type"] == "object"
        assert "properties" in schema_contract
        assert "participant_id" in schema_contract["properties"]
    
    def test_schema_enforces_required_fields(self, schema_contract):
        """Schema should define required fields."""
        assert "required" in schema_contract
        assert "participant_id" in schema_contract["required"]
    
    def test_schema_compliance_rejects_invalid(self, schema_contract):
        """Schema compliance check should reject invalid data."""
        invalid_data = {
            "participant_id": "P003",
            "demographics": {
                "age": "not_a_number",  # Invalid type
                "sex": "M",
                "diagnosis": "ASD",
                "nonverbal_intellectual_ability": 85,
                "verbal_intellectual_ability": 90,
                "language_profile": "verbal",
                "comorbidities": []
            },
            "consent": {
                "parent_consent": True,
                "child_assent": True,
                "consent_date": "2025-01-15",
                "irb_approved": True
            },
            "site": "SITE_A",
            "enrollment_date": "2025-01-20"
        }
        result = validate_schema_compliance(
            invalid_data,
            schema_contract,
            "participant"
        )
        assert result["valid"] is False
        assert len(result["errors"]) > 0
    
    def test_schema_compliance_accepts_valid(self, valid_participant_data, schema_contract):
        """Schema compliance check should accept valid data."""
        result = validate_schema_compliance(
            valid_participant_data,
            schema_contract,
            "participant"
        )
        assert result["valid"] is True

# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_comorbidities_list(self, valid_participant_data):
        """Empty comorbidities list should be valid."""
        valid_participant_data["demographics"]["comorbidities"] = []
        participant = Participant(**valid_participant_data)
        assert participant.demographics.comorbidities == []
    
    def test_boundary_age_minimum(self):
        """Minimum age (4) should be valid."""
        data = {
            "participant_id": "P004",
            "demographics": {
                "age": 4,
                "sex": "M",
                "diagnosis": "ASD",
                "nonverbal_intellectual_ability": 85,
                "verbal_intellectual_ability": 90,
                "language_profile": "verbal",
                "comorbidities": []
            },
            "consent": {
                "parent_consent": True,
                "child_assent": True,
                "consent_date": "2025-01-15",
                "irb_approved": True
            },
            "site": "SITE_A",
            "enrollment_date": "2025-01-20"
        }
        participant = Participant(**data)
        assert participant.demographics.age == 4
    
    def test_boundary_age_maximum(self):
        """Maximum age (18) should be valid."""
        data = {
            "participant_id": "P005",
            "demographics": {
                "age": 18,
                "sex": "F",
                "diagnosis": "ASD",
                "nonverbal_intellectual_ability": 85,
                "verbal_intellectual_ability": 90,
                "language_profile": "verbal",
                "comorbidities": []
            },
            "consent": {
                "parent_consent": True,
                "child_assent": True,
                "consent_date": "2025-01-15",
                "irb_approved": True
            },
            "site": "SITE_A",
            "enrollment_date": "2025-01-20"
        }
        participant = Participant(**data)
        assert participant.demographics.age == 18
    
    def test_multiple_comorbidities(self, valid_participant_data):
        """Multiple comorbidities should be valid."""
        valid_participant_data["demographics"]["comorbidities"] = [
            "ADHD",
            "anxiety"
        ]
        participant = Participant(**valid_participant_data)
        assert len(participant.demographics.comorbidities) == 2

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegrationWithValidators:
    """Test integration with validation utilities."""
    
    def test_validator_integration(self, valid_participant_data):
        """Validator should work with model validation."""
        from src.lib.validators import validate_participant
        
        result = validate_participant(valid_participant_data)
        assert result["valid"] is True
    
    def test_validator_rejects_invalid(self):
        """Validator should reject invalid data."""
        from src.lib.validators import validate_participant
        
        invalid_data = {
            "participant_id": "P006",
            "demographics": {
                "age": -1,  # Invalid
                "sex": "M",
                "diagnosis": "ASD",
                "nonverbal_intellectual_ability": 85,
                "verbal_intellectual_ability": 90,
                "language_profile": "verbal",
                "comorbidities": []
            },
            "consent": {
                "parent_consent": True,
                "child_assent": True,
                "consent_date": "2025-01-15",
                "irb_approved": True
            },
            "site": "SITE_A",
            "enrollment_date": "2025-01-20"
        }
        result = validate_participant(invalid_data)
        assert result["valid"] is False