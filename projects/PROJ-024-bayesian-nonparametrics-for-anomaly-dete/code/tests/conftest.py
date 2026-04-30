"""
Pytest configuration and shared fixtures.

This file is automatically loaded by pytest and provides:
- Shared fixtures for all test modules
- Test configuration
- Common setup/teardown logic
"""
import os
import sys
import pytest
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to path for imports
@pytest.fixture(scope="session", autouse=True)
def setup_path():
    """Add project root to sys.path for imports."""
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    yield
    sys.path.remove(str(project_root))

@pytest.fixture
def sample_timeseries():
    """Create a sample time series for testing."""
    np.random.seed(42)
    n_points = 100
    # Normal observations
    data = np.random.normal(loc=0, scale=1, size=n_points)
    # Add some anomalies (5% of data)
    anomaly_indices = np.random.choice(n_points, size=int(n_points * 0.05), replace=False)
    data[anomaly_indices] += np.random.uniform(3, 5, size=len(anomaly_indices))
    timestamps = pd.date_range(start="2024-01-01", periods=n_points, freq="H")
    return pd.DataFrame({
        "timestamp": timestamps,
        "value": data,
        "is_anomaly": [i in anomaly_indices for i in range(n_points)]
    })

@pytest.fixture
def synthetic_config():
    """Create a minimal config for testing."""
    return {
        "random_seed": 42,
        "dp_gmm": {
            "alpha": 1.0,
            "max_clusters": 10,
            "convergence_threshold": 1e-6
        },
        "threshold": {
            "percentile": 95,
            "min_anomaly_rate": 0.01,
            "max_anomaly_rate": 0.1
        },
        "paths": {
            "data_dir": "data/",
            "output_dir": "state/"
        }
    }

@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create a temporary output directory for test artifacts."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True)
    yield output_dir

@pytest.fixture(autouse=True)
def reset_random_state():
    """Reset random state before each test for reproducibility."""
    np.random.seed(42)
    yield
