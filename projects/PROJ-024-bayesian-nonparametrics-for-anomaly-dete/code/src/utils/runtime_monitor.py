"""
Runtime monitoring utility for verifying SC-003 requirement:
Model processing must complete within 30 minutes per dataset.

Provides timing instrumentation, warnings, and failure reporting
for long-running evaluation tasks.
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable, List
import json

# Constants for SC-003 compliance
MAX_RUNTIME_SECONDS = 30 * 60  # 30 minutes
WARNING_THRESHOLD_SECONDS = 25 * 60  # Warn at 25 minutes
CRITICAL_THRESHOLD_SECONDS = 28 * 60  # Critical at 28 minutes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class RuntimeReport:
    """Runtime monitoring report for a dataset processing task."""
    dataset_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    elapsed_seconds: float = 0.0
    status: str = "running"  # running, completed, timeout, warning
    message: str = ""
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'dataset_name': self.dataset_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'elapsed_seconds': self.elapsed_seconds,
            'status': self.status,
            'message': self.message,
            'warnings': self.warnings,
            'max_allowed_seconds': MAX_RUNTIME_SECONDS
        }
    
    def save_report(self, output_path: Path) -> None:
        """Save runtime report to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Runtime report saved to {output_path}")


class RuntimeMonitor:
    """
    Monitor execution time for dataset processing tasks.
    
    Ensures compliance with SC-003: runtime < 30 minutes per dataset.
    """
    
    def __init__(
        self,
        dataset_name: str,
        max_runtime_seconds: int = MAX_RUNTIME_SECONDS,
        warning_threshold_seconds: int = WARNING_THRESHOLD_SECONDS,
        critical_threshold_seconds: int = CRITICAL_THRESHOLD_SECONDS,
        output_dir: Optional[Path] = None
    ):
        self.dataset_name = dataset_name
        self.max_runtime_seconds = max_runtime_seconds
        self.warning_threshold_seconds = warning_threshold_seconds
        self.critical_threshold_seconds = critical_threshold_seconds
        self.output_dir = output_dir or Path('code/logs/runtime')
        
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.elapsed_seconds: float = 0.0
        self.report: Optional[RuntimeReport] = None
        self.warnings: List[str] = []
        self._timer_thread: Optional[Any] = None
        self._stop_timer: bool = False
        
    def start(self) -> None:
        """Start the runtime monitor."""
        self.start_time = datetime.now()
        self.end_time = None
        self.elapsed_seconds = 0.0
        self.warnings = []
        self.report = RuntimeReport(
            dataset_name=self.dataset_name,
            start_time=self.start_time
        )
        logger.info(f"Runtime monitor started for {self.dataset_name}")
        logger.info(f"Max allowed runtime: {self.max_runtime_seconds} seconds ({self.max_runtime_seconds/60:.1f} minutes)")
        
    def stop(self, success: bool = True) -> RuntimeReport:
        """Stop the runtime monitor and generate report."""
        self.end_time = datetime.now()
        self.elapsed_seconds = (self.end_time - self.start_time).total_seconds()
        
        if self.elapsed_seconds >= self.max_runtime_seconds:
            self.report.status = "timeout"
            self.report.message = f"Runtime exceeded maximum allowed ({self.elapsed_seconds:.1f}s >= {self.max_runtime_seconds}s)"
            logger.error(self.report.message)
        elif self.elapsed_seconds >= self.critical_threshold_seconds:
            self.report.status = "warning"
            self.report.message = f"Runtime approaching limit ({self.elapsed_seconds:.1f}s >= {self.critical_threshold_seconds}s)"
            logger.warning(self.report.message)
        elif self.elapsed_seconds >= self.warning_threshold_seconds:
            self.report.status = "warning"
            self.report.message = f"Runtime exceeded warning threshold ({self.elapsed_seconds:.1f}s >= {self.warning_threshold_seconds}s)"
            logger.warning(self.report.message)
        else:
            self.report.status = "completed"
            self.report.message = f"Runtime within limits ({self.elapsed_seconds:.1f}s < {self.warning_threshold_seconds}s)"
            logger.info(self.report.message)
        
        self.report.elapsed_seconds = self.elapsed_seconds
        self.report.warnings = self.warnings
        
        # Save report if output directory is configured
        if self.output_dir:
            report_path = self.output_dir / f"runtime_{self.dataset_name.replace(' ', '_')}.json"
            self.report.save_report(report_path)
        
        return self.report
    
    def check_elapsed(self) -> Dict[str, Any]:
        """Check current elapsed time and return status."""
        if not self.start_time:
            return {'status': 'not_started', 'elapsed_seconds': 0}
        
        current_elapsed = (datetime.now() - self.start_time).total_seconds()
        
        if current_elapsed >= self.max_runtime_seconds:
            return {
                'status': 'timeout',
                'elapsed_seconds': current_elapsed,
                'remaining_seconds': 0,
                'message': f"Runtime exceeded maximum ({current_elapsed:.1f}s >= {self.max_runtime_seconds}s)"
            }
        elif current_elapsed >= self.critical_threshold_seconds:
            return {
                'status': 'critical',
                'elapsed_seconds': current_elapsed,
                'remaining_seconds': self.max_runtime_seconds - current_elapsed,
                'message': f"Runtime at critical level ({current_elapsed:.1f}s >= {self.critical_threshold_seconds}s)"
            }
        elif current_elapsed >= self.warning_threshold_seconds:
            return {
                'status': 'warning',
                'elapsed_seconds': current_elapsed,
                'remaining_seconds': self.max_runtime_seconds - current_elapsed,
                'message': f"Runtime exceeded warning threshold ({current_elapsed:.1f}s >= {self.warning_threshold_seconds}s)"
            }
        else:
            return {
                'status': 'ok',
                'elapsed_seconds': current_elapsed,
                'remaining_seconds': self.max_runtime_seconds - current_elapsed,
                'message': f"Runtime within limits ({current_elapsed:.1f}s < {self.warning_threshold_seconds}s)"
            }
    
    def verify_compliance(self) -> bool:
        """
        Verify that runtime is within SC-003 compliance.
        
        Returns True if runtime < 30 minutes, False otherwise.
        """
        if not self.start_time:
            logger.warning("Runtime monitor not started, cannot verify compliance")
            return False
        
        current_elapsed = (datetime.now() - self.start_time).total_seconds()
        
        if current_elapsed >= self.max_runtime_seconds:
            logger.error(f"SC-003 VIOLATION: Runtime {current_elapsed:.1f}s exceeds maximum {self.max_runtime_seconds}s")
            return False
        
        logger.info(f"SC-003 COMPLIANT: Runtime {current_elapsed:.1f}s within maximum {self.max_runtime_seconds}s")
        return True
    
    def __enter__(self) -> 'RuntimeMonitor':
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop(success=(exc_type is None))
    
    def decorate(
        self,
        func: Callable,
        dataset_name: Optional[str] = None
    ) -> Callable:
        """
        Decorator to wrap a function with runtime monitoring.
        
        Usage:
            monitor = RuntimeMonitor("my_dataset")
            monitored_func = monitor.decorate(my_function)
        """
        def wrapper(*args, **kwargs):
            monitor_name = dataset_name or func.__name__
            self.start()
            try:
                result = func(*args, **kwargs)
                self.stop(success=True)
                return result
            except Exception as e:
                self.stop(success=False)
                logger.error(f"Function {func.__name__} failed: {e}")
                raise
        return wrapper


def verify_runtime_compliance(
    dataset_name: str,
    max_runtime_seconds: int = MAX_RUNTIME_SECONDS
) -> bool:
    """
    Verify runtime compliance for a dataset processing task.
    
    Args:
        dataset_name: Name of the dataset being processed
        max_runtime_seconds: Maximum allowed runtime (default 1800s = 30min)
    
    Returns:
        True if within compliance, False otherwise
    """
    monitor = RuntimeMonitor(
        dataset_name=dataset_name,
        max_runtime_seconds=max_runtime_seconds
    )
    
    with monitor:
        # This is a placeholder - actual work would be passed in
        # For testing, we just sleep briefly
        logger.info(f"Processing {dataset_name}...")
        time.sleep(0.1)  # Placeholder for actual work
        
    return monitor.verify_compliance()


def main() -> None:
    """
    Main entry point for runtime monitoring demonstration.
    
    Runs a test that verifies runtime compliance for synthetic datasets.
    """
    print("=" * 60)
    print("Runtime Monitor - SC-003 Compliance Verification")
    print("=" * 60)
    print(f"Max runtime per dataset: {MAX_RUNTIME_SECONDS} seconds ({MAX_RUNTIME_SECONDS/60:.1f} minutes)")
    print(f"Warning threshold: {WARNING_THRESHOLD_SECONDS} seconds ({WARNING_THRESHOLD_SECONDS/60:.1f} minutes)")
    print(f"Critical threshold: {CRITICAL_THRESHOLD_SECONDS} seconds ({CRITICAL_THRESHOLD_SECONDS/60:.1f} minutes)")
    print()
    
    # Test 1: Normal completion within limits
    print("Test 1: Normal completion (within limits)")
    print("-" * 60)
    monitor1 = RuntimeMonitor(
        dataset_name="test_normal",
        output_dir=Path('code/logs/runtime')
    )
    
    with monitor1:
        # Simulate normal processing (less than 5 minutes)
        time.sleep(2)
    
    report1 = monitor1.stop()
    print(f"Status: {report1.status}")
    print(f"Elapsed: {report1.elapsed_seconds:.2f} seconds")
    print(f"Compliance: {'PASS' if report1.status == 'completed' else 'FAIL'}")
    print()
    
    # Test 2: Check elapsed time method
    print("Test 2: Elapsed time checking")
    print("-" * 60)
    monitor2 = RuntimeMonitor(dataset_name="test_check")
    monitor2.start()
    time.sleep(1)
    
    status = monitor2.check_elapsed()
    print(f"Status: {status['status']}")
    print(f"Elapsed: {status['elapsed_seconds']:.2f} seconds")
    print(f"Remaining: {status['remaining_seconds']:.2f} seconds")
    print()
    
    # Test 3: Verify compliance function
    print("Test 3: Compliance verification function")
    print("-" * 60)
    compliant = verify_runtime_compliance("test_compliance")
    print(f"Compliance check: {'PASS' if compliant else 'FAIL'}")
    print()
    
    # Test 4: Context manager usage
    print("Test 4: Context manager usage")
    print("-" * 60)
    with RuntimeMonitor("test_context", output_dir=Path('code/logs/runtime')) as monitor4:
        time.sleep(1)
    
    print(f"Context manager completed: {monitor4.report.status}")
    print()
    
    print("=" * 60)
    print("Runtime Monitor Tests Complete")
    print("=" * 60)
    print(f"All tests passed: {all([report1.status == 'completed', compliant])}")


if __name__ == '__main__':
    main()
