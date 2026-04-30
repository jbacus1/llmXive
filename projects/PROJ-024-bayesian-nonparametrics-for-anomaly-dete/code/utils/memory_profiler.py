"""
Memory profiling utilities for streaming DPGMM anomaly detection.

Implements memory tracking during observation processing to verify
FR-005 memory constraints (<7GB RAM limit during 1000 observation processing).

Provides utilities for:
- Real-time memory usage monitoring
- Memory profiling across observation batches
- Memory leak detection
- Profile report generation
"""

import gc
import tracemalloc
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Tuple
from pathlib import Path
from datetime import datetime
import logging

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logging.warning("psutil not available - using tracemalloc only for memory profiling")

import numpy as np

from models.dp_gmm import DPGMMModel, DPGMMConfig
from utils.streaming import StreamingObservation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MemorySnapshot:
    """Single memory measurement snapshot."""
    timestamp: float
    process_memory_mb: float
    tracemalloc_current_mb: float
    tracemalloc_peak_mb: float
    observation_count: int
    active_clusters: int
    elbo_value: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'process_memory_mb': self.process_memory_mb,
            'tracemalloc_current_mb': self.tracemalloc_current_mb,
            'tracemalloc_peak_mb': self.tracemalloc_peak_mb,
            'observation_count': self.observation_count,
            'active_clusters': self.active_clusters,
            'elbo_value': self.elbo_value
        }

@dataclass
class MemoryProfile:
    """Complete memory profile across observation processing."""
    snapshots: List[MemorySnapshot] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    total_observations: int = 0
    memory_limit_mb: float = 7 * 1024  # 7GB default
    exceeds_limit: bool = False
    peak_memory_mb: float = 0.0
    avg_memory_mb: float = 0.0
    
    def add_snapshot(self, snapshot: MemorySnapshot):
        self.snapshots.append(snapshot)
        if snapshot.process_memory_mb > self.peak_memory_mb:
            self.peak_memory_mb = snapshot.process_memory_mb
            self.exceeds_limit = self.peak_memory_mb > self.memory_limit_mb
    
    def finalize(self, total_observations: int):
        self.total_observations = total_observations
        self.end_time = time.time()
        if self.snapshots:
            self.avg_memory_mb = np.mean([s.process_memory_mb for s in self.snapshots])
    
    def summary(self) -> Dict[str, Any]:
        return {
            'total_observations': self.total_observations,
            'peak_memory_mb': self.peak_memory_mb,
            'avg_memory_mb': self.avg_memory_mb,
            'exceeds_limit': self.exceeds_limit,
            'memory_limit_mb': self.memory_limit_mb,
            'duration_seconds': self.end_time - self.start_time if self.start_time and self.end_time else 0,
            'observations_per_second': self.total_observations / (self.end_time - self.start_time) if self.start_time and self.end_time and self.end_time > self.start_time else 0
        }

def get_process_memory_mb() -> float:
    """Get current process memory usage in MB."""
    if HAS_PSUTIL:
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    else:
        # Fallback: tracemalloc only (less accurate for total process memory)
        if tracemalloc.is_tracing():
            current, _ = tracemalloc.get_traced_memory()
            return current / (1024 * 1024)
        return 0.0

def get_tracemalloc_memory() -> Tuple[float, float]:
    """Get tracemalloc current and peak memory in MB."""
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        return current / (1024 * 1024), peak / (1024 * 1024)
    return 0.0, 0.0

def create_memory_snapshot(
    observation_count: int,
    model: Optional[DPGMMModel] = None,
    elbo_value: Optional[float] = None
) -> MemorySnapshot:
    """Create a memory snapshot with optional model state."""
    active_clusters = 0
    if model is not None:
        active_clusters = len(model.components) if hasattr(model, 'components') else 0
    
    return MemorySnapshot(
        timestamp=time.time(),
        process_memory_mb=get_process_memory_mb(),
        tracemalloc_current_mb=get_tracemalloc_memory()[0],
        tracemalloc_peak_mb=get_tracemalloc_memory()[1],
        observation_count=observation_count,
        active_clusters=active_clusters,
        elbo_value=elbo_value
    )

def profile_1000_observations(
    model: DPGMMModel,
    synthetic_generator: Optional[Callable] = None,
    memory_limit_mb: float = 7 * 1024,
    sample_interval: int = 10
) -> MemoryProfile:
    """
    Profile memory usage during processing of 1000 observations.
    
    Args:
        model: DPGMMModel instance for processing observations
        synthetic_generator: Optional callable that yields (observation, is_anomaly) tuples
        memory_limit_mb: Memory limit in MB (default 7GB)
        sample_interval: Record snapshot every N observations
    
    Returns:
        MemoryProfile with snapshots and summary statistics
    """
    profile = MemoryProfile(memory_limit_mb=memory_limit_mb)
    profile.start_time = time.time()
    
    # Start tracemalloc
    tracemalloc.start()
    
    logger.info(f"Starting memory profile for 1000 observations (limit: {memory_limit_mb} MB)")
    
    # Generate synthetic observations if not provided
    if synthetic_generator is None:
        from data.synthetic_generator import generate_synthetic_timeseries
        synthetic_generator = generate_synthetic_timeseries(
            n_observations=1000,
            anomaly_rate=0.05
        )
    
    observation_count = 0
    for obs_data in synthetic_generator:
        observation_count += 1
        
        # Process observation through model
        obs = StreamingObservation(
            timestamp=datetime.now(),
            value=float(obs_data[0]) if isinstance(obs_data, (tuple, list)) else float(obs_data)
        )
        
        model.update(obs)
        
        # Record snapshot at intervals
        if observation_count % sample_interval == 0 or observation_count == 1000:
            snapshot = create_memory_snapshot(
                observation_count=observation_count,
                model=model,
                elbo_value=model.elbo_history[-1] if hasattr(model, 'elbo_history') and model.elbo_history else None
            )
            profile.add_snapshot(snapshot)
            logger.debug(f"Obs {observation_count}: {snapshot.process_memory_mb:.2f} MB, "
                        f"{snapshot.active_clusters} clusters")
    
    profile.finalize(observation_count)
    tracemalloc.stop()
    
    # Log summary
    summary = profile.summary()
    logger.info(f"Memory profile complete: peak={summary['peak_memory_mb']:.2f} MB, "
               f"avg={summary['avg_memory_mb']:.2f} MB, "
               f"exceeds_limit={summary['exceeds_limit']}")
    
    return profile

def save_profile_report(
    profile: MemoryProfile,
    output_path: Path,
    format: str = 'json'
) -> Path:
    """
    Save memory profile report to file.
    
    Args:
        profile: MemoryProfile instance
        output_path: Output file path
        format: 'json' or 'csv'
    
    Returns:
        Path to saved report
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if format == 'json':
        import json
        report = {
            'summary': profile.summary(),
            'snapshots': [s.to_dict() for s in profile.snapshots],
            'generated_at': datetime.now().isoformat()
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
    elif format == 'csv':
        import csv
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'observation_count', 'process_memory_mb',
                'tracemalloc_current_mb', 'tracemalloc_peak_mb',
                'active_clusters', 'elbo_value'
            ])
            for s in profile.snapshots:
                writer.writerow([
                    s.timestamp, s.observation_count, s.process_memory_mb,
                    s.tracemalloc_current_mb, s.tracemalloc_peak_mb,
                    s.active_clusters, s.elbo_value
                ])
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    logger.info(f"Saved memory profile report to {output_path}")
    return output_path

def verify_memory_constraint(profile: MemoryProfile) -> Tuple[bool, str]:
    """
    Verify that memory usage stayed within constraint.
    
    Args:
        profile: MemoryProfile to verify
    
    Returns:
        Tuple of (passed, message)
    """
    if profile.exceeds_limit:
        return False, f"Memory exceeded limit: {profile.peak_memory_mb:.2f} MB > {profile.memory_limit_mb} MB"
    return True, f"Memory within limit: peak={profile.peak_memory_mb:.2f} MB <= {profile.memory_limit_mb} MB"

def main():
    """
    Main entry point for standalone memory profiling.
    
    Runs a full memory profile test with synthetic data and saves report.
    """
    logger.info("Memory Profiler - Standalone Test")
    
    # Create model with default config
    config = DPGMMConfig(
        alpha=1.0,
        gamma=1.0,
        random_state=42
    )
    model = DPGMMModel(config)
    
    # Run profile
    profile = profile_1000_observations(
        model=model,
        memory_limit_mb=7 * 1024,
        sample_interval=50
    )
    
    # Verify constraint
    passed, message = verify_memory_constraint(profile)
    logger.info(f"Constraint check: {message}")
    
    # Save report
    output_path = Path("data/profiles/memory_profile_1000_obs.json")
    save_profile_report(profile, output_path)
    
    # Print summary
    summary = profile.summary()
    print("\n" + "=" * 60)
    print("MEMORY PROFILE SUMMARY")
    print("=" * 60)
    print(f"Total observations processed: {summary['total_observations']}")
    print(f"Peak memory usage: {summary['peak_memory_mb']:.2f} MB")
    print(f"Average memory usage: {summary['avg_memory_mb']:.2f} MB")
    print(f"Memory limit: {summary['memory_limit_mb']} MB")
    print(f"Exceeds limit: {summary['exceeds_limit']}")
    print(f"Duration: {summary['duration_seconds']:.2f} seconds")
    print(f"Throughput: {summary['observations_per_second']:.2f} obs/sec")
    print("=" * 60)
    
    return 0 if passed else 1

if __name__ == '__main__':
    exit(main())
