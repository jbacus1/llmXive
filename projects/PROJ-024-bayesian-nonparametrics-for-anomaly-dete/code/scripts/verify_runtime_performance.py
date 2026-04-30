"""
T072: Verify <30 minutes runtime per dataset using runtime_profiler.py

This script validates that the anomaly detection pipeline completes
within the 30-minute runtime constraint per dataset as per SC-003.
"""
import os
import sys
import time
import yaml
import json
from pathlib import Path
from datetime import datetime

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.runtime_profiler import RuntimeProfiler
from utils.memory_profiler import MemoryProfiler
from models.dpgmm import DPGMMModel
from services.anomaly_detector import AnomalyDetector
from data.synthetic_anomaly_generator import SyntheticAnomalyGenerator

MAX_RUNTIME_SECONDS = 1800  # 30 minutes
PROJECT_ROOT = Path(__file__).parent.parent.parent

def load_config():
    """Load project configuration."""
    config_path = PROJECT_ROOT / 'code' / 'config.yaml'
    if not config_path.exists():
        # Create minimal config if missing
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config = {
            'random_seed': 42,
            'concentration_param': 1.0,
            'n_observations': 1000,
            'anomaly_rate': 0.05,
            'dataset_path': str(PROJECT_ROOT / 'data' / 'processed' / 'synthetic_timeseries.csv')
        }
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        return config
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def save_runtime_report(runtime_seconds, success, details=None):
    """Save runtime verification report to state/ directory."""
    state_dir = PROJECT_ROOT / 'state'
    state_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        'task_id': 'T072',
        'timestamp': datetime.utcnow().isoformat(),
        'max_runtime_seconds': MAX_RUNTIME_SECONDS,
        'actual_runtime_seconds': round(runtime_seconds, 2),
        'success': success,
        'details': details or {}
    }
    
    report_path = state_dir / 'runtime_verification_T072.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to: {report_path}")

def run_performance_verification():
    """Run the full pipeline and measure runtime."""
    print("=" * 70)
    print("T072: Runtime Performance Verification")
    print("Constraint: <30 minutes (1800 seconds) per dataset")
    print("=" * 70)
    
    config = load_config()
    profiler = RuntimeProfiler()
    memory_profiler = MemoryProfiler()
    
    # Test with representative dataset sizes
    test_sizes = [500, 1000, 2000]
    results = []
    
    for n_obs in test_sizes:
        print(f"\n{'-' * 70}")
        print(f"Testing with {n_obs} observations...")
        print(f"{'-' * 70}")
        
        # Generate synthetic dataset
        print("[1/4] Generating synthetic time series dataset...")
        generator = SyntheticAnomalyGenerator(
            n_observations=n_obs,
            anomaly_rate=config.get('anomaly_rate', 0.05),
            random_seed=config.get('random_seed', 42)
        )
        timeseries = generator.generate()
        print(f"    ✓ Generated {len(timeseries)} observations")
        
        # Initialize profiler
        profiler.start()
        memory_profiler.start()
        
        # Run anomaly detection pipeline
        print("[2/4] Initializing DPGMM model...")
        model = DPGMMModel(
            alpha=config.get('concentration_param', 1.0),
            random_seed=config.get('random_seed', 42),
            memory_optimized=True
        )
        print(f"    ✓ Model initialized with alpha={model.alpha}")
        
        print("[3/4] Running streaming anomaly detection...")
        detector = AnomalyDetector(model=model)
        
        # Process in streaming fashion (one observation at a time)
        anomaly_count = 0
        for i, obs in enumerate(timeseries):
            detector.update(obs)
            if i % (len(timeseries) // 10) == 0 and i > 0:
                print(f"    Progress: {i}/{len(timeseries)} observations processed")
        
        print("[4/4] Computing anomaly scores...")
        scores = detector.compute_scores(timeseries)
        
        # Stop profiler
        profiler.stop()
        memory_profiler.stop()
        
        runtime = profiler.get_total_runtime()
        peak_memory = memory_profiler.get_peak_memory_mb()
        
        success = runtime <= MAX_RUNTIME_SECONDS
        
        result = {
            'n_observations': n_obs,
            'runtime_seconds': round(runtime, 2),
            'peak_memory_mb': round(peak_memory, 2),
            'success': success,
            'anomalies_detected': len([s for s in scores if s.score > detector.threshold])
        }
        results.append(result)
        
        print(f"\n    Results for {n_obs} observations:")
        print(f"    - Runtime: {runtime:.2f} seconds")
        print(f"    - Peak Memory: {peak_memory:.2f} MB")
        print(f"    - Anomalies Detected: {result['anomalies_detected']}")
        print(f"    - Status: {'✓ PASS' if success else '✗ FAIL'}")
    
    # Overall verdict
    print(f"\n{'=' * 70}")
    print("OVERALL RESULTS")
    print(f"{'=' * 70}")
    
    all_passed = all(r['success'] for r in results)
    
    for r in results:
        status = '✓ PASS' if r['success'] else '✗ FAIL'
        print(f"  {r['n_observations']:4d} obs: {r['runtime_seconds']:8.2f}s ({status})")
    
    print(f"\n  Max allowed: {MAX_RUNTIME_SECONDS} seconds")
    print(f"  Overall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    # Save detailed report
    save_runtime_report(
        runtime_seconds=max(r['runtime_seconds'] for r in results),
        success=all_passed,
        details={
            'test_results': results,
            'max_runtime_seconds': MAX_RUNTIME_SECONDS,
            'constraint': 'SC-003: runtime per dataset does not exceed 30 minutes'
        }
    )
    
    return all_passed

def main():
    """Main entry point."""
    try:
        success = run_performance_verification()
        print(f"\n{'=' * 70}")
        print("T072 VERIFICATION: {'COMPLETE' if success else 'FAILED'}")
        print(f"{'=' * 70}\n")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR during verification: {e}")
        import traceback
        traceback.print_exc()
        save_runtime_report(
            runtime_seconds=0,
            success=False,
            details={'error': str(e)}
        )
        sys.exit(1)

if __name__ == '__main__':
    main()
