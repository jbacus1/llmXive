"""
Validation module for CSA recommendation outputs.

Ensures all recommendation outputs meet schema requirements
and data integrity constraints before being returned to users.

Validates against:
- Required fields (recommendation_id, practice, justification, etc.)
- Data type correctness
- Value ranges and constraints
- Schema compliance per contracts/output.schema.yaml
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


class ValidationErrorType(Enum):
    MISSING_FIELD = "missing_field"
    INVALID_TYPE = "invalid_type"
    OUT_OF_RANGE = "out_of_range"
    INVALID_FORMAT = "invalid_format"
    SCHEMA_VIOLATION = "schema_violation"


@dataclass
class ValidationError:
    """Represents a single validation error."""
    field_path: str
    error_type: ValidationErrorType
    message: str
    expected: Any = None
    actual: Any = None


@dataclass
class ValidationResult:
    """Aggregated validation result for a recommendation output."""
    is_valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(
        self,
        field_path: str,
        error_type: ValidationErrorType,
        message: str,
        expected: Any = None,
        actual: Any = None
    ) -> None:
        """Add a validation error to the result."""
        self.is_valid = False
        self.errors.append(ValidationError(
            field_path=field_path,
            error_type=error_type,
            message=message,
            expected=expected,
            actual=actual
        ))
    
    def add_warning(self, message: str) -> None:
        """Add a non-blocking warning."""
        self.warnings.append(message)

# =============================================================================
# Recommendation Output Schema Definition
# =============================================================================

REQUIRED_RECOMMENDATION_FIELDS = [
    "recommendation_id",
    "community_id",
    "practice_name",
    "practice_category",
    "expected_impact",
    "implementation_cost",
    "timeline_months",
    "justification",
    "sustainability_score",
    "equity_score",
    "confidence_level"
]

OPTIONAL_RECOMMENDATION_FIELDS = [
    "data_sources",
    "risk_factors",
    "alternative_practices",
    "stakeholder_notes",
    "created_at",
    "updated_at"
]

VALID_PRACITCE_CATEGORIES = [
    "crop_rotation",
    "cover_cropping",
    "conservation_tillage",
    "integrated_pest_management",
    "water_management",
    "agroforestry",
    "soil_health",
    "climate_adaptation"
]

VALID_CONFIDENCE_LEVELS = [
    "high",
    "medium",
    "low"
]

VALID_IMPACT_RANGES = [
    "positive",
    "neutral",
    "negative",
    "variable"
]

# =============================================================================
# Validation Functions
# =============================================================================

def validate_recommendation_output(
    recommendation: Dict[str, Any],
    strict: bool = True
) -> ValidationResult:
    """
    Validate a single recommendation output against the schema.
    
    Args:
        recommendation: The recommendation dict to validate
        strict: If True, fail on any error. If False, collect all errors.
    
    Returns:
        ValidationResult with validation status and any errors found
    """
    result = ValidationResult()
    
    # Check if recommendation is a dict
    if not isinstance(recommendation, dict):
        result.add_error(
            field_path="root",
            error_type=ValidationErrorType.SCHEMA_VIOLATION,
            message="Recommendation must be a dictionary",
            expected="dict",
            actual=type(recommendation).__name__
        )
        return result
    
    # Validate required fields
    for field_name in REQUIRED_RECOMMENDATION_FIELDS:
        if field_name not in recommendation:
            result.add_error(
                field_path=field_name,
                error_type=ValidationErrorType.MISSING_FIELD,
                message=f"Required field '{field_name}' is missing",
                expected="present"
            )
    
    # Validate field types
    _validate_field_types(recommendation, result)
    
    # Validate field values and ranges
    _validate_field_values(recommendation, result)
    
    # Validate relationships between fields
    _validate_field_relationships(recommendation, result)
    
    return result


def validate_recommendation_batch(
    recommendations: List[Dict[str, Any]],
    strict: bool = True
) -> ValidationResult:
    """
    Validate a batch of recommendation outputs.
    
    Args:
        recommendations: List of recommendation dicts to validate
        strict: If True, fail on any error in any recommendation
    
    Returns:
        ValidationResult with aggregated errors from all recommendations
    """
    result = ValidationResult()
    
    if not isinstance(recommendations, list):
        result.add_error(
            field_path="root",
            error_type=ValidationErrorType.SCHEMA_VIOLATION,
            message="Recommendations must be a list",
            expected="list",
            actual=type(recommendations).__name__
        )
        return result
    
    if len(recommendations) == 0:
        result.add_warning("Empty recommendation batch provided")
        return result
    
    for idx, rec in enumerate(recommendations):
        rec_result = validate_recommendation_output(rec, strict=strict)
        
        if not rec_result.is_valid:
            for error in rec_result.errors:
                result.add_error(
                    field_path=f"[{idx}].{error.field_path}",
                    error_type=error.error_type,
                    message=error.message,
                    expected=error.expected,
                    actual=error.actual
                )
        
        for warning in rec_result.warnings:
            result.add_warning(f"[{idx}] {warning}")
    
    return result


def _validate_field_types(
    recommendation: Dict[str, Any],
    result: ValidationResult
) -> None:
    """Validate that fields have correct data types."""
    type_constraints = {
        "recommendation_id": str,
        "community_id": str,
        "practice_name": str,
        "practice_category": str,
        "expected_impact": str,
        "implementation_cost": (int, float),
        "timeline_months": (int, float),
        "justification": str,
        "sustainability_score": (int, float),
        "equity_score": (int, float),
        "confidence_level": str,
        "data_sources": list,
        "risk_factors": list,
        "alternative_practices": list
    }
    
    for field_name, expected_type in type_constraints.items():
        if field_name in recommendation:
            value = recommendation[field_name]
            if not isinstance(value, expected_type):
                result.add_error(
                    field_path=field_name,
                    error_type=ValidationErrorType.INVALID_TYPE,
                    message=f"Field '{field_name}' must be {expected_type}",
                    expected=str(expected_type),
                    actual=type(value).__name__
                )


def _validate_field_values(
    recommendation: Dict[str, Any],
    result: ValidationResult
) -> None:
    """Validate that field values are within acceptable ranges."""
    
    # Validate practice_category
    if "practice_category" in recommendation:
        if recommendation["practice_category"] not in VALID_PRACITCE_CATEGORIES:
            result.add_error(
                field_path="practice_category",
                error_type=ValidationErrorType.INVALID_FORMAT,
                message=f"Invalid practice category",
                expected=VALID_PRACITCE_CATEGORIES,
                actual=recommendation["practice_category"]
            )
    
    # Validate confidence_level
    if "confidence_level" in recommendation:
        if recommendation["confidence_level"] not in VALID_CONFIDENCE_LEVELS:
            result.add_error(
                field_path="confidence_level",
                error_type=ValidationErrorType.INVALID_FORMAT,
                message=f"Invalid confidence level",
                expected=VALID_CONFIDENCE_LEVELS,
                actual=recommendation["confidence_level"]
            )
    
    # Validate expected_impact
    if "expected_impact" in recommendation:
        if recommendation["expected_impact"] not in VALID_IMPACT_RANGES:
            result.add_error(
                field_path="expected_impact",
                error_type=ValidationErrorType.INVALID_FORMAT,
                message=f"Invalid expected impact value",
                expected=VALID_IMPACT_RANGES,
                actual=recommendation["expected_impact"]
            )
    
    # Validate score ranges (0-100 scale)
    score_fields = ["sustainability_score", "equity_score"]
    for score_field in score_fields:
        if score_field in recommendation:
            score = recommendation[score_field]
            if score < 0 or score > 100:
                result.add_error(
                    field_path=score_field,
                    error_type=ValidationErrorType.OUT_OF_RANGE,
                    message=f"Score must be between 0 and 100",
                    expected="0 <= {field} <= 100",
                    actual=score
                )
    
    # Validate cost and timeline are non-negative
    cost_fields = ["implementation_cost", "timeline_months"]
    for cost_field in cost_fields:
        if cost_field in recommendation:
            value = recommendation[cost_field]
            if value < 0:
                result.add_error(
                    field_path=cost_field,
                    error_type=ValidationErrorType.OUT_OF_RANGE,
                    message=f"{cost_field} must be non-negative",
                    expected=">= 0",
                    actual=value
                )
    
    # Validate justification is not empty
    if "justification" in recommendation:
        if not recommendation["justification"].strip():
            result.add_error(
                field_path="justification",
                error_type=ValidationErrorType.INVALID_FORMAT,
                message="Justification cannot be empty",
                expected="non-empty string",
                actual="empty"
            )
    
    # Validate recommendation_id format (should be UUID-like)
    if "recommendation_id" in recommendation:
        rec_id = recommendation["recommendation_id"]
        if not rec_id or len(rec_id) < 5:
            result.add_error(
                field_path="recommendation_id",
                error_type=ValidationErrorType.INVALID_FORMAT,
                message="recommendation_id appears invalid",
                expected="valid identifier",
                actual=rec_id
            )


def _validate_field_relationships(
    recommendation: Dict[str, Any],
    result: ValidationResult
) -> None:
    """Validate relationships between fields."""
    
    # If confidence is 'high', scores should be reasonable
    if recommendation.get("confidence_level") == "high":
        if "sustainability_score" in recommendation:
            if recommendation["sustainability_score"] < 50:
                result.add_warning(
                    "High confidence with low sustainability score may indicate inconsistency"
                )
    
    # Cost and timeline should be positive for implementation
    if (recommendation.get("implementation_cost", 0) == 0 and 
        recommendation.get("timeline_months", 0) > 0):
        result.add_warning(
            "Zero cost with positive timeline may indicate incomplete data"
        )

# =============================================================================
# Convenience Functions
# =============================================================================

def assert_valid_recommendation(
    recommendation: Dict[str, Any],
    raise_on_error: bool = True
) -> None:
    """
    Assert that a recommendation is valid, optionally raising an exception.
    
    Args:
        recommendation: The recommendation to validate
        raise_on_error: If True, raise ValueError on validation failure
    
    Raises:
        ValueError: If validation fails and raise_on_error is True
    """
    result = validate_recommendation_output(recommendation)
    
    if not result.is_valid and raise_on_error:
        error_messages = [
            f"{e.field_path}: {e.message}" for e in result.errors
        ]
        raise ValueError(
            f"Recommendation validation failed:\n" +
            "\n".join(error_messages)
        )

def safe_recommendation_output(
    recommendation: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Return recommendation if valid, None if invalid.
    
    Useful for filtering recommendation batches.
    
    Args:
        recommendation: The recommendation to validate
    
    Returns:
        The original recommendation if valid, None otherwise
    """
    result = validate_recommendation_output(recommendation)
    return recommendation if result.is_valid else None