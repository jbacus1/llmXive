"""
Unit tests for concentration parameter (alpha) sensitivity in DPGMM.

These tests verify that the Dirichlet Process Gaussian Mixture Model
correctly responds to different concentration parameter values:

- Low alpha (< 1.0): Favors fewer, larger clusters
- Medium alpha (~1.0-10.0): Balanced cluster formation
- High alpha (> 10.0): Favors more, smaller clusters

Tests are written TDD-style and should FAIL before T030 implementation.

Edge cases covered:
- Numerical stability at extreme alpha values
- Memory usage across alpha range
- Anomaly score sensitivity to alpha changes
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.dpgmm import DPGMMModel
from utils.logger import get_logger
from utils.memory_profiler import MemoryProfiler

logger = get_logger(__name__)

@pytest.fixture
def synthetic_data():
    """Generate synthetic time series data for testing."""
    np.random.seed(42)
    # Create 3 distinct Gaussian clusters
    n_samples = 1000
    data = np.concatenate([
        np.random.normal(loc=0, scale=1, size=n_samples),
        np.random.normal(loc=5, scale=1, size=n_samples),
        np.random.normal(loc=-5, scale=1, size=n_samples),
    ])
    return data

@pytest.fixture
def anomaly_data():
    """Generate data with clear anomalies for sensitivity testing."""
    np.random.seed(123)
    n_normal = 500
    n_anomaly = 50
    
    # Normal observations
    normal = np.random.normal(loc=0, scale=1, size=n_normal)
    # Anomalous observations (far from normal)
    anomaly = np.random.normal(loc=20, scale=1, size=n_anomaly)
    
    return np.concatenate([normal, anomaly])

class TestConcentrationParameterSensitivity:
    """Test suite for concentration parameter sensitivity."""
    
    def test_low_alpha_favors_fewer_clusters(self, synthetic_data):
        """
        Test that low concentration parameter (alpha < 1) produces
        fewer clusters as expected by Dirichlet Process theory.
        
        Expected behavior:
        - alpha = 0.1: Should form 1-3 clusters max
        - Fewer clusters means higher intra-cluster variance tolerance
        """
        model_low = DPGMMModel(alpha=0.1, random_seed=42)
        model_low.fit(synthetic_data)
        
        n_clusters_low = model_low.get_n_clusters()
        
        # With alpha=0.1, expect very few clusters
        assert n_clusters_low <= 5, \
            f"Low alpha should favor fewer clusters, got {n_clusters_low}"
        
        logger.info(f"Low alpha (0.1) resulted in {n_clusters_low} clusters")
    
    def test_high_alpha_favors_more_clusters(self, synthetic_data):
        """
        Test that high concentration parameter (alpha > 10) produces
        more clusters as expected by Dirichlet Process theory.
        
        Expected behavior:
        - alpha = 100: Should form more clusters, potentially overfitting
        - More clusters means stricter clustering requirements
        """
        model_high = DPGMMModel(alpha=100.0, random_seed=42)
        model_high.fit(synthetic_data)
        
        n_clusters_high = model_high.get_n_clusters()
        
        # With alpha=100, expect more clusters than low alpha
        assert n_clusters_high >= 3, \
            f"High alpha should favor more clusters, got {n_clusters_high}"
        
        logger.info(f"High alpha (100.0) resulted in {n_clusters_high} clusters")
    
    def test_alpha_monotonicity_cluster_count(self, synthetic_data):
        """
        Test that cluster count generally increases with alpha.
        
        This is a statistical property of the Dirichlet Process:
        E[K] ≈ alpha * log(n) for n observations
        """
        alphas = [0.1, 1.0, 10.0, 50.0, 100.0]
        cluster_counts = []
        
        for alpha in alphas:
            model = DPGMMModel(alpha=alpha, random_seed=42)
            model.fit(synthetic_data)
            cluster_counts.append(model.get_n_clusters())
            logger.info(f"alpha={alpha}: {model.get_n_clusters()} clusters")
        
        # Check monotonicity (allowing for some stochastic variation)
        # We expect cluster_counts to be non-decreasing with some tolerance
        increases = sum(1 for i in range(1, len(cluster_counts)) 
                      if cluster_counts[i] >= cluster_counts[i-1] - 1)
        
        # At least 80% should be non-decreasing
        assert increases / (len(cluster_counts) - 1) >= 0.8, \
            f"Cluster count should generally increase with alpha: {cluster_counts}"
    
    def test_numerical_stability_extreme_alpha(self, synthetic_data):
        """
        Test numerical stability at extreme alpha values.
        
        Very low alpha can cause:
        - Division by near-zero in stick-breaking
        - Log(0) errors in likelihood computation
        
        Very high alpha can cause:
        - Numerical overflow in cluster weights
        - Memory issues from too many clusters
        """
        extreme_alphas = [0.001, 1000.0]
        
        for alpha in extreme_alphas:
            logger.info(f"Testing numerical stability at alpha={alpha}")
            try:
                model = DPGMMModel(alpha=alpha, random_seed=42)
                model.fit(synthetic_data)
                
                # Check that we can compute anomaly scores without errors
                scores = model.compute_anomaly_scores(synthetic_data)
                
                # Check for NaN or Inf in scores
                assert not np.any(np.isnan(scores)), \
                    f"NaN scores at alpha={alpha}"
                assert not np.any(np.isinf(scores)), \
                    f"Inf scores at alpha={alpha}"
                
                # Check that scores are finite numbers
                assert np.all(np.isfinite(scores)), \
                    f"Non-finite scores at alpha={alpha}"
                
            except Exception as e:
                pytest.fail(f"Numerical instability at alpha={alpha}: {e}")
    
    def test_alpha_affects_anomaly_scores(self, anomaly_data):
        """
        Test that concentration parameter affects anomaly score distribution.
        
        Different alpha values should produce different:
        - Score ranges
        - Score distributions
        - Anomaly detection sensitivity
        """
        alphas = [0.1, 1.0, 10.0]
        score_stats = {}
        
        for alpha in alphas:
            model = DPGMMModel(alpha=alpha, random_seed=42)
            model.fit(anomaly_data)
            
            scores = model.compute_anomaly_scores(anomaly_data)
            
            score_stats[alpha] = {
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores)),
                'min': float(np.min(scores)),
                'max': float(np.max(scores)),
                'median': float(np.median(scores)),
            }
            
            logger.info(f"alpha={alpha}: mean={score_stats[alpha]['mean']:.4f}, "
                       f"std={score_stats[alpha]['std']:.4f}")
        
        # Verify that different alphas produce different score distributions
        means = [s['mean'] for s in score_stats.values()]
        stds = [s['std'] for s in score_stats.values()]
        
        # At least two different alphas should produce meaningfully different scores
        mean_variance = np.var(means)
        std_variance = np.var(stds)
        
        assert mean_variance > 0.01 or std_variance > 0.01, \
            f"Alpha should affect score distribution: means={means}, stds={stds}"
    
    def test_memory_usage_across_alpha_range(self, synthetic_data):
        """
        Test memory usage remains acceptable across alpha values.
        
        Higher alpha may create more clusters, potentially increasing memory.
        Must stay under 7GB constraint per project requirements.
        """
        alphas = [0.1, 1.0, 10.0, 50.0, 100.0]
        max_memory_mb = 7 * 1024  # 7GB in MB
        
        profiler = MemoryProfiler()
        
        for alpha in alphas:
            profiler.start()
            
            model = DPGMMModel(alpha=alpha, random_seed=42)
            model.fit(synthetic_data)
            _ = model.compute_anomaly_scores(synthetic_data)
            
            memory_mb = profiler.stop()
            logger.info(f"alpha={alpha}: memory usage = {memory_mb:.2f} MB")
            
            assert memory_mb < max_memory_mb, \
                f"Memory usage {memory_mb}MB exceeds limit at alpha={alpha}"
    
    def test_alpha_in_streaming_mode(self, synthetic_data):
        """
        Test concentration parameter behavior in streaming/incremental mode.
        
        Streaming updates should respect the alpha parameter:
        - Low alpha: New observations more likely to join existing clusters
        - High alpha: New observations more likely to form new clusters
        """
        # Fit on first half
        half_data = synthetic_data[:len(synthetic_data)//2]
        
        model = DPGMMModel(alpha=10.0, random_seed=42)
        model.fit(half_data)
        
        initial_clusters = model.get_n_clusters()
        initial_scores = model.compute_anomaly_scores(half_data)
        
        # Stream remaining observations
        streaming_data = synthetic_data[len(synthetic_data)//2:]
        for obs in streaming_data:
            model.update(obs)
        
        final_clusters = model.get_n_clusters()
        final_scores = model.compute_anomaly_scores(synthetic_data)
        
        logger.info(f"Streaming: {initial_clusters} -> {final_clusters} clusters")
        
        # Verify streaming completed without errors
        assert final_clusters >= initial_clusters, \
            "Cluster count should not decrease during streaming"
        
        # Verify scores are valid
        assert np.all(np.isfinite(final_scores)), \
            "Streaming should produce finite anomaly scores"
    
    def test_alpha_default_value(self):
        """
        Test that default concentration parameter is reasonable.
        
        Default alpha should be in a sensible range for typical use cases.
        """
        model = DPGMMModel(random_seed=42)  # Use default alpha
        
        # Default should be between 0.1 and 100
        assert 0.1 <= model.alpha <= 100.0, \
            f"Default alpha={model.alpha} out of expected range [0.1, 100]"
        
        logger.info(f"Default alpha: {model.alpha}")
    
    def test_alpha_change_after_init(self, synthetic_data):
        """
        Test that changing alpha after initialization affects behavior.
        
        This tests the model's ability to adapt to hyperparameter changes.
        """
        model = DPGMMModel(alpha=1.0, random_seed=42)
        model.fit(synthetic_data[:500])
        
        clusters_before = model.get_n_clusters()
        
        # Change alpha and refit
        model.alpha = 10.0
        model.fit(synthetic_data[:500])
        
        clusters_after = model.get_n_clusters()
        
        # Higher alpha should produce >= clusters
        assert clusters_after >= clusters_before, \
            f"Increasing alpha should not reduce clusters: {clusters_before} -> {clusters_after}"
        
        logger.info(f"Alpha change: {clusters_before} -> {clusters_after} clusters")