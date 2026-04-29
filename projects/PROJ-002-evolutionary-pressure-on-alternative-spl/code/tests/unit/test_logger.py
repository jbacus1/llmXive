"""
Unit tests for the logging infrastructure.
"""

import pytest
import logging
from pathlib import Path
import tempfile
import shutil
from code.src.utils.logger import PipelineLogger, get_logger, init_logging


class TestPipelineLogger:
    """Tests for PipelineLogger class."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.temp_dir)
    
    def test_singleton_pattern(self):
        """Test that PipelineLogger is a singleton."""
        logger1 = PipelineLogger()
        logger2 = PipelineLogger()
        assert logger1 is logger2
    
    def test_default_initialization(self):
        """Test logger initialization with defaults."""
        logger = PipelineLogger()
        assert logger.pipeline_name == "evolutionary-pressure-pipeline"
        assert logger.config["console_output"] is True
    
    def test_custom_log_level(self):
        """Test custom log level configuration."""
        logger = PipelineLogger(log_level="DEBUG")
        assert logger.config["log_level"] == "DEBUG"
    
    def test_custom_log_directory(self):
        """Test custom log directory."""
        custom_dir = Path(self.temp_dir) / "custom_logs"
        logger = PipelineLogger(log_dir=custom_dir)
        assert logger.config["log_dir"] == str(custom_dir)
        assert custom_dir.exists()
    
    def test_console_output_disabled(self):
        """Test disabling console output."""
        logger = PipelineLogger(console_output=False)
        assert logger.config["console_output"] is False
    
    def test_get_logger(self):
        """Test getting underlying logger."""
        logger = PipelineLogger()
        underlying = logger.get_logger()
        assert isinstance(underlying, logging.Logger)
    
    def test_log_levels(self, caplog):
        """Test different log levels."""
        logger = PipelineLogger(log_level="DEBUG")
        
        with caplog.at_level(logging.DEBUG):
            logger.debug("debug message")
            logger.info("info message")
            logger.warning("warning message")
            logger.error("error message")
            logger.critical("critical message")
        
        assert "debug message" in caplog.text
        assert "info message" in caplog.text
        assert "warning message" in caplog.text
        assert "error message" in caplog.text
        assert "critical message" in caplog.text
    
    def test_pipeline_start_logging(self, caplog):
        """Test pipeline stage start logging."""
        logger = PipelineLogger(log_level="INFO")
        
        with caplog.at_level(logging.INFO):
            logger.pipeline_start("data_acquisition", samples=100, species="human")
        
        assert "PIPELINE_START" in caplog.text
        assert "stage=data_acquisition" in caplog.text
        assert "samples=100" in caplog.text
    
    def test_pipeline_stage_logging(self, caplog):
        """Test pipeline stage action logging."""
        logger = PipelineLogger(log_level="INFO")
        
        with caplog.at_level(logging.INFO):
            logger.pipeline_stage("alignment", "process_batch", batch_id=1, reads=1000000)
        
        assert "STAGE" in caplog.text
        assert "action=process_batch" in caplog.text
    
    def test_pipeline_error_logging(self, caplog):
        """Test pipeline error logging."""
        logger = PipelineLogger(log_level="ERROR")
        
        with caplog.at_level(logging.ERROR):
            logger.pipeline_error("alignment", "STAR failed", sample_id="S001")
        
        assert "PIPELINE_ERROR" in caplog.text
        assert "error=STAR failed" in caplog.text
    
    def test_pipeline_complete_logging(self, caplog):
        """Test pipeline completion logging with metrics."""
        logger = PipelineLogger(log_level="INFO")
        
        with caplog.at_level(logging.INFO):
            logger.pipeline_complete("quantification", psi_events=500, fdr=0.05)
        
        assert "PIPELINE_COMPLETE" in caplog.text
        assert "psi_events=500" in caplog.text
    
    def test_set_level(self):
        """Test dynamic log level change."""
        logger = PipelineLogger(log_level="ERROR")
        assert logger.config["log_level"] == "ERROR"
        
        logger.set_level("DEBUG")
        assert logger.config["log_level"] == "DEBUG"
    
    def test_get_config(self):
        """Test getting logger configuration."""
        logger = PipelineLogger(log_level="WARNING", log_file="test.log")
        config = logger.get_config()
        
        assert config["log_level"] == "WARNING"
        assert config["log_file"] == "test.log"
        assert "pipeline_name" in config
    
    def test_exception_logging(self, caplog):
        """Test exception logging with traceback."""
        logger = PipelineLogger(log_level="ERROR")
        
        try:
            raise ValueError("Test error")
        except ValueError:
            with caplog.at_level(logging.ERROR):
                logger.exception("An error occurred")
        
        assert "An error occurred" in caplog.text
        assert "ValueError" in caplog.text

class TestGetLogger:
    """Tests for get_logger function."""
    
    def test_get_logger_returns_instance(self):
        """Test that get_logger returns a PipelineLogger."""
        logger = get_logger()
        assert isinstance(logger, PipelineLogger)
    
    def test_get_logger_with_name(self):
        """Test get_logger with custom name."""
        logger = get_logger(pipeline_name="custom-pipeline")
        assert logger.pipeline_name == "custom-pipeline"

class TestInitLogging:
    """Tests for init_logging function."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.temp_dir)
    
    def test_init_logging(self):
        """Test init_logging function."""
        logger = init_logging(
            log_level="DEBUG",
            log_dir=Path(self.temp_dir),
            log_file="init_test.log",
            pipeline_name="test-pipeline"
        )
        
        assert logger.pipeline_name == "test-pipeline"
        assert logger.config["log_level"] == "DEBUG"
    
    def test_init_logging_returns_logger(self):
        """Test that init_logging returns a PipelineLogger."""
        logger = init_logging()
        assert isinstance(logger, PipelineLogger)

class TestLog:
    """Tests for log convenience function."""
    
    def test_log_debug(self, caplog):
        """Test log function with DEBUG level."""
        with caplog.at_level(logging.DEBUG):
            from code.src.utils.logger import log
            log("debug message", level="DEBUG")
        assert "debug message" in caplog.text
    
    def test_log_info(self, caplog):
        """Test log function with INFO level."""
        with caplog.at_level(logging.INFO):
            from code.src.utils.logger import log
            log("info message", level="INFO")
        assert "info message" in caplog.text