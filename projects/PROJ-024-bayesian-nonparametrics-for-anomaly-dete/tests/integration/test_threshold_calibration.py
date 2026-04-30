"""
Integration test for unlabeled data threshold calibration.

US3 Acceptance Scenarios:
1. Can calibrate threshold on unlabeled data and produce reasonable anomaly rates
2. Threshold calibration works across multiple datasets
3. Adaptive adjustment maintains anomaly rate within expected bounds

This test verifies that the threshold calibration pipeline works end-to-end
without requiring labeled ground truth data.
"""

import pytest
import numpy as np
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add code/src to path
code_src = Path(__file__).parent.parent.parent / "code" / "src"
sys.path.insert(0, str(code_src))

from utils.threshold import (
    ThresholdConfig,
    ThresholdCalibrationResult,
    compute_adaptive_threshold,
    calibrate_threshold_unlabeled,
    validate_anomaly_rate,
    calibrate_threshold_multi_dataset
)
from data.synthetic_generator import generate_validation_dataset


class TestThresholdCalibrationUnlabeled:
    """Integration tests for threshold calibration on unlabeled data."""
    
    def test_calibrate_threshold_basic(self):
        """Test basic threshold calibration on synthetic unlabeled data."""
        # Generate synthetic unlabeled data with known anomaly injection
        np.random.seed(42)
        n_observations = 1000
        
        # Create scores with ~5% anomalies
        normal_scores = np.random.exponential(scale=1.0, size=int(0.95 * n_observations))
        anomaly_scores = np.random.exponential(scale=5.0, size=int(0.05 * n_observations))
        scores = np.concatenate([normal_scores, anomaly_scores])
        np.random.shuffle(scores)
        
        # Calibrate threshold
        config = ThresholdConfig(
            percentile=95.0,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.10
        )
        result = calibrate_threshold_unlabeled(scores, config)
        
        # Verify result structure
        assert isinstance(result, ThresholdCalibrationResult)
        assert result.threshold > 0
        assert 0 <= result.anomaly_rate <= 1
        assert result.n_observations == n_observations
        assert result.n_anomalies <= result.n_observations
        assert result.score_mean > 0
        assert result.score_std >= 0
        
        # Verify anomaly rate is within bounds
        is_valid, message = validate_anomaly_rate(
            result.anomaly_rate,
            config.min_anomaly_rate,
            config.max_anomaly_rate
        )
        assert is_valid, f"Anomaly rate {result.anomaly_rate} not in bounds: {message}"
        
        print(f"✓ Basic calibration: threshold={result.threshold:.4f}, "
             f"rate={result.anomaly_rate:.4f}")
    
    def test_calibrate_threshold_adjusts_percentile(self):
        """Test that threshold adjusts percentile when rate is out of bounds."""
        # Create extreme case: very few anomalies
        np.random.seed(123)
        n_observations = 1000
        
        # 99% normal, 1% anomalies (below min rate)
        normal_scores = np.random.exponential(scale=1.0, size=int(0.99 * n_observations))
        anomaly_scores = np.random.exponential(scale=10.0, size=int(0.01 * n_observations))
        scores = np.concatenate([normal_scores, anomaly_scores])
        np.random.shuffle(scores)
        
        config = ThresholdConfig(
            percentile=95.0,
            min_anomaly_rate=0.05,  # Require at least 5%
            max_anomaly_rate=0.20
        )
        
        result = calibrate_threshold_unlabeled(scores, config)
        
        # Should have adjusted percentile to meet min rate
        assert result.anomaly_rate >= config.min_anomaly_rate, \
            f"Rate {result.anomaly_rate} below min {config.min_anomaly_rate}"
        assert result.anomaly_rate <= config.max_anomaly_rate, \
            f"Rate {result.anomaly_rate} above max {config.max_anomaly_rate}"
        
        print(f"✓ Percentile adjustment: rate={result.anomaly_rate:.4f}")
    
    def test_calibrate_threshold_high_anomaly_rate(self):
        """Test threshold adjustment when too many anomalies detected."""
        # Create case with many high scores
        np.random.seed(456)
        n_observations = 1000
        
        # 70% normal, 30% anomalies (above max rate)
        normal_scores = np.random.exponential(scale=1.0, size=int(0.70 * n_observations))
        anomaly_scores = np.random.exponential(scale=3.0, size=int(0.30 * n_observations))
        scores = np.concatenate([normal_scores, anomaly_scores])
        np.random.shuffle(scores)
        
        config = ThresholdConfig(
            percentile=95.0,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.15  # Max 15%
        )
        
        result = calibrate_threshold_unlabeled(scores, config)
        
        # Should have adjusted to meet max rate
        assert result.anomaly_rate <= config.max_anomaly_rate, \
            f"Rate {result.anomaly_rate} above max {config.max_anomaly_rate}"
        assert result.anomaly_rate >= config.min_anomaly_rate, \
            f"Rate {result.anomaly_rate} below min {config.min_anomaly_rate}"
        
        print(f"✓ High rate adjustment: rate={result.anomaly_rate:.4f}")
    
    def test_calibrate_threshold_minimum_observations(self):
        """Test behavior with minimum observation count."""
        np.random.seed(789)
        n_observations = 100  # At minimum
        
        normal_scores = np.random.exponential(scale=1.0, size=int(0.90 * n_observations))
        anomaly_scores = np.random.exponential(scale=5.0, size=int(0.10 * n_observations))
        scores = np.concatenate([normal_scores, anomaly_scores])
        np.random.shuffle(scores)
        
        config = ThresholdConfig(min_observations=100)
        result = calibrate_threshold_unlabeled(scores, config)
        
        assert result.n_observations == n_observations
        assert result.threshold > 0
        
        print(f"✓ Minimum observations: n={result.n_observations}")
    
    def test_calibrate_threshold_empty_array(self):
        """Test that empty score array raises appropriate error."""
        scores = np.array([])
        
        with pytest.raises(ValueError, match="Cannot compute threshold"):
            compute_adaptive_threshold(scores)
    
    def test_calibrate_threshold_multi_dataset(self):
        """Test threshold calibration across multiple datasets."""
        np.random.seed(999)
        
        # Create multiple datasets with different characteristics
        datasets = {
            'dataset_a': np.random.exponential(scale=1.0, size=1000),
            'dataset_b': np.random.exponential(scale=2.0, size=800),
            'dataset_c': np.random.exponential(scale=0.5, size=1200)
        }
        
        # Inject some anomalies into each
        for name, scores in datasets.items():
            n_anomalies = int(0.05 * len(scores))
            anomaly_values = np.random.exponential(scale=5.0, size=n_anomalies)
            indices = np.random.choice(len(scores), n_anomalies, replace=False)
            scores[indices] = anomaly_values
        
        config = ThresholdConfig(
            percentile=95.0,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.10
        )
        
        results = calibrate_threshold_multi_dataset(datasets, config)
        
        # Verify all datasets calibrated
        assert len(results) == 3
        for name, result in results.items():
            assert isinstance(result, ThresholdCalibrationResult)
            assert result.threshold > 0
            assert 0.01 <= result.anomaly_rate <= 0.10
        
        print(f"✓ Multi-dataset calibration: {len(results)} datasets")
    
    def test_calibrate_threshold_with_realistic_scores(self):
        """Test calibration with realistic anomaly score distribution."""
        # Simulate DPGMM-style scores: mostly low, some high
        np.random.seed(2024)
        n_observations = 5000
        
        # Realistic score distribution (negative log posterior)
        normal_scores = np.random.gamma(shape=2.0, scale=1.5, size=int(0.95 * n_observations))
        anomaly_scores = np.random.gamma(shape=5.0, scale=3.0, size=int(0.05 * n_observations))
        scores = np.concatenate([normal_scores, anomaly_scores])
        np.random.shuffle(scores)
        
        config = ThresholdConfig(
            percentile=95.0,
            min_anomaly_rate=0.02,
            max_anomaly_rate=0.08
        )
        
        result = calibrate_threshold_unlabeled(scores, config)
        
        # Verify reasonable statistics
        assert result.score_mean > 0
        assert result.score_std > 0
        assert result.anomaly_rate >= config.min_anomaly_rate
        assert result.anomaly_rate <= config.max_anomaly_rate
        assert result.n_observations == n_observations
        
        print(f"✓ Realistic scores: mean={result.score_mean:.2f}, "
             f"std={result.score_std:.2f}, rate={result.anomaly_rate:.4f}")
    
    def test_threshold_consistency_across_runs(self):
        """Test that threshold is reproducible with same seed."""
        np.random.seed(42)
        scores = np.random.exponential(scale=1.0, size=1000)
        np.random.seed(42)
        scores2 = np.random.exponential(scale=1.0, size=1000)
        
        config = ThresholdConfig(percentile=95.0)
        
        result1 = calibrate_threshold_unlabeled(scores, config)
        result2 = calibrate_threshold_unlabeled(scores2, config)
        
        # Should be identical with same random seed
        assert result1.threshold == result2.threshold
        assert result1.anomaly_rate == result2.anomaly_rate
        
        print("✓ Threshold consistency: reproducible with same seed")
    
    def test_calibrate_threshold_score_floor(self):
        """Test that score floor prevents numerical issues."""
        # Create scores with zeros
        scores = np.array([0.0, 0.0, 0.1, 0.2, 0.5, 1.0, 2.0])
        
        config = ThresholdConfig(
            percentile=80.0,
            score_floor=1e-6
        )
        
        result = calibrate_threshold_unlabeled(scores, config)
        
        # Threshold should be positive even with zero scores
        assert result.threshold > 0
        
        print(f"✓ Score floor: threshold={result.threshold:.6f}")
    
    def test_calibrate_threshold_result_serialization(self):
        """Test that calibration result can be serialized."""
        np.random.seed(42)
        scores = np.random.exponential(scale=1.0, size=1000)
        
        config = ThresholdConfig(percentile=95.0)
        result = calibrate_threshold_unlabeled(scores, config)
        
        # Test to_dict
        result_dict = result.to_dict()
        assert 'threshold' in result_dict
        assert 'anomaly_rate' in result_dict
        assert 'n_observations' in result_dict
        assert 'calibration_timestamp' in result_dict
        
        # Verify types
        assert isinstance(result_dict['threshold'], float)
        assert isinstance(result_dict['anomaly_rate'], float)
        assert isinstance(result_dict['n_observations'], int)
        
        print("✓ Result serialization: dict format valid")


class TestThresholdCalibrationIntegration:
    """End-to-end integration tests with DPGMM model."""
    
    @pytest.mark.skip(reason="Requires DPGMMModel implementation")
    def test_calibrate_with_streaming_dpgmm(self):
        """Test threshold calibration with actual streaming DPGMM scores."""
        # This test would:
        # 1. Generate synthetic time series with known anomalies
        # 2. Run DPGMM in streaming mode
        # 3. Collect anomaly scores
        # 4. Calibrate threshold
        # 5. Verify anomaly rate is reasonable
        pass
    
    @pytest.mark.skip(reason="Requires DPGMMModel implementation")
    def test_threshold_applied_to_new_observations(self):
        """Test that calibrated threshold works on new observations."""
        # This test would:
        # 1. Calibrate threshold on training data
        # 2. Apply threshold to test data
        # 3. Verify flagged anomalies match expected rate
        pass


def run_integration_tests():
    """Run all integration tests and report results."""
    import traceback
    
    test_class = TestThresholdCalibrationUnlabeled()
    test_methods = [m for m in dir(test_class) if m.startswith('test_')]
    
    passed = 0
    failed = 0
    
    print("=" * 70)
    print("THRESHOLD CALIBRATION INTEGRATION TESTS")
    print("=" * 70)
    
    for method_name in test_methods:
        try:
            method = getattr(test_class, method_name)
            method()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"✗ {method_name}: {e}")
            traceback.print_exc()
    
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
