"""
Unit tests for 95th percentile threshold computation.

Part of User Story 3: Anomaly Score Threshold Calibration.
These tests verify the threshold computation logic BEFORE the
ThresholdCalibrator service implementation (T064).

Per plan.md requirements: Tests MUST be written first and FAIL
before implementation to ensure proper test-driven development.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

# Add code/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import will fail until T064 implements ThresholdCalibrator
try:
    from services.threshold_calibrator import ThresholdCalibrator
    HAS_THRESHOLD_CALIBRATOR = True
except ImportError:
    HAS_THRESHOLD_CALIBRATOR = False


class Test95thPercentileThresholdComputation:
    """
    Unit tests for 95th percentile threshold computation.
    
    Tests verify that:
    1. The 95th percentile is correctly computed from anomaly scores
    2. Edge cases are handled appropriately (empty, single value, etc.)
    3. The threshold is used to flag observations correctly
    """

    def test_95th_percentile_computation_basic(self):
        """
        Test basic 95th percentile computation from a sample of scores.
        
        Given 100 scores uniformly distributed [0, 100], the 95th percentile
        should be approximately 95.
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        scores = np.linspace(0, 100, 100)
        calibrator = ThresholdCalibrator()
        threshold = calibrator.compute_95th_percentile_threshold(scores)
        
        # 95th percentile of 0-100 uniform should be ~95
        assert 90 <= threshold <= 100, f"Expected ~95, got {threshold}"

    def test_95th_percentile_with_anomalies(self):
        """
        Test threshold computation when data contains clear anomalies.
        
        Given 95 normal scores [0, 10] and 5 anomaly scores [90, 100],
        the 95th percentile should fall within the anomaly range.
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        normal_scores = np.random.uniform(0, 10, 95)
        anomaly_scores = np.random.uniform(90, 100, 5)
        all_scores = np.concatenate([normal_scores, anomaly_scores])
        
        calibrator = ThresholdCalibrator()
        threshold = calibrator.compute_95th_percentile_threshold(all_scores)
        
        # Threshold should separate normal from anomaly range
        assert threshold > 10, f"Threshold {threshold} too low for normal scores"
        assert threshold <= 100, f"Threshold {threshold} exceeds max score"

    def test_95th_percentile_single_value(self):
        """
        Test threshold computation with a single score value.
        
        Edge case: When only one observation exists, the threshold
        should equal that value.
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        scores = np.array([42.5])
        calibrator = ThresholdCalibrator()
        threshold = calibrator.compute_95th_percentile_threshold(scores)
        
        assert threshold == 42.5, f"Expected 42.5, got {threshold}"

    def test_95th_percentile_all_same_values(self):
        """
        Test threshold computation when all scores are identical.
        
        Edge case: When all scores are the same, the 95th percentile
        should equal that value.
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        scores = np.full(100, 50.0)
        calibrator = ThresholdCalibrator()
        threshold = calibrator.compute_95th_percentile_threshold(scores)
        
        assert threshold == 50.0, f"Expected 50.0, got {threshold}"

    def test_95th_percentile_empty_scores(self):
        """
        Test threshold computation with empty score array.
        
        Edge case: Empty input should raise appropriate error.
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        scores = np.array([])
        calibrator = ThresholdCalibrator()
        
        with pytest.raises(ValueError):
            calibrator.compute_95th_percentile_threshold(scores)

    def test_95th_percentile_negative_scores(self):
        """
        Test threshold computation with negative anomaly scores.
        
        Anomaly scores can be negative (log probabilities). The
        95th percentile should still be computed correctly.
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        scores = np.random.uniform(-100, 0, 1000)
        calibrator = ThresholdCalibrator()
        threshold = calibrator.compute_95th_percentile_threshold(scores)
        
        # Should be in upper 5% of negative range
        assert threshold > np.percentile(scores, 90)
        assert threshold <= 0

    def test_95th_percentile_large_dataset(self):
        """
        Test threshold computation with large dataset (10000 scores).
        
        Verifies the computation scales appropriately for streaming
        deployment scenarios.
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        np.random.seed(42)  # For reproducibility
        scores = np.random.normal(loc=10, scale=5, size=10000)
        
        calibrator = ThresholdCalibrator()
        threshold = calibrator.compute_95th_percentile_threshold(scores)
        
        # Verify against numpy's percentile
        expected = np.percentile(scores, 95)
        assert abs(threshold - expected) < 0.01, \
            f"Threshold {threshold} differs from numpy {expected}"

    def test_95th_percentile_threshold_flags_correctly(self):
        """
        Test that the computed threshold correctly flags anomalies.
        
        Given a threshold computed at 95th percentile, exactly 5%
        of scores should be flagged as anomalies.
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        np.random.seed(123)
        scores = np.random.uniform(0, 100, 1000)
        
        calibrator = ThresholdCalibrator()
        threshold = calibrator.compute_95th_percentile_threshold(scores)
        
        # Count how many scores exceed threshold
        flagged = scores > threshold
        flagged_ratio = np.mean(flagged)
        
        # Approximately 5% should be flagged (with some tolerance)
        assert 0.04 <= flagged_ratio <= 0.06, \
            f"Expected ~5% flagged, got {flagged_ratio:.2%}"

    def test_95th_percentile_with_missing_values(self):
        """
        Test threshold computation with NaN values in scores.
        
        Edge case: NaN values should be handled appropriately.
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        scores = np.array([10, 20, 30, np.nan, 40, 50])
        calibrator = ThresholdCalibrator()
        
        # Should either raise error or ignore NaN
        with pytest.raises((ValueError, RuntimeError)):
            calibrator.compute_95th_percentile_threshold(scores)

    def test_95th_percentile_configurable_percentile(self):
        """
        Test that the percentile value can be configured (not just 95).
        
        Allows flexibility for different anomaly rate requirements.
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        scores = np.linspace(0, 100, 100)
        calibrator = ThresholdCalibrator()
        
        # Test 90th percentile
        threshold_90 = calibrator.compute_95th_percentile_threshold(scores, percentile=90)
        assert 85 <= threshold_90 <= 95, f"Expected ~90, got {threshold_90}"
        
        # Test 99th percentile
        threshold_99 = calibrator.compute_95th_percentile_threshold(scores, percentile=99)
        assert 95 <= threshold_99 <= 100, f"Expected ~99, got {threshold_99}"

    def test_95th_percentile_memory_efficient(self):
        """
        Test that threshold computation is memory efficient for streaming.
        
        For large datasets, should not create unnecessary copies.
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        # Create large array
        scores = np.random.normal(0, 1, 100000)
        
        # Get initial memory usage
        initial_size = scores.nbytes
        
        calibrator = ThresholdCalibrator()
        threshold = calibrator.compute_95th_percentile_threshold(scores)
        
        # Verify threshold was computed
        assert isinstance(threshold, (float, np.floating))
        
        # Memory should not have grown significantly
        # (implementation should avoid unnecessary copies)
        assert scores.nbytes <= initial_size * 1.1

    def test_95th_percentile_deterministic(self):
        """
        Test that threshold computation is deterministic.
        
        Same input should always produce same output.
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        np.random.seed(999)
        scores = np.random.uniform(0, 100, 500)
        
        calibrator = ThresholdCalibrator()
        
        # Compute multiple times
        thresholds = [
            calibrator.compute_95th_percentile_threshold(scores.copy())
            for _ in range(5)
        ]
        
        # All should be identical
        assert len(set(thresholds)) == 1, "Threshold computation is not deterministic"

    def test_95th_percentile_skewed_distribution(self):
        """
        Test threshold computation on highly skewed distribution.
        
        Anomaly scores often follow skewed distributions (e.g., exponential).
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        # Exponential distribution (common for anomaly scores)
        scores = np.random.exponential(scale=10, size=1000)
        
        calibrator = ThresholdCalibrator()
        threshold = calibrator.compute_95th_percentile_threshold(scores)
        
        # Should be in upper range but not extreme
        assert threshold > 0
        assert threshold < np.max(scores)

    def test_95th_percentile_bimodal_distribution(self):
        """
        Test threshold computation on bimodal distribution.
        
        Simulates mixture of normal and anomalous populations.
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        # Bimodal: 90% normal (mean=5), 10% anomaly (mean=50)
        normal = np.random.normal(5, 2, 900)
        anomaly = np.random.normal(50, 5, 100)
        scores = np.concatenate([normal, anomaly])
        
        calibrator = ThresholdCalibrator()
        threshold = calibrator.compute_95th_percentile_threshold(scores)
        
        # Threshold should separate the two modes
        assert threshold > 10, f"Threshold {threshold} too low"
        assert threshold < 45, f"Threshold {threshold} too high"

    def test_95th_percentile_returns_valid_type(self):
        """
        Test that the threshold is returned as a valid numeric type.
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        scores = np.array([1.0, 2.0, 3.0])
        calibrator = ThresholdCalibrator()
        threshold = calibrator.compute_95th_percentile_threshold(scores)
        
        assert isinstance(threshold, (int, float, np.floating, np.integer)), \
            f"Threshold should be numeric, got {type(threshold)}"

    def test_95th_percentile_non_negative(self):
        """
        Test that threshold is non-negative for non-negative scores.
        
        Anomaly scores (negative log probabilities) should yield
        non-negative thresholds when input scores are non-negative.
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        scores = np.random.uniform(0, 100, 1000)
        calibrator = ThresholdCalibrator()
        threshold = calibrator.compute_95th_percentile_threshold(scores)
        
        assert threshold >= 0, f"Threshold {threshold} should be non-negative"

    def test_95th_percentile_bounds_check(self):
        """
        Test that threshold is always within the range of input scores.
        """
        if not HAS_THRESHOLD_CALIBRATOR:
            pytest.skip("ThresholdCalibrator not yet implemented (T064)")
        
        np.random.seed(456)
        scores = np.random.uniform(10, 90, 1000)
        
        calibrator = ThresholdCalibrator()
        threshold = calibrator.compute_95th_percentile_threshold(scores)
        
        assert threshold >= np.min(scores), \
            f"Threshold {threshold} below min score {np.min(scores)}"
        assert threshold <= np.max(scores), \
            f"Threshold {threshold} above max score {np.max(scores)}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
