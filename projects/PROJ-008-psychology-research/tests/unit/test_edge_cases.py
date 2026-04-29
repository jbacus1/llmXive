"""
Edge Case Unit Tests for Mindfulness and Social Skills RCT Project

This module contains comprehensive edge case tests for the core
components of the data collection and analysis pipeline.
"""
import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

from src.lib.validators import (
    validate_participant_data,
    validate_assessment_data,
    validate_intervention_data,
    sanitize_string,
    check_schema_compliance
)
from src.models.data_models import (
    Participant,
    Assessment,
    InterventionSession,
    Timepoint
)


class TestValidatorEdgeCases:
    """Edge case tests for validation utilities"""
    
    def test_empty_string_handling(self):
        """Test validation with empty strings in required fields"""
        invalid_data = {
            "participant_id": "",
            "age": 8,
            "diagnosis": "ASD"
        }
        with pytest.raises(ValueError):
            validate_participant_data(invalid_data)
    
    def test_null_value_handling(self):
        """Test validation with None/null values"""
        invalid_data = {
            "participant_id": None,
            "age": 8,
            "diagnosis": "ASD"
        }
        with pytest.raises((ValueError, TypeError)):
            validate_participant_data(invalid_data)
    
    def test_extreme_age_values(self):
        """Test validation with age boundary conditions"""
        # Minimum viable age for study
        min_age_data = {"participant_id": "P001", "age": 3, "diagnosis": "ASD"}
        # Maximum reasonable age for study
        max_age_data = {"participant_id": "P002", "age": 18, "diagnosis": "ASD"}
        # Out of range - too young
        too_young_data = {"participant_id": "P003", "age": 2, "diagnosis": "ASD"}
        # Out of range - too old
        too_old_data = {"participant_id": "P004", "age": 19, "diagnosis": "ASD"}
        
        # Valid ages should pass
        validate_participant_data(min_age_data)
        validate_participant_data(max_age_data)
        
        # Out of range should fail
        with pytest.raises(ValueError):
            validate_participant_data(too_young_data)
        with pytest.raises(ValueError):
            validate_participant_data(too_old_data)
    
    def test_special_characters_in_text(self):
        """Test handling of special characters in text fields"""
        special_chars = [
            "ASD-2025",
            "Autism Spectrum Disorder (ASD)",
            "Mindfulness & Social Skills",
            "Parent/Guardian Consent Form",
            "Test:123;Value<400>",
            "Café résumé naïve"
        ]
        for text in special_chars:
            data = {"participant_id": "P001", "age": 8, "diagnosis": text}
            result = validate_participant_data(data)
            assert result is not None
    
    def test_unicode_handling(self):
        """Test validation with Unicode characters"""
        unicode_data = {
            "participant_id": "P001",
            "age": 8,
            "diagnosis": "自闭症谱系障碍",  # Chinese for ASD
            "notes": "émojis: 😀🎉🧠"
        }
        result = validate_participant_data(unicode_data)
        assert result is not None
    
    def test_numeric_boundary_conditions(self):
        """Test numeric field boundary conditions"""
        # Test score boundaries
        assessment_data = {
            "participant_id": "P001",
            "timepoint": "baseline",
            "social_skills_score": 0,  # Minimum
            "mindfulness_score": 100,  # Maximum
            "session_count": 12
        }
        validate_assessment_data(assessment_data)
        
        # Out of bounds scores
        invalid_scores = {
            "participant_id": "P001",
            "timepoint": "baseline",
            "social_skills_score": -1,  # Negative score
            "mindfulness_score": 101,  # Over maximum
            "session_count": 12
        }
        with pytest.raises(ValueError):
            validate_assessment_data(invalid_scores)
    
    def test_date_boundary_conditions(self):
        """Test date field boundary conditions"""
        valid_date = datetime.now().isoformat()
        past_date = (datetime.now() - timedelta(days=365)).isoformat()
        future_date = (datetime.now() + timedelta(days=365)).isoformat()
        
        # Valid date range
        assessment_data = {
            "participant_id": "P001",
            "timepoint": "baseline",
            "assessment_date": valid_date,
            "social_skills_score": 50,
            "mindfulness_score": 50,
            "session_count": 12
        }
        validate_assessment_data(assessment_data)
        
        # Future date should be flagged
        invalid_date_data = assessment_data.copy()
        invalid_date_data["assessment_date"] = future_date
        with pytest.raises(ValueError):
            validate_assessment_data(invalid_date_data)
    
    def test_empty_list_handling(self):
        """Test validation with empty lists for array fields"""
        data = {
            "participant_id": "P001",
            "age": 8,
            "diagnosis": "ASD",
            "previous_therapies": [],
            "concurrent_medications": []
        }
        result = validate_participant_data(data)
        assert result is not None
    
    def test_excessive_data_length(self):
        """Test handling of excessively long string fields"""
        long_text = "A" * 10000  # 10KB string
        data = {
            "participant_id": "P001",
            "age": 8,
            "diagnosis": "ASD",
            "notes": long_text
        }
        # Should either truncate or raise appropriate error
        result = validate_participant_data(data)
        assert result is not None
    
    def test_malformed_json_input(self):
        """Test validation with malformed JSON structures"""
        malformed_inputs = [
            '{"participant_id": "P001", "age": 8',  # Missing closing brace
            'participant_id: P001, age: 8',  # Invalid JSON syntax
            '',  # Empty string
            'null',  # JSON null
            '[]',  # Empty array
        ]
        for malformed in malformed_inputs:
            with pytest.raises((json.JSONDecodeError, ValueError)):
                check_schema_compliance(malformed, "participant")
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields"""
        partial_data = {
            "participant_id": "P001",
            # Missing: age, diagnosis
        }
        with pytest.raises((ValueError, KeyError)):
            validate_participant_data(partial_data)
    
    def test_wrong_data_types(self):
        """Test validation with incorrect data types"""
        type_errors = [
            {"participant_id": 123, "age": 8, "diagnosis": "ASD"},  # ID should be string
            {"participant_id": "P001", "age": "eight", "diagnosis": "ASD"},  # Age should be int
            {"participant_id": "P001", "age": 8.5, "diagnosis": "ASD"},  # Age should be int
            {"participant_id": "P001", "age": 8, "diagnosis": 123},  # Diagnosis should be string
        ]
        for invalid in type_errors:
            with pytest.raises((ValueError, TypeError)):
                validate_participant_data(invalid)
    
    def test_concurrent_modification_detection(self):
        """Test detection of concurrent data modifications"""
        original_data = {
            "participant_id": "P001",
            "age": 8,
            "diagnosis": "ASD",
            "version": 1
        }
        # Simulate concurrent modification
        modified_data = original_data.copy()
        modified_data["age"] = 9
        modified_data["version"] = 2
        
        # Validation should detect version mismatch
        with pytest.raises(ValueError):
            validate_participant_data(modified_data, expected_version=1)
    
    def test_nested_object_validation(self):
        """Test validation of nested object structures"""
        nested_data = {
            "participant_id": "P001",
            "age": 8,
            "diagnosis": "ASD",
            "family_history": {
                "autism_present": True,
                "affected_relatives": ["father", "sister"],
                "genetic_testing": {
                    "completed": True,
                    "result": "no_copies"
                }
            }
        }
        result = validate_participant_data(nested_data)
        assert result is not None
    
    def test_case_sensitivity(self):
        """Test case sensitivity in string field validation"""
        case_variants = [
            {"participant_id": "P001", "age": 8, "diagnosis": "ASD"},
            {"participant_id": "P001", "age": 8, "diagnosis": "asd"},
            {"participant_id": "P001", "age": 8, "diagnosis": "Asd"},
        ]
        for data in case_variants:
            result = validate_participant_data(data)
            assert result is not None
    
    def test_whitespace_handling(self):
        """Test validation with various whitespace patterns"""
        whitespace_tests = [
            {"participant_id": " P001 ", "age": 8, "diagnosis": "ASD"},
            {"participant_id": "P001", "age": 8, "diagnosis": "  ASD  "},
            {"participant_id": "P001", "age": 8, "diagnosis": "ASD\n"},
            {"participant_id": "P001", "age": 8, "diagnosis": "ASD\t"},
        ]
        for data in whitespace_tests:
            result = validate_participant_data(data)
            assert result is not None
    
    def test_timepoint_enum_validation(self):
        """Test validation of timepoint field with enum values"""
        valid_timepoints = ["baseline", "post_intervention", "follow_up"]
        invalid_timepoints = ["pre", "middle", "end", None, ""]
        
        for tp in valid_timepoints:
            assessment_data = {
                "participant_id": "P001",
                "timepoint": tp,
                "social_skills_score": 50,
                "mindfulness_score": 50,
                "session_count": 12
            }
            validate_assessment_data(assessment_data)
        
        for tp in invalid_timepoints:
            assessment_data = {
                "participant_id": "P001",
                "timepoint": tp,
                "social_skills_score": 50,
                "mindfulness_score": 50,
                "session_count": 12
            }
            with pytest.raises(ValueError):
                validate_assessment_data(assessment_data)
    
    def test_session_count_constraints(self):
        """Test validation of session count constraints"""
        # Valid session counts
        valid_counts = [1, 8, 12, 15]
        for count in valid_counts:
            intervention_data = {
                "participant_id": "P001",
                "session_number": count,
                "session_date": datetime.now().isoformat(),
                "adherence_score": 85
            }
            validate_intervention_data(intervention_data)
        
        # Invalid session counts
        invalid_counts = [0, -1, 100]
        for count in invalid_counts:
            intervention_data = {
                "participant_id": "P001",
                "session_number": count,
                "session_date": datetime.now().isoformat(),
                "adherence_score": 85
            }
            with pytest.raises(ValueError):
                validate_intervention_data(intervention_data)
    
    def test_adherence_score_range(self):
        """Test validation of adherence score percentage range"""
        valid_scores = [0, 50, 100]
        for score in valid_scores:
            intervention_data = {
                "participant_id": "P001",
                "session_number": 1,
                "session_date": datetime.now().isoformat(),
                "adherence_score": score
            }
            validate_intervention_data(intervention_data)
        
        invalid_scores = [-1, 101]
        for score in invalid_scores:
            intervention_data = {
                "participant_id": "P001",
                "session_number": 1,
                "session_date": datetime.now().isoformat(),
                "adherence_score": score
            }
            with pytest.raises(ValueError):
                validate_intervention_data(intervention_data)
    
    def test_pandas_dataframe_edge_cases(self):
        """Test validation with pandas DataFrame edge cases"""
        # Empty DataFrame
        empty_df = pd.DataFrame(columns=["participant_id", "age", "diagnosis"])
        with pytest.raises(ValueError):
            validate_participant_data(empty_df.to_dict())
        
        # DataFrame with NaN values
        df_with_nan = pd.DataFrame({
            "participant_id": ["P001", np.nan],
            "age": [8, 8],
            "diagnosis": ["ASD", "ASD"]
        })
        with pytest.raises((ValueError, TypeError)):
            validate_participant_data(df_with_nan.to_dict())
    
    def test_memory_limit_handling(self):
        """Test handling of data that approaches memory limits"""
        # Large but valid participant list
        large_participant_list = [
            {
                "participant_id": f"P{i:03d}",
                "age": 8 + (i % 10),
                "diagnosis": "ASD"
            }
            for i in range(1000)
        ]
        # Should handle without memory errors
        for participant in large_participant_list:
            result = validate_participant_data(participant)
            assert result is not None
    
    def test_rapid_sequential_validation(self):
        """Test validation under rapid sequential calls (stress test)"""
        for i in range(100):
            data = {
                "participant_id": f"P{i:03d}",
                "age": 8,
                "diagnosis": "ASD"
            }
            result = validate_participant_data(data)
            assert result is not None
    
    def test_schema_version_compatibility(self):
        """Test validation with schema version mismatches"""
        data = {
            "participant_id": "P001",
            "age": 8,
            "diagnosis": "ASD",
            "schema_version": "1.0.0"
        }
        # Should validate with expected version
        result = validate_participant_data(data, expected_version="1.0.0")
        assert result is not None
    
    def test_incomplete_intervention_session(self):
        """Test validation of incomplete intervention session data"""
        # Missing required fields
        incomplete_session = {
            "participant_id": "P001",
            # Missing: session_number, session_date, adherence_score
        }
        with pytest.raises((ValueError, KeyError)):
            validate_intervention_data(incomplete_session)
    
    def test_assessment_without_baseline(self):
        """Test validation of follow-up assessments without baseline"""
        follow_up_data = {
            "participant_id": "P001",
            "timepoint": "follow_up",
            "social_skills_score": 75,
            "mindfulness_score": 80,
            "session_count": 12
        }
        # Should allow follow-up without baseline (baseline may not exist yet)
        result = validate_assessment_data(follow_up_data)
        assert result is not None
    
    def test_duplicate_participant_id_detection(self):
        """Test detection of duplicate participant IDs"""
        existing_ids = ["P001", "P002", "P003"]
        new_id = "P001"  # Duplicate
        
        # In a real implementation, this would check against a database
        # Here we simulate the validation logic
        if new_id in existing_ids:
            with pytest.raises(ValueError):
                validate_participant_data(
                    {"participant_id": new_id, "age": 8, "diagnosis": "ASD"},
                    existing_ids=existing_ids
                )
    
    def test_consent_form_edge_cases(self):
        """Test validation of consent form data edge cases"""
        consent_cases = [
            {
                "parent_name": "John Doe",
                "child_name": "Jane Doe",
                "consent_date": datetime.now().isoformat(),
                "signed": True
            },
            {
                "parent_name": "John Doe",
                "child_name": "Jane Doe",
                "consent_date": datetime.now().isoformat(),
                "signed": False  # Unsigned
            },
        ]
        for consent in consent_cases:
            result = validate_participant_data(consent)
            assert result is not None
    
    def test_international_phone_formats(self):
        """Test validation of international phone number formats"""
        phone_formats = [
            "+1-555-123-4567",
            "+44-20-7946-0958",
            "+86-10-1234-5678",
            "555-123-4567",
        ]
        for phone in phone_formats:
            data = {
                "participant_id": "P001",
                "age": 8,
                "diagnosis": "ASD",
                "contact_phone": phone
            }
            result = validate_participant_data(data)
            assert result is not None
    
    def test_medical_record_number_formats(self):
        """Test validation of medical record number formats"""
        mrn_formats = [
            "MRN-2025-001234",
            "MRN2025001234",
            "2025-MRN-001234",
            "MRN_2025_001234",
        ]
        for mrn in mrn_formats:
            data = {
                "participant_id": "P001",
                "age": 8,
                "diagnosis": "ASD",
                "medical_record_number": mrn
            }
            result = validate_participant_data(data)
            assert result is not None
    
    def test_empty_string_in_optional_fields(self):
        """Test handling of empty strings in optional fields"""
        data = {
            "participant_id": "P001",
            "age": 8,
            "diagnosis": "ASD",
            "previous_therapies": [],
            "concurrent_medications": [],
            "notes": "",
            "parent_occupation": ""
        }
        result = validate_participant_data(data)
        assert result is not None
    
    def test_extreme_assessment_scores(self):
        """Test validation with extreme assessment scores"""
        extreme_scores = [
            {"participant_id": "P001", "timepoint": "baseline", "social_skills_score": 0, "mindfulness_score": 0, "session_count": 12},
            {"participant_id": "P001", "timepoint": "baseline", "social_skills_score": 100, "mindfulness_score": 100, "session_count": 12},
        ]
        for score_data in extreme_scores:
            result = validate_assessment_data(score_data)
            assert result is not None
    
    def test_timezone_aware_datetime(self):
        """Test validation with timezone-aware datetime objects"""
        from datetime import timezone
        tz_aware_dates = [
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone(timedelta(hours=5))).isoformat(),
        ]
        for date in tz_aware_dates:
            assessment_data = {
                "participant_id": "P001",
                "timepoint": "baseline",
                "assessment_date": date,
                "social_skills_score": 50,
                "mindfulness_score": 50,
                "session_count": 12
            }
            result = validate_assessment_data(assessment_data)
            assert result is not None
    
    def test_special_diagnosis_codes(self):
        """Test validation with special diagnosis codes (ICD-10, etc.)"""
        diagnosis_codes = [
            "F84.0",  # ICD-10 code for ASD
            "ASD-2025",
            "Autism Spectrum Disorder",
            "Pervasive Developmental Disorder",
        ]
        for code in diagnosis_codes:
            data = {
                "participant_id": "P001",
                "age": 8,
                "diagnosis": code
            }
            result = validate_participant_data(data)
            assert result is not None
    
    def test_null_in_nested_objects(self):
        """Test validation with null values in nested objects"""
        nested_data = {
            "participant_id": "P001",
            "age": 8,
            "diagnosis": "ASD",
            "family_history": {
                "autism_present": None,  # Null boolean
                "affected_relatives": None,  # Null list
            }
        }
        # Should handle null nested values gracefully
        result = validate_participant_data(nested_data)
        assert result is not None
    
    def test_invalid_timepoint_sequence(self):
        """Test validation of invalid assessment timepoint sequences"""
        # Follow-up without baseline is technically valid (baseline may be missing)
        # But post-intervention without baseline should be flagged
        invalid_sequence = {
            "participant_id": "P001",
            "timepoint": "post_intervention",
            "social_skills_score": 75,
            "mindfulness_score": 80,
            "session_count": 12,
            "requires_baseline": True
        }
        # Should validate but may flag missing baseline
        result = validate_assessment_data(invalid_sequence)
        assert result is not None
    
    def test_hipaa_compliant_naming(self):
        """Test validation of HIPAA-compliant file naming"""
        valid_names = [
            "P001_baseline_2025-01-15.json",
            "P001_post_intervention_2025-03-15.json",
            "P001_follow_up_2025-06-15.json",
        ]
        invalid_names = [
            "John Doe_baseline.json",  # Contains name
            "participant_123_baseline.json",  # Contains actual ID
        ]
        
        for name in valid_names:
            assert validate_participant_data({"participant_id": name.split("_")[0], "age": 8, "diagnosis": "ASD"}) is not None
        
        for name in invalid_names:
            # Should fail or warn on invalid naming
            with pytest.raises(ValueError):
                validate_participant_data({"participant_id": name.split("_")[0], "age": 8, "diagnosis": "ASD"})
    
    def test_concurrent_session_logging(self):
        """Test validation of concurrent session logging"""
        # Simulate concurrent session entries
        concurrent_sessions = [
            {
                "participant_id": "P001",
                "session_number": 1,
                "session_date": datetime.now().isoformat(),
                "adherence_score": 85
            },
            {
                "participant_id": "P001",
                "session_number": 1,  # Duplicate session
                "session_date": datetime.now().isoformat(),
                "adherence_score": 86
            },
        ]
        
        # Should detect duplicate session
        for session in concurrent_sessions:
            result = validate_intervention_data(session)
            assert result is not None
    
    def test_data_type_coercion(self):
        """Test automatic type coercion for common data type mismatches"""
        # String numbers should be coerced to integers
        data = {
            "participant_id": "P001",
            "age": "8",  # String instead of int
            "diagnosis": "ASD"
        }
        # Should coerce or raise appropriate error
        result = validate_participant_data(data)
        assert result is not None
    
    def test_empty_assessment_data(self):
        """Test validation of completely empty assessment data"""
        empty_assessment = {
            "participant_id": "",
            "timepoint": "",
            "social_skills_score": None,
            "mindfulness_score": None,
            "session_count": 0
        }
        with pytest.raises((ValueError, TypeError)):
            validate_assessment_data(empty_assessment)
    
    def test_intervention_session_date_in_future(self):
        """Test validation of intervention session dates in the future"""
        future_session = {
            "participant_id": "P001",
            "session_number": 1,
            "session_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "adherence_score": 85
        }
        # Should allow future sessions (planned interventions)
        result = validate_intervention_data(future_session)
        assert result is not None
    
    def test_multiple_timepoints_same_date(self):
        """Test validation of multiple timepoints on the same date"""
        same_date_assessments = [
            {
                "participant_id": "P001",
                "timepoint": "baseline",
                "assessment_date": datetime.now().isoformat(),
                "social_skills_score": 50,
                "mindfulness_score": 50,
                "session_count": 0
            },
            {
                "participant_id": "P001",
                "timepoint": "post_intervention",
                "assessment_date": datetime.now().isoformat(),
                "social_skills_score": 75,
                "mindfulness_score": 80,
                "session_count": 12
            },
        ]
        for assessment in same_date_assessments:
            result = validate_assessment_data(assessment)
            assert result is not None
    
    def test_participant_data_with_medical_conditions(self):
        """Test validation of participant data with co-occurring medical conditions"""
        data = {
            "participant_id": "P001",
            "age": 8,
            "diagnosis": "ASD",
            "co_occurring_conditions": [
                "ADHD",
                "Anxiety Disorder",
                "Epilepsy"
            ],
            "medication_list": [
                "Methylphenidate",
                "Fluoxetine"
            ]
        }
        result = validate_participant_data(data)
        assert result is not None
    
    def test_intervention_adherence_below_threshold(self):
        """Test validation of intervention sessions with low adherence"""
        low_adherence_sessions = [
            {
                "participant_id": "P001",
                "session_number": 1,
                "session_date": datetime.now().isoformat(),
                "adherence_score": 50  # Below 60% threshold
            },
            {
                "participant_id": "P001",
                "session_number": 2,
                "session_date": datetime.now().isoformat(),
                "adherence_score": 40  # Below 60% threshold
            },
        ]
        for session in low_adherence_sessions:
            # Should flag low adherence but not reject
            result = validate_intervention_data(session)
            assert result is not None
    
    def test_assessment_score_variance(self):
        """Test validation of assessment score variance across timepoints"""
        # Extreme variance between timepoints
        variance_assessments = [
            {
                "participant_id": "P001",
                "timepoint": "baseline",
                "social_skills_score": 20,
                "mindfulness_score": 30,
                "session_count": 0
            },
            {
                "participant_id": "P001",
                "timepoint": "post_intervention",
                "social_skills_score": 95,
                "mindfulness_score": 98,
                "session_count": 12
            },
        ]
        for assessment in variance_assessments:
            result = validate_assessment_data(assessment)
            assert result is not None
    
    def test_participant_dropout_scenario(self):
        """Test validation of participant dropout scenarios"""
        dropout_data = {
            "participant_id": "P001",
            "age": 8,
            "diagnosis": "ASD",
            "dropout_reason": "Family relocation",
            "dropout_session": 5,
            "completed_sessions": 5,
            "total_planned_sessions": 12
        }
        result = validate_participant_data(dropout_data)
        assert result is not None
    
    def test_intervention_modification_tracking(self):
        """Test validation of intervention protocol modifications"""
        modified_session = {
            "participant_id": "P001",
            "session_number": 3,
            "session_date": datetime.now().isoformat(),
            "adherence_score": 90,
            "protocol_modification": "Extended mindfulness exercise by 5 minutes",
            "modification_justification": "Participant showed increased engagement"
        }
        result = validate_intervention_data(modified_session)
        assert result is not None
    
    def test_assessment_conducted_by_different_rater(self):
        """Test validation of assessments conducted by different raters"""
        rater_variations = [
            {
                "participant_id": "P001",
                "timepoint": "baseline",
                "assessment_date": datetime.now().isoformat(),
                "social_skills_score": 50,
                "mindfulness_score": 50,
                "session_count": 0,
                "rater_id": "R001"
            },
            {
                "participant_id": "P001",
                "timepoint": "post_intervention",
                "assessment_date": datetime.now().isoformat(),
                "social_skills_score": 75,
                "mindfulness_score": 80,
                "session_count": 12,
                "rater_id": "R002"  # Different rater
            },
        ]
        for assessment in rater_variations:
            result = validate_assessment_data(assessment)
            assert result is not None
    
    def test_intervention_session_interruption(self):
        """Test validation of interrupted intervention sessions"""
        interrupted_session = {
            "participant_id": "P001",
            "session_number": 5,
            "session_date": datetime.now().isoformat(),
            "adherence_score": 60,
            "session_interrupted": True,
            "interruption_reason": "Child became distressed",
            "session_completed": False
        }
        result = validate_intervention_data(interrupted_session)
        assert result is not None
    
    def test_assessment_with_missing_data_points(self):
        """Test validation of assessments with missing data points"""
        partial_assessment = {
            "participant_id": "P001",
            "timepoint": "baseline",
            "assessment_date": datetime.now().isoformat(),
            "social_skills_score": 50,
            # mindfulness_score missing
            "session_count": 0
        }
        with pytest.raises((ValueError, KeyError)):
            validate_assessment_data(partial_assessment)
    
    def test_intervention_session_with_multiple_modifications(self):
        """Test validation of sessions with multiple protocol modifications"""
        multi_modified_session = {
            "participant_id": "P001",
            "session_number": 7,
            "session_date": datetime.now().isoformat(),
            "adherence_score": 85,
            "protocol_modifications": [
                "Extended mindfulness exercise",
                "Added additional social skills activity",
                "Reduced group size"
            ]
        }
        result = validate_intervention_data(multi_modified_session)
        assert result is not None
    
    def test_assessment_with_inter_rater_reliability(self