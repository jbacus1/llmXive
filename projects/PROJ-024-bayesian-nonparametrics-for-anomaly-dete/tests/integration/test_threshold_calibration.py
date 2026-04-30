"""
Integration test for unlabeled data threshold calibration (T043).

This test verifies that the threshold calibration mechanism works correctly
on unlabeled time series data, producing reasonable anomaly rates based on
statistical properties of the scores.

Independent Test: Can be fully tested by running the model on unlabeled data
and verifying that the adaptive threshold produces reasonable anomaly rates.

Per spec.md US3 acceptance scenarios:
- US3-1: Adaptive threshold produces anomaly rate within expected bounds
- US3-2: Decision boundary documented in config.yaml
- US3-3: Threshold calibration works across multiple datasets without labels
"""

import pytest
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Import test utilities
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.synthetic_generator import (
    generate_synthetic_timeseries,
    generate_validation_dataset,
    SyntheticDataset
)
from models.time_series import TimeSeries
from utils.streaming import StreamingObservation, create_streaming_processor

# Note: threshold module will be created by T044-T048
# This test imports will fail until those tasks complete
# pytest will catch ImportError and mark test as setup error (not failure)
try:
    from utils.threshold import (
        compute_adaptive_threshold,
        calibrate_threshold_unlabeled,
        validate_anomaly_rate,
        ThresholdCalibrationResult
    )
    THRESHOLD_AVAILABLE = True
except ImportError:
    THRESHOLD_AVAILABLE = False
    # Define placeholder for type hints when module not available
    ThresholdCalibrationResult = None


class TestThresholdCalibrationIntegration:
    """Integration tests for unlabeled data threshold calibration."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.test_data_dir = Path(__file__).parent.parent / 'test_data'
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Seed for reproducibility
        self.seed = 42
        np.random.seed(self.seed)
        
        # Skip if threshold module not yet implemented
        if not THRESHOLD_AVAILABLE:
            pytest.skip("Threshold calibration module not yet implemented (T044-T048)")
    
    def test_adaptive_threshold_computation(self):
        """
        Test that adaptive threshold computation uses 95th percentile
        of score distribution on unlabeled data.
        
        Per Assumptions: Adaptive threshold computation using 95th percentile
        """
        # Generate synthetic unlabeled time series
        dataset: SyntheticDataset = generate_validation_dataset(
            n_points=1000,
            n_anomalies=50,  # 5% anomaly rate
            seed=self.seed,
            anomaly_type='point'
        )
        
        # Create time series object
        ts = TimeSeries(
            name='test_unlabeled',
            values=dataset.values,
            timestamps=dataset.timestamps
        )
        
        # Process through streaming processor to get observations
        processor = create_streaming_processor(window_size=50)
        scores = []
        
        for obs in processor.process(ts):
            # In real implementation, would compute anomaly score from DPGMM
            # For integration test, use placeholder score distribution
            score = np.abs(obs.value - np.mean(dataset.values)) / np.std(dataset.values)
            scores.append(score)
        
        scores = np.array(scores)
        
        # Test adaptive threshold computation
        threshold = compute_adaptive_threshold(
            scores=scores,
            percentile=95.0
        )
        
        # Verify threshold is at approximately 95th percentile
        actual_percentile = np.percentile(scores, 95.0)
        assert np.isclose(threshold, actual_percentile, rtol=0.01), \
            f"Threshold {threshold} should be close to 95th percentile {actual_percentile}"
        
        # Verify threshold is positive
        assert threshold > 0, "Threshold must be positive"
        
        # Save result for inspection
        result_path = self.test_data_dir / 'threshold_test_scores.npy'
        np.save(result_path, scores)
    
    def test_unlabeled_data_calibration(self):
        """
        Test threshold calibration on unlabeled data produces reasonable anomaly rates.
        
        Per US3 acceptance scenario 1: Anomaly rate validation against expected bounds
        """
        # Generate multiple synthetic datasets
        datasets = []
        for i in range(3):
            ds = generate_validation_dataset(
                n_points=500,
                n_anomalies=25,  # 5% anomaly rate
                seed=self.seed + i,
                anomaly_type='point'
            )
            datasets.append(ds)
        
        # Test calibration across all datasets
        calibration_results = []
        
        for ds in datasets:
            ts = TimeSeries(
                name=f'test_unlabeled_{ds.name}',
                values=ds.values,
                timestamps=ds.timestamps
            )
            
            # Compute scores (placeholder - would use DPGMM in production)
            processor = create_streaming_processor(window_size=30)
            scores = []
            
            for obs in processor.process(ts):
                score = np.abs(obs.value - np.mean(ds.values)) / (np.std(ds.values) + 1e-8)
                scores.append(score)
            
            scores = np.array(scores)
            
            # Calibrate threshold
            result = calibrate_threshold_unlabeled(
                scores=scores,
                target_anomaly_rate=0.05,
                min_anomaly_rate=0.01,
                max_anomaly_rate=0.10
            )
            
            calibration_results.append(result)
        
        # Verify all results have expected structure
        for result in calibration_results:
            assert hasattr(result, 'threshold'), "Result must have threshold"
            assert hasattr(result, 'anomaly_rate'), "Result must have anomaly_rate"
            assert hasattr(result, 'n_anomalies'), "Result must have n_anomalies"
            assert hasattr(result, 'n_total'), "Result must have n_total"
            
            # Verify anomaly rate within bounds
            assert result.min_anomaly_rate <= result.anomaly_rate <= result.max_anomaly_rate, \
                f"Anomaly rate {result.anomaly_rate} outside bounds [{result.min_anomaly_rate}, {result.max_anomaly_rate}]"
    
    def test_threshold_validation_bounds(self):
        """
        Test anomaly rate validation against expected bounds.
        
        Per US3 acceptance scenario 1: Anomaly rate validation against expected bounds
        """
        # Generate test scores
        np.random.seed(self.seed)
        scores = np.random.exponential(scale=2.0, size=1000)
        
        # Test with valid bounds
        valid_result = validate_anomaly_rate(
            scores=scores,
            threshold=np.percentile(scores, 95.0),
            expected_min=0.01,
            expected_max=0.10
        )
        
        assert valid_result.within_bounds, "Valid rate should be within bounds"
        
        # Test with invalid bounds
        invalid_result = validate_anomaly_rate(
            scores=scores,
            threshold=np.percentile(scores, 99.9),  # Very high threshold
            expected_min=0.01,
            expected_max=0.05  # Max is too low
        )
        
        # Rate should be below expected min
        assert not invalid_result.within_bounds or invalid_result.anomaly_rate < invalid_result.expected_min, \
            "Very high threshold should produce rate below expected min"
    
    def test_multiple_dataset_calibration(self):
        """
        Test threshold calibration across multiple datasets without labels.
        
        Per US3 acceptance scenario 3: Support for threshold calibration across multiple datasets
        """
        # Generate multiple datasets with different characteristics
        dataset_configs = [
            {'n_points': 500, 'anomaly_rate': 0.03, 'noise_level': 0.5},
            {'n_points': 1000, 'anomaly_rate': 0.05, 'noise_level': 1.0},
            {'n_points': 750, 'anomaly_rate': 0.07, 'noise_level': 1.5},
        ]
        
        all_scores = []
        
        for config in dataset_configs:
            ds = generate_validation_dataset(
                n_points=config['n_points'],
                n_anomalies=int(config['n_points'] * config['anomaly_rate']),
                seed=self.seed,
                anomaly_type='point'
            )
            
            # Compute scores
            processor = create_streaming_processor(window_size=30)
            scores = []
            
            for obs in processor.process(TimeSeries(
                name=config['name'],
                values=ds.values,
                timestamps=ds.timestamps
            )):
                score = np.abs(obs.value - np.mean(ds.values)) / (np.std(ds.values) + 1e-8)
                scores.append(score)
            
            all_scores.extend(scores)
        
        all_scores = np.array(all_scores)
        
        # Calibrate across combined scores
        result = calibrate_threshold_unlabeled(
            scores=all_scores,
            target_anomaly_rate=0.05,
            min_anomaly_rate=0.02,
            max_anomaly_rate=0.10
        )
        
        # Verify calibration succeeded
        assert result.threshold > 0, "Threshold must be positive"
        assert result.n_total == len(all_scores), "Total count must match"
        assert result.anomaly_rate <= result.max_anomaly_rate, \
            f"Anomaly rate {result.anomaly_rate} exceeds max {result.max_anomaly_rate}"
    
    def test_threshold_persistence(self):
        """
        Test that calibrated thresholds can be saved and loaded.
        
        Per FR-007: Document decision boundary in config.yaml for replication
        """
        # Generate test data
        ds = generate_validation_dataset(
            n_points=500,
            n_anomalies=25,
            seed=self.seed,
            anomaly_type='point'
        )
        
        scores = np.abs(ds.values - np.mean(ds.values)) / (np.std(ds.values) + 1e-8)
        
        # Calibrate
        result = calibrate_threshold_unlabeled(
            scores=scores,
            target_anomaly_rate=0.05,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.10
        )
        
        # Save calibration result
        save_path = self.test_data_dir / 'calibration_result.json'
        
        # Convert result to dict for JSON serialization
        result_dict = {
            'threshold': float(result.threshold),
            'anomaly_rate': float(result.anomaly_rate),
            'n_anomalies': int(result.n_anomalies),
            'n_total': int(result.n_total),
            'min_anomaly_rate': float(result.min_anomaly_rate),
            'max_anomaly_rate': float(result.max_anomaly_rate),
        }
        
        import json
        with open(save_path, 'w') as f:
            json.dump(result_dict, f, indent=2)
        
        # Load and verify
        with open(save_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['threshold'] == result_dict['threshold'], "Threshold must match"
        assert loaded['anomaly_rate'] == result_dict['anomaly_rate'], "Anomaly rate must match"
    
    def test_edge_case_low_variance(self):
        """
        Test threshold calibration handles low-variance time series.
        
        Per Edge Cases: Low-variance time series causing numerical instability
        """
        # Generate low-variance data
        np.random.seed(self.seed)
        base_signal = np.ones(500) * 10.0
        noise = np.random.normal(0, 0.001, 500)  # Very low noise
        scores = np.abs(base_signal + noise - np.mean(base_signal))
        
        # Should handle without crashing
        result = calibrate_threshold_unlabeled(
            scores=scores,
            target_anomaly_rate=0.05,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.10
        )
        
        # Verify result is valid
        assert result.threshold >= 0, "Threshold must be non-negative"
        assert result.n_total == len(scores), "Total count must match"
    
    def test_edge_case_high_anomaly_rate(self):
        """
        Test threshold calibration when actual anomaly rate is high.
        
        Should adapt threshold to maintain within expected bounds.
        """
        # Generate data with high anomaly rate
        np.random.seed(self.seed)
        normal_scores = np.random.exponential(scale=1.0, size=800)
        anomaly_scores = np.random.exponential(scale=10.0, size=200)
        scores = np.concatenate([normal_scores, anomaly_scores])
        
        # Target rate is lower than actual
        result = calibrate_threshold_unlabeled(
            scores=scores,
            target_anomaly_rate=0.05,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.10
        )
        
        # Threshold should be set to achieve target rate
        assert result.threshold > 0, "Threshold must be positive"
        assert result.anomaly_rate <= result.max_anomaly_rate, \
            "Calibrated rate should respect max bound"
    
    def test_contract_compliance(self):
        """
        Test that threshold calibration output matches contract schema.
        
        Per T042: Contract test for threshold calibration output schema
        """
        if not THRESHOLD_AVAILABLE:
            pytest.skip("Threshold module not available for contract check")
        
        # Generate test data
        ds = generate_validation_dataset(
            n_points=500,
            n_anomalies=25,
            seed=self.seed,
            anomaly_type='point'
        )
        
        scores = np.abs(ds.values - np.mean(ds.values)) / (np.std(ds.values) + 1e-8)
        
        # Calibrate
        result = calibrate_threshold_unlabeled(
            scores=scores,
            target_anomaly_rate=0.05,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.10
        )
        
        # Verify contract schema fields
        assert hasattr(result, 'threshold'), "Missing threshold field"
        assert hasattr(result, 'anomaly_rate'), "Missing anomaly_rate field"
        assert hasattr(result, 'n_anomalies'), "Missing n_anomalies field"
        assert hasattr(result, 'n_total'), "Missing n_total field"
        assert hasattr(result, 'min_anomaly_rate'), "Missing min_anomaly_rate field"
        assert hasattr(result, 'max_anomaly_rate'), "Missing max_anomaly_rate field"
        
        # Verify types
        assert isinstance(result.threshold, (int, float)), "Threshold must be numeric"
        assert isinstance(result.anomaly_rate, (int, float)), "Anomaly rate must be numeric"
        assert isinstance(result.n_anomalies, int), "n_anomalies must be integer"
        assert isinstance(result.n_total, int), "n_total must be integer"
        
        # Verify value constraints
        assert result.threshold >= 0, "Threshold must be non-negative"
        assert 0 <= result.anomaly_rate <= 1, "Anomaly rate must be between 0 and 1"
        assert result.n_anomalies >= 0, "n_anomalies must be non-negative"
        assert result.n_total > 0, "n_total must be positive"
        assert result.n_anomalies <= result.n_total, "n_anomalies cannot exceed n_total"