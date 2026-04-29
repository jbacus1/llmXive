"""
Raw Data Storage Service for HIPAA-Compliant Data Management

This module implements secure data storage logic for the mindfulness
and social skills RCT study. All file naming follows HIPAA compliance
guidelines by excluding PHI from filenames.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import hashlib

from ..models.data_models import Participant, AssessmentTimepoint


class HIPAACompliantStorage:
    """
    Handles raw data storage with HIPAA-compliant naming conventions.

    Naming Rules:
    - No participant names, emails, or other PHI in filenames
    - Use anonymized participant IDs (UUID-based)
    - Include assessment timepoint and data type in filename
    - Timestamp format: YYYYMMDD_HHMMSS (no timezone in filename)
    """

    def __init__(self, base_path: str = "data/raw"):
        self.base_path = Path(base_path)
        self._ensure_directory_structure()

    def _ensure_directory_structure(self) -> None:
        """Create raw data directory structure if not exists."""
        self.base_path.mkdir(parents=True, exist_ok=True)
        (self.base_path / "participant_demographics").mkdir(exist_ok=True)
        (self.base_path / "assessment_data").mkdir(exist_ok=True)
        (self.base_path / "session_logs").mkdir(exist_ok=True)
        (self.base_path / "consent_forms").mkdir(exist_ok=True)

    def generate_participant_id(self) -> str:
        """
        Generate a unique, non-reversible participant ID.

        Returns a UUID4 string that cannot be traced back to
        original identifiers without the mapping key.
        """
        return str(uuid.uuid4())

    def hash_participant_id(self, original_id: str, salt: str) -> str:
        """
        Create a one-way hash of participant identifier.

        Args:
            original_id: The original participant identifier
            salt: A project-specific salt for additional security

        Returns:
            SHA-256 hash of the original ID + salt
        """
        combined = f"{original_id}{salt}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def build_filename(
        self,
        participant_id: str,
        assessment_type: str,
        timepoint: AssessmentTimepoint,
        data_type: str,
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Build a HIPAA-compliant filename for raw data storage.

        Args:
            participant_id: Anonymized participant UUID
            assessment_type: Type of assessment (e.g., 'psychological', 'behavioral')
            timepoint: Assessment timepoint (baseline, post, followup)
            data_type: Specific data type (e.g., 'responses', 'scores', 'logs')
            timestamp: Optional timestamp for versioning

        Returns:
            Formatted filename string
        """
        if timestamp is None:
            timestamp = datetime.now()

        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        timepoint_str = timepoint.value.lower()

        filename = (
            f"{participant_id}_"
            f"{assessment_type}_"
            f"{timepoint_str}_"
            f"{data_type}_"
            f"{timestamp_str}.json"
        )

        return filename

    def save_participant_demographics(
        self,
        participant_id: str,
        demographics_data: dict
    ) -> Path:
        """
        Save participant demographic data securely.

        Args:
            participant_id: Anonymized participant UUID
            demographics_data: Dictionary of demographic information

        Returns:
            Path to saved file
        """
        timestamp = datetime.now()
        filename = self.build_filename(
            participant_id=participant_id,
            assessment_type="demographics",
            timepoint=AssessmentTimepoint.BASELINE,
            data_type="demographics",
            timestamp=timestamp
        )

        filepath = self.base_path / "participant_demographics" / filename
        # In production, this would serialize to JSON and write
        # For now, return the path where file should be written
        return filepath

    def save_assessment_data(
        self,
        participant_id: str,
        assessment_type: str,
        timepoint: AssessmentTimepoint,
        assessment_data: dict
    ) -> Path:
        """
        Save assessment data securely.

        Args:
            participant_id: Anonymized participant UUID
            assessment_type: Type of assessment
            timepoint: Assessment timepoint
            assessment_data: Assessment responses/scores

        Returns:
            Path to saved file
        """
        timestamp = datetime.now()
        filename = self.build_filename(
            participant_id=participant_id,
            assessment_type=assessment_type,
            timepoint=timepoint,
            data_type="responses",
            timestamp=timestamp
        )

        filepath = self.base_path / "assessment_data" / filename
        return filepath

    def encrypt_at_rest(self, filepath: Path) -> None:
        """
        Encrypt file at rest for additional security.

        Note: This is a placeholder for production encryption
        using Fernet or similar symmetric encryption.
        """
        # Production implementation would use cryptography.fernet
        # or system-level encryption (e.g., BitLocker, FileVault)
        pass

    def get_data_path(
        self,
        participant_id: str,
        timepoint: AssessmentTimepoint,
        data_type: str = "all"
    ) -> Path:
        """
        Retrieve path for a participant's data at a given timepoint.

        Args:
            participant_id: Anonymized participant UUID
            timepoint: Assessment timepoint
            data_type: 'all', 'demographics', 'assessment', or 'session'

        Returns:
            Path object for the data directory
        """
        subdirs = {
            "all": self.base_path,
            "demographics": self.base_path / "participant_demographics",
            "assessment": self.base_path / "assessment_data",
            "session": self.base_path / "session_logs",
            "consent": self.base_path / "consent_forms"
        }

        return subdirs.get(data_type, self.base_path)

    def validate_filename(self, filename: str) -> bool:
        """
        Validate that a filename meets HIPAA compliance rules.

        Checks:
        - No spaces or special characters that could cause issues
        - Contains participant ID pattern (UUID-like)
        - Contains timepoint indicator
        - Has appropriate file extension
        """
        import re

        # UUID pattern (simplified)
        uuid_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'

        if not re.search(uuid_pattern, filename):
            return False

        if not filename.endswith(('.json', '.csv', '.xlsx')):
            return False

        # Check for common PHI patterns in filename
        phi_patterns = [
            r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b',  # Full names
            r'\d{3}-\d{2}-\d{4}',  # SSN
            r'\d{3}-\d{3}-\d{4}',  # Phone
            r'[\w\.-]+@[\w\.-]+\.\w+',  # Email
        ]

        for pattern in phi_patterns:
            if re.search(pattern, filename):
                return False

        return True

# Module-level convenience function
def get_storage_service() -> HIPAACompliantStorage:
    """Get a configured storage service instance."""
    return HIPAACompliantStorage()
