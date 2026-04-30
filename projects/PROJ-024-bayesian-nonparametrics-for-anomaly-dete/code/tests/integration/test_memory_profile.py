"""
Memory usage test for DPGMM streaming implementation.

Verifies that processing 1000 observations stays under 7GB RAM constraint (FR-005).

NOTE: This test is designed to FAIL initially because DPGMMModel (T030) is not yet
implemented. This is expected - tests are written FIRST per plan.md requirements.
Run after T030 implementation to verify memory constraint.
"""

import pytest
import sys
import tracemalloc
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.memory_profiler import MemoryProfiler, MemoryUsageResult
from models.timeseries import TimeSeries
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Constants
MAX_MEMORY_GB = 7.0
MAX_MEMORY_MB = MAX_MEMORY_GB * 1024
TEST_OBSERVATIONS = 1000
MEMORY_TOLERANCE = 0.10  # 10% tolerance for measurement variance


@pytest.mark.integration
class TestDPGMMMemoryUsage:
    """Memory usage tests for DPGMM streaming implementation."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for memory tracking."""
        tracemalloc.start()
        yield
        tracemalloc.stop()

    def test_streaming_1000_observations_under_7gb(self):
        """Test that processing 1000 observations stays under 7GB RAM.

        This verifies FR-005: Memory usage constraint for streaming deployment.
        The DPGMM streaming architecture should not accumulate memory during
        incremental updates.

        Expected: Peak memory < 7GB (typically < 1GB for this workload)
        """
        logger.info(f"Testing memory usage for {TEST_OBSERVATIONS} observations")

        # Generate synthetic time series data
        ts = TimeSeries.generate_synthetic(
            n_observations=TEST_OBSERVATIONS,
            n_features=1,
            anomaly_rate=0.05,
            seed=42
        )

        # Import DPGMMModel - will raise ImportError if not implemented (expected)
        try:
            from models.dpgmm import DPGMMModel
        except ImportError as e:
            pytest.fail(
                f"DPGMMModel not yet implemented (T030). "
                f"Import error: {e}. "
                f"Complete T030 before running this test."
            )

        # Initialize model with memory profiler
        profiler = MemoryProfiler()
        model = DPGMMModel()

        # Process observations in streaming fashion
        memory_samples = []
        for i, observation in enumerate(ts.observations):
            model.update(observation)

            # Sample memory every 100 observations
            if i % 100 == 0:
                mem_result = profiler.get_memory_usage()
                memory_samples.append(mem_result.current_mb)
                logger.debug(
                    f"Observation {i}: Memory = {mem_result.current_mb:.2f} MB"
                )

        # Add final sample
        final_mem = profiler.get_memory_usage()
        memory_samples.append(final_mem.current_mb)
        logger.info(f"Final memory: {final_mem.current_mb:.2f} MB")

        # Assert memory stays under limit
        peak_memory = max(memory_samples)
        assert peak_memory < MAX_MEMORY_MB, (
            f"Memory exceeded 7GB limit: {peak_memory:.2f} MB. "
            f"Streaming architecture may have memory leak."
        )

        logger.info(
            f"Memory test PASSED: Peak {peak_memory:.2f} MB / {MAX_MEMORY_GB} GB"
        )

    def test_memory_bounded_during_updates(self):
        """Test that memory does not grow unboundedly during streaming updates.

        This verifies the streaming architecture maintains bounded memory
        regardless of observation count (within reason for 1000 observations).
        """
        logger.info("Testing memory boundedness during streaming updates")

        # Generate time series
        ts = TimeSeries.generate_synthetic(
            n_observations=TEST_OBSERVATIONS,
            n_features=1,
            anomaly_rate=0.05,
            seed=42
        )

        try:
            from models.dpgmm import DPGMMModel
        except ImportError as e:
            pytest.skip(f"DPGMMModel not implemented: {e}")

        profiler = MemoryProfiler()
        model = DPGMMModel()

        # Track memory at start, middle, and end
        start_mem = profiler.get_memory_usage().current_mb
        logger.debug(f"Start memory: {start_mem:.2f} MB")

        # Process first half
        mid_idx = len(ts.observations) // 2
        for i in range(mid_idx):
            model.update(ts.observations[i])

        mid_mem = profiler.get_memory_usage().current_mb
        logger.debug(f"Middle memory: {mid_mem:.2f} MB")

        # Process second half
        for i in range(mid_idx, len(ts.observations)):
            model.update(ts.observations[i])

        end_mem = profiler.get_memory_usage().current_mb
        logger.debug(f"End memory: {end_mem:.2f} MB")

        # Memory growth should be bounded (less than 2x from start)
        growth_factor = end_mem / max(start_mem, 1)
        assert growth_factor < 2.0, (
            f"Memory grew {growth_factor:.2f}x from start to end. "
            f"Streaming architecture may not be properly bounded."
        )

        logger.info(
            f"Boundedness test PASSED: Growth factor {growth_factor:.2f}x"
        )

    def test_memory_profiler_integration(self):
        """Test that MemoryProfiler utilities work correctly with test harness."""
        logger.info("Testing memory profiler integration")

        profiler = MemoryProfiler()
        result = profiler.get_memory_usage()

        # Verify result structure
        assert isinstance(result, MemoryUsageResult), (
            "MemoryProfiler should return MemoryUsageResult"
        )
        assert result.current_mb >= 0, "Current memory should be non-negative"
        assert result.peak_mb >= result.current_mb, (
            "Peak memory should be >= current memory"
        )

        logger.info("Memory profiler integration test PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])