"""
Pytest configuration and shared fixtures for all test suites.

Per spec.md: Tests are REQUIRED per Independent Test scenarios.
All fixtures here are available to contract/, integration/, and unit/ tests.
"""
import os
import sys
import pytest
from pathlib import Path
from datetime import datetime
import numpy as np

# Add project code to path for imports
@pytest.fixture(scope="session", autouse=True)
def add_project_to_path():
    """Ensure project code is importable during tests."""
    project_root = Path(__file__).parent.parent
    code_path = project_root / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    yield
    if str(code_path) in sys.path:
        sys.path.remove(str(code_path))

@pytest.fixture
def project_root():
    """Return the project root directory path."""
    return Path(__file__).parent.parent

@pytest.fixture
def code_dir(project_root):
    """Return the code directory path."""
    return project_root / "code"

@pytest.fixture
def data_dir(project_root):
    """Return the data directory path."""
    return project_root / "data"

@pytest.fixture
def raw_data_dir(data_dir):
    """Return the raw data directory path."""
    return data_dir / "raw"

@pytest.fixture
def processed_data_dir(data_dir):
    """Return the processed data directory path."""
    return data_dir / "processed"

@pytest.fixture
def config_path(code_dir):
    """Return the config.yaml path."""
    return code_dir / "config.yaml"

@pytest.fixture
def synthetic_timeseries(length=1000, seed=42):
    """
    Generate a synthetic time series with known anomaly points.
    
    Used for US1 independent testing: processes synthetic time series with
    known anomaly points and verifies model produces anomaly scores.
    
    Args:
        length: Number of observations
        seed: Random seed for reproducibility
    
    Returns:
        tuple: (values array, anomaly_indices array)
    """
    np.random.seed(seed)
    t = np.arange(length)
    
    # Base signal: sine wave + trend + noise
    base = 10 * np.sin(2 * np.pi * t / 100) + 0.01 * t + np.random.normal(0, 1, length)
    
    # Inject known anomalies at specific indices
    anomaly_indices = np.array([150, 151, 152, 450, 451, 750, 751, 752])
    base[anomaly_indices] = base[anomaly_indices] + np.random.choice([-1, 1], len(anomaly_indices)) * 5
    
    return base, anomaly_indices

@pytest.fixture
def synthetic_streaming_data(num_observations=100, seed=42):
    """
    Generate streaming observations for US1 streaming update testing.
    
    Used for T014 integration test for streaming observation update.
    
    Args:
        num_observations: Number of streaming observations
        seed: Random seed for reproducibility
    
    Returns:
        generator: Yields observations one at a time
    """
    np.random.seed(seed)
    
    def observation_generator():
        for i in range(num_observations):
            # Normal observation
            value = np.random.normal(0, 1)
            
            # Inject anomaly at observation 50
            if i == 50:
                value = 5.0
            
            yield {"timestamp": datetime.now(), "value": value, "index": i}
    
    return observation_generator()

@pytest.fixture
def memory_budget_gb():
    """Return memory budget per SC-003 (7GB for US1)."""
    return 7.0

@pytest.fixture
def runtime_budget_minutes():
    """Return runtime budget per SC-003 (30 minutes)."""
    return 30

@pytest.fixture
def anomaly_threshold_percentile():
    """Return default anomaly threshold percentile (95th per FR-004)."""
    return 95
