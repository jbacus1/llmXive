"""
Schema validation helpers for Climate-Smart Agricultural Practices project.

This module provides validation utilities for:
- Data schemas (datasets, API responses)
- Configuration validation
- Pipeline output schemas
- Contract testing support

Uses Pydantic for type validation and JSON Schema for complex validation rules.
"""

from typing import Any, Dict, List, Optional, Union, get_type_hints
import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, validator, ValidationError
from pydantic.errors import PydanticError
import jsonschema
from jsonschema import validate, ValidationError as JSONSchemaValidationError


class SchemaValidationError(Exception):
    """Custom exception for schema validation failures."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


def validate_schema(
    data: Dict[str, Any],
    schema: Dict[str, Any],
    schema_name: str = "unknown"
) -> bool:
    """
    Validate data against a JSON Schema.

    Args:
        data: The data to validate
        schema: JSON Schema definition
        schema_name: Name of schema for error reporting

    Returns:
        True if validation passes

    Raises:
        SchemaValidationError: If validation fails
    """
    try:
        validate(instance=data, schema=schema)
        return True
    except JSONSchemaValidationError as e:
        raise SchemaValidationError(
            message=f"Schema validation failed for {schema_name}",
            details={
                "error": str(e.message),
                "path": list(e.absolute_path),
                "schema_path": list(e.absolute_schema_path)
            }
        )


def validate_pydantic_model(
    model_class: type,
    data: Dict[str, Any],
    model_name: Optional[str] = None
) -> BaseModel:
    """
    Validate and instantiate a Pydantic model from data.

    Args:
        model_class: Pydantic model class
        data: Data to validate
        model_name: Optional name for error reporting

    Returns:
        Validated model instance

    Raises:
        SchemaValidationError: If validation fails
    """
    try:
        return model_class(**data)
    except ValidationError as e:
        model_name = model_name or model_class.__name__
        errors = []
        for error in e.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "type": error["type"],
                "message": error["msg"]
            })

        raise SchemaValidationError(
            message=f"Pydantic validation failed for {model_name}",
            details={"errors": errors}
        )


def validate_required_fields(
    data: Dict[str, Any],
    required_fields: List[str],
    context: str = "data"
) -> Dict[str, Any]:
    """
    Validate that all required fields are present in data.

    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        context: Context name for error messages

    Returns:
        The validated data (unchanged)

    Raises:
        SchemaValidationError: If required fields are missing
    """
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise SchemaValidationError(
            message=f"Missing required fields in {context}",
            details={"missing_fields": missing, "context": context}
        )
    return data


def validate_field_types(
    data: Dict[str, Any],
    field_types: Dict[str, type],
    strict: bool = False
) -> Dict[str, Any]:
    """
    Validate that fields have expected types.

    Args:
        data: Data dictionary to validate
        field_types: Dict mapping field names to expected types
        strict: If True, raise error on type mismatch; if False, coerce

    Returns:
        The validated/coerced data

    Raises:
        SchemaValidationError: If type validation fails in strict mode
    """
    for field, expected_type in field_types.items():
        if field not in data:
            continue

        value = data[field]
        if not isinstance(value, expected_type):
            if strict:
                raise SchemaValidationError(
                    message=f"Type mismatch for field '{field}'",
                    details={
                        "field": field,
                        "expected": expected_type.__name__,
                        "actual": type(value).__name__,
                        "value": value
                    }
                )
            else:
                try:
                    data[field] = expected_type(value)
                except (ValueError, TypeError):
                    raise SchemaValidationError(
                        message=f"Cannot coerce field '{field}' to {expected_type.__name__}",
                        details={"field": field, "value": value}
                    )

    return data


def validate_nested_schema(
    data: Dict[str, Any],
    nested_schemas: Dict[str, Dict[str, Any]],
    parent_path: str = ""
) -> bool:
    """
    Recursively validate nested schemas in data.

    Args:
        data: Data dictionary to validate
        nested_schemas: Dict mapping field names to their schemas
        parent_path: Current path for error reporting

    Returns:
        True if all nested schemas validate

    Raises:
        SchemaValidationError: If any nested schema fails validation
    """
    for field_name, schema in nested_schemas.items():
        if field_name not in data:
            continue

        field_path = f"{parent_path}.{field_name}" if parent_path else field_name

        if isinstance(data[field_name], dict):
            validate_schema(data[field_name], schema, schema_name=field_path)
        elif isinstance(data[field_name], list):
            for i, item in enumerate(data[field_name]):
                if isinstance(item, dict):
                    validate_schema(item, schema, schema_name=f"{field_path}[{i}]")

    return True


# Common schema definitions for the project

DATASET_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["metadata", "data"],
    "properties": {
        "metadata": {
            "type": "object",
            "required": ["source", "created_at", "version"],
            "properties": {
                "source": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"},
                "version": {"type": "string"},
                "description": {"type": "string"},
                "license": {"type": "string"}
            }
        },
        "data": {
            "type": "array",
            "items": {"type": "object"}
        }
    }
}

API_RESPONSE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["status", "timestamp"],
    "properties": {
        "status": {"type": "string", "enum": ["success", "error", "partial"]},
        "timestamp": {"type": "string", "format": "date-time"},
        "data": {"type": ["object", "array", "null"]},
        "error": {"type": ["object", "null"]},
        "metadata": {"type": ["object", "null"]}
    }
}

CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["project_id", "version"],
    "properties": {
        "project_id": {"type": "string"},
        "version": {"type": "string"},
        "environment": {"type": "string", "enum": ["dev", "staging", "prod"]},
        "api_keys": {"type": "object"},
        "settings": {"type": "object"}
    }
}

OUTPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["pipeline_id", "results", "metadata"],
    "properties": {
        "pipeline_id": {"type": "string"},
        "results": {"type": "array"},
        "metadata": {
            "type": "object",
            "required": ["processed_at", "version"],
            "properties": {
                "processed_at": {"type": "string", "format": "date-time"},
                "version": {"type": "string"},
                "records_processed": {"type": "integer"}
            }
        }
    }
}


def load_schema_from_file(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON Schema from a file.

    Args:
        schema_path: Path to the schema file

    Returns:
        Parsed schema dictionary

    Raises:
        FileNotFoundError: If schema file doesn't exist
        json.JSONDecodeError: If schema file is not valid JSON
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_schema_file(schema_path: Union[str, Path]) -> bool:
    """
    Validate that a schema file is valid JSON Schema.

    Args:
        schema_path: Path to the schema file

    Returns:
        True if schema is valid

    Raises:
        FileNotFoundError: If schema file doesn't exist
        json.JSONDecodeError: If schema file is not valid JSON
        SchemaValidationError: If schema structure is invalid
    """
    schema = load_schema_from_file(schema_path)
    validate_schema(schema, {
        "type": "object",
        "required": ["$schema", "type"],
        "properties": {
            "$schema": {"type": "string"},
            "type": {"type": "string"}
        }
    }, schema_name=Path(schema_path).name)
    return True


def validate_timestamp(value: Any, field_name: str = "timestamp") -> datetime:
    """
    Validate and parse a timestamp string.

    Args:
        value: Timestamp value (string or datetime)
        field_name: Field name for error reporting

    Returns:
        Parsed datetime object

    Raises:
        SchemaValidationError: If timestamp is invalid
    """
    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError as e:
            raise SchemaValidationError(
                message=f"Invalid timestamp format for {field_name}",
                details={"field": field_name, "value": value, "error": str(e)}
            )

    raise SchemaValidationError(
        message=f"Invalid timestamp type for {field_name}",
        details={"field": field_name, "type": type(value).__name__}
    )


def validate_url(value: str, field_name: str = "url") -> str:
    """
    Validate that a value is a valid URL.

    Args:
        value: URL string to validate
        field_name: Field name for error reporting

    Returns:
        Validated URL string

    Raises:
        SchemaValidationError: If URL is invalid
    """
    from urllib.parse import urlparse

    try:
        result = urlparse(value)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL structure")
        return value
    except Exception as e:
        raise SchemaValidationError(
            message=f"Invalid URL for {field_name}",
            details={"field": field_name, "value": value, "error": str(e)}
        )


def validate_enum(
    value: Any,
    allowed_values: List[Any],
    field_name: str,
    case_sensitive: bool = True
) -> Any:
    """
    Validate that a value is in the allowed set.

    Args:
        value: Value to validate
        allowed_values: List of allowed values
        field_name: Field name for error reporting
        case_sensitive: If False, comparison is case-insensitive

    Returns:
        Validated value

    Raises:
        SchemaValidationError: If value is not in allowed set
    """
    if case_sensitive:
        if value not in allowed_values:
            raise SchemaValidationError(
                message=f"Invalid value for {field_name}",
                details={
                    "field": field_name,
                    "value": value,
                    "allowed": allowed_values
                }
            )
    else:
        value_lower = str(value).lower()
        allowed_lower = [str(v).lower() for v in allowed_values]
        if value_lower not in allowed_lower:
            raise SchemaValidationError(
                message=f"Invalid value for {field_name}",
                details={
                    "field": field_name,
                    "value": value,
                    "allowed": allowed_values
                }
            )

    return value


class ValidationResult:
    """
    Container for validation results.

    Provides structured access to validation success/failure state
    and detailed error information.
    """

    def __init__(self, success: bool, errors: Optional[List[Dict[str, Any]]] = None):
        self.success = success
        self.errors = errors or []

    @property
    def failed(self) -> bool:
        return not self.success

    def add_error(self, field: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Add an error to the validation result."""
        self.errors.append({
            "field": field,
            "message": message,
            "details": details or {}
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            "success": self.success,
            "error_count": len(self.errors),
            "errors": self.errors if self.failed else []
        }

    def raise_if_failed(self):
        """Raise SchemaValidationError if validation failed."""
        if self.failed:
            error_messages = [f"{e['field']}: {e['message']}" for e in self.errors]
            raise SchemaValidationError(
                message="Validation failed",
                details={"errors": self.errors}
            )


def validate_with_result(
    data: Dict[str, Any],
    validators: List,
    context: str = "data"
) -> ValidationResult:
    """
    Run multiple validators and collect results.

    Args:
        data: Data to validate
        validators: List of validator functions
        context: Context name for error reporting

    Returns:
        ValidationResult with all errors collected
    """
    result = ValidationResult(success=True)

    for validator in validators:
        try:
            validator(data)
        except SchemaValidationError as e:
            result.success = False
            result.add_error(
                field=e.details.get("field", "unknown"),
                message=e.message,
                details=e.details
            )

    return result


# Pydantic models for common use cases

class DatasetMetadata(BaseModel):
    """Metadata for dataset records."""
    source: str
    created_at: datetime
    version: str
    description: Optional[str] = None
    license: Optional[str] = None


class Dataset(BaseModel):
    """Dataset container with metadata."""
    metadata: DatasetMetadata
    data: List[Dict[str, Any]]


class APIResponse(BaseModel):
    """Standard API response structure."""
    status: str
    timestamp: datetime
    data: Optional[Union[Dict[str, Any], List[Any]]] = None
    error: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class Config(BaseModel):
    """Configuration schema."""
    project_id: str
    version: str
    environment: str = "dev"
    api_keys: Dict[str, str] = {}
    settings: Dict[str, Any] = {}


class PipelineOutput(BaseModel):
    """Pipeline output schema."""