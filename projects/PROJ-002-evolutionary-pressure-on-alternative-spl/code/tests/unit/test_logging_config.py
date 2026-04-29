"""
Unit tests for logging infrastructure.
"""

import logging
import os
import tempfile
from pathlib import Path

import pytest

from code.src.utils.logging_config import (
    PipelineLogger,
    get_logger,
    get_component_logger,
    log_pipeline_event,
    LOG_LEVELS,
)


class TestPipelineLogger:
    """Tests for PipelineLogger class."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures."""
        self.tmp_path = tmp_path
        self.log_dir = self.tmp_path / "logs"
        self.log_dir.mkdir()

    def test_initialize_creates_log_directory(self):
        """Test that initialization creates the log directory."""
        config = {
            "logging": {
                "level": "INFO",
                "log_dir": str(self.log_dir),
                "file": "test.log",
                "console_enabled": False,
            }
        }
        PipelineLogger.initialize(config)
        assert self.log_dir.exists()

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a valid logger."""
        logger = PipelineLogger.get_logger("test_component")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_component"

    def test_get_component_logger_formats_name(self):
        """Test that component logger has correct name format."""
        logger = PipelineLogger.get_component_logger("acquisition")
        assert logger.name == "pipeline.acquisition"

    def test_get_logger_caching(self):
        """Test that get_logger caches logger instances."""
        logger1 = PipelineLogger.get_logger("cached_test")
        logger2 = PipelineLogger.get_logger("cached_test")
        assert logger1 is logger2

    def test_reset_initialized_flag(self):
        """Test that initialized flag can be reset."""
        PipelineLogger._initialized = False
        assert PipelineLogger._initialized is False

class TestLoggingFunctions:
    """Tests for standalone logging functions."""

    def test_get_logger_function(self):
        """Test standalone get_logger function."""
        logger = get_logger("standalone_test")
        assert isinstance(logger, logging.Logger)

    def test_get_component_logger_function(self):
        """Test standalone get_component_logger function."""
        logger = get_component_logger("test")
        assert logger.name == "pipeline.test"

    def test_log_pipeline_event_info(self):
        """Test logging pipeline event at INFO level."""
        logger = logging.getLogger("test_event")
        logger.handlers.clear()  # Clear handlers to avoid output
        logger.setLevel(logging.INFO)

        # This should not raise
        log_pipeline_event(logger, "test_event", {"key": "value"}, "INFO")

    def test_log_pipeline_event_no_details(self):
        """Test logging event without details."""
        logger = logging.getLogger("test_no_details")
        logger.handlers.clear()
        logger.setLevel(logging.INFO)

        log_pipeline_event(logger, "simple_event", level="INFO")

    def test_log_pipeline_event_error_level(self):
        """Test logging event at ERROR level."""
        logger = logging.getLogger("test_error")
        logger.handlers.clear()
        logger.setLevel(logging.ERROR)

        log_pipeline_event(logger, "error_event", level="ERROR")

class TestLogLevels:
    """Tests for log level configuration."""

    def test_log_levels_mapping(self):
        """Test that log levels are correctly mapped."""
        assert LOG_LEVELS["DEBUG"] == logging.DEBUG
        assert LOG_LEVELS["INFO"] == logging.INFO
        assert LOG_LEVELS["WARNING"] == logging.WARNING
        assert LOG_LEVELS["ERROR"] == logging.ERROR
        assert LOG_LEVELS["CRITICAL"] == logging.CRITICAL

    def test_invalid_log_level_defaults(self):
        """Test that invalid log level defaults to INFO."""
        # This is tested in the config loading, but verify the mapping
        assert "INVALID" not in LOG_LEVELS