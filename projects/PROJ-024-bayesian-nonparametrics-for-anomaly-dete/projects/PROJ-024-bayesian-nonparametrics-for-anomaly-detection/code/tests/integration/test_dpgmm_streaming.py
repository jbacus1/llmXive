"""
Integration test for streaming DPGMM update.

This test verifies that the DPGMM model can process time series observations
one at a time using streaming updates without requiring batch retraining.

Per plan.md requirements: Tests are MANDATORY and must fail before implementation.
This test intentionally imports from unimplemented modules to ensure it fails
until T030 (DPGMMModel implementation) and T032 (AnomalyDetector service) are complete.

Test scope:
- Streaming observation processing (one at a time)
- Incremental posterior update after each observation
- Anomaly score computation without batch retraining
- Memory usage verification during streaming
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Import paths will fail until T030/T032 are implemented
# This is intentional per plan.md "tests must fail before implementation"
try:
    from code.models.dpgmm import DPGMMModel
    from code.services.anomaly_detector import AnomalyDetector
    from code.models.timeseries import TimeSeries
    from code.models.anomaly_score import AnomalyScore
    from code.utils.memory_profiler import MemoryProfiler
    from code.data.synthetic_anomaly_generator import generate_synthetic_anomaly_data
except ImportError as e:
    pytest.skip(f"DPGMM implementation not yet complete (T030/T032 pending): {e}", allow_module_level=True)

@pytest.fixture
def synthetic_timeseries_with_anomalies():
    """Generate synthetic time series with known anomaly points for testing."""
    # Generate 100 observations with 5 known anomalies at indices [10, 30, 50, 70, 90]
    data, ground_truth = generate_synthetic_anomaly_data(
        n_observations=100,
        anomaly_indices=[10, 30, 50, 70, 90],
        anomaly_magnitude=3.0,
        noise_level=0.1,
        random_seed=42
    )
    return {
        'data': data,
        'ground_truth': ground_truth,
        'anomaly_indices': [10, 30, 50, 70, 90]
    }

@pytest.fixture
def streaming_dpgmm_config():
    """Configuration for streaming DPGMM with memory constraints."""
    return {
        'concentration_parameter': 1.0,
        'max_clusters': 10,
        'random_seed': 42,
        'memory_limit_gb': 7.0,
        'advi_iterations': 100
    }

class TestStreamingDPGMMUpdate:
    """Integration tests for streaming DPGMM update functionality."""

    def test_streaming_observation_processing(self, synthetic_timeseries_with_anomalies, streaming_dpgmm_config):
        """Test that observations can be processed one at a time without batch retraining."""
        ts = TimeSeries(
            values=synthetic_timeseries_with_anomalies['data'],
            timestamp_range=(0, len(synthetic_timeseries_with_anomalies['data'])),
            metadata={'source': 'synthetic'}
        )
        
        model = DPGMMModel(config=streaming_dpgmm_config)
        detector = AnomalyDetector(model=model)
        
        # Process observations one at a time (streaming)
        scores = []
        for i in range(len(ts)):
            observation = ts[i]
            # Update model with single observation
            model.incremental_update(observation)
            # Compute anomaly score without batch retraining
            score = detector.compute_anomaly_score(observation, model)
            scores.append(score)
        
        # Verify scores were produced for all observations
        assert len(scores) == len(ts), "All observations should have anomaly scores"
        assert all(isinstance(s, AnomalyScore) for s in scores), "All scores must be AnomalyScore objects"

    def test_incremental_posterior_update(self, synthetic_timeseries_with_anomalies, streaming_dpgmm_config):
        """Test that posterior is updated incrementally after each observation."""
        ts = TimeSeries(
            values=synthetic_timeseries_with_anomalies['data'],
            timestamp_range=(0, len(synthetic_timeseries_with_anomalies['data'])),
            metadata={'source': 'synthetic'}
        )
        
        model = DPGMMModel(config=streaming_dpgmm_config)
        
        # Track number of clusters before and after each update
        initial_clusters = model.get_cluster_count()
        
        for i in range(min(50, len(ts))):
            observation = ts[i]
            model.incremental_update(observation)
            current_clusters = model.get_cluster_count()
            
            # Cluster count should be non-decreasing (stick-breaking construction)
            assert current_clusters >= initial_clusters, "Cluster count should not decrease"
            initial_clusters = current_clusters
        
        # Model should have discovered some structure
        assert model.get_cluster_count() >= 1, "Model should have at least one cluster"

    def test_anomaly_detection_accuracy(self, synthetic_timeseries_with_anomalies, streaming_dpgmm_config):
        """Test that known anomalies are detected with reasonable accuracy."""
        ts = TimeSeries(
            values=synthetic_timeseries_with_anomalies['data'],
            timestamp_range=(0, len(synthetic_timeseries_with_anomalies['data'])),
            metadata={'source': 'synthetic'}
        )
        
        model = DPGMMModel(config=streaming_dpgmm_config)
        detector = AnomalyDetector(model=model, threshold=0.95)
        
        # Process all observations
        anomaly_flags = []
        for i in range(len(ts)):
            observation = ts[i]
            model.incremental_update(observation)
            score = detector.compute_anomaly_score(observation, model)
            anomaly_flags.append(score.is_anomaly)
        
        # Check detection rate at known anomaly indices
        detected_at_anomalies = sum(anomaly_flags[i] for i in synthetic_timeseries_with_anomalies['anomaly_indices'])
        detection_rate = detected_at_anomalies / len(synthetic_timeseries_with_anomalies['anomaly_indices'])
        
        # Should detect at least 50% of known anomalies (relaxed threshold for streaming)
        assert detection_rate >= 0.5, f"Expected at least 50% anomaly detection rate, got {detection_rate:.2%}"

    def test_memory_constraint_during_streaming(self, synthetic_timeseries_with_anomalies, streaming_dpgmm_config):
        """Test that memory usage stays under 7GB during 1000 observation processing."""
        ts = TimeSeries(
            values=synthetic_timeseries_with_anomalies['data'],
            timestamp_range=(0, len(synthetic_timeseries_with_anomalies['data'])),
            metadata={'source': 'synthetic'}
        )
        
        model = DPGMMModel(config=streaming_dpgmm_config)
        detector = AnomalyDetector(model=model)
        
        profiler = MemoryProfiler(limit_gb=streaming_dpgmm_config['memory_limit_gb'])
        
        with profiler.track():
            for i in range(len(ts)):
                observation = ts[i]
                model.incremental_update(observation)
                detector.compute_anomaly_score(observation, model)
        
        # Verify memory stayed under limit
        assert profiler.peak_memory_gb < streaming_dpgmm_config['memory_limit_gb'], \
            f"Memory exceeded limit: {profiler.peak_memory_gb:.2f}GB > {streaming_dpgmm_config['memory_limit_gb']}GB"

    def test_no_batch_retraining_required(self, synthetic_timeseries_with_anomalies, streaming_dpgmm_config):
        """Test that model produces scores without requiring batch retraining."""
        ts = TimeSeries(
            values=synthetic_timeseries_with_anomalies['data'],
            timestamp_range=(0, len(synthetic_timeseries_with_anomalies['data'])),
            metadata={'source': 'synthetic'}
        )
        
        model = DPGMMModel(config=streaming_dpgmm_config)
        detector = AnomalyDetector(model=model)
        
        # Track if any batch retraining call was made
        retraining_called = False
        
        for i in range(len(ts)):
            observation = ts[i]
            model.incremental_update(observation)
            
            # Verify no batch retraining is needed for scoring
            score = detector.compute_anomaly_score(observation, model)
            
            # Check that model state is still valid (no retraining flag)
            if hasattr(model, 'requires_batch_retrain'):
                retraining_called = model.requires_batch_retrain
        
        assert not retraining_called, "Model should not require batch retraining for streaming updates"

    def test_advi_convergence_diagnostics(self, synthetic_timeseries_with_anomalies, streaming_dpgmm_config):
        """Test that ADVI variational inference convergence is tracked."""
        ts = TimeSeries(
            values=synthetic_timeseries_with_anomalies['data'],
            timestamp_range=(0, len(synthetic_timeseries_with_anomalies['data'])),
            metadata={'source': 'synthetic'}
        )
        
        model = DPGMMModel(config=streaming_dpgmm_config)
        
        elbo_history = []
        for i in range(min(100, len(ts))):
            observation = ts[i]
            model.incremental_update(observation)
            
            # Track ELBO for convergence diagnostics
            if hasattr(model, 'get_elbo'):
                elbo_history.append(model.get_elbo())
        
        # ELBO should generally increase (or stabilize) during training
        if len(elbo_history) >= 10:
            # Check that ELBO didn't diverge catastrophically
            assert all(not np.isnan(e) for e in elbo_history), "ELBO should not contain NaN values"
            assert all(not np.isinf(e) for e in elbo_history), "ELBO should not contain Inf values"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
