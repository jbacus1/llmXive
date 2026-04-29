"""
Custom exception classes and error handling utilities.

Provides a hierarchy of exceptions for the Climate-Smart Agricultural
Practices project, enabling consistent error handling and clear error
messages across all modules.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .errors import get_logger

logger = get_logger("errors")

# ============================================================================
# Base Exception Classes
# ============================================================================

class CSAError(Exception):
    """Base exception for all Climate-Smart Agricultural Practices errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "CSA000",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/API responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp,
            "details": self.details,
        }
    
    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"

# ============================================================================
# Configuration Errors (CSA1xx)
# ============================================================================

class ConfigurationError(CSAError):
    """Error related to configuration issues."""
    error_code = "CSA100"

class MissingAPIKeyError(ConfigurationError):
    """Raised when a required API key is missing."""
    error_code = "CSA101"
    
    def __init__(self, service_name: str):
        super().__init__(
            f"Missing API key for service: {service_name}",
            self.error_code,
            {"service": service_name}
        )

class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration values are invalid."""
    error_code = "CSA102"

# ============================================================================
# Data Errors (CSA2xx)
# ============================================================================

class DataError(CSAError):
    """Base error for data-related issues."""
    error_code = "CSA200"

class DataValidationError(DataError):
    """Raised when data fails schema validation."""
    error_code = "CSA201"
    
    def __init__(self, message: str, schema_name: str, violations: list):
        super().__init__(
            message,
            self.error_code,
            {"schema": schema_name, "violations": violations}
        )

class DataIngestionError(DataError):
    """Raised when data ingestion fails."""
    error_code = "CSA202"

class DataNotFoundError(DataError):
    """Raised when requested data is not found."""
    error_code = "CSA203"

# ============================================================================
# API/Network Errors (CSA3xx)
# ============================================================================

class APIError(CSAError):
    """Base error for API-related issues."""
    error_code = "CSA300"

class APIConnectionError(APIError):
    """Raised when API connection fails."""
    error_code = "CSA301"

class APIRateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    error_code = "CSA302"
    
    def __init__(self, service_name: str, retry_after: int):
        super().__init__(
            f"API rate limit exceeded for {service_name}",
            self.error_code,
            {"service": service_name, "retry_after_seconds": retry_after}
        )

class APIAuthenticationError(APIError):
    """Raised when API authentication fails."""
    error_code = "CSA303"

# ============================================================================
# Model/Analysis Errors (CSA4xx)
# ============================================================================

class ModelError(CSAError):
    """Base error for model-related issues."""
    error_code = "CSA400"

class ModelTrainingError(ModelError):
    """Raised when model training fails."""
    error_code = "CSA401"

class ModelPredictionError(ModelError):
    """Raised when model prediction fails."""
    error_code = "CSA402"

# ============================================================================
# File System Errors (CSA5xx)
# ============================================================================

class FileError(CSAError):
    """Base error for file system issues."""
    error_code = "CSA500"

class FileNotFoundError(FileError):
    """Raised when a file is not found."""
    error_code = "CSA501"

class FilePermissionError(FileError):
    """Raised when file access is denied."""
    error_code = "CSA502"

# ============================================================================
# Error Handling Utilities
# ============================================================================

class ErrorHandler:
    """Centralized error handling utilities."""
    
    @staticmethod
    def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
        """
        Log an error with context.
        
        Args:
            error: The exception to log
            context: Additional context information
        """
        if isinstance(error, CSAError):
            logger.error(
                f"{error.error_code}: {error.message}",
                extra={"details": error.details, "context": context or {}}
            )
        else:
            logger.error(
                f"Unhandled error: {type(error).__name__}: {str(error)}",
                extra={"context": context or {}}
            )
    
    @staticmethod
    def handle_and_raise(
        error: Exception,
        default_error: CSAError = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Log an error and optionally re-raise or raise a default error.
        
        Args:
            error: The exception to handle
            default_error: Error to raise if default_error is provided
            context: Additional context information
        
        Returns:
            None (always raises or re-raises)
        """
        ErrorHandler.log_error(error, context)
        
        if default_error:
            raise default_error
        raise error
    
    @staticmethod
    def wrap_in_error(
        operation: str,
        exception_class: type = DataError,
        error_code: str = None,
    ):
        """
        Decorator to wrap operations in error handling.
        
        Args:
            operation: Name of the operation for error context
            exception_class: Exception class to raise on failure
            error_code: Optional error code override
        
        Returns:
            Decorated function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except CSAError:
                    raise
                except Exception as e:
                    raise exception_class(
                        f"Operation '{operation}' failed: {str(e)}",
                        error_code or "CSA000",
                        {"operation": operation, "original_error": str(e)}
                    )
            return wrapper
        return decorator

# ============================================================================
# Error Recovery Utilities
# ============================================================================

class RetryHandler:
    """Utility for retrying operations with exponential backoff."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        retryable_exceptions: tuple = (APIConnectionError, APIRateLimitError),
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retryable_exceptions = retryable_exceptions
    
    def execute(self, func, *args, **kwargs):
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
        
        Returns:
            Result of func
        
        Raises:
            Last exception if all retries fail
        """
        import time
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except self.retryable_exceptions as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.warning(
                        f"Retry {attempt + 1}/{self.max_retries} after {delay}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All retries exhausted: {e}")
        
        raise last_exception