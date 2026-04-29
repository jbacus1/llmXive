"""
Logging configuration for Climate-Smart Agricultural Practices project.

Provides centralized logging setup with configurable levels, handlers,
and formatters. Follows Principle I (Constitutional Compliance) for
consistent logging across all modules.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Project root for log file placement
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Log directory
LOG_DIR = PROJECT_ROOT / "logs"

# Default configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5


class LoggingConfig:
    """Centralized logging configuration manager."""
    
    _logger: Optional[logging.Logger] = None
    _configured: bool = False
    
    @classmethod
    def configure(
        cls,
        log_level: int = DEFAULT_LOG_LEVEL,
        log_file: Optional[str] = None,
        console_output: bool = True,
        file_output: bool = True,
    ) -> logging.Logger:
        """
        Configure logging for the application.
        
        Args:
            log_level: Minimum logging level (e.g., logging.DEBUG, logging.INFO)
            log_file: Optional path to log file (default: logs/app.log)
            console_output: Whether to log to console
            file_output: Whether to log to file
        
        Returns:
            Configured root logger
        """
        if cls._configured:
            return cls._logger
        
        # Create log directory if it doesn't exist
        if file_output:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            log_path = Path(log_file) if log_file else LOG_DIR / "app.log"
        else:
            log_path = None
        
        # Get or create root logger
        logger = logging.getLogger("climate_smart_ag")
        logger.setLevel(log_level)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Add console handler if requested
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_formatter = logging.Formatter(
                fmt=DEFAULT_LOG_FORMAT,
                datefmt=DEFAULT_DATE_FORMAT
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # Add file handler if requested
        if file_output and log_path:
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=MAX_LOG_SIZE,
                backupCount=BACKUP_COUNT,
                encoding="utf-8"
            )
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter(
                fmt=DEFAULT_LOG_FORMAT,
                datefmt=DEFAULT_DATE_FORMAT
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        cls._logger = logger
        cls._configured = True
        
        return logger
    
    @classmethod
    def get_logger(cls, name: str = None) -> logging.Logger:
        """
        Get a logger instance.
        
        Args:
            name: Logger name (defaults to "climate_smart_ag")
        
        Returns:
            Logger instance
        """
        if not cls._configured:
            cls.configure()
        
        if name:
            return logging.getLogger(f"climate_smart_ag.{name}")
        return cls._logger
    
    @classmethod
    def reset(cls):
        """Reset logging configuration (useful for testing)."""
        cls._logger = None
        cls._configured = False


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    file_output: bool = True,
) -> logging.Logger:
    """
    Convenience function to configure logging.
    
    Args:
        log_level: Log level as string ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        log_file: Optional path to log file
        console_output: Whether to output to console
        file_output: Whether to output to file
    
    Returns:
        Configured root logger
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    
    level = level_map.get(log_level.upper(), DEFAULT_LOG_LEVEL)
    return LoggingConfig.configure(
        log_level=level,
        log_file=log_file,
        console_output=console_output,
        file_output=file_output,
    )

# Module-level convenience logger
def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance for the module."""
    return LoggingConfig.get_logger(name)

# Initialize default configuration
setup_logging()
