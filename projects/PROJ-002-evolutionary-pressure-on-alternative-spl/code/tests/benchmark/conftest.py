"""
Pytest configuration for benchmark tests

This conftest provides custom fixtures and configuration for
running performance benchmarks with pytest-benchmark plugin.
"""

import pytest
from pathlib import Path
import sys
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))


@pytest.fixture(scope='session')
def benchmark_data_dir(tmp_path_factory):
    """Fixture providing temporary directory for benchmark data"""
    return tmp_path_factory.mktemp('benchmark_data')


@pytest.fixture(scope='session')
def baseline_metrics():
    """Fixture loading baseline performance metrics for comparison"""
    baseline_file = Path(__file__).parent / 'baseline_metrics.json'
    if baseline_file.exists():
        with open(baseline_file, 'r') as f:
            return json.load(f)
    return {}


@pytest.fixture(scope='function')
def benchmark_suite():
    """Fixture providing fresh benchmark suite instance"""
    from test_benchmark_suite import BenchmarkSuite
    return BenchmarkSuite()


def pytest_configure(config):
    """Configure pytest markers for benchmarks"""
    config.addinivalue_line(
        "markers", "benchmark: mark test as a performance benchmark"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection for benchmark-specific behavior"""
    # Separate benchmark tests from regular tests
    benchmark_items = []
    regular_items = []

    for item in items:
        if 'benchmark' in item.keywords:
            benchmark_items.append(item)
        else:
            regular_items.append(item)

    # Run benchmark tests after regular tests
    if config.getoption('--benchmark-only'):
        items[:] = benchmark_items
    else:
        items[:] = regular_items + benchmark_items


# Benchmark-specific command line options
def pytest_addoption(parser):
    parser.addoption(
        "--benchmark-only",
        action="store_true",
        default=False,
        help="Run only benchmark tests"
    )
    parser.addoption(
        "--benchmark-iterations",
        type=int,
        default=3,
        help="Number of iterations for each benchmark"
    )
    parser.addoption(
        "--benchmark-save-results",
        action="store_true",
        default=True,
        help="Save benchmark results to JSON file"
    )
