"""
Pydantic models for Mindfulness and Social Skills RCT data.

These models reflect the contract schemas defined in:
- contracts/participant.schema.yaml
- contracts/assessment.schema.yaml
- contracts/intervention.schema.yaml

All models are validated against IRB requirements for data protection.
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============================================================================
# Enums for controlled vocabularies
# ============================================================================

class GenderEnum(str, Enum):
    """Participant gender options per IRB guidelines."""
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class RaceEthnicityEnum(str, Enum):
    """Race/ethnicity options per IRB guidelines."""
    WHITE = "white"
    BLACK = "black"
    HISPANIC_LATINO = "hispanic_latino"
    ASIAN = "asian"
    NATIVE_AMERICAN = "native_american"
    PACIFIC_ISLANDER = "pacific_islander"
    MULTIPLE = "multiple"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class TimepointEnum(str, Enum):
    """Assessment timepoints for the RCT."""
    BASELINE = "baseline"
    POST_INTERVENTION = "post_intervention"
    FOLLOW_UP = "follow_up"

class GroupAssignmentEnum(str, Enum):
    """Randomized group assignment."""
    INTERVENTION = "intervention"
    CONTROL = "control"

class AdherenceLevelEnum(str, Enum):
    """Session adherence levels."""
    FULL = "full"
    PARTIAL = "partial"
    MISSED = "missed"

# ============================================================================
# Participant Models (contracts/participant.schema.yaml)
# ============================================================================

class ConsentInfo(BaseModel):
    """Parent/guardian consent information."""
    model_config = ConfigDict(populate_by_name=True)
    
    consent_given: bool = Field(..., description="Whether consent was provided")
    consent_date: date = Field(..., description="Date consent was obtained")
    consent_version: str = Field(..., description="IRB-approved consent form version")
    assent_given: Optional[bool] = Field(None, description="Child assent (if age-appropriate)")
    assent_date: Optional[date] = Field(None, description="Date assent was obtained")

class ParticipantDemographics(BaseModel):
    """Core participant demographic information."""
    model_config = ConfigDict(populate_by_name=True)
    
    participant_id: str = Field(..., pattern=r"^[A-Z]{2}\d{6}$", 
                                description="Anonymized participant ID (e.g., AB123456)")
    enrollment_date: date = Field(..., description="Date participant enrolled in study")
    age_at_enrollment: int = Field(..., ge=3, le=17, 
                                   description="Age in years at enrollment")
    gender: GenderEnum = Field(..., description="Participant gender")
    race_ethnicity: List[RaceEthnicityEnum] = Field(
        ..., min_length=1, max_length=3,
        description="Race/ethnicity (multiple selections allowed)"
    )
    primary_language: str = Field(
        ..., min_length=2, max_length=50,
        description="Primary language spoken at home"
    )

class Participant(BaseModel):
    """Complete participant record combining demographics, consent, and assignment."""
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    
    demographics: ParticipantDemographics
    consent: ConsentInfo
    group_assignment: GroupAssignmentEnum = Field(
        ..., description="Randomized group assignment"
    )
    randomization_date: date = Field(..., description="Date of randomization")
    stratification_factors: Dict[str, str] = Field(
        default_factory=dict,
        description="Stratification factors used in randomization (e.g., age_group, severity)"
    )
    exclusion_reasons: Optional[List[str]] = Field(
        None,
        description="Any exclusion criteria that were screened but not met"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('participant_id')
    @classmethod
    def validate_participant_id(cls, v: str) -> str:
        if not v[0].isalpha() or not v[1].isalpha():
            raise ValueError("participant_id must start with two letters")
        if not v[2:].isdigit():
            raise ValueError("participant_id must have 6 digits after letters")
        return v.upper()

# ============================================================================
# Assessment Models (contracts/assessment.schema.yaml)
# ============================================================================

class AssessmentMeasure(BaseModel):
    """Individual assessment measure result."""
    model_config = ConfigDict(populate_by_name=True)
    
    measure_name: str = Field(..., description="Name of the assessment measure")
    measure_type: str = Field(..., description="Type (e.g., parent_report, observer_rating, direct_assessment)")
    raw_score: float = Field(..., ge=0, description="Raw score from assessment")
    standardized_score: Optional[float] = Field(
        None, ge=0, description="Standardized score if applicable"
    )
    t_score: Optional[float] = Field(None, ge=20, le=80, 
                                     description="T-score if norm-referenced")
    percentile_rank: Optional[int] = Field(None, ge=1, le=99,
                                           description="Percentile rank if applicable")
    data_quality_flags: List[str] = Field(
        default_factory=list,
        description="Flags for data quality (e.g., 'missing_values', 'out_of_range')"
    )
    assessor_id: Optional[str] = Field(None, description="ID of person who administered assessment")

class AssessmentTimepoint(BaseModel):
    """Assessment data for a single timepoint."""
    model_config = ConfigDict(populate_by_name=True)
    
    timepoint: TimepointEnum = Field(..., description="Assessment timepoint")
    assessment_date: date = Field(..., description="Date assessment was completed")
    measures: List[AssessmentMeasure] = Field(
        ..., min_length=1,
        description="Individual measure results"
    )
    completion_status: str = Field(
        ..., pattern=r"^(complete|partial|not_started|skipped)$",
        description="Overall completion status"
    )
    notes: Optional[str] = Field(None, max_length=500, 
                                 description="Assessor notes")

class Assessment(BaseModel):
    """Complete assessment record for a participant."""
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    
    participant_id: str = Field(..., description="Reference to participant")
    assessments: List[AssessmentTimepoint] = Field(
        ..., min_length=1, max_length=3,
        description="Assessments across timepoints"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('participant_id')
    @classmethod
    def validate_participant_id(cls, v: str) -> str:
        if len(v) != 8:
            raise ValueError("participant_id must be 8 characters (2 letters + 6 digits)")
        return v.upper()

# ============================================================================
# Intervention Models (contracts/intervention.schema.yaml)
# ============================================================================

class SessionLog(BaseModel):
    """Individual intervention session log."""
    model_config = ConfigDict(populate_by_name=True)
    
    session_number: int = Field(..., ge=1, le=12, 
                                description="Session number (1-12 for intervention group)")
    session_date: date = Field(..., description="Date session occurred")
    duration_minutes: int = Field(..., ge=15, le=90,
                                  description="Actual session duration in minutes")
    adherence_level: AdherenceLevelEnum = Field(..., description="Adherence to protocol")
    curriculum_delivered: List[str] = Field(
        ..., description="Curriculum components covered in this session"
    )
    activities_completed: List[str] = Field(
        default_factory=list,
        description="Specific activities completed"
    )
    child_engagement_score: Optional[float] = Field(
        None, ge=0, le=10,
        description="10-point engagement scale"
    )
    facilitator_id: str = Field(..., description="Facilitator who led the session")
    notes: Optional[str] = Field(None, max_length=1000,
                                 description="Session notes")

class InterventionSession(BaseModel):
    """Intervention session tracking for a participant."""
    model_config = ConfigDict(populate_by_name=True)
    
    participant_id: str = Field(..., description="Reference to participant")
    group_assignment: GroupAssignmentEnum = Field(..., 
                                                  description="Should be 'intervention' for this model")
    session_logs: List[SessionLog] = Field(
        default_factory=list,
        description="Individual session records"
    )
    start_date: Optional[date] = Field(None, description="Intervention start date")
    end_date: Optional[date] = Field(None, description="Intervention end date")
    total_sessions_completed: int = Field(
        0,
        description="Total sessions completed"
    )
    adherence_rate: Optional[float] = Field(
        None, ge=0, le=1,
        description="Proportion of sessions attended (0-1)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ============================================================================
# Aggregated/Composite Models
# ============================================================================

class ParticipantFullRecord(BaseModel):
    """Complete participant record combining all data."""
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    
    participant: Participant
    assessment: Optional[Assessment] = None
    intervention: Optional[InterventionSession] = None
    data_complete: bool = Field(
        default=False,
        description="Whether all required data has been collected"
    )

# ============================================================================
# Utility Functions
# ============================================================================

def create_anonymized_id(seed: str, salt: str = "ASD-2025") -> str:
    """
    Generate anonymized participant ID from seed.
    
    Args:
        seed: Unique identifier (e.g., enrollment number)
        salt: Salt value for reproducibility
    
    Returns:
        Anonymized ID in format AB123456
    """
    import hashlib
    combined = f"{seed}{salt}"
    hash_bytes = hashlib.sha256(combined.encode()).digest()
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    digits = "0123456789"
    letter1 = letters[hash_bytes[0] % len(letters)]
    letter2 = letters[hash_bytes[1] % len(letters)]
    number = ''.join(str(d) for d in hash_bytes[2:5])
    return f"{letter1}{letter2}{number}"

# ============================================================================
# Validation Helpers
# ============================================================================

def validate_assessment_completeness(assessment: Assessment) -> Dict[str, Any]:
    """
    Validate that assessment has required timepoints.
    
    Returns:
        Dict with validation results and missing timepoints
    """
    required_timepoints = {TimepointEnum.BASELINE, 
                           TimepointEnum.POST_INTERVENTION,
                           TimepointEnum.FOLLOW_UP}
    present_timepoints = {a.timepoint for a in assessment.assessments}
    missing = required_timepoints - present_timepoints
    
    return {
        "is_complete": len(missing) == 0,
        "missing_timepoints": [t.value for t in missing],
        "present_timepoints": [t.value for t in present_timepoints]
    }

def validate_intervention_adherence(intervention: InterventionSession) -> Dict[str, Any]:
    """
    Validate intervention session adherence metrics.
    
    Returns:
        Dict with adherence metrics and flags
    """
    total_expected = 12  # 12 sessions for intervention protocol
    completed = len(intervention.session_logs)
    adherence_rate = completed / total_expected if total_expected > 0 else 0
    
    missed_sessions = [s for s in intervention.session_logs 
                      if s.adherence_level == AdherenceLevelEnum.MISSED]
    
    return {
        "total_expected": total_expected,
        "sessions_completed": completed,
        "adherence_rate": round(adherence_rate, 2),
        "missed_sessions": len(missed_sessions),
        "is_sufficient": adherence_rate >= 0.75  # 75% threshold
    }