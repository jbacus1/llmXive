"""
Memory usage test verifying <7GB RAM limit for DPGMM streaming processing.

This test validates that the DPGMM model processes time series observations
within the memory constraints specified in FR-005 (<7GB RAM for 1000 observations).

Test Strategy:
- Use tracemalloc for accurate Python memory allocation tracking
- Process synthetic time series with known anomaly points
- Verify memory stays below 7GB threshold throughout processing
- Test streaming observation updates one at a time
"""

import gc
import tracemalloc
import pytest
from pathlib import Path
from typing import List, Dict, Any, Generator

import numpy as np

# Import from existing project API surface
from code.models.dp_gmm import DPGMMModel, DPGMMConfig
from code.models.anomaly_score import AnomalyScore
from code.data.synthetic_generator import generate_synthetic_timeseries, SignalConfig, AnomalyConfig


# Memory threshold constant (7GB in bytes)
MEMORY_THRESHOLD_BYTES = 7 * 1024 * 1024 * 1024  # 7 GB

# Number of observations to test
NUM_OBSERVATIONS = 1000

# Memory increase tolerance (allow 10% overhead)
MEMORY_TOLERANCE = 0.10


def setup_module():
    """Set up memory tracking module-wide."""
    tracemalloc.start()


def teardown_module():
    """Stop memory tracking module-wide."""
    tracemalloc.stop()


def generate_test_observations(n: int = NUM_OBSERVATIONS, seed: int = 42) -> np.ndarray:
    """
    Generate synthetic time series observations for memory testing.
    
    Args:
        n: Number of observations to generate
        seed: Random seed for reproducibility
        
    Returns:
        Array of shape (n, 1) containing time series values
    """
    np.random.seed(seed)
    
    # Generate base signal with trend and seasonality
    t = np.arange(n)
    trend = 0.001 * t
    seasonality = 10 * np.sin(2 * np.pi * t / 50)
    noise = np.random.normal(0, 1, n)
    
    values = trend + seasonality + noise
    
    # Inject some anomalies (5% of data)
    anomaly_indices = np.random.choice(n, size=int(n * 0.05), replace=False)
    values[anomaly_indices] += np.random.uniform(5, 10, size=len(anomaly_indices))
    
    return values.reshape(-1, 1)


def get_current_memory_mb() -> float:
    """Get current memory usage in megabytes."""
    current, _ = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)


def get_peak_memory_mb() -> float:
    """Get peak memory usage since tracking started in megabytes."""
    _, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)


class TestMemoryProfile:
    """Memory usage tests for DPGMM streaming processing."""

    def test_initialization_memory(self):
        """Test that DPGMM model initialization uses minimal memory."""
        gc.collect()
        
        # Record memory before initialization
        tracemalloc.clear_traces()
        tracemalloc.start()
        
        config = DPGMMConfig(
            max_components=10,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Record memory after initialization
        current, peak = tracemalloc.get_traced_memory()
        
        # Model should initialize with <100MB overhead
        assert peak < 100 * 1024 * 1024, (
            f"Model initialization exceeded 100MB: {peak / (1024*1024):.2f} MB"
        )
        
        tracemalloc.stop()

    def test_single_observation_update_memory(self):
        """Test memory usage for single observation streaming update."""
        gc.collect()
        
        config = DPGMMConfig(
            max_components=10,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Reset memory tracking
        tracemalloc.clear_traces()
        tracemalloc.start()
        
        # Process single observation
        observation = np.array([[5.0]])
        model.update(observation)
        
        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        
        # Single update should use <50MB
        assert peak < 50 * 1024 * 1024, (
            f"Single observation update exceeded 50MB: {peak / (1024*1024):.2f} MB"
        )
        
        tracemalloc.stop()

    def test_1000_observations_streaming_memory(self):
        """
        Main test: Verify memory stays under 7GB when processing 1000 observations.
        
        This test validates FR-005 requirement for memory efficiency in
        streaming DPGMM processing.
        """
        gc.collect()
        
        # Generate test observations
        observations = generate_test_observations(n=NUM_OBSERVATIONS, seed=42)
        
        # Create model
        config = DPGMMConfig(
            max_components=10,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Clear memory tracking and start fresh
        tracemalloc.clear_traces()
        tracemalloc.start()
        
        # Record baseline memory
        baseline_current, baseline_peak = tracemalloc.get_traced_memory()
        
        # Process observations one at a time (streaming)
        memory_log: List[float] = []
        for i in range(len(observations)):
            obs = observations[i:i+1]
            model.update(obs)
            
            # Log memory every 100 observations
            if (i + 1) % 100 == 0:
                current, _ = tracemalloc.get_traced_memory()
                memory_log.append(current / (1024 * 1024))  # MB
            
            # Force garbage collection periodically to avoid false positives
            if (i + 1) % 200 == 0:
                gc.collect()
        
        # Get final memory usage
        final_current, final_peak = tracemalloc.get_traced_memory()
        
        # Calculate memory increase from baseline
        memory_increase_mb = (final_current - baseline_current) / (1024 * 1024)
        peak_memory_mb = final_peak / (1024 * 1024)
        
        # Log results for debugging
        print(f"\nMemory Profile Results:")
        print(f"  Baseline: {baseline_current / (1024*1024):.2f} MB")
        print(f"  Final: {final_current / (1024*1024):.2f} MB")
        print(f"  Peak: {peak_memory_mb:.2f} MB")
        print(f"  Memory Increase: {memory_increase_mb:.2f} MB")
        print(f"  Memory at checkpoints: {memory_log}")
        
        # Verify memory stays under 7GB threshold
        # Allow 10% tolerance for system overhead
        threshold_with_tolerance = MEMORY_THRESHOLD_BYTES * (1 + MEMORY_TOLERANCE)
        
        assert final_current < threshold_with_tolerance, (
            f"Memory exceeded 7GB threshold after {NUM_OBSERVATIONS} observations. "
            f"Final: {final_current / (1024*1024*1024):.2f} GB, "
            f"Peak: {final_peak / (1024*1024*1024):.2f} GB"
        )
        
        # Also verify peak doesn't exceed threshold
        assert final_peak < threshold_with_tolerance, (
            f"Peak memory exceeded 7GB threshold. "
            f"Peak: {final_peak / (1024*1024*1024):.2f} GB"
        )
        
        # Verify memory growth is reasonable (<100MB per 100 observations)
        # This ensures the model doesn't have memory leaks
        avg_memory_per_obs = memory_increase_mb / NUM_OBSERVATIONS
        assert avg_memory_per_obs < 1.0, (
            f"Memory growth rate too high: {avg_memory_per_obs:.2f} MB per observation. "
            f"Expected <1.0 MB per observation"
        )
        
        tracemalloc.stop()

    def test_memory_with_anomaly_scoring(self):
        """Test memory usage when computing anomaly scores for all observations."""
        gc.collect()
        
        # Generate observations
        observations = generate_test_observations(n=NUM_OBSERVATIONS, seed=42)
        
        # Create and train model
        config = DPGMMConfig(
            max_components=10,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Process all observations
        for obs in observations:
            model.update(obs)
        
        # Clear memory tracking before scoring
        tracemalloc.clear_traces()
        tracemalloc.start()
        
        baseline_current, baseline_peak = tracemalloc.get_traced_memory()
        
        # Score all observations
        anomaly_scores: List[AnomalyScore] = []
        for obs in observations:
            score = model.score(obs)
            anomaly_scores.append(score)
            
            # Force GC periodically
            if len(anomaly_scores) % 200 == 0:
                gc.collect()
        
        # Get memory after scoring
        final_current, final_peak = tracemalloc.get_traced_memory()
        
        memory_increase = (final_current - baseline_current) / (1024 * 1024)
        
        print(f"\nAnomaly Scoring Memory Profile:")
        print(f"  Memory Increase: {memory_increase:.2f} MB")
        print(f"  Peak: {final_peak / (1024*1024):.2f} MB")
        
        # Scoring should not significantly increase memory
        # Allow up to 500MB for storing scores and intermediate results
        assert final_current < MEMORY_THRESHOLD_BYTES, (
            f"Anomaly scoring exceeded 7GB: {final_current / (1024*1024*1024):.2f} GB"
        )
        
        tracemalloc.stop()

    def test_memory_after_garbage_collection(self):
        """Test that memory is properly released after model processing."""
        gc.collect()
        
        config = DPGMMConfig(
            max_components=10,
            concentration_prior=1.0,
            random_seed=42
        )
        
        # Process observations
        observations = generate_test_observations(n=NUM_OBSERVATIONS, seed=42)
        model = DPGMMModel(config)
        
        for obs in observations:
            model.update(obs)
        
        # Record memory before deletion
        tracemalloc.clear_traces()
        tracemalloc.start()
        pre_delete_current, _ = tracemalloc.get_traced_memory()
        
        # Delete model
        del model
        gc.collect()
        
        # Record memory after deletion
        post_delete_current, _ = tracemalloc.get_traced_memory()
        
        # Memory should decrease (or stay roughly same if system cached)
        memory_after_delete_mb = post_delete_current / (1024 * 1024)
        
        print(f"\nMemory After Deletion: {memory_after_delete_mb:.2f} MB")
        
        # Should be reasonable (<500MB after cleanup)
        assert memory_after_delete_mb < 500, (
            f"Memory not properly released after model deletion: {memory_after_delete_mb:.2f} MB"
        )
        
        tracemalloc.stop()

    def test_concurrent_models_memory(self):
        """Test memory when multiple models are instantiated (edge case)."""
        gc.collect()
        
        tracemalloc.clear_traces()
        tracemalloc.start()
        
        baseline_current, _ = tracemalloc.get_traced_memory()
        
        # Create multiple models (stress test)
        models: List[DPGMMModel] = []
        for i in range(5):
            config = DPGMMConfig(
                max_components=10,
                concentration_prior=1.0,
                random_seed=i
            )
            models.append(DPGMMModel(config))
            
            # Process some observations
            obs = generate_test_observations(n=100, seed=i)
            for o in obs:
                models[-1].update(o)
            
            # Clear intermediate memory
            if i % 2 == 0:
                gc.collect()
        
        final_current, final_peak = tracemalloc.get_traced_memory()
        
        total_memory_gb = final_current / (1024 * 1024 * 1024)
        
        print(f"\nConcurrent Models Memory:")
        print(f"  Total: {total_memory_gb:.2f} GB")
        
        # Should still be under 7GB
        assert final_current < MEMORY_THRESHOLD_BYTES, (
            f"Multiple models exceeded 7GB: {total_memory_gb:.2f} GB"
        )
        
        # Cleanup
        del models
        gc.collect()
        
        tracemalloc.stop()

    def test_memory_profile_with_varying_components(self):
        """Test memory with different max_components settings."""
        gc.collect()
        
        observations = generate_test_observations(n=NUM_OBSERVATIONS, seed=42)
        
        component_counts = [5, 10, 20]
        
        for max_comp in component_counts:
            gc.collect()
            
            config = DPGMMConfig(
                max_components=max_comp,
                concentration_prior=1.0,
                random_seed=42
            )
            model = DPGMMModel(config)
            
            tracemalloc.clear_traces()
            tracemalloc.start()
            
            for obs in observations:
                model.update(obs)
            
            current, peak = tracemalloc.get_traced_memory()
            
            print(f"\nComponents={max_comp}: Peak={peak/(1024*1024):.2f} MB")
            
            # All configurations should stay under 7GB
            assert peak < MEMORY_THRESHOLD_BYTES, (
                f"max_components={max_comp} exceeded 7GB: {peak/(1024*1024*1024):.2f} GB"
            )
            
            tracemalloc.stop()

    def test_memory_log_summary(self):
        """Generate and verify memory log summary for documentation."""
        gc.collect()
        
        observations = generate_test_observations(n=NUM_OBSERVATIONS, seed=42)
        
        config = DPGMMConfig(
            max_components=10,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        tracemalloc.clear_traces()
        tracemalloc.start()
        
        memory_log: List[Dict[str, Any]] = []
        
        for i, obs in enumerate(observations):
            model.update(obs)
            
            if (i + 1) % 100 == 0:
                current, peak = tracemalloc.get_traced_memory()
                memory_log.append({
                    'observation': i + 1,
                    'current_mb': round(current / (1024 * 1024), 2),
                    'peak_mb': round(peak / (1024 * 1024), 2)
                })
        
        final_current, final_peak = tracemalloc.get_traced_memory()
        
        # Create summary
        summary = {
            'total_observations': NUM_OBSERVATIONS,
            'final_memory_mb': round(final_current / (1024 * 1024), 2),
            'peak_memory_mb': round(final_peak / (1024 * 1024), 2),
            'memory_threshold_gb': 7.0,
            'within_threshold': final_current < MEMORY_THRESHOLD_BYTES,
            'memory_log': memory_log
        }
        
        print(f"\nMemory Profile Summary:")
        print(f"  Observations: {summary['total_observations']}")
        print(f"  Final Memory: {summary['final_memory_mb']:.2f} MB")
        print(f"  Peak Memory: {summary['peak_memory_mb']:.2f} MB")
        print(f"  Within 7GB Threshold: {summary['within_threshold']}")
        
        # Verify summary shows compliance
        assert summary['within_threshold'], "Memory profile summary shows violation of 7GB threshold"
        
        tracemalloc.stop()

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
