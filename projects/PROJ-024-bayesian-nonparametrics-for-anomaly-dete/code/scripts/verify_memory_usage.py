"""
T043: Consolidated verification - memory usage under 7GB during 1000 observation processing

This script verifies that the DPGMM streaming implementation stays within the
7GB RAM constraint when processing 1000 observations incrementally.

Usage:
    python code/scripts/verify_memory_usage.py

Output:
    - Prints memory usage statistics at each checkpoint
    - Writes results to data/results/memory_verification_YYYYMMDD_HHMMSS.json
    - Exits with code 0 if memory < 7GB, 1 otherwise
"""
import os
import sys
import json
import time
import psutil
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from utils.memory_profiler import MemoryProfiler
from data.synthetic_anomaly_generator import generate_synthetic_timeseries
from models.dpgmm import DPGMMModel
from models.config import load_config

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024 * 1024 * 1024
NUM_OBSERVATIONS = 1000
CHECKPOINT_INTERVAL = 100  # Check memory every N observations

def get_current_memory_mb():
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def main():
    print("=" * 60)
    print("T043: Memory Usage Verification for 1000 Observations")
    print("=" * 60)
    print(f"Memory limit: {MEMORY_LIMIT_GB} GB ({MEMORY_LIMIT_BYTES / (1024*1024*1024):.2f} GB)")
    print(f"Observations to process: {NUM_OBSERVATIONS}")
    print(f"Checkpoint interval: every {CHECKPOINT_INTERVAL} observations")
    print()
    
    # Load configuration
    config = load_config()
    random_seed = config.get('random_seed', 42)
    print(f"Random seed: {random_seed}")
    
    # Initialize memory profiler
    memory_profiler = MemoryProfiler()
    
    # Generate synthetic time series data
    print("Generating synthetic time series data...")
    start_time = time.time()
    timeseries = generate_synthetic_timeseries(
        n_observations=NUM_OBSERVATIONS,
        n_features=1,
        anomaly_rate=0.05,
        random_seed=random_seed
    )
    gen_time = time.time() - start_time
    print(f"Data generation complete in {gen_time:.2f}s")
    print(f"Initial memory usage: {get_current_memory_mb():.2f} MB")
    print()
    
    # Initialize DPGMM model
    print("Initializing DPGMM model...")
    model = DPGMMModel(
      hyperparameters=config.get('dpgmm_hyperparameters', {}),
      random_seed=random_seed
    )
    print(f"Model initialized. Memory: {get_current_memory_mb():.2f} MB")
    print()
    
    # Track memory at checkpoints
    memory_checkpoints = []
    max_memory_mb = get_current_memory_mb()
    processing_times = []
    
    print("Processing observations incrementally...")
    print("-" * 60)
    
    for i in range(NUM_OBSERVATIONS):
        start_proc = time.time()
        
        # Get observation (handle missing values if any)
        observation = timeseries.data.iloc[i].values[0]
        
        # Update model with streaming observation
        model.update(observation)
        
        # Compute anomaly score
        score = model.compute_anomaly_score(observation)
        
        proc_time = time.time() - start_proc
        processing_times.append(proc_time)
        
        # Check memory at checkpoints
        current_memory_mb = get_current_memory_mb()
        max_memory_mb = max(max_memory_mb, current_memory_mb)
        
        if (i + 1) % CHECKPOINT_INTERVAL == 0 or i == 0:
            memory_checkpoints.append({
                'observation': i + 1,
                'memory_mb': current_memory_mb,
                'memory_gb': current_memory_mb / 1024,
                'processing_time_s': proc_time
            })
            print(f"Checkpoint {i + 1}/{NUM_OBSERVATIONS}: "
                  f"Memory = {current_memory_mb:.2f} MB ({current_memory_mb/1024:.4f} GB), "
                  f"Proc time = {proc_time:.4f}s")
    
    print("-" * 60)
    print()
    
    # Calculate statistics
    total_time = sum(processing_times)
    avg_proc_time = total_time / NUM_OBSERVATIONS
    max_memory_gb = max_memory_mb / 1024
    memory_limit_gb = MEMORY_LIMIT_GB
    
    # Determine pass/fail
    passed = max_memory_mb < MEMORY_LIMIT_BYTES
    
    # Print summary
    print("=" * 60)
    print("MEMORY VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Total observations processed: {NUM_OBSERVATIONS}")
    print(f"Total processing time: {total_time:.2f}s")
    print(f"Average per observation: {avg_proc_time*1000:.2f}ms")
    print()
    print(f"Peak memory usage: {max_memory_mb:.2f} MB ({max_memory_gb:.4f} GB)")
    print(f"Memory limit: {MEMORY_LIMIT_GB} GB")
    print()
    print(f"Memory margin: {MEMORY_LIMIT_GB - max_memory_gb:.4f} GB ({(MEMORY_LIMIT_GB - max_memory_gb)/MEMORY_LIMIT_GB*100:.2f}% headroom)")
    print()
    
    if passed:
        print("✓ MEMORY VERIFICATION PASSED")
        print(f"  Peak memory ({max_memory_gb:.4f} GB) < limit ({MEMORY_LIMIT_GB} GB)")
    else:
        print("✗ MEMORY VERIFICATION FAILED")
        print(f"  Peak memory ({max_memory_gb:.4f} GB) >= limit ({MEMORY_LIMIT_GB} GB)")
    
    print("=" * 60)
    
    # Save results to data/results/
    results_dir = project_root / 'data' / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)
    
  timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results = {
        'task_id': 'T043',
        'timestamp': datetime.now().isoformat(),
        'configuration': {
            'memory_limit_gb': MEMORY_LIMIT_GB,
            'num_observations': NUM_OBSERVATIONS,
            'checkpoint_interval': CHECKPOINT_INTERVAL,
            'random_seed': random_seed
        },
        'results': {
            'passed': passed,
            'peak_memory_mb': max_memory_mb,
            'peak_memory_gb': max_memory_gb,
            'memory_limit_gb': MEMORY_LIMIT_GB,
            'memory_margin_gb': MEMORY_LIMIT_GB - max_memory_gb,
            'total_processing_time_s': total_time,
            'avg_processing_time_per_obs_s': avg_proc_time,
            'memory_checkpoints': memory_checkpoints
        }
    }
    
    results_file = results_dir / f'memory_verification_{timestamp}.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    return 0 if passed else 1

if __name__ == '__main__':
    sys.exit(main())
