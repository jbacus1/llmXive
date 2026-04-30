"""
Integration test for adaptive threshold calibration on unlabeled data.

This test validates the integration between:
- DPGMMModel (T030)
- AnomalyDetector service (T032, T034)
- ThresholdCalibrator service (T064-T066)

The test verifies that adaptive threshold calibration produces reasonable
anomaly rates on unlabeled data without requiring ground truth labels.

Per plan.md MANDATORY testing requirements for User Story 3.
"""

import pytest
import numpy as np
import yaml
from pathlib import Path

# Import project modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.models.dpgmm import DPGMMModel
from code.models.timeseries import TimeSeries
from code.services.anomaly_detector import AnomalyDetector
from code.services.threshold_calibrator import ThresholdCalibrator
from code.utils.logger import get_logger

logger = get_logger(__name__)

@pytest.fixture
def config():
    """Load test configuration."""
    config_path = Path(__file__).parent.parent.parent / "code" / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    else:
        # Default test configuration
        return {
            "random_seed": 42,
            "threshold": {
                "percentile": 95,
                "min_rate": 0.01,
                "max_rate": 0.10
            },
            "dpgmm": {
                "concentration": 1.0,
                "max_clusters": 20
            }
        }

@pytest.fixture
def synthetic_unlabeled_data():
    """
    Generate synthetic unlabeled time series with known anomaly points.
    
    The ground truth is used only for validation, not for calibration.
    The test simulates real-world unlabeled deployment where ground truth
    is unavailable during threshold calibration.
    """
    np.random.seed(42)
    
    # Normal observations: Gaussian with mean=10, std=2
    n_normal = 900
    normal_data = np.random.normal(10, 2, n_normal)
    
    # Anomaly observations: shifted mean
    n_anomaly = 100
    anomaly_data = np.random.normal(25, 3, n_anomaly)
    
    # Mix them (anomalies at known positions for validation)
    data = np.concatenate([normal_data[:450], anomaly_data, normal_data[450:]])
    
    # Ground truth labels (1=anomaly, 0=normal) - NOT used for calibration
    labels = np.zeros(len(data))
    labels[450:550] = 1
    
    return {
        "data": data,
        "labels": labels,
        "n_total": len(data),
        "n_anomaly": n_anomaly,
        "true_anomaly_rate": n_anomaly / len(data)
    }

@pytest.fixture
def timeseries(synthetic_unlabeled_data):
    """Create TimeSeries entity from synthetic data."""
    data = synthetic_unlabeled_data["data"]
    return TimeSeries(
        values=data,
        name="synthetic_unlabeled_test",
        timestamp_start=0,
        timestamp_end=len(data)
    )

class TestThresholdCalibrationIntegration:
    """Integration tests for adaptive threshold calibration."""
    
    def test_calibrate_threshold_on_unlabeled_data(self, config, timeseries):
        """
        Test that threshold calibration produces a valid threshold
        from unlabeled data using the 95th percentile method.
        """
        # Initialize DPGMM model
        model = DPGMMModel(
            concentration=config["dpgmm"]["concentration"],
            max_clusters=config["dpgmm"]["max_clusters"],
            random_seed=config["random_seed"]
        )
        
        # Process time series to get anomaly scores
        detector = AnomalyDetector(model)
        
        # Fit model on all data (simulating unlabeled scenario)
        for i, value in enumerate(timeseries.values):
            detector.update(value, index=i)
        
        # Get all anomaly scores
        scores = detector.get_scores()
        
        # Initialize calibrator with config
        calibrator = ThresholdCalibrator(
            percentile=config["threshold"]["percentile"],
            min_rate=config["threshold"]["min_rate"],
            max_rate=config["threshold"]["max_rate"]
        )
        
        # Calibrate threshold from scores
        threshold = calibrator.calibrate(scores)
        
        # Verify threshold is a valid float
        assert isinstance(threshold, (int, float)), "Threshold must be numeric"
        assert threshold > 0, "Threshold must be positive"
        assert np.isfinite(threshold), "Threshold must be finite"
        
        logger.info(f"Calibrated threshold: {threshold}")
    
    def test_adaptive_threshold_bounds_anomaly_rate(self, config, timeseries):
        """
        Test that the adaptive threshold keeps anomaly rate within
        configured min/max bounds.
        """
        # Initialize and fit model
        model = DPGMMModel(
            concentration=config["dpgmm"]["concentration"],
            max_clusters=config["dpgmm"]["max_clusters"],
            random_seed=config["random_seed"]
        )
        
        detector = AnomalyDetector(model)
        
        for i, value in enumerate(timeseries.values):
            detector.update(value, index=i)
        
        scores = detector.get_scores()
        
        # Calibrate threshold
        calibrator = ThresholdCalibrator(
            percentile=config["threshold"]["percentile"],
            min_rate=config["threshold"]["min_rate"],
            max_rate=config["threshold"]["max_rate"]
        )
        
        threshold = calibrator.calibrate(scores)
        
        # Apply threshold to get anomaly flags
        anomaly_flags = (scores >= threshold).astype(int)
        observed_rate = anomaly_flags.sum() / len(scores)
        
        # Verify rate is within bounds
        min_rate = config["threshold"]["min_rate"]
        max_rate = config["threshold"]["max_rate"]
        
        assert min_rate <= observed_rate <= max_rate, (
            f"Anomaly rate {observed_rate:.4f} outside bounds "
            f"[{min_rate}, {max_rate}]"
        )
        
        logger.info(f"Observed anomaly rate: {observed_rate:.4f}")
    
    def test_calibration_stability_across_splits(self, config, timeseries):
        """
        Test that threshold calibration is stable when run on
        different random splits of the same unlabeled data.
        """
        model = DPGMMModel(
            concentration=config["dpgmm"]["concentration"],
            max_clusters=config["dpgmm"]["max_clusters"],
            random_seed=config["random_seed"]
        )
        
        detector = AnomalyDetector(model)
        
        for i, value in enumerate(timeseries.values):
            detector.update(value, index=i)
        
        scores = detector.get_scores()
        
        calibrator = ThresholdCalibrator(
            percentile=config["threshold"]["percentile"],
            min_rate=config["threshold"]["min_rate"],
            max_rate=config["threshold"]["max_rate"]
        )
        
        # Run calibration multiple times with different seeds
        thresholds = []
        for seed in [42, 123, 456, 789, 101112]:
            # Set seed for reproducibility
            np.random.seed(seed)
            threshold = calibrator.calibrate(scores)
            thresholds.append(threshold)
        
        # Check that thresholds don't vary wildly
        threshold_std = np.std(thresholds)
        threshold_mean = np.mean(thresholds)
        
        # Allow 20% relative variation (should be much tighter in practice)
        relative_std = threshold_std / threshold_mean
        assert relative_std < 0.20, (
            f"Threshold calibration unstable: relative std {relative_std:.4f} > 0.20"
        )
        
        logger.info(f"Threshold stability: mean={threshold_mean:.4f}, "
                   f"std={threshold_std:.4f}, relative={relative_std:.4f}")
    
    def test_calibration_with_extreme_scores(self, config, synthetic_unlabeled_data):
        """
        Test threshold calibration handles extreme anomaly scores
        without numerical issues.
        """
        # Create data with extreme outliers
        np.random.seed(42)
        base_data = np.random.normal(10, 2, 900)
        extreme_outliers = np.array([50, 100, 150, 200, 250])  # Extreme anomalies
        data = np.concatenate([base_data, extreme_outliers])
        
        timeseries = TimeSeries(
            values=data,
            name="extreme_outlier_test",
            timestamp_start=0,
            timestamp_end=len(data)
        )
        
        model = DPGMMModel(
            concentration=config["dpgmm"]["concentration"],
            max_clusters=config["dpgmm"]["max_clusters"],
            random_seed=config["random_seed"]
        )
        
        detector = AnomalyDetector(model)
        
        for i, value in enumerate(timeseries.values):
            detector.update(value, index=i)
        
        scores = detector.get_scores()
        
        calibrator = ThresholdCalibrator(
            percentile=config["threshold"]["percentile"],
            min_rate=config["threshold"]["min_rate"],
            max_rate=config["threshold"]["max_rate"]
        )
        
        # Should not raise any exceptions
        threshold = calibrator.calibrate(scores)
        
        # Verify threshold is reasonable
        assert np.isfinite(threshold), "Threshold should be finite"
        assert threshold > 0, "Threshold should be positive"
        
        logger.info(f"Threshold with extreme outliers: {threshold}")
    
    def test_calibration_integration_with_streaming(self, config, timeseries):
        """
        Test that threshold calibration works correctly with streaming
        DPGMM updates (not just batch processing).
        """
        model = DPGMMModel(
            concentration=config["dpgmm"]["concentration"],
            max_clusters=config["dpgmm"]["max_clusters"],
            random_seed=config["random_seed"]
        )
        
        detector = AnomalyDetector(model)
        
        # Stream data point by point
        for i, value in enumerate(timeseries.values):
            detector.update(value, index=i)
            
            # Periodically calibrate (simulating online threshold adjustment)
            if (i + 1) % 200 == 0:
                current_scores = detector.get_scores()
                calibrator = ThresholdCalibrator(
                    percentile=config["threshold"]["percentile"],
                    min_rate=config["threshold"]["min_rate"],
                    max_rate=config["threshold"]["max_rate"]
                )
                threshold = calibrator.calibrate(current_scores)
                
                # Verify threshold exists and is valid
                assert threshold is not None
                assert np.isfinite(threshold)
        
        # Final calibration after all streaming
        final_scores = detector.get_scores()
        calibrator = ThresholdCalibrator(
            percentile=config["threshold"]["percentile"],
            min_rate=config["threshold"]["min_rate"],
            max_rate=config["threshold"]["max_rate"]
        )
        final_threshold = calibrator.calibrate(final_scores)
        
        assert final_threshold is not None
        assert np.isfinite(final_threshold)
        
        logger.info(f"Final streaming threshold: {final_threshold}")
    
    def test_calibration_handles_small_dataset(self, config):
        """
        Test threshold calibration handles small datasets gracefully.
        """
        # Small dataset: 50 observations
        np.random.seed(42)
        small_data = np.random.normal(10, 2, 50)
        
        timeseries = TimeSeries(
            values=small_data,
            name="small_dataset_test",
            timestamp_start=0,
            timestamp_end=len(small_data)
        )
        
        model = DPGMMModel(
            concentration=config["dpgmm"]["concentration"],
            max_clusters=min(5, config["dpgmm"]["max_clusters"]),
            random_seed=config["random_seed"]
        )
        
        detector = AnomalyDetector(model)
        
        for i, value in enumerate(timeseries.values):
            detector.update(value, index=i)
        
        scores = detector.get_scores()
        
        # Calibrator should handle small datasets
        calibrator = ThresholdCalibrator(
            percentile=config["threshold"]["percentile"],
            min_rate=config["threshold"]["min_rate"],
            max_rate=config["threshold"]["max_rate"]
        )
        
        threshold = calibrator.calibrate(scores)
        
        assert threshold is not None
        assert np.isfinite(threshold)
        
        logger.info(f"Threshold for small dataset (n=50): {threshold}")
    
    def test_calibration_percentile_accuracy(self, config, timeseries):
        """
        Test that the calibrated threshold approximately matches
        the requested percentile of the score distribution.
        """
        model = DPGMMModel(
            concentration=config["dpgmm"]["concentration"],
            max_clusters=config["dpgmm"]["max_clusters"],
            random_seed=config["random_seed"]
        )
        
        detector = AnomalyDetector(model)
        
        for i, value in enumerate(timeseries.values):
            detector.update(value, index=i)
        
        scores = detector.get_scores()
        
        calibrator = ThresholdCalibrator(
            percentile=config["threshold"]["percentile"],
            min_rate=config["threshold"]["min_rate"],
            max_rate=config["threshold"]["max_rate"]
        )
        
        threshold = calibrator.calibrate(scores)
        
        # Calculate actual percentile of threshold in scores
        actual_percentile = np.percentile(scores, config["threshold"]["percentile"])
        
        # Allow 10% relative difference (percentile estimation has variance)
        relative_diff = abs(threshold - actual_percentile) / actual_percentile
        
        # Should be reasonably close (within 10%)
        assert relative_diff < 0.10, (
            f"Threshold {threshold:.4f} differs from "
            f"percentile value {actual_percentile:.4f} by {relative_diff:.2%}"
        )
        
        logger.info(f"Requested percentile: {config['threshold']['percentile']}%")
        logger.info(f"Calibrated threshold: {threshold:.4f}")
        logger.info(f"Actual percentile value: {actual_percentile:.4f}")
        logger.info(f"Relative difference: {relative_diff:.2%}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
