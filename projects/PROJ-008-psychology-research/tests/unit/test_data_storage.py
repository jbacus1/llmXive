"""
Unit tests for HIPAA-compliant data storage logic.

Tests verify that:
- Filenames do not contain PHI
- Participant IDs are properly anonymized
- Directory structure is created correctly
- Filename validation works as expected
"""

import pytest
from datetime import datetime
from pathlib import Path

from src.services.data_storage import HIPAACompliantStorage
from src.models.data_models import AssessmentTimepoint


class TestHIPAACompliantStorage:
    """Test suite for HIPAACompliantStorage class."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create storage instance with temporary directory."""
        return HIPAACompliantStorage(base_path=str(tmp_path / "data" / "raw"))

    def test_directory_structure_created(self, storage):
        """Verify that all required directories are created."""
        expected_dirs = [
            "participant_demographics",
            "assessment_data",
            "session_logs",
            "consent_forms"
        ]

        for dir_name in expected_dirs:
            assert (storage.base_path / dir_name).exists()

    def test_participant_id_generation(self, storage):
        """Verify participant IDs are unique UUIDs."""
        id1 = storage.generate_participant_id()
        id2 = storage.generate_participant_id()

        assert id1 != id2
        assert len(id1) == 36  # Standard UUID format
        assert id1 != id2

    def test_filename_no_phi(self, storage):
        """Verify generated filenames do not contain PHI."""
        filename = storage.build_filename(
            participant_id="test-participant-id",
            assessment_type="psychological",
            timepoint=AssessmentTimepoint.BASELINE,
            data_type="responses"
        )

        # Check for common PHI patterns
        assert "John" not in filename
        assert "Smith" not in filename
        assert "@" not in filename
        assert "ssn" not in filename.lower()

    def test_filename_format(self, storage):
        """Verify filename follows expected format."""
        filename = storage.build_filename(
            participant_id="test-participant-id",
            assessment_type="psychological",
            timepoint=AssessmentTimepoint.POST,
            data_type="responses"
        )

        assert "test-participant-id" in filename
        assert "psychological" in filename
        assert "post" in filename
        assert "responses" in filename
        assert filename.endswith(".json")

    def test_hash_participant_id(self, storage):
        """Verify participant ID hashing is one-way."""
        original = "participant_123"
        salt = "research_project_salt_2025"

        hashed = storage.hash_participant_id(original, salt)

        assert len(hashed) == 16  # Truncated to 16 chars
        assert hashed != original
        assert hashed.isalnum()

    def test_validate_filename_valid(self, storage):
        """Test validation accepts compliant filenames."""
        valid_filename = (
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890_"
            "psychological_baseline_responses_20250101_120000.json"
        )

        assert storage.validate_filename(valid_filename)

    def test_validate_filename_invalid_phi(self, storage):
        """Test validation rejects filenames with PHI."""
        invalid_filenames = [
            "John_Smith_baseline.json",  # Contains name
            "participant_123@company.com.json",  # Contains email
            "123-45-6789_data.json",  # Contains SSN
            "555-123-4567_call.json",  # Contains phone
        ]

        for filename in invalid_filenames:
            assert not storage.validate_filename(filename)

    def test_get_data_path(self, storage):
        """Test data path retrieval for different types."""
        test_id = "test-participant-id"
        timepoint = AssessmentTimepoint.BASELINE

        # Test different data types
        assert storage.get_data_path(test_id, timepoint, "all") == storage.base_path
        assert storage.get_data_path(
            test_id, timepoint, "demographics"
        ) == storage.base_path / "participant_demographics"
        assert storage.get_data_path(
            test_id, timepoint, "assessment"
        ) == storage.base_path / "assessment_data"

    def test_timepoint_in_filename(self, storage):
        """Verify timepoint is correctly reflected in filename."""
        baseline_file = storage.build_filename(
            participant_id="test-id",
            assessment_type="test",
            timepoint=AssessmentTimepoint.BASELINE,
            data_type="data"
        )
        post_file = storage.build_filename(
            participant_id="test-id",
            assessment_type="test",
            timepoint=AssessmentTimepoint.POST,
            data_type="data"
        )
        followup_file = storage.build_filename(
            participant_id="test-id",
            assessment_type="test",
            timepoint=AssessmentTimepoint.FOLLOWUP,
            data_type="data"
        )

        assert "baseline" in baseline_file
        assert "post" in post_file
        assert "followup" in followup_file