"""
Runtime monitoring utilities for enforcing SC-003 (30-minute per-dataset limit).

This module provides tools to track and enforce execution time budgets
for dataset processing operations, ensuring compliance with SC-003:
runtime < 30 minutes per dataset.

Usage:
    monitor = RuntimeMonitor(timeout_seconds=1800)
    with monitor.monitor("dataset_processing"):
        # Your code here
        ...

Or use the decorator:
    @monitor_runtime(timeout_seconds=1800)
    def process_dataset(...):
        ...
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Optional, Callable, Any, Dict, Generator
from datetime import datetime
from pathlib import Path
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class RuntimeSnapshot:
    """Snapshot of runtime monitoring state."""
    start_time: float
    elapsed_seconds: float = 0.0
    timeout_seconds: float = 1800.0  # 30 minutes default
    status: str = "running"
    warning_threshold: float = 0.8  # Warn at 80% of timeout

@dataclass
class RuntimeResult:
    """Result of a monitored operation."""
    success: bool
    elapsed_seconds: float
    timeout_seconds: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)

class RuntimeMonitor:
    """
    Monitors execution time to enforce SC-003: <30 minutes per dataset.
    
    Provides context manager support for automatic start/stop tracking
    and optional timeout enforcement.
    
    Attributes:
        timeout_seconds: Maximum allowed runtime (default 1800 = 30 minutes)
        warning_threshold: Threshold to trigger warnings (default 0.8 = 80%)
        operation_name: Name of the monitored operation for logging
    """
    
    def __init__(self, timeout_seconds: float = 1800.0, warning_threshold: float = 0.8):
        """
        Initialize runtime monitor.
        
        Args:
            timeout_seconds: Maximum allowed runtime (default 1800 = 30 minutes)
            warning_threshold: Threshold to trigger warnings (default 0.8 = 80%)
        """
        self.timeout_seconds = timeout_seconds
        self.warning_threshold = warning_threshold
        self._start_time: Optional[float] = None
        self._snapshot: Optional[RuntimeSnapshot] = None
        self._operation_name: str = "unknown"
        
    def start(self, operation_name: str = "operation") -> RuntimeSnapshot:
        """
        Start monitoring an operation.
        
        Args:
            operation_name: Name of the operation for logging purposes
        
        Returns:
            RuntimeSnapshot with initial state
        """
        self._start_time = time.time()
        self._operation_name = operation_name
        self._snapshot = RuntimeSnapshot(
            start_time=self._start_time,
            timeout_seconds=self.timeout_seconds,
            status="running"
        )
        logger.info(f"Started monitoring: {operation_name}")
        return self._snapshot
    
    def check(self) -> RuntimeResult:
        """
        Check current runtime status.
        
        Returns:
            RuntimeResult with current status and elapsed time
        
        Raises:
            RuntimeError: If monitor was not started
        """
        if self._start_time is None:
            raise RuntimeError("Monitor not started. Call start() first.")
        
        elapsed = time.time() - self._start_time
        threshold = self.timeout_seconds * self.warning_threshold
        
        if elapsed >= self.timeout_seconds:
            self._snapshot.status = "timeout"
            return RuntimeResult(
                success=False,
                elapsed_seconds=elapsed,
                timeout_seconds=self.timeout_seconds,
                message=f"Runtime exceeded timeout: {elapsed:.2f}s > {self.timeout_seconds}s"
            )
        elif elapsed >= threshold:
            self._snapshot.status = "warning"
            logger.warning(f"Runtime approaching timeout: {elapsed:.2f}s / {self.timeout_seconds}s ({elapsed/threshold*100:.1f}%)")
            return RuntimeResult(
                success=True,
                elapsed_seconds=elapsed,
                timeout_seconds=self.timeout_seconds,
                message=f"Warning: Runtime approaching timeout: {elapsed:.2f}s / {self.timeout_seconds}s"
            )
        else:
            self._snapshot.status = "running"
            return RuntimeResult(
                success=True,
                elapsed_seconds=elapsed,
                timeout_seconds=self.timeout_seconds,
                message=f"Runtime OK: {elapsed:.2f}s / {self.timeout_seconds}s"
            )
    
    def stop(self) -> RuntimeResult:
        """
        Stop monitoring and return final result.
        
        Returns:
            RuntimeResult with final status and elapsed time
        
        Raises:
            RuntimeError: If monitor was not started
        """
        if self._start_time is None:
            raise RuntimeError("Monitor not started. Call start() first.")
        
        elapsed = time.time() - self._start_time
        self._snapshot.status = "completed" if elapsed < self.timeout_seconds else "timeout"
        
        result = RuntimeResult(
            success=elapsed < self.timeout_seconds,
            elapsed_seconds=elapsed,
            timeout_seconds=self.timeout_seconds,
            message=f"Completed in {elapsed:.2f}s" if elapsed < self.timeout_seconds else f"Timed out after {elapsed:.2f}s"
        )
        
        if result.success:
            logger.info(f"Finished monitoring {self._operation_name}: {elapsed:.2f}s")
        else:
            logger.error(f"Timeout for {self._operation_name}: {elapsed:.2f}s")
        
        return result
    
    def monitor(self, operation_name: str = "operation") -> Generator[RuntimeMonitor, None, None]:
        """
        Context manager for automatic start/stop monitoring.
        
        Usage:
            with RuntimeMonitor().monitor("dataset_processing"):
                # Your code here
                ...
        
        Args:
            operation_name: Name of the operation for logging
        
        Yields:
            RuntimeMonitor instance
        """
        self.start(operation_name)
        try:
            yield self
        finally:
            self.stop()
    
    def __enter__(self) -> "RuntimeMonitor":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._start_time is not None:
            result = self.stop()
            if not result.success:
                logger.error(result.message)
        return False  # Don't suppress exceptions

@dataclass
class RuntimeBudget:
    """
    Configuration for runtime budget across multiple operations.
    
    Attributes:
        total_budget_seconds: Total budget for all operations (default 1800)
        per_operation_budget_seconds: Budget per individual operation (default 600)
        warning_threshold: Threshold to trigger warnings (default 0.8)
        retry_on_timeout: Whether to retry on timeout (default False)
        max_retries: Maximum retry attempts (default 3)
    """
    total_budget_seconds: float = 1800.0  # 30 minutes
    per_operation_budget_seconds: float = 600.0  # 10 minutes per operation
    warning_threshold: float = 0.8
    retry_on_timeout: bool = False
    max_retries: int = 3

class MultiOperationMonitor:
    """
    Monitor for multiple sequential operations with budget tracking.
    
    Tracks cumulative runtime across multiple operations and enforces
    both per-operation and total budget constraints.
    """
    
    def __init__(self, budget: Optional[RuntimeBudget] = None):
        """
        Initialize multi-operation monitor.
        
        Args:
            budget: RuntimeBudget configuration (default: 30 min total, 10 min per op)
        """
        self.budget = budget or RuntimeBudget()
        self._start_time: Optional[float] = None
        self._current_monitor: Optional[RuntimeMonitor] = None
        self._operation_count: int = 0
        self._cumulative_time: float = 0.0
        self._operation_times: Dict[str, float] = {}
        
    def start(self) -> None:
        """Start overall monitoring."""
        self._start_time = time.time()
        logger.info(f"Started multi-operation monitoring with budget: {self.budget.total_budget_seconds}s total")
    
    def stop(self) -> RuntimeResult:
        """Stop monitoring and return final result."""
        if self._start_time is None:
            raise RuntimeError("Monitor not started. Call start() first.")
        
        total_elapsed = time.time() - self._start_time
        success = total_elapsed < self.budget.total_budget_seconds
        
        return RuntimeResult(
            success=success,
            elapsed_seconds=total_elapsed,
            timeout_seconds=self.budget.total_budget_seconds,
            message=f"Completed {self._operation_count} operations in {total_elapsed:.2f}s"
        )
    
    def begin_operation(self, name: str) -> RuntimeMonitor:
        """
        Begin tracking a specific operation.
        
        Args:
            name: Operation name for logging
        
        Returns:
            RuntimeMonitor for the operation
        """
        self._operation_count += 1
        self._current_monitor = RuntimeMonitor(
            timeout_seconds=self.budget.per_operation_budget_seconds,
            warning_threshold=self.budget.warning_threshold
        )
        self._current_monitor.start(f"op_{self._operation_count}_{name}")
        return self._current_monitor
    
    def end_operation(self) -> None:
        """End tracking the current operation."""
        if self._current_monitor is not None:
            result = self._current_monitor.stop()
            self._operation_times[f"op_{self._operation_count}"] = result.elapsed_seconds
            self._cumulative_time += result.elapsed_seconds
            self._current_monitor = None
    
    def check_budget(self) -> Dict[str, Any]:
        """
        Check current budget status.
        
        Returns:
            Dict with budget status information
        """
        if self._start_time is None:
            return {"status": "not_started"}
        
        total_elapsed = time.time() - self._start_time
        return {
            "status": "running" if total_elapsed < self.budget.total_budget_seconds else "over_budget",
            "total_elapsed": total_elapsed,
            "total_budget": self.budget.total_budget_seconds,
            "per_operation_budget": self.budget.per_operation_budget_seconds,
            "operations_completed": self._operation_count,
            "cumulative_time": self._cumulative_time,
            "remaining": max(0, self.budget.total_budget_seconds - total_elapsed)
        }

def monitor_runtime(timeout_seconds: float = 1800.0):
    """
    Decorator to monitor function execution time.
    
    Args:
        timeout_seconds: Maximum allowed runtime for the decorated function
    
    Returns:
        Decorator function
    
    Example:
        @monitor_runtime(timeout_seconds=1800)
        def process_dataset(dataset_path):
            # Your code here
            ...
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            monitor = RuntimeMonitor(timeout_seconds=timeout_seconds)
            monitor.start(f"function: {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                final_result = monitor.stop()
                if not final_result.success:
                    raise TimeoutError(final_result.message)
                return result
            except Exception as e:
                monitor.stop()
                raise
        return wrapper
    return decorator

def main():
    """Test the runtime monitor."""
    print("=" * 60)
    print("Testing RuntimeMonitor...")
    print("=" * 60)
    
    # Test 1: Normal operation
    print("\n[Test 1] Normal operation (2s within 5s timeout):")
    monitor = RuntimeMonitor(timeout_seconds=5)
    monitor.start("test_operation")
    time.sleep(2)
    result = monitor.check()
    print(f"  Check result: {result.message}")
    
    # Test 2: Context manager
    print("\n[Test 2] Context manager (1s within 10s timeout):")
    with RuntimeMonitor(timeout_seconds=10) as m:
        m.start("context_test")
        time.sleep(1)
        result = m.stop()
        print(f"  Context result: {result.message}")
    
    # Test 3: Multi-operation monitor
    print("\n[Test 3] Multi-operation monitor (3 operations):")
    multi = MultiOperationMonitor(RuntimeBudget(
        total_budget_seconds=30,
        per_operation_budget_seconds=10
    ))
    multi.start()
    for i in range(3):
        monitor = multi.begin_operation(f"op_{i}")
        time.sleep(0.5)
        multi.end_operation()
    result = multi.stop()
    print(f"  Multi-op result: {result.message}")
    
    # Test 4: Budget check
    print("\n[Test 4] Budget check status:")
    status = multi.check_budget()
    print(f"  Status: {status['status']}")
    print(f"  Operations: {status['operations_completed']}")
    print(f"  Remaining: {status['remaining']:.2f}s")
    
    print("\n" + "=" * 60)
    print("RuntimeMonitor tests completed successfully.")
    print("=" * 60)

if __name__ == "__main__":
    main()