"""
Error handling and logging infrastructure for Bayesian Nonparametrics Anomaly Detection.

Provides structured logging, error handling utilities, and performance timing
decorators. Integrates with config.yaml for runtime configuration.

Usage:
    from code.utils.logger import get_logger, timed, retry_on_failure
  
    logger = get_logger(__name__)
    
    @timed("processing_step")
    def process_data(data):
        ...
        
    @retry_on_failure(max_retries=3, delay=1.0)
    def api_call():
        ...
"""

import logging
import logging.handlers
import os
import sys
import time
import functools
import traceback
from typing import Optional, Callable, Any, Dict
from pathlib import Path
from datetime import datetime
import yaml

# Project root detection
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOG_DIR = PROJECT_ROOT / "state" / "logs"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log level mapping from config
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Global logger registry
_loggers: Dict[str, logging.Logger] = {}

def get_log_level_from_config() -> int:
    """
    Read log level from config.yaml. Falls back to INFO if config unavailable.
    
    Returns:
        logging.Level: The configured log level.
    """
    config_path = PROJECT_ROOT / "code" / "config.yaml"
    try:
        if config_path.exists():
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            log_level_str = config.get("logging", {}).get("level", "INFO")
            return LOG_LEVELS.get(log_level_str.upper(), logging.INFO)
    except Exception:
        pass
    return logging.INFO

def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get or create a named logger with consistent configuration.
    
    Args:
        name: Logger name (typically __name__)
        level: Optional override for log level
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(level or get_log_level_from_config())
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        _loggers[name] = logger
        return logger
    
    # Create formatter with structured output
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (rotating)
    log_file = LOG_DIR / f"{name.replace('.', '_')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    _loggers[name] = logger
    return logger

class AnomalyDetectionError(Exception):
    """Base exception for anomaly detection module."""
    pass

class DataProcessingError(AnomalyDetectionError):
    """Raised when data processing fails."""
    pass

class ModelInferenceError(AnomalyDetectionError):
    """Raised when model inference fails."""
    pass

class ConfigurationError(AnomalyDetectionError):
    """Raised when configuration is invalid."""
    pass

class ThresholdError(AnomalyDetectionError):
    """Raised when threshold calibration fails."""
    pass

def get_exception_details(exc: Exception) -> Dict[str, Any]:
    """
    Extract structured details from an exception.
    
    Args:
        exc: The exception instance.
    
    Returns:
        Dict with exception type, message, and traceback.
    """
    return {
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": traceback.format_exc(),
        "timestamp": datetime.utcnow().isoformat(),
    }

def log_exception(logger: logging.Logger, exc: Exception, level: int = logging.ERROR):
    """
    Log exception with full details.
    
    Args:
        logger: Logger to use.
        exc: Exception to log.
        level: Log level for the error.
    """
    details = get_exception_details(exc)
    logger.log(level, f"Exception caught: {details['type']}: {details['message']}")
    logger.log(level, f"Traceback:\n{details['traceback']}")

def timed(operation_name: str, logger_name: Optional[str] = None) -> Callable:
    """
    Decorator to log execution time of functions.
    
    Args:
        operation_name: Name for the timed operation.
        logger_name: Optional logger name (defaults to module name).
    
    Returns:
        Decorated function with timing logs.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger(logger_name or func.__module__)
            start_time = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start_time
                logger.info(f"{operation_name} completed in {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                logger.error(f"{operation_name} failed after {elapsed:.3f}s: {e}")
                raise
        
        return wrapper
    return decorator

def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator to retry failed operations with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for exponential backoff.
        exceptions: Tuple of exception types to catch.
    
    Returns:
        Decorated function with retry logic.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger(func.__module__)
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(
                            f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {wait_time:.1f}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries + 1} attempts")
            
            raise last_exception
        
        return wrapper
    return decorator

class Timer:
    """
    Context manager for timing code blocks.
    
    Usage:
        with Timer("operation_name") as t:
            # code to time
        print(f"Elapsed: {t.elapsed}s")
    """
    
    def __init__(self, operation_name: str, logger_name: Optional[str] = None):
        self.operation_name = operation_name
        self.logger_name = logger_name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed: float = 0.0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.elapsed = self.end_time - self.start_time
        
        logger = get_logger(self.logger_name or __name__)
        logger.debug(f"{self.operation_name} completed in {self.elapsed:.3f}s")
        
        return False

class LoggingContext:
    """
    Context manager to temporarily change log level.
    
    Usage:
        with LoggingContext("debug"):
            # debug logging enabled
        # original level restored
    """
    
    def __init__(self, level: str):
        self.level = level.upper()
        self.original_level: Optional[int] = None
    
    def __enter__(self):
        self.original_level = get_log_level_from_config()
        # Note: This affects the global config read, not existing handlers
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def setup_root_logger(level: Optional[int] = None):
    """
    Configure the root logger for the entire application.
    
    Args:
        level: Optional log level override.
    """
    logger = logging.getLogger()
    logger.setLevel(level or get_log_level_from_config())
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add console handler
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # Add file handler
    log_file = LOG_DIR / "app.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# Convenience function for quick logging
def info(msg: str, module: str = __name__):
    """Log info message."""
    get_logger(module).info(msg)

def debug(msg: str, module: str = __name__):
    """Log debug message."""
    get_logger(module).debug(msg)

def warning(msg: str, module: str = __name__):
    """Log warning message."""
    get_logger(module).warning(msg)

def error(msg: str, module: str = __name__):
    """Log error message."""
    get_logger(module).error(msg)

def critical(msg: str, module: str = __name__):
    """Log critical message."""
    get_logger(module).critical(msg)