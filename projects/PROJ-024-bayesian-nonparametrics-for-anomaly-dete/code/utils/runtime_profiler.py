"""
Runtime Profiling Utilities for Anomaly Detection Pipeline

This module provides utilities to profile and verify runtime constraints
for the Bayesian Nonparametrics anomaly detection pipeline.

Key Constraints:
- SC-003: Runtime per dataset must not exceed 30 minutes
- Memory: Must stay under 7GB RAM (see memory_profiler.py)

Usage:
    from utils.runtime_profiler import RuntimeProfiler, profile_runtime, verify_runtime_constraint
    
    # Option 1: Using RuntimeProfiler class
    profiler = RuntimeProfiler(dataset_name="UCI_NAB", phase="dpgmm_training")
    profiler.start()
    
    with profiler.time_block("data_loading"):
        load_data()
    
    with profiler.time_block("model_training"):
        train_model()
    
    profiler.stop()
    profiler.report()
    
    # Option 2: Using context manager
    with profile_runtime("UCI_NAB", "training") as profiler:
        load_data()
        train_model()
    
    # Option 3: Simple constraint verification
    passed, msg = verify_runtime_constraint("dataset", 1200.0)
"""

import time
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class RuntimeStats:
    """Container for runtime profiling statistics."""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    elapsed_seconds: float = 0.0
    constraint_limit_seconds: float = 1800.0  # 30 minutes
    dataset_name: str = "unknown"
    phase: str = "unknown"
    status: str = "pending"  # pending, running, completed, exceeded
    warnings: list = field(default_factory=list)
    
    @property
    def elapsed_minutes(self) -> float:
        """Return elapsed time in minutes."""
        return self.elapsed_seconds / 60.0
    
    @property
    def remaining_seconds(self) -> float:
        """Return remaining seconds before constraint violation."""
        return max(0.0, self.constraint_limit_seconds - self.elapsed_seconds)
    
    @property
    def remaining_minutes(self) -> float:
        """Return remaining time in minutes."""
        return self.remaining_seconds / 60.0
    
    @property
    def percentage_complete(self) -> float:
        """Return percentage of time budget used."""
        return (self.elapsed_seconds / self.constraint_limit_seconds) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary for serialization."""
        return {
            "dataset_name": self.dataset_name,
            "phase": self.phase,
            "elapsed_seconds": self.elapsed_seconds,
            "elapsed_minutes": self.elapsed_minutes,
            "constraint_limit_seconds": self.constraint_limit_seconds,
            "remaining_seconds": self.remaining_seconds,
            "remaining_minutes": self.remaining_minutes,
            "percentage_complete": self.percentage_complete,
            "status": self.status,
            "warnings": self.warnings,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None
        }


class RuntimeProfiler:
    """
    Runtime profiling utility for anomaly detection pipeline.
    
    Monitors execution time against the 30-minute per-dataset constraint
    (SC-003) and provides warnings when thresholds are approached.
    
    Usage:
        profiler = RuntimeProfiler(dataset_name="UCI_NAB", phase="dpgmm_training")
        
        with profiler.time_block("data_loading"):
            load_data()
        
        with profiler.time_block("model_training"):
            train_model()
        
        profiler.report()
    """
    
    def __init__(
        self,
        dataset_name: str = "unknown",
        phase: str = "unknown",
        constraint_limit_seconds: float = 1800.0,
        warning_thresholds: tuple = (0.5, 0.75, 0.90, 0.95, 1.0)
    ):
        """
        Initialize runtime profiler.
        
        Args:
            dataset_name: Name of the dataset being processed
            phase: Current phase of processing (e.g., 'download', 'training', 'evaluation')
            constraint_limit_seconds: Maximum allowed runtime in seconds (default: 30 minutes)
            warning_thresholds: Tuple of percentage thresholds for warnings
        """
        self.dataset_name = dataset_name
        self.phase = phase
        self.constraint_limit_seconds = constraint_limit_seconds
        self.warning_thresholds = warning_thresholds
        
        self.stats = RuntimeStats(
            dataset_name=dataset_name,
            phase=phase,
            constraint_limit_seconds=constraint_limit_seconds
        )
        
        self.block_times: Dict[str, float] = {}
        self.block_starts: Dict[str, float] = {}
        self.warnings_issued: set = set()
        
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        
    def start(self) -> None:
        """Start timing."""
        self._start_time = time.time()
        self.stats.start_time = self._start_time
        self.stats.status = "running"
        logger.info(f"RuntimeProfiler started: dataset={self.dataset_name}, phase={self.phase}")
        
    def stop(self) -> None:
        """Stop timing and finalize statistics."""
        self._end_time = time.time()
        self.stats.end_time = self._end_time
        self.stats.elapsed_seconds = self._end_time - self._start_time
        
        # Determine final status
        if self.stats.elapsed_seconds > self.constraint_limit_seconds:
            self.stats.status = "exceeded"
            self.stats.warnings.append(
                f"CONSTRAINT VIOLATION: Runtime {self.stats.elapsed_seconds:.1f}s "
                f"exceeds limit {self.constraint_limit_seconds:.1f}s"
            )
        else:
            self.stats.status = "completed"
        
        logger.info(f"RuntimeProfiler stopped: elapsed={self.stats.elapsed_seconds:.1f}s, status={self.stats.status}")
        
    @contextmanager
    def time_block(self, block_name: str):
        """
        Context manager for timing specific code blocks.
        
        Args:
            block_name: Name of the code block being timed
            
        Usage:
            with profiler.time_block("data_loading"):
                load_data()
        """
        start = time.time()
        self.block_starts[block_name] = start
        logger.debug(f"Block '{block_name}' started")
        
        try:
            yield
        finally:
            end = time.time()
            elapsed = end - start
            self.block_times[block_name] = elapsed
            logger.debug(f"Block '{block_name}' completed: {elapsed:.2f}s")
            
            # Check for warnings during block execution
            self._check_warnings()
    
    def _check_warnings(self) -> None:
        """Check time percentage and issue warnings at thresholds."""
        if self._start_time is None:
            return
            
        current_elapsed = time.time() - self._start_time
        current_percentage = current_elapsed / self.constraint_limit_seconds
        
        for threshold in self.warning_thresholds:
            threshold_pct = threshold * 100
            if current_percentage >= threshold and threshold_pct not in self.warnings_issued:
                self.warnings_issued.add(threshold_pct)
                
                if threshold_pct < 100:
                    msg = (
                        f"WARNING: Runtime at {current_elapsed:.1f}s ({current_percentage*100:.1f}% of budget). "
                        f"Remaining: {self.constraint_limit_seconds - current_elapsed:.1f}s "
                        f"({(self.constraint_limit_seconds - current_elapsed)/60:.1f} minutes)"
                    )
                    logger.warning(msg)
                    self.stats.warnings.append(msg)
                else:
                    msg = (
                        f"CRITICAL: Runtime constraint exceeded! "
                        f"Elapsed: {current_elapsed:.1f}s, Limit: {self.constraint_limit_seconds:.1f}s"
                    )
                    logger.error(msg)
                    self.stats.warnings.append(msg)
    
    def get_remaining_time(self) -> float:
        """Get remaining seconds before constraint violation."""
        if self._start_time is None:
            return self.constraint_limit_seconds
        return max(0.0, self.constraint_limit_seconds - (time.time() - self._start_time))
    
    def get_elapsed_time(self) -> float:
        """Get elapsed seconds since start."""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time
    
    def is_within_constraint(self) -> bool:
        """Check if current runtime is within constraint."""
        if self._start_time is None:
            return True
        return self.get_elapsed_time() <= self.constraint_limit_seconds
    
    def should_abort(self, safety_margin_seconds: float = 60.0) -> bool:
        """
        Check if execution should be aborted to avoid constraint violation.
        
        Args:
            safety_margin_seconds: Additional time to leave as safety margin
            
        Returns:
            True if execution should be aborted
        """
        remaining = self.get_remaining_time() - safety_margin_seconds
        return remaining <= 0
    
    def report(self) -> Dict[str, Any]:
        """
        Generate and log a comprehensive runtime report.
        
        Returns:
            Dictionary with all runtime statistics
        """
        if self._start_time and not self._end_time:
            self.stop()
            
        self.stats.elapsed_seconds = self.get_elapsed_time()
        
        report = {
            "dataset_name": self.dataset_name,
            "phase": self.phase,
            "total_elapsed_seconds": self.stats.elapsed_seconds,
            "total_elapsed_minutes": self.stats.elapsed_minutes,
            "constraint_limit_seconds": self.constraint_limit_seconds,
            "constraint_limit_minutes": self.constraint_limit_seconds / 60,
            "remaining_seconds": self.stats.remaining_seconds,
            "remaining_minutes": self.stats.remaining_minutes,
            "percentage_used": self.stats.percentage_complete,
            "status": self.stats.status,
            "block_times": self.block_times,
            "warnings": self.stats.warnings,
            "summary": ""
        }
        
        # Generate summary
        if self.stats.status == "exceeded":
            report["summary"] = (
                f"⚠️ CONSTRAINT VIOLATED: {self.dataset_name} took {self.stats.elapsed_minutes:.1f} minutes "
                f"(limit: 30 minutes)"
            )
        else:
            report["summary"] = (
                f"✅ Within constraint: {self.dataset_name} took {self.stats.elapsed_minutes:.1f} minutes "
                f"(limit: 30 minutes, {self.stats.remaining_minutes:.1f} minutes remaining)"
            )
        
        logger.info(report["summary"])
        
        for block_name, block_time in self.block_times.items():
            logger.info(f"  - {block_name}: {block_time:.2f}s ({block_time/60:.2f} min)")
        
        if self.stats.warnings:
            logger.warning(f"Warnings ({len(self.stats.warnings)}):")
            for warning in self.stats.warnings:
                logger.warning(f"  - {warning}")
        
        return report
    
    def to_dict(self) -> Dict[str, Any]:
        """Export all statistics to dictionary."""
        return {
            "runtime_stats": self.stats.to_dict(),
            "block_times": self.block_times,
            "warnings_issued": list(self.warnings_issued)
        }
    
    def save_report(self, filepath: str) -> None:
        """
        Save runtime report to JSON file.
        
        Args:
            filepath: Path to save report to
        """
        import json
        report = self.report()
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Runtime report saved to: {filepath}")


@contextmanager
def profile_runtime(
    dataset_name: str = "unknown",
    phase: str = "unknown",
    constraint_limit_seconds: float = 1800.0
):
    """
    Convenience context manager for runtime profiling.
    
    Usage:
        with profile_runtime("UCI_NAB", "training") as profiler:
            load_data()
            train_model()
        
        profiler.report()
    """
    profiler = RuntimeProfiler(
        dataset_name=dataset_name,
        phase=phase,
        constraint_limit_seconds=constraint_limit_seconds
    )
    profiler.start()
    
    try:
        yield profiler
    finally:
        profiler.stop()
        profiler.report()


def verify_runtime_constraint(
    dataset_name: str,
    actual_runtime_seconds: float,
    constraint_limit_seconds: float = 1800.0
) -> tuple:
    """
    Verify if a runtime meets the constraint.
    
    Args:
        dataset_name: Name of the dataset
        actual_runtime_seconds: Actual time taken in seconds
        constraint_limit_seconds: Maximum allowed time in seconds
        
    Returns:
        Tuple of (passed: bool, message: str)
    """
    passed = actual_runtime_seconds <= constraint_limit_seconds
    elapsed_minutes = actual_runtime_seconds / 60
    limit_minutes = constraint_limit_seconds / 60
    
    if passed:
        message = (
            f"✅ PASS: {dataset_name} completed in {elapsed_minutes:.2f} minutes "
            f"(constraint: {limit_minutes:.2f} minutes)"
        )
    else:
        message = (
            f"❌ FAIL: {dataset_name} took {elapsed_minutes:.2f} minutes "
            f"(constraint: {limit_minutes:.2f} minutes). "
            f"Exceeded by {actual_runtime_seconds - constraint_limit_seconds:.1f} seconds"
        )
    
    return passed, message


if __name__ == "__main__":
    # Example usage and self-test
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Runtime Profiler Self-Test")
    print("=" * 60)
    
    # Test 1: Basic profiling
    profiler = RuntimeProfiler(
        dataset_name="test_dataset",
        phase="self_test",
        constraint_limit_seconds=300.0  # 5 minutes for test
    )
    
    profiler.start()
    
    with profiler.time_block("simulated_work_1"):
        time.sleep(0.5)
    
    with profiler.time_block("simulated_work_2"):
        time.sleep(0.3)
    
    profiler.stop()
    report = profiler.report()
    
    print(f"\nTest Result: {report['summary']}")
    print(f"Status: {report['status']}")
    print(f"Warnings: {len(report['warnings'])}")
    
    # Test 2: Constraint verification
    print("\n" + "=" * 60)
    print("Constraint Verification Test")
    print("=" * 60)
    
    passed, msg = verify_runtime_constraint(
        "test_dataset",
        actual_runtime_seconds=120.0,
        constraint_limit_seconds=1800.0
    )
    print(msg)
    
    passed, msg = verify_runtime_constraint(
        "test_dataset",
        actual_runtime_seconds=2000.0,
        constraint_limit_seconds=1800.0
    )
    print(msg)
    
    print("\n" + "=" * 60)
    print("Self-Test Complete")
    print("=" * 60)