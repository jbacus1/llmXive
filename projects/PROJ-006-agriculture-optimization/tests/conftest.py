"""
Shared pytest fixtures and configuration for the Climate-Smart Agricultural
Practices project.

This file is automatically discovered by pytest and provides fixtures
that can be used across all test modules.
"""
import os
import sys
import tempfile
from pathlib import Path
from typing import Generator, Optional

import pytest

# Add src to path for imports during testing
@pytest.fixture(autouse=True)
def add_src_to_path():
    """Automatically add src directory to Python path for all tests."""
    src_path = Path(__file__).parent.parent / "src"
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    yield
    if str(src_path) in sys.path:
        sys.path.remove(str(src_path))

@pytest.fixture
def test_data_dir() -> Path:
    """Provide path to test data directory."""
    base_dir = Path(__file__).parent.parent
    test_data = base_dir / "tests" / "data"
    test_data.mkdir(parents=True, exist_ok=True)
    return test_data

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_config() -> dict:
    """Provide a sample configuration for testing."""
    return {
        "api_keys": {
            "openweathermap": "test_key",
            "usgs": "test_key"
        },
        "paths": {
            "data_raw": "data/raw",
            "data_processed": "data/processed",
            "output": "data/output"
        },
        "settings": {
            "cache_enabled": True,
            "log_level": "DEBUG"
        }
    }

@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "test_api_key_12345")
    monkeypatch.setenv("USGS_API_KEY", "test_usgs_key_12345")
    monkeypatch.setenv("PROJECT_ROOT", str(Path(__file__).parent.parent))

@pytest.fixture
def sample_climate_data() -> dict:
    """Provide sample climate data for testing."""
    return {
        "location": {"lat": 40.7128, "lon": -74.0060},
        "temperature": {"avg": 25.5, "min": 18.0, "max": 32.0},
        "precipitation": {"total": 120.5, "days": 15},
        "humidity": 65,
        "wind_speed": 12.3
    }

@pytest.fixture
def sample_survey_data() -> dict:
    """Provide sample survey data for testing."""
    return {
        "farm_id": "FARM_001",
        "location": {"lat": 40.7128, "lon": -74.0060},
        "area_hectares": 50.5,
        "crops": ["maize", "wheat"],
        "yield_history": [4.2, 4.5, 4.8],
        "practices": ["irrigation", "crop_rotation"]
    }

@pytest.fixture
def skip_if_no_api_keys() -> None:
    """Skip test if required API keys are not configured."""
    required_keys = ["OPENWEATHERMAP_API_KEY", "USGS_API_KEY"]
    missing = [key for key in required_keys if not os.environ.get(key)]
    if missing:
        pytest.skip(f"Missing required API keys: {', '.join(missing)}")

@pytest.fixture
def skip_if_no_network() -> None:
    """Skip test if network is unavailable."""
    import socket
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=1)
    except socket.timeout:
        pytest.skip("No network connection available")

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Provide path to project root directory."""
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def src_root(project_root: Path) -> Path:
    """Provide path to src directory."""
    return project_root / "src"

@pytest.fixture(scope="session")
def tests_root(project_root: Path) -> Path:
    """Provide path to tests directory."""
    return project_root / "tests"

@pytest.fixture
def data_model_schema() -> dict:
    """Provide sample data model schema for contract tests."""
    return {
        "type": "object",
        "properties": {
            "farm_id": {"type": "string"},
            "location": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lon": {"type": "number"}
                },
                "required": ["lat", "lon"]
            },
            "timestamp": {"type": "string", "format": "date-time"}
        },
        "required": ["farm_id", "location"]
    }