"""
Data Collector Service for ASD Mindfulness Research Project

This module provides the interface for collecting, validating, and
storing participant data in a HIPAA-compliant manner.

Responsibilities:
- Validate incoming data against schema contracts
- Manage raw data storage with de-identified naming
- Log data collection operations (without PHI)
- Provide error handling for data ingestion pipeline

Dependencies:
- src/models/data_models.py: Pydantic models for participant/assessment data
- src/lib/validators.py: Schema compliance validation utilities
- contracts/: YAML schema definitions
"""

import logging
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

from pydantic import ValidationError

# Import project models and validators
from src.models.data_models import (
    Participant,
    Assessment,
    InterventionSession,
    ConsentForm,
)
from src.lib.validators import (
    validate_participant_data,
    validate_assessment_data,
    validate_intervention_data,
    validate_consent_data,
    SchemaValidationError,
)

# Configure logger for data collection operations
logger = logging.getLogger(__name__)


@dataclass
class DataCollectionResult:
    """Result object for data collection operations."""

    success: bool
    participant_id: Optional[str] = None
    errors: List[str] = None
    warnings: List[str] = None
    storage_path: Optional[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class CollectionBatchResult:
    """Result object for batch data collection operations."""

    total_submitted: int
    successful: int
    failed: int
    results: List[DataCollectionResult] = None

    def __post_init__(self):
        if self.results is None:
            self.results = []


class DataCollector:
    """
    Main interface for data collection operations.

    This class provides methods for:
    - Collecting and validating participant demographic data
    - Collecting and validating assessment data (pre/post/follow-up)
    - Collecting and validating intervention session logs
    - Managing raw data storage with HIPAA-compliant naming

    Usage:
        collector = DataCollector(data_root="data/raw")
        result = collector.collect_participant(participant_data)
        if result.success:
            print(f"Stored at: {result.storage_path}")
    """

    def __init__(
        self,
        data_root: str = "data/raw",
        log_level: int = logging.INFO,
    ):
        """
        Initialize the DataCollector.

        Args:
            data_root: Root directory for raw data storage
            log_level: Logging level for data collection operations
        """
        self.data_root = Path(data_root)
        self._setup_directories()
        self._configure_logging(log_level)
        logger.info(f"DataCollector initialized with root: {self.data_root}")

    def _setup_directories(self) -> None:
        """Create required directory structure for data storage."""
        directories = [
            "participants",
            "assessments",
            "interventions",
            "consent_forms",
            "processed",
        ]

        for dir_name in directories:
            dir_path = self.data_root / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {dir_path}")

    def _configure_logging(self, level: int) -> None:
        """Configure logging for data collection operations."""
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(level)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(level)

    def _generate_deidentified_id(self, original_id: str) -> str:
        """
        Generate a de-identified participant ID for storage.

        Uses SHA-256 hash with salt to create a consistent but
        non-reversible identifier.

        Args:
            original_id: Original participant identifier (PII)

        Returns:
            De-identified hash-based identifier
        """
        # Salt for additional security layer
        salt = os.environ.get("DATA_SALT", "asdr2025_mindfulness")
        combined = f"{salt}:{original_id}"
        hash_value = hashlib.sha256(combined.encode()).hexdigest()[:12]
        return f"P{hash_value.upper()}"

    def _validate_path_security(self, path: Path) -> bool:
        """
        Validate that a path is within allowed data directories.

        Prevents path traversal attacks and ensures data stays
        within project boundaries.

        Args:
            path: Path to validate

        Returns:
            True if path is secure, False otherwise
        """
        try:
            resolved = path.resolve()
            return str(resolved).startswith(str(self.data_root.resolve()))
        except (ValueError, RuntimeError):
            return False

    def collect_participant(
        self,
        participant_data: Dict[str, Any],
        original_id: str,
        overwrite: bool = False,
    ) -> DataCollectionResult:
        """
        Collect and store participant demographic data.

        Args:
            participant_data: Dictionary containing participant demographics
            original_id: Original participant identifier (will be de-identified)
            overwrite: Whether to overwrite existing data

        Returns:
            DataCollectionResult with success status and storage path
        """
        result = DataCollectionResult(success=False, participant_id=original_id)

        try:
            # Validate against schema
            validation_result = validate_participant_data(participant_data)

            if not validation_result.is_valid:
                result.errors.extend(validation_result.errors)
                logger.warning(
                    f"Participant data validation failed for {original_id}: "
                    f"{validation_result.errors}"
                )
                return result

            # Create Pydantic model instance
            try:
                participant = Participant(**participant_data)
            except ValidationError as e:
                result.errors.append(f"Model validation error: {str(e)}")
                logger.error(f"Participant model validation failed: {e}")
                return result

            # Generate de-identified ID
            deidentified_id = self._generate_deidentified_id(original_id)
            result.participant_id = deidentified_id

            # Create storage path
            storage_dir = self.data_root / "participants" / deidentified_id
            storage_dir.mkdir(parents=True, exist_ok=True)

            # Check for existing data
            existing_path = storage_dir / "demographics.json"
            if existing_path.exists() and not overwrite:
                result.errors.append("Participant data already exists. Set overwrite=True to update.")
                result.warnings.append(f"Existing data at: {existing_path}")
                logger.warning(f"Existing participant data found: {deidentified_id}")
                return result

            # Store data
            import json
            storage_path = storage_dir / "demographics.json"
            with open(storage_path, "w") as f:
                json.dump(participant.model_dump(), f, indent=2)

            # Log operation (without PHI)
            logger.info(
                f"Participant data collected and stored: {deidentified_id} "
                f"(original_id masked)"
            )

            result.success = True
            result.storage_path = str(storage_path)

        except Exception as e:
            result.errors.append(f"Unexpected error: {str(e)}")
            logger.error(f"Error collecting participant data: {e}", exc_info=True)

        return result

    def collect_assessment(
        self,
        assessment_data: Dict[str, Any],
        participant_id: str,
        timepoint: str,
        overwrite: bool = False,
    ) -> DataCollectionResult:
        """
        Collect and store assessment data for a participant.

        Args:
            assessment_data: Dictionary containing assessment measures
            participant_id: De-identified participant ID
            timepoint: Assessment timepoint (baseline, post, followup)
            overwrite: Whether to overwrite existing data

        Returns:
            DataCollectionResult with success status and storage path
        """
        result = DataCollectionResult(success=False, participant_id=participant_id)

        valid_timepoints = ["baseline", "post", "followup"]
        if timepoint not in valid_timepoints:
            result.errors.append(
                f"Invalid timepoint: {timepoint}. Must be one of {valid_timepoints}"
            )
            logger.error(f"Invalid assessment timepoint: {timepoint}")
            return result

        try:
            # Validate against schema
            validation_result = validate_assessment_data(assessment_data)

            if not validation_result.is_valid:
                result.errors.extend(validation_result.errors)
                logger.warning(
                    f"Assessment data validation failed for {participant_id}: "
                    f"{validation_result.errors}"
                )
                return result

            # Create Pydantic model instance
            try:
                assessment = Assessment(**assessment_data)
            except ValidationError as e:
                result.errors.append(f"Model validation error: {str(e)}")
                logger.error(f"Assessment model validation failed: {e}")
                return result

            # Create storage path
            storage_dir = (
                self.data_root / "assessments" / participant_id / timepoint
            )
            storage_dir.mkdir(parents=True, exist_ok=True)

            # Check for existing data
            existing_path = storage_dir / "assessment.json"
            if existing_path.exists() and not overwrite:
                result.errors.append("Assessment data already exists. Set overwrite=True to update.")
                result.warnings.append(f"Existing data at: {existing_path}")
                logger.warning(f"Existing assessment data found: {participant_id}/{timepoint}")
                return result

            # Store data
            import json
            storage_path = storage_dir / "assessment.json"
            with open(storage_path, "w") as f:
                json.dump(assessment.model_dump(), f, indent=2)

            # Log operation (without PHI)
            logger.info(
                f"Assessment data collected and stored: {participant_id} "
                f"at {timepoint}"
            )

            result.success = True
            result.storage_path = str(storage_path)

        except Exception as e:
            result.errors.append(f"Unexpected error: {str(e)}")
            logger.error(f"Error collecting assessment data: {e}", exc_info=True)

        return result

    def collect_intervention_session(
        self,
        session_data: Dict[str, Any],
        participant_id: str,
        session_number: int,
        overwrite: bool = False,
    ) -> DataCollectionResult:
        """
        Collect and store intervention session log data.

        Args:
            session_data: Dictionary containing session details and adherence
            participant_id: De-identified participant ID
            session_number: Session number (1-8 or 1-12 based on protocol)
            overwrite: Whether to overwrite existing data

        Returns:
            DataCollectionResult with success status and storage path
        """
        result = DataCollectionResult(success=False, participant_id=participant_id)

        try:
            # Validate session number
            if session_number < 1 or session_number > 12:
                result.errors.append(
                    f"Invalid session number: {session_number}. Must be 1-12."
                )
                logger.error(f"Invalid intervention session number: {session_number}")
                return result

            # Validate against schema
            validation_result = validate_intervention_data(session_data)

            if not validation_result.is_valid:
                result.errors.extend(validation_result.errors)
                logger.warning(
                    f"Intervention data validation failed for {participant_id}/S{session_number}: "
                    f"{validation_result.errors}"
                )
                return result

            # Create Pydantic model instance
            try:
                session = InterventionSession(**session_data)
            except ValidationError as e:
                result.errors.append(f"Model validation error: {str(e)}")
                logger.error(f"Intervention session model validation failed: {e}")
                return result

            # Create storage path
            storage_dir = (
                self.data_root / "interventions" / participant_id / f"session_{session_number:02d}"
            )
            storage_dir.mkdir(parents=True, exist_ok=True)

            # Check for existing data
            existing_path = storage_dir / "session_log.json"
            if existing_path.exists() and not overwrite:
                result.errors.append("Session log already exists. Set overwrite=True to update.")
                result.warnings.append(f"Existing data at: {existing_path}")
                logger.warning(f"Existing session log found: {participant_id}/S{session_number}")
                return result

            # Store data
            import json
            storage_path = storage_dir / "session_log.json"
            with open(storage_path, "w") as f:
                json.dump(session.model_dump(), f, indent=2)

            # Log operation (without PHI)
            logger.info(
                f"Intervention session log collected: {participant_id} "
                f"Session {session_number}"
            )

            result.success = True
            result.storage_path = str(storage_path)

        except Exception as e:
            result.errors.append(f"Unexpected error: {str(e)}")
            logger.error(f"Error collecting intervention session data: {e}", exc_info=True)

        return result

    def collect_consent_form(
        self,
        consent_data: Dict[str, Any],
        participant_id: str,
        form_type: str,
        overwrite: bool = False,
    ) -> DataCollectionResult:
        """
        Collect and store consent form data.

        Args:
            consent_data: Dictionary containing consent form responses
            participant_id: De-identified participant ID
            form_type: Type of consent form (parent or child)
            overwrite: Whether to overwrite existing data

        Returns:
            DataCollectionResult with success status and storage path
        """
        result = DataCollectionResult(success=False, participant_id=participant_id)

        valid_form_types = ["parent", "child", "both"]
        if form_type not in valid_form_types:
            result.errors.append(
                f"Invalid form type: {form_type}. Must be one of {valid_form_types}"
            )
            logger.error(f"Invalid consent form type: {form_type}")
            return result

        try:
            # Validate against schema
            validation_result = validate_consent_data(consent_data)

            if not validation_result.is_valid:
                result.errors.extend(validation_result.errors)
                logger.warning(
                    f"Consent data validation failed for {participant_id}: "
                    f"{validation_result.errors}"
                )
                return result

            # Create Pydantic model instance
            try:
                consent = ConsentForm(**consent_data)
            except ValidationError as e:
                result.errors.append(f"Model validation error: {str(e)}")
                logger.error(f"Consent form model validation failed: {e}")
                return result

            # Create storage path
            storage_dir = (
                self.data_root / "consent_forms" / participant_id
            )
            storage_dir.mkdir(parents=True, exist_ok=True)

            # Check for existing data
            existing_path = storage_dir / f"consent_{form_type}.json"
            if existing_path.exists() and not overwrite:
                result.errors.append("Consent form already exists. Set overwrite=True to update.")
                result.warnings.append(f"Existing data at: {existing_path}")
                logger.warning(f"Existing consent form found: {participant_id}/{form_type}")
                return result

            # Store data
            import json
            storage_path = storage_dir / f"consent_{form_type}.json"
            with open(storage_path, "w") as f:
                json.dump(consent.model_dump(), f, indent=2)

            # Log operation (without PHI)
            logger.info(
                f"Consent form collected: {participant_id} ({form_type})"
            )

            result.success = True
            result.storage_path = str(storage_path)

        except Exception as e:
            result.errors.append(f"Unexpected error: {str(e)}")
            logger.error(f"Error collecting consent form data: {e}", exc_info=True)

        return result

    def collect_batch_participants(
        self,
        participants: List[Dict[str, Any]],
        original_ids: List[str],
        overwrite: bool = False,
    ) -> CollectionBatchResult:
        """
        Collect multiple participants in a batch operation.

        Args:
            participants: List of participant data dictionaries
            original_ids: List of original participant identifiers
            overwrite: Whether to overwrite existing data

        Returns:
            CollectionBatchResult with summary of batch operation
        """
        if len(participants) != len(original_ids):
            raise ValueError(
                f"Number of participants ({len(participants)}) must match "
                f"number of IDs ({len(original_ids)})"
            )

        results = []
        successful = 0
        failed = 0

        for participant_data, original_id in zip(participants, original_ids):
            result = self.collect_participant(
                participant_data=participant_data,
                original_id=original_id,
                overwrite=overwrite,
            )
            results.append(result)

            if result.success:
                successful += 1
            else:
                failed += 1

        batch_result = CollectionBatchResult(
            total_submitted=len(participants),
            successful=successful,
            failed=failed,
            results=results,
        )

        logger.info(
            f"Batch collection complete: {successful}/{len(participants)} successful"
        )

        return batch_result

    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all collected data.

        Returns:
            Dictionary with counts and paths for each data type
        """
        summary = {
            "data_root": str(self.data_root),
            "last_updated": datetime.now().isoformat(),
            "participants": {
                "count": 0,
                "path": str(self.data_root / "participants"),
            },
            "assessments": {
                "count": 0,
                "path": str(self.data_root / "assessments"),
            },
            "interventions": {
                "count": 0,
                "path": str(self.data_root / "interventions"),
            },
            "consent_forms": {
                "count": 0,
                "path": str(self.data_root / "consent_forms"),
            },
        }

        # Count files in each directory
        for key, dir_path in summary.items():
            if key == "data_root" or key == "last_updated":
                continue

            dir_path = Path(dir_path["path"])
            if dir_path.exists():
                dir_path["count"] = len(list(dir_path.glob("**/*.json")))

        logger.debug(f"Data summary generated: {summary}")
        return summary