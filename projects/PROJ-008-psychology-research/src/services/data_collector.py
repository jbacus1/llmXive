"""
Data Collector Service for Mindfulness and Social Skills RCT

Handles safe, schema-compliant data entry for 60 participants across 3 timepoints.
HIPAA-compliant logging (no PII in log messages).
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..models.data_models import Participant, Assessment
from ..lib.validators import validate_participant, validate_assessment

# Configure module-level logger
logger = logging.getLogger(__name__)

# HIPAA-compliant log sanitization
PII_FIELDS = {'name', 'ssn', 'mrn', 'dob', 'address', 'phone', 'email'}

class DataCollector:
    """
    Service for collecting and storing research data.
    
    Ensures all data operations are logged for audit trails while
    maintaining HIPAA compliance (no PII in log messages).
    """

    def __init__(self, data_root: str, log_level: int = logging.INFO):
        """
        Initialize data collector.

        Args:
            data_root: Root directory for raw data storage
            log_level: Logging verbosity level
        """
        self.data_root = Path(data_root)
        self.raw_dir = self.data_root / 'raw'
        self.raw_dir.mkdir(parents=True, exist_ok=True)

        # Configure file handler for audit trail
        self._setup_logging(log_level)
        logger.info("DataCollector initialized with data_root=%s", self.data_root)

    def _setup_logging(self, level: int) -> None:
        """Configure logging handlers for audit compliance."""
        logger.setLevel(level)

        # Prevent duplicate handlers
        if logger.handlers:
            return

        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler for audit trail
        log_file = self.data_root.parent / 'logs' / 'data_collection.log'
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    def _sanitize_for_logging(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove PII from data before logging."""
        sanitized = {}
        for key, value in data.items():
            if key.lower() in PII_FIELDS:
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = value
        return sanitized

    def collect_participant_data(
        self,
        participant_id: str,
        participant_data: Dict[str, Any]
    ) -> Optional[Participant]:
        """
        Collect and validate participant demographic data.

        Args:
            participant_id: Unique participant identifier (non-PII)
            participant_data: Raw participant data dictionary

        Returns:
            Validated Participant model or None on validation failure
        """
        logger.info("Starting participant data collection for ID=%s", participant_id)

        try:
            # Validate against schema
            logger.debug("Validating participant data for ID=%s", participant_id)
            sanitized_data = self._sanitize_for_logging(participant_data)
            logger.debug("Sanitized data: %s", sanitized_data)

            is_valid, errors = validate_participant(participant_data)
            if not is_valid:
                logger.error(
                    "Participant validation failed for ID=%s with errors: %s",
                    participant_id, errors
                )
                return None

            # Create model
            participant = Participant(**participant_data)
            logger.info("Participant created successfully for ID=%s", participant_id)

            # Store raw data
            self._store_raw_data(participant_id, participant_data)

            return participant

        except Exception as e:
            logger.exception(
                "Unexpected error during participant collection for ID=%s: %s",
                participant_id, str(e)
            )
            return None

    def collect_assessment_data(
        self,
        participant_id: str,
        timepoint: str,
        assessment_data: Dict[str, Any]
    ) -> Optional[Assessment]:
        """
        Collect and validate assessment data for a timepoint.

        Args:
            participant_id: Unique participant identifier (non-PII)
            timepoint: Assessment timepoint (baseline, post, followup)
            assessment_data: Raw assessment data dictionary

        Returns:
            Validated Assessment model or None on validation failure
        """
        logger.info(
            "Starting assessment data collection for ID=%s timepoint=%s",
            participant_id, timepoint
        )

        try:
            # Validate against schema
            logger.debug("Validating assessment data for ID=%s timepoint=%s",
                        participant_id, timepoint)
            sanitized_data = self._sanitize_for_logging(assessment_data)
            logger.debug("Sanitized assessment data: %s", sanitized_data)

            is_valid, errors = validate_assessment(assessment_data)
            if not is_valid:
                logger.error(
                    "Assessment validation failed for ID=%s timepoint=%s with errors: %s",
                    participant_id, timepoint, errors
                )
                return None

            # Create model
            assessment = Assessment(
                participant_id=participant_id,
                timepoint=timepoint,
                **assessment_data
            )
            logger.info(
                "Assessment created successfully for ID=%s timepoint=%s",
                participant_id, timepoint
            )

            # Store raw data
            self._store_raw_data(f"{participant_id}_{timepoint}", assessment_data)

            return assessment

        except Exception as e:
            logger.exception(
                "Unexpected error during assessment collection for ID=%s timepoint=%s: %s",
                participant_id, timepoint, str(e)
            )
            return None

    def _store_raw_data(self, identifier: str, data: Dict[str, Any]) -> None:
        """
        Store raw data with HIPAA-compliant naming.

        Args:
            identifier: Non-PII identifier for the file
            data: Data to store
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{identifier}_{timestamp}.json"
        filepath = self.raw_dir / filename

        try:
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info("Raw data stored successfully at %s", filepath)
        except Exception as e:
            logger.exception("Failed to store raw data at %s: %s", filepath, str(e))
            raise

    def get_collection_stats(self) -> Dict[str, int]:
        """
        Get statistics about collected data.

        Returns:
            Dictionary with collection counts by type
        """
        logger.info("Generating collection statistics")
        stats = {
            'participant_files': 0,
            'assessment_files': 0,
            'total_files': 0
        }

        try:
            for file in self.raw_dir.glob('*.json'):
                stats['total_files'] += 1
                if file.name.count('_') >= 2:
                    # Likely assessment file (ID_timepoint_timestamp.json)
                    stats['assessment_files'] += 1
                else:
                    stats['participant_files'] += 1

            logger.info("Collection stats: %s", stats)
        except Exception as e:
            logger.exception("Error generating collection stats: %s", str(e))

        return stats

    def close(self) -> None:
        """Close all logging handlers and flush buffers."""
        logger.info("Closing DataCollector and flushing logs")
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)