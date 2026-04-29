"""
Analysis Service for Mindfulness and Social Skills RCT Study

This service provides the core infrastructure for statistical analysis
of collected participant data. It integrates with User Story 1 data
collection components and prepares data for statistical routines.

Responsible: US2 - Statistical Analysis Pipeline
Dependencies: T008 (data_models), T009 (validators), US1 components
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

import pandas as pd
from pydantic import BaseModel, ValidationError

from src.models.data_models import (
    Participant,
    Assessment,
    InterventionSession,
    ProcessedData
)
from src.lib.validators import (
    validate_participant_schema,
    validate_assessment_schema,
    validate_intervention_schema
)

logger = logging.getLogger(__name__)


@dataclass
class AnalysisConfig:
    """Configuration for analysis pipeline."""
    data_directory: Path = field(default=Path("data/processed"))
    raw_directory: Path = field(default=Path("data/raw"))
    contracts_directory: Path = field(default=Path("contracts"))
    report_directory: Path = field(default=Path("docs"))
    timepoints: List[str] = field(default_factory=lambda: ["baseline", "post", "followup"])
    outcome_measures: List[str] = field(default_factory=lambda: [
        "social_skills_score",
        "mindfulness_score",
        "adaptive_behavior_score"
    ])


@dataclass
class AnalysisResult:
    """Container for analysis results."""
    participant_id: str
    group: str  # 'intervention' or 'control'
    timepoint: str
    measures: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)


class AnalysisService:
    """
    Main service for statistical analysis pipeline.

    This service orchestrates data loading, validation, statistical
    analysis, and report generation for the RCT study.

    Attributes:
        config: Analysis configuration settings
        participants: Loaded participant data
        assessments: Loaded assessment data
        interventions: Loaded intervention session data
    """

    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Initialize the analysis service.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or AnalysisConfig()
        self.participants: List[Participant] = []
        self.assessments: List[Assessment] = []
        self.interventions: List[InterventionSession] = []
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for analysis operations."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger.info("AnalysisService initialized with data directory: %s",
                   self.config.data_directory)

    def load_participant_data(self, file_path: Optional[Path] = None) -> List[Participant]:
        """
        Load participant data from processed files.

        Args:
            file_path: Optional specific file path. Loads all from
                       data_directory if not provided.

        Returns:
            List of validated Participant models.

        Raises:
            FileNotFoundError: If data file does not exist.
            ValidationError: If data fails schema validation.
        """
        if file_path is None:
            file_path = self.config.data_directory / "participants.csv"

        if not file_path.exists():
            raise FileNotFoundError(f"Participant data not found: {file_path}")

        logger.info("Loading participant data from %s", file_path)
        df = pd.read_csv(file_path)

        participants = []
        for _, row in df.iterrows():
            try:
                participant = Participant(**row.to_dict())
                validate_participant_schema(participant.model_dump())
                participants.append(participant)
            except ValidationError as e:
                logger.error("Validation error for participant %s: %s",
                            row.get('participant_id'), e)
                raise

        self.participants = participants
        logger.info("Loaded %d participants", len(participants))
        return participants

    def load_assessment_data(self, file_path: Optional[Path] = None) -> List[Assessment]:
        """
        Load assessment data from processed files.

        Args:
            file_path: Optional specific file path. Loads all from
                       data_directory if not provided.

        Returns:
            List of validated Assessment models.

        Raises:
            FileNotFoundError: If data file does not exist.
            ValidationError: If data fails schema validation.
        """
        if file_path is None:
            file_path = self.config.data_directory / "assessments.csv"

        if not file_path.exists():
            raise FileNotFoundError(f"Assessment data not found: {file_path}")

        logger.info("Loading assessment data from %s", file_path)
        df = pd.read_csv(file_path)

        assessments = []
        for _, row in df.iterrows():
            try:
                assessment = Assessment(**row.to_dict())
                validate_assessment_schema(assessment.model_dump())
                assessments.append(assessment)
            except ValidationError as e:
                logger.error("Validation error for assessment %s: %s",
                            row.get('assessment_id'), e)
                raise

        self.assessments = assessments
        logger.info("Loaded %d assessments", len(assessments))
        return assessments

    def load_intervention_data(self, file_path: Optional[Path] = None) -> List[InterventionSession]:
        """
        Load intervention session data from processed files.

        Args:
            file_path: Optional specific file path. Loads all from
                       data_directory if not provided.

        Returns:
            List of validated InterventionSession models.

        Raises:
            FileNotFoundError: If data file does not exist.
            ValidationError: If data fails schema validation.
        """
        if file_path is None:
            file_path = self.config.data_directory / "intervention_sessions.csv"

        if not file_path.exists():
            raise FileNotFoundError(f"Intervention data not found: {file_path}")

        logger.info("Loading intervention data from %s", file_path)
        df = pd.read_csv(file_path)

        interventions = []
        for _, row in df.iterrows():
            try:
                intervention = InterventionSession(**row.to_dict())
                validate_intervention_schema(intervention.model_dump())
                interventions.append(intervention)
            except ValidationError as e:
                logger.error("Validation error for session %s: %s",
                            row.get('session_id'), e)
                raise

        self.interventions = interventions
        logger.info("Loaded %d intervention sessions", len(interventions))
        return interventions

    def load_all_data(self) -> Dict[str, Any]:
        """
        Load all data sources for analysis.

        Returns:
            Dictionary containing all loaded data.

        Raises:
            FileNotFoundError: If any required data file is missing.
        """
        logger.info("Loading all analysis data sources")

        data = {
            'participants': self.load_participant_data(),
            'assessments': self.load_assessment_data(),
            'interventions': self.load_intervention_data()
        }

        logger.info("All data loaded successfully")
        return data

    def get_group_data(self, group: str) -> pd.DataFrame:
        """
        Get data filtered by intervention group.

        Args:
            group: Either 'intervention' or 'control'.

        Returns:
            DataFrame with participant and assessment data for the group.

        Raises:
            ValueError: If group is invalid or data not loaded.
        """
        if not self.participants:
            raise ValueError("No participant data loaded. Call load_all_data() first.")

        if group not in ['intervention', 'control']:
            raise ValueError(f"Invalid group: {group}. Must be 'intervention' or 'control'.")

        df = pd.DataFrame([p.model_dump() for p in self.participants])
        return df[df['group'] == group]

    def get_longitudinal_data(self, participant_id: str) -> pd.DataFrame:
        """
        Get longitudinal assessment data for a participant.

        Args:
            participant_id: The participant identifier.

        Returns:
            DataFrame with assessment data across timepoints.

        Raises:
            ValueError: If participant not found or data not loaded.
        """
        if not self.assessments:
            raise ValueError("No assessment data loaded. Call load_all_data() first.")

        df = pd.DataFrame([a.model_dump() for a in self.assessments])
        participant_data = df[df['participant_id'] == participant_id]

        if participant_data.empty:
            raise ValueError(f"No data found for participant: {participant_id}")

        return participant_data

    def prepare_for_analysis(self) -> ProcessedData:
        """
        Prepare and validate all data for statistical analysis.

        Returns:
            ProcessedData object ready for statistical routines.
        """
        logger.info("Preparing data for statistical analysis")

        # Validate all loaded data
        self._validate_data_integrity()

        # Create processed data structure
        processed = ProcessedData(
            participants=self.participants,
            assessments=self.assessments,
            interventions=self.interventions,
            config=self.config
        )

        logger.info("Data preparation complete")
        return processed

    def _validate_data_integrity(self) -> None:
        """
        Validate that all data sources are consistent.

        Checks:
        - All participants have assessments at all timepoints
        - Intervention group has session logs
        - No missing required fields
        """
        logger.info("Validating data integrity")

        participant_ids = {p.participant_id for p in self.participants}
        assessment_participant_ids = {a.participant_id for a in self.assessments}

        # Check all participants have assessments
        missing = participant_ids - assessment_participant_ids
        if missing:
            logger.warning("Participants without assessments: %s", missing)

        # Check timepoint coverage
        for pid in participant_ids:
            participant_assessments = [
                a for a in self.assessments if a.participant_id == pid
            ]
            timepoints_covered = {a.timepoint for a in participant_assessments}
            missing_timepoints = set(self.config.timepoints) - timepoints_covered
            if missing_timepoints:
                logger.warning(
                    "Participant %s missing timepoints: %s",
                    pid, missing_timepoints
                )

        logger.info("Data integrity validation complete")

    def run_treatment_effect_analysis(self) -> Dict[str, Any]:
        """
        Placeholder for treatment effect analysis (T021).

        This method will be implemented with statistical routines
        including t-tests and ANOVA for the RCT design.

        Returns:
            Dictionary with analysis results (to be implemented).
        """
        logger.info("Treatment effect analysis not yet implemented (T021)")
        return {
            'status': 'pending',
            'message': 'Statistical routines to be implemented in T021'
        }

    def generate_report(self, output_path: Optional[Path] = None) -> Path:
        """
        Placeholder for report generation (T022).

        This method will generate Markdown/PDF reports of analysis results.

        Args:
            output_path: Optional output path. Uses report_directory if not provided.

        Returns:
            Path to generated report file.
        """
        if output_path is None:
            output_path = self.config.report_directory / "analysis_report.md"

        logger.info("Report generation not yet implemented (T022)")
        return output_path


def create_analysis_service(config: Optional[AnalysisConfig] = None) -> AnalysisService:
    """
    Factory function to create an AnalysisService instance.

    Args:
        config: Optional configuration for the service.

    Returns:
        Configured AnalysisService instance.
    """
    return AnalysisService(config=config)