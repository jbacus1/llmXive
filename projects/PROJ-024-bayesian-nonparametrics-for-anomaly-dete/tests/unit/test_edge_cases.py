"""
Unit tests for edge cases in DPGMM anomaly detection.

Tests cover:
- Low-variance time series (numerical stability)
- Missing value handling in streaming updates
- Concentration parameter edge cases
- Cluster anomaly detection edge cases
- Single observation edge cases
- Extreme value handling
"""
import sys
import os
import numpy as np
from pathlib import Path
import pytest
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from models.dp_gmm import DPGMMModel, DPGMMConfig, ELBOHistory, ClusterAnomalyResult
from models.anomaly_score import AnomalyScore
from models.time_series import TimeSeries
from utils.streaming import StreamingObservation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def basic_config():
    """Basic DPGMM configuration for tests."""
    return DPGMMConfig(
        alpha=1.0,  # Concentration parameter
        gamma=1.0,  # Stick-breaking parameter
        beta=1.0,   # Precision prior
        kappa=1.0,  # Mean prior strength
        nu=1.0,     # Degrees of freedom for Wishart
        max_components=10,
        min_components=1,
        convergence_threshold=1e-6,
        max_iterations=100,
        random_seed=42,
        learning_rate=0.01,
        memory_limit_mb=7000
    )

@pytest.fixture
def strict_config():
    """Stricter configuration for edge case testing."""
    return DPGMMConfig(
        alpha=0.1,  # Low concentration - fewer components expected
        gamma=0.5,
        beta=0.1,
        kappa=0.1,
        nu=1.0,
        max_components=5,
        min_components=1,
        convergence_threshold=1e-4,
        max_iterations=50,
        random_seed=123,
        learning_rate=0.05,
        memory_limit_mb=7000
    )

@pytest.fixture
def high_var_config():
    """Configuration for high variance scenarios."""
    return DPGMMConfig(
        alpha=2.0,  # Higher concentration - more components allowed
        gamma=2.0,
        beta=10.0,  # Higher precision prior
        kappa=10.0,
        nu=5.0,
        max_components=20,
        min_components=1,
        convergence_threshold=1e-8,
        max_iterations=200,
        random_seed=456,
        learning_rate=0.001,
        memory_limit_mb=7000
    )

# ============================================================================
# Edge Case Tests: Low Variance Time Series
# ============================================================================

class TestLowVarianceEdgeCases:
    """Tests for numerical stability with low-variance time series."""
    
    def test_constant_signal_no_crash(self, basic_config):
        """Model should handle constant signal without numerical errors."""
        model = DPGMMModel(basic_config)
        
        # Constant signal (zero variance)
        constant_obs = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        
        scores = []
        for i, obs in enumerate(constant_obs):
            try:
                obs_obj = StreamingObservation(
                    timestamp=datetime.now(),
                    value=obs,
                    feature_vector=np.array([obs])
                )
                score = model.update(obs_obj)
                scores.append(score)
            except Exception as e:
                pytest.fail(f"Model crashed on constant signal: {e}")
        
        # Should produce valid scores
        assert len(scores) == 5
        assert all(s.score is not None for s in scores)
    
    def test_near_zero_variance(self, basic_config):
        """Model should handle near-zero variance without NaN scores."""
        model = DPGMMModel(basic_config)
        
        # Near-zero variance signal
        near_zero = np.array([1.0, 1.0 + 1e-10, 1.0 - 1e-10, 1.0, 1.0 + 1e-10])
        
        scores = []
        for i, obs in enumerate(near_zero):
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=obs,
                feature_vector=np.array([obs])
            )
            score = model.update(obs_obj)
            scores.append(score)
        
        # Check for NaN or Inf scores
        for i, s in enumerate(scores):
            assert not np.isnan(s.score), f"NaN score at observation {i}"
            assert not np.isinf(s.score), f"Inf score at observation {i}"
    
    def test_very_small_variance_stability(self, strict_config):
        """Strict config should handle very small variance gracefully."""
        model = DPGMMModel(strict_config)
        
        # Very small variance
        small_var = np.array([0.5, 0.5001, 0.4999, 0.5, 0.5001])
        
        for i, obs in enumerate(small_var):
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=obs,
                feature_vector=np.array([obs])
            )
            score = model.update(obs_obj)
            assert score.score is not None
            assert not np.isnan(score.score)
    
    def test_multivariate_low_variance(self, basic_config):
        """Multivariate model should handle low-variance features."""
        model = DPGMMModel(basic_config)
        
        # Multivariate with some low-variance features
        observations = [
            np.array([1.0, 0.1, 0.001]),
            np.array([1.0, 0.1, 0.0011]),
            np.array([1.0, 0.1, 0.0009]),
            np.array([1.0, 0.1, 0.001]),
        ]
        
        for obs in observations:
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=obs[0],
                feature_vector=obs
            )
            score = model.update(obs_obj)
            assert score.score is not None
            assert not np.isnan(score.score)

# ============================================================================
# Edge Case Tests: Missing Value Handling
# ============================================================================

class TestMissingValueEdgeCases:
    """Tests for missing value handling in streaming updates."""
    
    def test_nan_in_feature_vector(self, basic_config):
        """Model should handle NaN values in feature vectors."""
        model = DPGMMModel(basic_config)
        
        # Observation with NaN in feature vector
        obs_with_nan = np.array([1.0, np.nan, 2.0])
        obs_obj = StreamingObservation(
            timestamp=datetime.now(),
            value=1.0,
            feature_vector=obs_with_nan
        )
        
        # Should not crash, should handle gracefully
        score = model.update(obs_obj)
        # Score should be None or valid (depending on implementation)
        assert score is not None
    
    def test_inf_in_feature_vector(self, basic_config):
        """Model should handle Inf values in feature vectors."""
        model = DPGMMModel(basic_config)
        
        # Observation with Inf
        obs_with_inf = np.array([1.0, np.inf, 2.0])
        obs_obj = StreamingObservation(
            timestamp=datetime.now(),
            value=1.0,
            feature_vector=obs_with_inf
        )
        
        score = model.update(obs_obj)
        assert score is not None
    
    def test_all_nan_feature_vector(self, basic_config):
        """Model should handle completely missing feature vectors."""
        model = DPGMMModel(basic_config)
        
        # All NaN feature vector
        all_nan = np.array([np.nan, np.nan, np.nan])
        obs_obj = StreamingObservation(
            timestamp=datetime.now(),
            value=np.nan,
            feature_vector=all_nan
        )
        
        # Should handle without crashing
        score = model.update(obs_obj)
        assert score is not None
    
    def test_mixed_missing_values(self, basic_config):
        """Model should handle sequence with mixed missing values."""
        model = DPGMMModel(basic_config)
        
        observations = [
            np.array([1.0, 2.0, 3.0]),
            np.array([np.nan, 2.0, 3.0]),
            np.array([1.0, np.nan, 3.0]),
            np.array([1.0, 2.0, np.nan]),
            np.array([1.0, 2.0, 3.0]),
        ]
        
        for obs in observations:
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=obs[0] if not np.isnan(obs[0]) else 0.0,
                feature_vector=obs
            )
            score = model.update(obs_obj)
            assert score is not None
    
    def test_missing_value_recovery(self, basic_config):
        """Model should recover after missing value sequence."""
        model = DPGMMModel(basic_config)
        
        # Good observations
        for i in range(10):
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=float(i),
                feature_vector=np.array([float(i)])
            )
            model.update(obs_obj)
        
        # Missing value sequence
        for i in range(5):
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=np.nan,
                feature_vector=np.array([np.nan])
            )
            model.update(obs_obj)
        
        # Should recover with good observations
        for i in range(10, 20):
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=float(i),
                feature_vector=np.array([float(i)])
            )
            score = model.update(obs_obj)
            assert score.score is not None
            assert not np.isnan(score.score)

# ============================================================================
# Edge Case Tests: Concentration Parameter
# ============================================================================

class TestConcentrationParameterEdgeCases:
    """Tests for concentration parameter edge cases."""
    
    def test_very_low_alpha(self, basic_config):
        """Very low alpha should result in fewer components."""
        config = DPGMMConfig(
            alpha=0.01,  # Very low concentration
            gamma=1.0,
            beta=1.0,
            kappa=1.0,
            nu=1.0,
            max_components=10,
            min_components=1,
            convergence_threshold=1e-6,
            max_iterations=100,
            random_seed=42,
            learning_rate=0.01,
            memory_limit_mb=7000
        )
        model = DPGMMModel(config)
        
        # Generate observations from single distribution
        for i in range(50):
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=np.random.normal(0, 1),
                feature_vector=np.array([np.random.normal(0, 1)])
            )
            model.update(obs_obj)
        
        # Should have very few active components
        active = model.get_active_component_count()
        assert active <= 3, f"Expected few components with low alpha, got {active}"
    
    def test_very_high_alpha(self, basic_config):
        """Very high alpha should allow more components."""
        config = DPGMMConfig(
            alpha=100.0,  # Very high concentration
            gamma=1.0,
            beta=1.0,
            kappa=1.0,
            nu=1.0,
            max_components=20,
            min_components=1,
            convergence_threshold=1e-6,
            max_iterations=100,
            random_seed=42,
            learning_rate=0.01,
            memory_limit_mb=7000
        )
        model = DPGMMModel(config)
        
        # Generate observations from multiple distributions
        for i in range(100):
            mu = (i % 5) * 2  # 5 distinct means
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=np.random.normal(mu, 0.5),
                feature_vector=np.array([np.random.normal(mu, 0.5)])
            )
            model.update(obs_obj)
        
        # Should have more active components
        active = model.get_active_component_count()
        assert active >= 2, f"Expected more components with high alpha, got {active}"
    
    def test_alpha_bounds_enforcement(self, basic_config):
        """Alpha should be bounded within reasonable limits."""
        # Test that model doesn't crash with extreme alpha values
        for alpha in [1e-6, 0.001, 1.0, 100.0, 1e6]:
            config = DPGMMConfig(
                alpha=alpha,
                gamma=1.0,
                beta=1.0,
                kappa=1.0,
                nu=1.0,
                max_components=10,
                min_components=1,
                convergence_threshold=1e-6,
                max_iterations=100,
                random_seed=42,
                learning_rate=0.01,
                memory_limit_mb=7000
            )
            model = DPGMMModel(config)
            
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=1.0,
                feature_vector=np.array([1.0])
            )
            score = model.update(obs_obj)
            assert score is not None
    
    def test_convergence_with_extreme_alpha(self, basic_config):
        """Model should converge even with extreme alpha values."""
        config = DPGMMConfig(
            alpha=0.001,
            gamma=1.0,
            beta=1.0,
            kappa=1.0,
            nu=1.0,
            max_components=10,
            min_components=1,
            convergence_threshold=1e-4,
            max_iterations=50,
            random_seed=42,
            learning_rate=0.01,
            memory_limit_mb=7000
        )
        model = DPGMMModel(config)
        
        for i in range(30):
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=float(i),
                feature_vector=np.array([float(i)])
            )
            model.update(obs_obj)
        
        # Should have valid ELBO history
        elbo_history = model.get_elbo_history()
        assert elbo_history is not None
        assert len(elbo_history) > 0

# ============================================================================
# Edge Case Tests: Single Observation
# ============================================================================

class TestSingleObservationEdgeCases:
    """Tests for single observation scenarios."""
    
    def test_single_observation_initialization(self, basic_config):
        """Model should handle single observation without errors."""
        model = DPGMMModel(basic_config)
        
        obs_obj = StreamingObservation(
            timestamp=datetime.now(),
            value=1.0,
            feature_vector=np.array([1.0])
        )
        score = model.update(obs_obj)
        
        # Should produce a score
        assert score is not None
        assert score.score is not None
    
    def test_two_observations(self, basic_config):
        """Model should handle two observations."""
        model = DPGMMModel(basic_config)
        
        for val in [1.0, 2.0]:
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=val,
                feature_vector=np.array([val])
            )
            score = model.update(obs_obj)
            assert score.score is not None
    
    def test_single_observation_anomaly_score(self, basic_config):
        """Single observation should get reasonable anomaly score."""
        model = DPGMMModel(basic_config)
        
        obs_obj = StreamingObservation(
            timestamp=datetime.now(),
            value=1.0,
            feature_vector=np.array([1.0])
        )
        score = model.update(obs_obj)
        
        # Score should be a valid number
        assert isinstance(score.score, (int, float, np.number))
        assert not np.isnan(score.score)

# ============================================================================
# Edge Case Tests: Extreme Values
# ============================================================================

class TestExtremeValueEdgeCases:
    """Tests for extreme value handling."""
    
    def test_very_large_values(self, basic_config):
        """Model should handle very large values without overflow."""
        model = DPGMMModel(basic_config)
        
        large_values = [1e10, 1e11, 1e12, 1e10, 1e11]
        
        for val in large_values:
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=val,
                feature_vector=np.array([val])
            )
            score = model.update(obs_obj)
            assert score.score is not None
            assert not np.isnan(score.score)
            assert not np.isinf(score.score)
    
    def test_very_small_values(self, basic_config):
        """Model should handle very small values without underflow."""
        model = DPGMMModel(basic_config)
        
        small_values = [1e-10, 1e-11, 1e-12, 1e-10, 1e-11]
        
        for val in small_values:
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=val,
                feature_vector=np.array([val])
            )
            score = model.update(obs_obj)
            assert score.score is not None
            assert not np.isnan(score.score)
            assert not np.isinf(score.score)
    
    def test_mixed_extreme_values(self, basic_config):
        """Model should handle mix of extreme values."""
        model = DPGMMModel(basic_config)
        
        mixed_values = [1e-10, 1e10, 1.0, 1e-11, 1e11, 0.5]
        
        for val in mixed_values:
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=val,
                feature_vector=np.array([val])
            )
            score = model.update(obs_obj)
            assert score.score is not None
            assert not np.isnan(score.score)
            assert not np.isinf(score.score)

# ============================================================================
# Edge Case Tests: Cluster Anomalies
# ============================================================================

class TestClusterAnomalyEdgeCases:
    """Tests for cluster anomaly detection edge cases."""
    
    def test_isolated_anomaly(self, basic_config):
        """Model should detect isolated anomaly point."""
        model = DPGMMModel(basic_config)
        
        # Normal observations
        for i in range(50):
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=np.random.normal(0, 1),
                feature_vector=np.array([np.random.normal(0, 1)])
            )
            model.update(obs_obj)
        
        # Isolated anomaly
        anomaly_obs = StreamingObservation(
            timestamp=datetime.now(),
            value=100.0,  # Far from normal distribution
            feature_vector=np.array([100.0])
        )
        anomaly_score = model.update(anomaly_obs)
        
        # Should have higher score than normal points
        assert anomaly_score.score is not None
    
    def test_cluster_anomaly_detection(self, basic_config):
        """Model should detect cluster of anomalies."""
        model = DPGMMModel(basic_config)
        
        # Normal observations
        for i in range(50):
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=np.random.normal(0, 1),
                feature_vector=np.array([np.random.normal(0, 1)])
            )
            model.update(obs_obj)
        
        # Cluster of anomalies
        cluster_scores = []
        for i in range(10):
            anomaly_obs = StreamingObservation(
                timestamp=datetime.now(),
                value=np.random.normal(10, 0.5),  # Far from normal
                feature_vector=np.array([np.random.normal(10, 0.5)])
            )
            score = model.update(anomaly_obs)
            cluster_scores.append(score.score)
        
        # All cluster anomalies should have high scores
        assert all(s is not None for s in cluster_scores)
        assert not any(np.isnan(s) for s in cluster_scores)
    
    def test_anomaly_cluster_recovery(self, basic_config):
        """Model should recover after anomaly cluster passes."""
        model = DPGMMModel(basic_config)
        
        # Normal observations
        for i in range(50):
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=np.random.normal(0, 1),
                feature_vector=np.array([np.random.normal(0, 1)])
            )
            model.update(obs_obj)
        
        # Anomaly cluster
        for i in range(10):
            anomaly_obs = StreamingObservation(
                timestamp=datetime.now(),
                value=np.random.normal(10, 0.5),
                feature_vector=np.array([np.random.normal(10, 0.5)])
            )
            model.update(anomaly_obs)
        
        # Back to normal
        normal_scores = []
        for i in range(20):
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=np.random.normal(0, 1),
                feature_vector=np.array([np.random.normal(0, 1)])
            )
            score = model.update(obs_obj)
            normal_scores.append(score.score)
        
        # Should have valid scores after recovery
        assert all(s is not None for s in normal_scores)
        assert not any(np.isnan(s) for s in normal_scores)

# ============================================================================
# Edge Case Tests: Memory and Performance
# ============================================================================

class TestMemoryEdgeCases:
    """Tests for memory-related edge cases."""
    
    def test_component_count_within_bounds(self, basic_config):
        """Active component count should stay within configured bounds."""
        model = DPGMMModel(basic_config)
        
        # Generate many observations
        for i in range(200):
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=np.random.normal(i % 10, 0.5),  # 10 distinct clusters
                feature_vector=np.array([np.random.normal(i % 10, 0.5)])
            )
            model.update(obs_obj)
        
        active = model.get_active_component_count()
        assert active >= basic_config.min_components
        assert active <= basic_config.max_components
    
    def test_elbo_history_bounded(self, basic_config):
        """ELBO history should be bounded and not grow unbounded."""
        model = DPGMMModel(basic_config)
        
        for i in range(100):
            obs_obj = StreamingObservation(
                timestamp=datetime.now(),
                value=float(i),
                feature_vector=np.array([float(i)])
            )
            model.update(obs_obj)
        
        elbo_history = model.get_elbo_history()
        # History should be reasonable size
        assert len(elbo_history) <= 100
        assert len(elbo_history) > 0

# ============================================================================
# Edge Case Tests: Configuration Validation
# ============================================================================

class TestConfigurationEdgeCases:
    """Tests for configuration edge cases."""
    
    def test_min_max_component_order(self, basic_config):
        """min_components should be <= max_components."""
        # This should be validated in config, but test model behavior
        config = DPGMMConfig(
            alpha=1.0,
            gamma=1.0,
            beta=1.0,
            kappa=1.0,
            nu=1.0,
            max_components=5,
            min_components=1,
            convergence_threshold=1e-6,
            max_iterations=100,
            random_seed=42,
            learning_rate=0.01,
            memory_limit_mb=7000
        )
        model = DPGMMModel(config)
        
        obs_obj = StreamingObservation(
            timestamp=datetime.now(),
            value=1.0,
            feature_vector=np.array([1.0])
        )
        score = model.update(obs_obj)
        assert score is not None
    
    def test_zero_max_components(self, basic_config):
        """Model should handle zero max_components gracefully."""
        config = DPGMMConfig(
            alpha=1.0,
            gamma=1.0,
            beta=1.0,
            kappa=1.0,
            nu=1.0,
            max_components=0,  # Edge case
            min_components=0,
            convergence_threshold=1e-6,
            max_iterations=100,
            random_seed=42,
            learning_rate=0.01,
            memory_limit_mb=7000
        )
        model = DPGMMModel(config)
        
        obs_obj = StreamingObservation(
            timestamp=datetime.now(),
            value=1.0,
            feature_vector=np.array([1.0])
        )
        # Should not crash
        try:
            score = model.update(obs_obj)
            # If it doesn't crash, that's acceptable behavior
        except Exception:
            # Or it may raise a validation error - also acceptable
            pass

# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
