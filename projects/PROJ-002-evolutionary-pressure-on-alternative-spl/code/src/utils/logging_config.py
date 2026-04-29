"""
Logging infrastructure for pipeline operations.

Provides centralized logging configuration with consistent formatting,
multiple handlers (file and console), and proper log level management
for the evolutionary pressure analysis pipeline.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from .config import get_config


# Log format patterns
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEBUG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
PIPELINE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

# Log level mapping
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class PipelineLogger:
    """
    Centralized logger for pipeline operations.

    Manages loggers for different pipeline components with consistent
    formatting and output destinations.
    """

    _loggers: dict[str, logging.Logger] = {}
    _initialized: bool = False

    @classmethod
    def initialize(cls, config: Optional[dict] = None) -> None:
        """
        Initialize the logging infrastructure.

        Args:
            config: Optional configuration dict. If None, loads from config file.
        """
        if cls._initialized:
            return

        # Load configuration
        if config is None:
            config = get_config()

        log_config = config.get("logging", {})
        log_level = log_config.get("level", "INFO").upper()
        log_dir = log_config.get("log_dir", "state/logs")
        log_file = log_config.get("file", "pipeline.log")
        max_bytes = log_config.get("max_bytes", 10 * 1024 * 1024)  # 10MB
        backup_count = log_config.get("backup_count", 5)
        console_enabled = log_config.get("console_enabled", True)

        # Ensure log directory exists
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Get log level
        level = LOG_LEVELS.get(log_level, logging.INFO)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Create file handler with rotation
        log_file_path = log_path / log_file
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(DEFAULT_FORMAT))

        # Create console handler if enabled
        if console_enabled:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(logging.Formatter(DEFAULT_FORMAT))
            root_logger.addHandler(console_handler)

        # Add file handler
        root_logger.addHandler(file_handler)

        # Suppress noisy third-party logs
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

        cls._initialized = True
        logging.info("Logging infrastructure initialized")

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get or create a named logger for a pipeline component.

        Args:
            name: Logger name (typically module name)

        Returns:
            Configured logger instance
        """
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            # Don't propagate to root to avoid duplicate handlers
            logger.propagate = False
            cls._loggers[name] = logger
        return cls._loggers[name]

    @classmethod
    def get_component_logger(cls, component: str) -> logging.Logger:
        """
        Get a logger for a specific pipeline component.

        Args:
            component: Component name (e.g., 'acquisition', 'alignment', 'quantification')

        Returns:
            Configured logger instance for the component
        """
        return cls.get_logger(f"pipeline.{component}")


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    return PipelineLogger.get_logger(name)


def get_component_logger(component: str) -> logging.Logger:
    """
    Convenience function to get a component logger.

    Args:
        component: Component name

    Returns:
        Configured logger instance
    """
    return PipelineLogger.get_component_logger(component)


def log_pipeline_event(
    logger: logging.Logger,
    event: str,
    details: Optional[dict] = None,
    level: str = "INFO",
) -> None:
    """
    Log a structured pipeline event.

    Args:
        logger: Logger instance to use
        event: Event name (e.g., 'sample_downloaded', 'alignment_complete')
        details: Optional dict of event details for structured logging
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_method = getattr(logger, level.lower(), logger.info)
    message = f"EVENT: {event}"
    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        message += f" | {detail_str}"
    log_method(message)

# Initialize logging when module is imported (optional, can be called explicitly)
# PipelineLogger.initialize()
