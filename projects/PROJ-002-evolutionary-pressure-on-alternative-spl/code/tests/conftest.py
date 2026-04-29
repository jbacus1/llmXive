"""
Shared pytest fixtures and configuration for the evolutionary splicing project.
"""
import pytest
import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
TEST_DATA_DIR = PROJECT_ROOT / "test_data"

# Common test configuration
@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return PROJECT_ROOT

@pytest.fixture(scope="session")
def code_dir():
    """Return the code source directory."""
    return CODE_DIR

@pytest.fixture(scope="session")
def data_dir():
    """Return the data directory."""
    return DATA_DIR

@pytest.fixture(scope="session")
def test_data_dir():
    """Return the test data directory."""
    return TEST_DATA_DIR

@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path):
    """Set up isolated test environment for each test."""
    # Set environment variables for test isolation
    os.environ["TEST_MODE"] = "true"
    os.environ["PROJECT_ROOT"] = str(PROJECT_ROOT)
    yield
    # Cleanup after test
    os.environ.pop("TEST_MODE", None)

@pytest.fixture
def sample_metadata():
    """Provide sample metadata for testing."""
    return {
        "species": "human",
        "tissue": "cortex",
        "sample_id": "test_sample_001",
        "sra_accession": "SRR1234567",
        "fastq_path": str(TEST_DATA_DIR / "test.fastq.gz")
    }