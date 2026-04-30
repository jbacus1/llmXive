"""
Memory profiling utilities for verifying <7GB RAM constraint.

This module provides tools to track and profile memory usage during
DPGMM model training and inference, ensuring compliance with the
7GB RAM constraint specified in the project requirements.

Usage:
    with MemoryProfiler() as profiler:
        # Run memory-intensive operations
        model.fit(data)
      
      memory_report = profiler.get_report()
      assert memory_report.max_memory_gb < 7.0

For edge case handling:
    - Low variance time series (minimal memory overhead)
    - Missing values recovery (streaming, no full data loading)
    - Large datasets (chunked processing)
"""

import tracemalloc
import psutil
import os
import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from contextlib import contextmanager
import logging

# Configure logger for memory profiling
logger = logging.getLogger(__name__)

# Memory constraint constants (from FR-007)
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3
WARNING_THRESHOLD_GB = 6.0  # Warn at 85% of limit
CRITICAL_THRESHOLD_GB = 6.5  # Critical at 93% of limit


@dataclass
class MemorySnapshot:
    """A single memory usage snapshot with timestamp."""
    timestamp: float
    current_bytes: int
    peak_bytes: int
    process_memory_bytes: int
    system_available_gb: float

    @property
    def current_gb(self) -> float:
        return self.current_bytes / (1024**3)

    @property
    def peak_gb(self) -> float:
        return self.peak_bytes / (1024**3)

    @property
    def process_memory_gb(self) -> float:
        return self.process_memory_bytes / (1024**3)


@dataclass
class MemoryReport:
    """Summary report of memory profiling session."""
    snapshots: List[MemorySnapshot] = field(default_factory=list)
    max_memory_bytes: int = 0
    max_memory_gb: float = 0.0
    avg_memory_gb: float = 0.0
    duration_seconds: float = 0.0
    start_timestamp: float = 0.0
    end_timestamp: float = 0.0
    violations: List[str] = field(default_factory=list)

    def validate_constraint(self, limit_gb: float = MEMORY_LIMIT_GB) -> bool:
        """
        Validate that memory usage stayed within constraint.

        Args:
            limit_gb: Memory limit in GB (default 7.0)

        Returns:
            True if within constraint, False otherwise
        """
        self.violations.clear()
        if self.max_memory_gb > limit_gb:
            self.violations.append(
                f"Memory limit exceeded: {self.max_memory_gb:.2f}GB > {limit_gb}GB"
            )
            return False
        return True

    def get_warning_status(self) -> str:
        """
        Get warning status based on memory usage.

        Returns:
            'ok', 'warning', or 'critical'
        """
        if self.max_memory_gb >= CRITICAL_THRESHOLD_GB:
            return "critical"
        elif self.max_memory_gb >= WARNING_THRESHOLD_GB:
            return "warning"
        return "ok"


class MemoryProfiler:
    """
    Context manager and utility class for memory profiling.

    Tracks memory usage using tracemalloc (Python allocations) and
    psutil (process memory) to provide comprehensive memory monitoring.

    Example:
        profiler = MemoryProfiler()
        profiler.start()

        # Run operations to profile
        model.fit(data)

        profiler.stop()
        report = profiler.get_report()

        if not report.validate_constraint():
            raise MemoryError(f"Memory constraint violated: {report.violations}")
    """

    def __init__(self, sample_interval_seconds: float = 0.1):
        """
        Initialize memory profiler.

        Args:
            sample_interval_seconds: Interval for sampling memory (default 0.1s)
        """
        self.sample_interval = sample_interval_seconds
        self._snapshots: List[MemorySnapshot] = []
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._tracemalloc_started = False
        self._sampling_thread: Optional[Any] = None
        self._stop_sampling = False

    def _get_process_memory(self) -> int:
        """Get current process memory usage in bytes."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss

    def _get_system_available_gb(self) -> float:
        """Get available system memory in GB."""
        mem = psutil.virtual_memory()
        return mem.available / (1024**3)

    def _take_snapshot(self) -> MemorySnapshot:
        """Take a single memory snapshot."""
        tracemalloc.take_snapshot()
        current, peak = tracemalloc.get_traced_memory()
        process_mem = self._get_process_memory()
        system_avail = self._get_system_available_gb()

        return MemorySnapshot(
            timestamp=time.time(),
            current_bytes=current,
            peak_bytes=peak,
            process_memory_bytes=process_mem,
            system_available_gb=system_avail
        )

    def _sampling_loop(self):
        """Background thread for continuous sampling."""
        while not self._stop_sampling:
            try:
                snapshot = self._take_snapshot()
                self._snapshots.append(snapshot)
                time.sleep(self.sample_interval)
            except Exception as e:
                logger.warning(f"Memory sampling error: {e}")
                time.sleep(self.sample_interval)

    def start(self, continuous: bool = False):
        """
        Start memory profiling.

        Args:
            continuous: If True, sample continuously in background thread
        """
        if self._start_time is not None:
            logger.warning("MemoryProfiler already started, stopping previous session")
            self.stop()

        tracemalloc.start()
        self._tracemalloc_started = True
        self._start_time = time.time()
        self._snapshots.clear()

        # Take initial snapshot
        self._snapshots.append(self._take_snapshot())

        if continuous:
            self._stop_sampling = False
            import threading
            self._sampling_thread = threading.Thread(
                target=self._sampling_loop,
                daemon=True
            )
            self._sampling_thread.start()
            logger.info("Memory profiling started (continuous mode)")
        else:
            logger.info("Memory profiling started")

    def stop(self) -> MemoryReport:
        """
        Stop memory profiling and return report.

        Returns:
            MemoryReport with profiling summary
        """
        self._end_time = time.time()

        if self._tracemalloc_started:
            tracemalloc.stop()
            self._tracemalloc_started = False

        if self._sampling_thread:
            self._stop_sampling = True
            self._sampling_thread.join(timeout=1.0)
            self._sampling_thread = None

        return self.get_report()

    def get_snapshot(self) -> MemorySnapshot:
        """
        Get current memory snapshot.

        Returns:
            Current MemorySnapshot
        """
        return self._take_snapshot()

    def get_report(self) -> MemoryReport:
        """
        Generate memory profiling report.

        Returns:
            MemoryReport with summary statistics
        """
        if not self._snapshots:
            return MemoryReport()

        # Calculate statistics
        max_bytes = max(s.peak_bytes for s in self._snapshots)
        max_gb = max_bytes / (1024**3)
        avg_gb = sum(s.current_bytes for s in self._snapshots) / len(self._snapshots) / (1024**3)

        duration = (self._end_time or time.time()) - (self._start_time or time.time())

        report = MemoryReport(
            snapshots=self._snapshots,
            max_memory_bytes=max_bytes,
            max_memory_gb=max_gb,
            avg_memory_gb=avg_gb,
            duration_seconds=duration,
            start_timestamp=self._start_time or 0,
            end_timestamp=self._end_time or time.time()
        )

        # Log summary
        status = report.get_warning_status()
        logger.info(
            f"Memory profile complete: max={max_gb:.2f}GB, "
            f"avg={avg_gb:.2f}GB, duration={duration:.1f}s, status={status}"
        )

        if status == "critical":
            logger.critical(f"Memory usage critical: {max_gb:.2f}GB")
        elif status == "warning":
            logger.warning(f"Memory usage warning: {max_gb:.2f}GB")

        return report

    def check_constraint(self, limit_gb: float = MEMORY_LIMIT_GB) -> bool:
        """
        Check if current memory usage is within constraint.

        Args:
            limit_gb: Memory limit in GB

        Returns:
            True if within constraint
        """
        snapshot = self.get_snapshot()
        within = snapshot.process_memory_gb < limit_gb

        if not within:
            logger.error(
                f"Memory constraint violated: "
                f"{snapshot.process_memory_gb:.2f}GB > {limit_gb}GB"
            )

        return within


@contextmanager
def profile_memory(
    name: str = "operation",
    limit_gb: float = MEMORY_LIMIT_GB,
    log_level: int = logging.INFO
):
    """
    Context manager for profiling memory of a code block.

    Args:
        name: Name for the profiled operation
        limit_gb: Memory limit in GB
        log_level: Logging level for output

    Yields:
        MemoryProfiler instance

    Raises:
        MemoryError: If memory limit exceeded

    Example:
        with profile_memory("model_training", limit_gb=7.0) as profiler:
            model.fit(data)

        if not profiler.get_report().validate_constraint():
            raise MemoryError("Memory constraint violated")
    """
    profiler = MemoryProfiler()
    profiler.start()

    try:
        yield profiler
    finally:
        report = profiler.stop()
        logger.log(
            log_level,
            f"Memory profile '{name}': max={report.max_memory_gb:.2f}GB, "
            f"duration={report.duration_seconds:.1f}s"
        )

        if not report.validate_constraint(limit_gb):
            raise MemoryError(
                f"Memory constraint violated for '{name}': "
                f"{report.max_memory_gb:.2f}GB > {limit_gb}GB"
            )


def get_current_memory_gb() -> float:
    """
    Get current process memory usage in GB.

    Returns:
        Current memory usage in GB
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024**3)


def get_available_memory_gb() -> float:
    """
    Get available system memory in GB.

    Returns:
        Available memory in GB
    """
    mem = psutil.virtual_memory()
    return mem.available / (1024**3)


def check_memory_constraint(
    limit_gb: float = MEMORY_LIMIT_GB,
    raise_on_violation: bool = False
) -> bool:
    """
    Check if current memory usage is within constraint.

    Args:
        limit_gb: Memory limit in GB
        raise_on_violation: If True, raise MemoryError on violation

    Returns:
        True if within constraint

    Raises:
        MemoryError: If raise_on_violation=True and constraint violated
    """
    current_gb = get_current_memory_gb()
    within = current_gb < limit_gb

    if not within:
        logger.error(
            f"Memory constraint check failed: "
            f"{current_gb:.2f}GB > {limit_gb}GB"
        )
        if raise_on_violation:
            raise MemoryError(
                f"Memory constraint violated: "
                f"{current_gb:.2f}GB > {limit_gb}GB"
            )

    return within


def estimate_memory_for_dataset(
    n_samples: int,
    n_features: int,
    dtype_bytes: int = 8,
    safety_factor: float = 2.0
) -> float:
    """
    Estimate memory usage for dataset in GB.

    Args:
        n_samples: Number of samples
        n_features: Number of features
        dtype_bytes: Bytes per element (8 for float64)
        safety_factor: Safety multiplier for overhead

    Returns:
        Estimated memory in GB
    """
    raw_bytes = n_samples * n_features * dtype_bytes
    estimated_bytes = raw_bytes * safety_factor
    return estimated_bytes / (1024**3)


# Unit test helper functions
def run_memory_test(
    test_function,
    max_memory_gb: float = MEMORY_LIMIT_GB,
    n_iterations: int = 3
) -> Dict[str, Any]:
    """
    Run a function multiple times and profile memory.

    Args:
        test_function: Function to profile
        max_memory_gb: Maximum allowed memory
        n_iterations: Number of iterations

    Returns:
        Dict with test results and memory statistics
    """
    results = []

    for i in range(n_iterations):
        profiler = MemoryProfiler()
        profiler.start()

        try:
            test_function()
            report = profiler.stop()
            results.append({
                "iteration": i + 1,
                "max_memory_gb": report.max_memory_gb,
                "within_constraint": report.validate_constraint(max_memory_gb)
            })
        finally:
            profiler.stop()

    avg_max = sum(r["max_memory_gb"] for r in results) / len(results)
    all_within = all(r["within_constraint"] for r in results)

    return {
        "iterations": n_iterations,
        "max_memory_gb": max(r["max_memory_gb"] for r in results),
        "avg_memory_gb": avg_max,
        "all_within_constraint": all_within,
        "results": results
    }