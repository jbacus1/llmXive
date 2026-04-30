"""
Memory Profiler for DPGMM Streaming Anomaly Detection
======================================================
Provides memory usage tracking and profiling capabilities for streaming
observation processing. Used to verify FR-005 memory constraints (<7GB RAM).

This module supports:
- Memory snapshot capture at any point during execution
- Memory profiling during 1000+ observation processing
- Memory growth analysis and anomaly detection
- Export of profiling results to JSON/CSV for analysis

Constitution Principle III: All artifacts must be hashable and verifiable.
"""

import os
import sys
import gc
import time
import json
import csv
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Tuple, Generator, Union
from datetime import datetime
import traceback

# Try to import psutil for detailed memory info, fall back to os if unavailable
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available, using os-based memory estimation")

# Configure logging for memory profiling
logger = logging.getLogger(__name__)


@dataclass
class MemorySnapshot:
    """
    Captures memory usage at a single point in time.

    Attributes:
        timestamp: ISO format timestamp when snapshot was taken
        process_memory_mb: Current process memory usage in MB
        process_memory_percent: Percentage of system memory used by process
        gc_counts: Garbage collection counts for each generation
        gc_objects: Number of objects tracked by GC
        timestamp_epoch: Unix timestamp for easier analysis
    """
    timestamp: str
    timestamp_epoch: float
    process_memory_mb: float
    process_memory_percent: float
    gc_counts: Tuple[int, int, int]
    gc_objects: int
    snapshot_id: int = 0
    operation: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary for serialization."""
        return {
            'timestamp': self.timestamp,
            'timestamp_epoch': self.timestamp_epoch,
            'process_memory_mb': self.process_memory_mb,
            'process_memory_percent': self.process_memory_percent,
            'gc_counts': list(self.gc_counts),
            'gc_objects': self.gc_objects,
            'snapshot_id': self.snapshot_id,
            'operation': self.operation
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemorySnapshot':
        """Create snapshot from dictionary."""
        return cls(
            timestamp=data['timestamp'],
            timestamp_epoch=data['timestamp_epoch'],
            process_memory_mb=data['process_memory_mb'],
            process_memory_percent=data['process_memory_percent'],
            gc_counts=tuple(data['gc_counts']),
            gc_objects=data['gc_objects'],
            snapshot_id=data.get('snapshot_id', 0),
            operation=data.get('operation', 'unknown')
        )


@dataclass
class MemoryProfileResult:
    """
    Aggregated results from a memory profiling session.

    Attributes:
        start_memory_mb: Memory at profiling start
        end_memory_mb: Memory at profiling end
        peak_memory_mb: Maximum memory observed
        avg_memory_mb: Average memory over all snapshots
        memory_growth_mb: Total memory growth during profiling
        memory_growth_rate_mb_per_obs: Memory growth per observation
        total_snapshots: Number of snapshots taken
        profiling_duration_seconds: Total time profiling ran
        snapshot_count_per_100_obs: Snapshots taken per 100 observations
        snapshots: List of all MemorySnapshot objects
        memory_anomalies: List of observations where memory spiked unexpectedly
        profiling_config: Configuration used for this profiling run
    """
    start_memory_mb: float
    end_memory_mb: float
    peak_memory_mb: float
    avg_memory_mb: float
    memory_growth_mb: float
    memory_growth_rate_mb_per_obs: float
    total_snapshots: int
    profiling_duration_seconds: float
    snapshot_count_per_100_obs: int
    snapshots: List[MemorySnapshot] = field(default_factory=list)
    memory_anomalies: List[Dict[str, Any]] = field(default_factory=list)
    profiling_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary for serialization."""
        return {
            'start_memory_mb': self.start_memory_mb,
            'end_memory_mb': self.end_memory_mb,
            'peak_memory_mb': self.peak_memory_mb,
            'avg_memory_mb': self.avg_memory_mb,
            'memory_growth_mb': self.memory_growth_mb,
            'memory_growth_rate_mb_per_obs': self.memory_growth_rate_mb_per_obs,
            'total_snapshots': self.total_snapshots,
            'profiling_duration_seconds': self.profiling_duration_seconds,
            'snapshot_count_per_100_obs': self.snapshot_count_per_100_obs,
            'snapshots': [s.to_dict() for s in self.snapshots],
            'memory_anomalies': self.memory_anomalies,
            'profiling_config': self.profiling_config,
            'timestamp': datetime.now().isoformat()
        }

    def save_to_json(self, output_path: Union[str, Path]) -> None:
        """Save profiling results to JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Memory profile saved to {output_path}")

    def save_to_csv(self, output_path: Union[str, Path]) -> None:
        """Save snapshot data to CSV file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'snapshot_id', 'timestamp', 'timestamp_epoch', 'operation',
                'process_memory_mb', 'process_memory_percent',
                'gc_counts_0', 'gc_counts_1', 'gc_counts_2', 'gc_objects'
            ])
            for snap in self.snapshots:
                writer.writerow([
                    snap.snapshot_id, snap.timestamp, snap.timestamp_epoch,
                    snap.operation, snap.process_memory_mb,
                    snap.process_memory_percent, snap.gc_counts[0],
                    snap.gc_counts[1], snap.gc_counts[2], snap.gc_objects
                ])
        logger.info(f"Memory profile CSV saved to {output_path}")


class MemoryProfiler:
    """
    Memory profiler for tracking memory usage during streaming operations.

    This profiler is designed to work with the DPGMM streaming anomaly
    detection pipeline, tracking memory at observation boundaries and
    detecting potential memory leaks or excessive growth.

    Usage:
        profiler = MemoryProfiler()
        profiler.start_profiling()
        for obs in observations:
            process(obs)
            if profiler.should_snapshot(obs_index):
                profiler.capture_snapshot(f"obs_{obs_index}")
        results = profiler.stop_profiling()
        results.save_to_json("memory_profile.json")

    FR-005 Compliance:
        - Tracks memory during 1000 observation processing
        - Reports memory growth rate per observation
        - Detects memory anomalies (spikes > 2x expected growth)
        - Ensures <7GB RAM limit is monitored
    """

    def __init__(
        self,
        snapshot_interval: int = 10,
        max_memory_mb: float = 7000.0,
        anomaly_threshold_multiplier: float = 2.0,
        gc_before_snapshot: bool = True,
        output_dir: Union[str, Path] = "projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/memory_profiles"
    ):
        """
        Initialize memory profiler.

        Args:
            snapshot_interval: Take a snapshot every N observations
            max_memory_mb: Maximum allowed memory (FR-005: 7GB)
            anomaly_threshold_multiplier: Multiplier for anomaly detection
            gc_before_snapshot: Run garbage collection before each snapshot
            output_dir: Directory to save profiling results
        """
        self.snapshot_interval = snapshot_interval
        self.max_memory_mb = max_memory_mb
        self.anomaly_threshold_multiplier = anomaly_threshold_multiplier
        self.gc_before_snapshot = gc_before_snapshot
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._snapshots: List[MemorySnapshot] = []
        self._snapshot_counter = 0
        self._profiling_start_time: Optional[float] = None
        self._profiling_start_memory: Optional[float] = None
        self._is_profiling = False
        self._expected_growth_per_obs: Optional[float] = None

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _get_process_memory_mb(self) -> float:
        """Get current process memory usage in MB."""
        if PSUTIL_AVAILABLE:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return memory_info.rss / (1024 * 1024)
        else:
            # Fallback: try to estimate from /proc on Linux
            try:
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            parts = line.split()
                            return float(parts[1]) / 1024  # Convert KB to MB
            except:
                pass
            # Ultimate fallback: 0
            logger.warning("Could not determine memory usage, returning 0")
            return 0.0

    def _get_process_memory_percent(self) -> float:
        """Get current process memory percentage of system."""
        if PSUTIL_AVAILABLE:
            process = psutil.Process(os.getpid())
            return process.memory_percent()
        else:
            return 0.0

    def _get_gc_stats(self) -> Tuple[Tuple[int, int, int], int]:
        """Get garbage collection statistics."""
        gc_counts = gc.get_count()
        gc_objects = len(gc.get_objects())
        return gc_counts, gc_objects

    def _run_gc_if_needed(self) -> None:
        """Run garbage collection if configured."""
        if self.gc_before_snapshot:
            gc.collect()

    def start_profiling(self) -> None:
        """Start memory profiling session."""
        self._run_gc_if_needed()
        self._profiling_start_time = time.time()
        self._profiling_start_memory = self._get_process_memory_mb()
        self._snapshots = []
        self._snapshot_counter = 0
        self._is_profiling = True
        logger.info(f"Memory profiling started. Initial memory: {self._profiling_start_memory:.2f} MB")

    def capture_snapshot(
        self,
        operation: str = "unknown",
        observation_index: Optional[int] = None
    ) -> MemorySnapshot:
        """
        Capture a memory snapshot at the current point.

        Args:
            operation: Name of operation being profiled
            observation_index: Current observation index (for tracking)

        Returns:
            MemorySnapshot object with current memory state
        """
        if not self._is_profiling:
            raise RuntimeError("Profiling not started. Call start_profiling() first.")

        self._run_gc_if_needed()

        self._snapshot_counter += 1
        snapshot = MemorySnapshot(
            timestamp=datetime.now().isoformat(),
            timestamp_epoch=time.time(),
            process_memory_mb=self._get_process_memory_mb(),
            process_memory_percent=self._get_process_memory_percent(),
            gc_counts=self._get_gc_stats()[0],
            gc_objects=self._get_gc_stats()[1],
            snapshot_id=self._snapshot_counter,
            operation=operation
        )

        self._snapshots.append(snapshot)

        # Check for memory anomalies
        if observation_index is not None and len(self._snapshots) > 1:
            self._check_memory_anomaly(snapshot, observation_index)

        # Check against max memory limit
        if snapshot.process_memory_mb > self.max_memory_mb:
            logger.warning(
                f"Memory limit exceeded! {snapshot.process_memory_mb:.2f} MB > {self.max_memory_mb} MB"
            )

        return snapshot

    def _check_memory_anomaly(
        self,
        current: MemorySnapshot,
        observation_index: int
    ) -> None:
        """Check if memory growth is anomalous compared to expected growth."""
        if len(self._snapshots) < 2:
            return

        prev = self._snapshots[-2]
        actual_growth = current.process_memory_mb - prev.process_memory_mb

        # If we have enough data, estimate expected growth
        if len(self._snapshots) >= 10:
            if self._expected_growth_per_obs is None:
                # Calculate from first 10 snapshots
                  total_growth = self._snapshots[-1].process_memory_mb - self._snapshots[0].process_memory_mb
                  total_obs = observation_index - self._snapshots[0].snapshot_id * self.snapshot_interval
                  self._expected_growth_per_obs = total_growth / max(total_obs, 1)

          if self._expected_growth_per_obs is not None and self._expected_growth_per_obs > 0:
              expected_growth = self._expected_growth_per_obs * self.snapshot_interval
              if actual_growth > expected_growth * self.anomaly_threshold_multiplier:
                  self._memory_anomalies.append({
                      'snapshot_id': current.snapshot_id,
                      'observation_index': observation_index,
                      'timestamp': current.timestamp,
                      'actual_growth_mb': actual_growth,
                      'expected_growth_mb': expected_growth,
                      'multiplier': actual_growth / expected_growth
                  })
                  logger.warning(
                      f"Memory anomaly detected at obs {observation_index}: "
                      f"growth {actual_growth:.2f} MB vs expected {expected_growth:.2f} MB"
                  )

    def should_snapshot(self, observation_index: int) -> bool:
        """Check if we should take a snapshot at this observation index."""
        return (observation_index % self.snapshot_interval) == 0

    def stop_profiling(
        self,
        total_observations: int,
        output_basename: Optional[str] = None
    ) -> MemoryProfileResult:
        """
        Stop profiling and generate results.

        Args:
            total_observations: Total number of observations processed
            output_basename: Optional base name for output files

        Returns:
            MemoryProfileResult with aggregated statistics
        """
        if not self._is_profiling:
            raise RuntimeError("Profiling not started. Call start_profiling() first.")

        self._is_profiling = False
        profiling_duration = time.time() - self._profiling_start_time

        # Calculate statistics
        memory_values = [s.process_memory_mb for s in self._snapshots]
        start_memory = memory_values[0] if memory_values else 0.0
        end_memory = memory_values[-1] if memory_values else 0.0
        peak_memory = max(memory_values) if memory_values else 0.0
        avg_memory = sum(memory_values) / len(memory_values) if memory_values else 0.0
        memory_growth = end_memory - start_memory

        # Calculate growth rate per observation
        memory_growth_rate = memory_growth / max(total_observations, 1)

        # Calculate snapshots per 100 observations
        snapshot_count_per_100 = int((len(self._snapshots) / total_observations) * 100)

        results = MemoryProfileResult(
            start_memory_mb=start_memory,
            end_memory_mb=end_memory,
            peak_memory_mb=peak_memory,
            avg_memory_mb=avg_memory,
            memory_growth_mb=memory_growth,
            memory_growth_rate_mb_per_obs=memory_growth_rate,
            total_snapshots=len(self._snapshots),
            profiling_duration_seconds=profiling_duration,
            snapshot_count_per_100_obs=snapshot_count_per_100,
            snapshots=self._snapshots,
            memory_anomalies=self._memory_anomalies,
            profiling_config={
                'snapshot_interval': self.snapshot_interval,
                'max_memory_mb': self.max_memory_mb,
                'anomaly_threshold_multiplier': self.anomaly_threshold_multiplier,
                'gc_before_snapshot': self.gc_before_snapshot,
                'total_observations': total_observations
            }
        )

        # Save results if output specified
        if output_basename:
          results.save_to_json(self.output_dir / f"{output_basename}.json")
          results.save_to_csv(self.output_dir / f"{output_basename}.csv")

        logger.info(f"Memory profiling complete. Duration: {profiling_duration:.2f}s")
        logger.info(f"Memory growth: {memory_growth:.2f} MB ({memory_growth_rate:.4f} MB/obs)")

        return results

    def reset(self) -> None:
        """Reset profiler state for a new profiling session."""
        self._snapshots = []
        self._snapshot_counter = 0
        self._profiling_start_time = None
        self._profiling_start_memory = None
        self._is_profiling = False
        self._expected_growth_per_obs = None
        self._memory_anomalies = []


def profile_memory_usage(
    observations: Generator[Any, None, None],
    process_func: Callable[[Any, int], Any],
    snapshot_interval: int = 10,
    max_memory_mb: float = 7000.0,
    output_dir: Union[str, Path] = "projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/memory_profiles",
    output_basename: Optional[str] = None,
    gc_before_snapshot: bool = True
) -> MemoryProfileResult:
    """
    Convenience function to profile memory during observation processing.

    This is the primary entry point for FR-005 memory profiling. It creates
    a MemoryProfiler, processes observations with the provided function,
    and returns aggregated results.

    Args:
        observations: Generator yielding observations to process
        process_func: Function to call for each observation (obs, index) -> result
        snapshot_interval: Take snapshot every N observations
        max_memory_mb: Maximum allowed memory (FR-005: 7GB)
        output_dir: Directory to save profiling results
        output_basename: Optional base name for output files
        gc_before_snapshot: Run GC before each snapshot

    Returns:
        MemoryProfileResult with all profiling statistics

    Example:
        def process_obs(obs, idx):
            model.update(obs)
            score = model.score(obs)
            return score

        results = profile_memory_usage(
            observations=my_observations,
            process_func=process_obs,
            snapshot_interval=50,
            output_basename="1000_obs_profile"
        )
        print(f"Peak memory: {results.peak_memory_mb:.2f} MB")
    """
    profiler = MemoryProfiler(
        snapshot_interval=snapshot_interval,
        max_memory_mb=max_memory_mb,
        gc_before_snapshot=gc_before_snapshot,
        output_dir=output_dir
    )

    profiler.start_profiling()
    observation_count = 0

    try:
        for obs in observations:
            process_func(obs, observation_count)
            observation_count += 1

            if profiler.should_snapshot(observation_count):
                profiler.capture_snapshot(
                    operation=f"obs_{observation_count}",
                    observation_index=observation_count
                )

    except Exception as e:
        logger.error(f"Error during memory profiling: {e}")
        raise
    finally:
        results = profiler.stop_profiling(
            total_observations=observation_count,
            output_basename=output_basename
        )

    return results


def main() -> None:
    """
    CLI entry point for memory profiling.

    Usage:
        python -m code.utils.memory_profiler --observations 1000 --interval 50
    """
    import argparse

    parser = argparse.ArgumentParser(description='Memory profiler for DPGMM streaming')
    parser.add_argument('--observations', type=int, default=1000,
                        help='Number of observations to process')
    parser.add_argument('--interval', type=int, default=50,
                        help='Snapshot interval')
    parser.add_argument('--max-memory', type=float, default=7000.0,
                        help='Maximum memory in MB')
    parser.add_argument('--output', type=str, default='memory_profile',
                        help='Output filename base')
    parser.add_argument('--no-gc', action='store_true',
                        help='Skip garbage collection before snapshots')

    args = parser.parse_args()

    # Generate synthetic observations for testing
    logger.info(f"Starting memory profile: {args.observations} observations")

    def generate_observations(n: int) -> Generator[Dict[str, Any], None, None]:
        """Generate synthetic observations for profiling."""
        import numpy as np
        np.random.seed(42)
        for i in range(n):
            yield {
                'timestamp': datetime.now().isoformat(),
                'value': np.random.normal(0, 1),
                'index': i
            }

    def process_observation(obs: Dict[str, Any], idx: int) -> None:
        """Simulate observation processing (no actual model for this demo)."""
        # Simulate some memory allocation
        _ = [0] * 1000

    results = profile_memory_usage(
        observations=generate_observations(args.observations),
        process_func=process_observation,
        snapshot_interval=args.interval,
        max_memory_mb=args.max_memory,
        output_dir="data/memory_profiles",
        output_basename=args.output,
        gc_before_snapshot=not args.no_gc
    )

    # Print summary
    print("\n" + "=" * 60)
    print("MEMORY PROFILING SUMMARY")
    print("=" * 60)
    print(f"Total observations: {results.total_snapshots * args.interval}")
    print(f"Profiling duration: {results.profiling_duration_seconds:.2f}s")
    print(f"Start memory: {results.start_memory_mb:.2f} MB")
    print(f"End memory: {results.end_memory_mb:.2f} MB")
    print(f"Peak memory: {results.peak_memory_mb:.2f} MB")
    print(f"Memory growth: {results.memory_growth_mb:.2f} MB")
    print(f"Growth rate: {results.memory_growth_rate_mb_per_obs:.4f} MB/observation")
    print(f"Snapshots taken: {results.total_snapshots}")
    print(f"Memory anomalies: {len(results.memory_anomalies)}")
    print(f"Results saved to: data/memory_profiles/{args.output}.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
