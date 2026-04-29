"""
Logging infrastructure for pipeline operations.

Provides configurable, thread-safe logging with support for:
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Console and file output
- Structured logging with timestamps and context
- Pipeline-specific log formatting
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import threading


class PipelineLogger:
    """
    Thread-safe logging infrastructure for pipeline operations.
    
    Supports multiple handlers, configurable log levels, and
    structured output suitable for pipeline monitoring and debugging.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure single logger instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        log_level: str = "INFO",
        log_dir: Optional[Path] = None,
        log_file: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        console_output: bool = True,
        pipeline_name: Optional[str] = None
    ):
        """
        Initialize the pipeline logger.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files (defaults to code/logs/)
            log_file: Specific log filename (defaults to pipeline.log)
            max_bytes: Max size before log rotation
            backup_count: Number of backup log files to keep
            console_output: Whether to output to console
            pipeline_name: Name to prefix in log messages
        """
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.pipeline_name = pipeline_name or "evolutionary-pressure-pipeline"
        
        # Set up logger
        self.logger = logging.getLogger(self.pipeline_name)
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        self.logger.handlers = []  # Clear existing handlers
        
        # Create log directory if needed
        if log_dir is None:
            log_dir = Path("code/logs")
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Format for log messages
        log_format = (
            "%(asctime)s | %(levelname)-8s | %(name)s | "
            "%(threadName)s | %(message)s"
        )
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler with rotation
        if log_file is None:
            log_file = "pipeline.log"
        log_path = log_dir / log_file
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Store configuration for reference
        self.config = {
            "log_level": log_level.upper(),
            "log_dir": str(log_dir),
            "log_file": log_file,
            "max_bytes": max_bytes,
            "backup_count": backup_count,
            "console_output": console_output,
            "pipeline_name": self.pipeline_name
        }
    
    def get_logger(self) -> logging.Logger:
        """Return the underlying logger instance."""
        return self.logger
    
    def debug(self, message: str, *args, **kwargs):
        """Log a DEBUG message."""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log an INFO message."""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log a WARNING message."""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log an ERROR message."""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log a CRITICAL message."""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log an ERROR message with exception traceback."""
        self.logger.exception(message, *args, **kwargs)
    
    def pipeline_start(self, stage: str, **context):
        """Log pipeline stage start with context."""
        context_str = " | ".join(f"{k}={v}" for k, v in context.items())
        self.info(f"PIPELINE_START | stage={stage} | {context_str}")
    
    def pipeline_stage(self, stage: str, action: str, **context):
        """Log a pipeline stage action."""
        context_str = " | ".join(f"{k}={v}" for k, v in context.items())
        self.info(f"STAGE | stage={stage} | action={action} | {context_str}")
    
    def pipeline_error(self, stage: str, error: str, **context):
        """Log a pipeline error."""
        context_str = " | ".join(f"{k}={v}" for k, v in context.items())
        self.error(f"PIPELINE_ERROR | stage={stage} | error={error} | {context_str}")
    
    def pipeline_complete(self, stage: str, **metrics):
        """Log pipeline stage completion with metrics."""
        metrics_str = " | ".join(f"{k}={v}" for k, v in metrics.items())
        self.info(f"PIPELINE_COMPLETE | stage={stage} | {metrics_str}")
    
    def set_level(self, level: str):
        """Change the logging level dynamically."""
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        for handler in self.logger.handlers:
            handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    def get_config(self) -> dict:
        """Return current logger configuration."""
        return self.config.copy()

def get_logger(pipeline_name: Optional[str] = None) -> PipelineLogger:
    """
    Factory function to get the pipeline logger instance.
    
    Args:
        pipeline_name: Optional name for the pipeline (uses default if None)
    
    Returns:
        Configured PipelineLogger instance
    """
    return PipelineLogger(pipeline_name=pipeline_name)

# Convenience function for simple logging
def log(message: str, level: str = "INFO"):
    """
    Quick logging function for simple use cases.
    
    Args:
        message: Message to log
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger = get_logger()
    getattr(logger, level.lower())(message)

# Module-level default logger
_default_logger = None

def init_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    log_file: Optional[str] = None,
    console_output: bool = True,
    pipeline_name: Optional[str] = None
) -> PipelineLogger:
    """
    Initialize logging for the entire application.
    
    Should be called once at application startup.
    
    Args:
        log_level: Logging level
        log_dir: Directory for log files
        log_file: Log filename
        console_output: Output to console
        pipeline_name: Pipeline name for identification
    
    Returns:
        Initialized PipelineLogger instance
    """
    global _default_logger
    _default_logger = PipelineLogger(
        log_level=log_level,
        log_dir=log_dir,
        log_file=log_file,
        console_output=console_output,
        pipeline_name=pipeline_name
    )
    return _default_logger

def get_default_logger() -> PipelineLogger:
    """Get the default logger, initializing if necessary."""
    global _default_logger
    if _default_logger is None:
        _default_logger = PipelineLogger()
    return _default_logger
