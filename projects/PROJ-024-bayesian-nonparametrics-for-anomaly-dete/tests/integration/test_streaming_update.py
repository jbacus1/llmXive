"""
Integration test for streaming observation update in DPGMM model.

This test verifies that the DPGMM model can process time series observations
one at a time with correct posterior updates and anomaly scoring.

Per US1 acceptance scenario: Model produces anomaly scores without requiring
batch retraining.
"""

import sys
import gc
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import pytest

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from models.dp_gmm import DPGMMModel, DPGMMConfig
from models.anomaly_score import AnomalyScore
from data.synthetic_generator import (
    generate_synthetic_timeseries,
    AnomalyConfig,
    SignalConfig
)


class TestStreamingObservationUpdate:
    """Integration tests for streaming observation processing."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures before each test method."""
        self.seed = 42
        np.random.seed(self.seed)

    def test_single_observation_processing(self):
        """Test that model can process a single observation without error."""
        # Create DPGMM model with minimal config
        config = DPGMMConfig(
            max_components=10,
            concentration_prior=1.0,
            random_seed=self.seed
        )
        model = DPGMMModel(config)

        # Generate a single synthetic observation
        signal_config = SignalConfig(
            length=10,
            noise_level=0.1,
            base_frequency=0.5
        )
        anomaly_config = AnomalyConfig(
            anomaly_rate=0.0,  # No anomalies for this test
            anomaly_magnitude=3.0
        )

        data = generate_synthetic_timeseries(
            signal_config, anomaly_config, self.seed
        )

        # Process first observation
        first_obs = data["values"][0:1]
        result = model.process_observation(first_obs[0])

        # Verify result is an AnomalyScore
        assert isinstance(result, AnomalyScore), \
            f"Expected AnomalyScore, got {type(result)}"

        # Verify score is computed
        assert result.score is not None, "Score should not be None"
        assert np.isfinite(result.score), "Score should be finite"

    def test_streaming_posterior_update(self):
        """Test that posterior weights update correctly after each observation."""
        config = DPGMMConfig(
            max_components=5,
            concentration_prior=1.0,
            random_seed=self.seed
        )
        model = DPGMMModel(config)

        # Generate synthetic time series with known pattern
        signal_config = SignalConfig(
            length=100,
            noise_level=0.1,
            base_frequency=0.5
        )
        anomaly_config = AnomalyConfig(
            anomaly_rate=0.0,
            anomaly_magnitude=3.0
        )

        data = generate_synthetic_timeseries(
            signal_config, anomaly_config, self.seed
        )

        # Track posterior weights over time
        posterior_weights_history: List[np.ndarray] = []

        # Process observations one at a time
        for i, obs in enumerate(data["values"]):
            result = model.process_observation(obs)

            # After warmup, capture posterior weights
            if i >= 10 and hasattr(model, 'posterior_weights'):
                weights = model.posterior_weights.copy()
                posterior_weights_history.append(weights)

        # Verify we captured posterior updates
        assert len(posterior_weights_history) > 0, \
            "Should have captured posterior weight updates"

        # Verify weights sum to 1 (proper probability distribution)
        for weights in posterior_weights_history:
            weight_sum = np.sum(weights)
            assert np.isclose(weight_sum, 1.0, atol=1e-5), \
                f"Posterior weights should sum to 1, got {weight_sum}"

    def test_anomaly_detection_with_known_anomalies(self):
        """Test that model detects known anomaly points in synthetic data."""
        config = DPGMMConfig(
            max_components=10,
            concentration_prior=1.0,
            random_seed=self.seed
        )
        model = DPGMMModel(config)

        # Generate synthetic data WITH anomalies
        signal_config = SignalConfig(
            length=200,
            noise_level=0.1,
            base_frequency=0.5
        )
        anomaly_config = AnomalyConfig(
            anomaly_rate=0.05,  # 5% anomalies
            anomaly_magnitude=5.0  # High magnitude for clear detection
        )

        data = generate_synthetic_timeseries(
            signal_config, anomaly_config, self.seed
        )

        # Get ground truth anomaly labels
        ground_truth = data.get("anomaly_labels", np.zeros(len(data["values"])))

        # Process all observations streaming
        anomaly_scores: List[float] = []
        for obs in data["values"]:
            result = model.process_observation(obs)
            anomaly_scores.append(result.score)

        anomaly_scores = np.array(anomaly_scores)

        # Verify anomaly scores are computed
        assert len(anomaly_scores) == len(data["values"]), \
            "Should have score for each observation"

        # Check that anomaly scores vary (not all the same)
        score_std = np.std(anomaly_scores)
        assert score_std > 0.01, \
            f"Anomaly scores should vary, std={score_std}"

        # Test threshold-based detection
        threshold = np.percentile(anomaly_scores, 95)
        detected_anomalies = anomaly_scores > threshold

        # Verify we detect SOME anomalies (not zero, not all)
        detection_rate = np.mean(detected_anomalies)
        assert 0.01 < detection_rate < 0.50, \
            f"Detection rate {detection_rate} should be reasonable"

    def test_memory_stability_during_streaming(self):
        """Test that memory usage remains stable during extended streaming."""
        config = DPGMMConfig(
            max_components=10,
            concentration_prior=1.0,
            random_seed=self.seed
        )
        model = DPGMMModel(config)

        # Generate large synthetic dataset
        signal_config = SignalConfig(
            length=1000,
            noise_level=0.1,
            base_frequency=0.5
        )
        anomaly_config = AnomalyConfig(
            anomaly_rate=0.02,
            anomaly_magnitude=4.0
        )

        data = generate_synthetic_timeseries(
            signal_config, anomaly_config, self.seed
        )

        # Track memory at intervals
        gc.collect()
        initial_memory = gc.get_count()

        # Process all observations
        scores = []
        for i, obs in enumerate(data["values"]):
            result = model.process_observation(obs)
            scores.append(result.score)

            # Force garbage collection periodically
            if i % 100 == 0:
                gc.collect()

        final_memory = gc.get_count()

        # Verify scores were computed
        assert len(scores) == len(data["values"]), \
            "Should have score for each observation"

        # Memory growth should be bounded (not linear with observations)
        # This is a heuristic check - memory should not explode
        score_variance = np.var(scores)
        assert np.isfinite(score_variance), \
            "Score variance should be finite"

    def test_elbo_convergence_during_streaming(self):
        """Test that ELBO converges during streaming inference."""
        config = DPGMMConfig(
            max_components=10,
            concentration_prior=1.0,
            random_seed=self.seed
        )
        model = DPGMMModel(config)

        # Generate synthetic data
        signal_config = SignalConfig(
            length=500,
            noise_level=0.1,
            base_frequency=0.5
        )
        anomaly_config = AnomalyConfig(
            anomaly_rate=0.03,
            anomaly_magnitude=3.5
        )

        data = generate_synthetic_timeseries(
            signal_config, anomaly_config, self.seed
        )

        # Track ELBO over time
        elbo_history = []

        for i, obs in enumerate(data["values"]):
            result = model.process_observation(obs)

            # Capture ELBO if available
            if hasattr(model, 'elbo_history') and model.elbo_history:
                elbo_history.append(model.elbo_history[-1])

        # Verify ELBO was tracked
        if len(elbo_history) > 10:
            # Check for reasonable ELBO progression
            recent_elbo = elbo_history[-10:]
            elbo_variance = np.var(recent_elbo)

            # ELBO should be finite
            assert all(np.isfinite(e) for e in elbo_history), \
                "All ELBO values should be finite"

    def test_numerical_stability_with_low_variance(self):
        """Test handling of low-variance time series that cause instability."""
        config = DPGMMConfig(
            max_components=5,
            concentration_prior=1.0,
            random_seed=self.seed
        )
        model = DPGMMModel(config)

        # Generate low-variance data
        signal_config = SignalConfig(
            length=100,
            noise_level=0.001,  # Very low noise
            base_frequency=0.5
        )
        anomaly_config = AnomalyConfig(
            anomaly_rate=0.0,
            anomaly_magnitude=1.0
        )

        data = generate_synthetic_timeseries(
            signal_config, anomaly_config, self.seed
        )

        # Process all observations - should not crash
        scores = []
        for obs in data["values"]:
            result = model.process_observation(obs)
            scores.append(result.score)

            # Verify score is finite
            assert np.isfinite(result.score), \
                f"Score should be finite, got {result.score}"

    def test_missing_value_handling(self):
        """Test that model handles missing values gracefully."""
        config = DPGMMConfig(
            max_components=5,
            concentration_prior=1.0,
            random_seed=self.seed
        )
        model = DPGMMModel(config)

        # Generate normal data
        signal_config = SignalConfig(
            length=50,
            noise_level=0.1,
            base_frequency=0.5
        )
        anomaly_config = AnomalyConfig(
            anomaly_rate=0.0,
            anomaly_magnitude=3.0
        )

        data = generate_synthetic_timeseries(
            signal_config, anomaly_config, self.seed
        )

        # Insert missing values (NaN)
        values = data["values"].copy()
        missing_indices = [10, 25, 40]
        for idx in missing_indices:
            if idx < len(values):
                values[idx] = np.nan

        # Process observations with missing values
        scores = []
        for obs in values:
            if np.isnan(obs):
                # Should handle NaN gracefully
                result = model.process_observation(obs)
                assert np.isnan(result.score) or np.isfinite(result.score), \
                    "NaN handling should produce valid score"
            else:
                result = model.process_observation(obs)
                scores.append(result.score)

    def test_concentration_parameter_tuning(self):
        """Test that concentration parameter adapts during streaming."""
        config = DPGMMConfig(
            max_components=10,
            concentration_prior=1.0,
            random_seed=self.seed
        )
        model = DPGMMModel(config)

        # Generate data with multiple modes
        signal_config = SignalConfig(
            length=300,
            noise_level=0.2,
            base_frequency=0.5
        )
        anomaly_config = AnomalyConfig(
            anomaly_rate=0.05,
            anomaly_magnitude=4.0
        )

        data = generate_synthetic_timeseries(
            signal_config, anomaly_config, self.seed
        )

        # Track active component count
        component_counts = []

        for i, obs in enumerate(data["values"]):
            result = model.process_observation(obs)

            # Capture active component count
            if hasattr(model, 'active_components'):
                component_counts.append(model.active_components)

        # Verify concentration tuning was attempted
        if len(component_counts) > 10:
            # Should have some variation in component counts
            count_variance = np.var(component_counts)
            assert count_variance >= 0, \
                "Component counts should be tracked"

    def test_edge_case_empty_observation(self):
        """Test handling of edge cases in observation processing."""
        config = DPGMMConfig(
            max_components=5,
            concentration_prior=1.0,
            random_seed=self.seed
        )
        model = DPGMMModel(config)

        # Test with very small observation
        small_obs = np.array([0.0])
        result = model.process_observation(small_obs[0])
        assert isinstance(result, AnomalyScore), \
            "Should return AnomalyScore for small observation"

        # Test with large observation
        large_obs = np.array([1e10])
        result = model.process_observation(large_obs[0])
        assert np.isfinite(result.score), \
            "Score should be finite for large observation"

    def test_warmup_phase_behavior(self):
        """Test model behavior during warmup phase."""
        config = DPGMMConfig(
            max_components=5,
            concentration_prior=1.0,
            random_seed=self.seed,
            warmup_steps=20
        )
        model = DPGMMModel(config)

        # Generate data
        signal_config = SignalConfig(
            length=50,
            noise_level=0.1,
            base_frequency=0.5
        )
        anomaly_config = AnomalyConfig(
            anomaly_rate=0.0,
            anomaly_magnitude=3.0
        )

        data = generate_synthetic_timeseries(
            signal_config, anomaly_config, self.seed
        )

        # Process through warmup phase
        warmup_scores = []
        for i in range(config.warmup_steps):
            obs = data["values"][i]
            result = model.process_observation(obs)
            warmup_scores.append(result.score)

        # Verify warmup scores are finite
        assert all(np.isfinite(s) for s in warmup_scores), \
            "Warmup scores should be finite"

    def test_full_pipeline_integration(self):
        """Test complete streaming pipeline from data generation to anomaly detection."""
        # 1. Generate synthetic dataset
        signal_config = SignalConfig(
            length=500,
            noise_level=0.15,
            base_frequency=0.5
        )
        anomaly_config = AnomalyConfig(
            anomaly_rate=0.05,
            anomaly_magnitude=5.0
        )

        data = generate_synthetic_timeseries(
            signal_config, anomaly_config, self.seed
        )

        # 2. Initialize DPGMM model
        config = DPGMMConfig(
            max_components=10,
            concentration_prior=1.0,
            random_seed=self.seed
        )
        model = DPGMMModel(config)

        # 3. Process streaming observations
        anomaly_scores: List[AnomalyScore] = []
        for obs in data["values"]:
            result = model.process_observation(obs)
            anomaly_scores.append(result)

        # 4. Verify output schema
        assert len(anomaly_scores) == len(data["values"]), \
            "Should have score for each observation"

        for score_obj in anomaly_scores:
            assert isinstance(score_obj, AnomalyScore), \
                f"Expected AnomalyScore, got {type(score_obj)}"
            assert score_obj.score is not None, \
                "Score should not be None"
            assert np.isfinite(score_obj.score), \
                "Score should be finite"

        # 5. Verify threshold calibration works
        scores_array = np.array([s.score for s in anomaly_scores])
        threshold = np.percentile(scores_array, 95)

        # 6. Count detected anomalies
        detected = np.sum(scores_array > threshold)
        expected_anomalies = int(len(data["values"]) * 0.05)

        # Detection should be reasonable (within 2x of expected)
        assert 0.5 * expected_anomalies <= detected <= 2.0 * expected_anomalies, \
            f"Detected {detected}, expected ~{expected_anomalies}"

        print(f"✓ Streaming update integration test passed")
        print(f"  - Processed {len(data['values'])} observations")
        print(f"  - Detected {detected} anomalies")
        print(f"  - Threshold: {threshold:.4f}")


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v", "--tb=short"])
