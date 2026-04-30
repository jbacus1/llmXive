"""
Pytest configuration and shared fixtures for the test suite.

This file provides:
- Shared fixtures for test data and models
- Configuration for test discovery
- Common test utilities
"""
import os
import sys
import pytest
from pathlib import Path
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Add project code to path for imports
@pytest.fixture(scope="session", autouse=True)
def setup_test_paths():
    """Add project code directory to Python path for imports."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    if code_dir not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    # Cleanup if needed
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture
def sample_timeseries_data():
    """Generate sample time series data for testing."""
    np.random.seed(42)
    n_points = 1000
    time = np.arange(n_points)
    # Base signal: sine wave with noise
    signal = np.sin(2 * np.pi * time / 50) + np.random.normal(0, 0.1, n_points)
    # Inject anomalies at known positions
    anomaly_positions = [100, 300, 500, 700, 900]
    for pos in anomaly_positions:
        if pos < n_points:
            signal[pos] += 5.0  # Add spike anomalies
    return {
        "time": time,
        "values": signal,
        "anomaly_positions": anomaly_positions,
        "n_points": n_points
    }

@pytest.fixture
def sample_anomaly_labels():
    """Generate sample anomaly labels for testing."""
    n_points = 1000
    labels = np.zeros(n_points, dtype=int)
    anomaly_positions = [100, 300, 500, 700, 900]
    for pos in anomaly_positions:
        if pos < n_points:
            labels[pos] = 1
    return labels

@pytest.fixture
def test_config():
    """Provide a test configuration dictionary."""
    return {
        "random_seed": 42,
        "n_components": 5,
        "concentration_parameter": 1.0,
        "learning_rate": 0.01,
        "max_iterations": 100,
        "anomaly_threshold": 0.95,
        "memory_limit_gb": 7.0,
        "runtime_limit_minutes": 30
    }

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory for test artifacts."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    yield data_dir

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for test results."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    yield output_dir

@pytest.fixture
def mock_streaming_observations(sample_timeseries_data):
    """Generate mock streaming observations for testing."""
    for i, value in enumerate(sample_timeseries_data["values"]):
        yield {
            "timestamp": datetime.now(),
            "value": float(value),
            "index": i
        }

@pytest.fixture
def contract_test_schema():
    """Provide a basic contract schema for validation tests."""
    return {
        "required_fields": [
            "model_type",
            "timestamp",
            "anomaly_score",
            "confidence_interval"
        ],
        "field_types": {
            "model_type": str,
            "timestamp": (str, datetime),
            "anomaly_score": (float, np.floating),
            "confidence_interval": (list, tuple, np.ndarray)
        }
    }

@pytest.fixture
def baseline_comparison_data():
    """Provide data for baseline comparison tests."""
    np.random.seed(123)
    n_samples = 500
    return {
        "dp_gmm_scores": np.random.normal(0.5, 0.2, n_samples),
        "arima_scores": np.random.normal(0.6, 0.25, n_samples),
        "ma_scores": np.random.normal(0.55, 0.3, n_samples),
        "ground_truth": np.random.randint(0, 2, n_samples)
    }

@pytest.fixture
def threshold_calibration_data():
    """Provide data for threshold calibration tests."""
    np.random.seed(456)
    n_samples = 1000
    return {
        "scores": np.random.exponential(scale=1.0, size=n_samples),
        "expected_percentile": 95,
        "target_anomaly_rate": 0.05
    }

@pytest.fixture
def memory_profile_config():
    """Provide configuration for memory profiling tests."""
    return {
        "max_memory_gb": 7.0,
        "sample_size": 1000,
        "measurement_interval_ms": 100,
        "gc_collect_before": True
    }

@pytest.fixture(autouse=True)
def reset_state_between_tests():
    """Reset any global state between test runs."""
    yield
    # Force garbage collection after each test
    import gc
    gc.collect()
