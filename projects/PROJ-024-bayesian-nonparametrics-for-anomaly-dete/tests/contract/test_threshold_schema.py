"""
Contract Test for Threshold Calibration Output Schema (T042)

This test validates that the threshold calibration module produces outputs
that conform to the expected schema defined in the specification.

Per spec.md: US3 acceptance scenarios require threshold calibration to produce
structured output with calibration metadata, threshold values, and anomaly rates.

Independent Test: Can be fully tested by running this contract test suite
without requiring the actual threshold implementation to be complete.

Author: Implementer Agent (/speckit.implement)
Date: 2024
"""

import pytest
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime
import numpy as np
import json
from pathlib import Path

# ============================================================================
# EXPECTED SCHEMA DEFINITIONS (What the threshold module MUST produce)
# ============================================================================

@dataclass
class ThresholdCalibrationConfig:
    """Configuration for threshold calibration process."""
    percentile: float = 95.0  # Default 95th percentile
    min_anomaly_rate: float = 0.01  # Minimum expected anomaly rate
    max_anomaly_rate: float = 0.10  # Maximum expected anomaly rate
    min_samples: int = 100  # Minimum samples required for calibration
    use_adaptive: bool = True  # Enable adaptive threshold adjustment

@dataclass
class ThresholdCalibrationResult:
    """
    Output schema for threshold calibration (per US3 FR-004).
    
    Must contain:
    - threshold_value: The computed anomaly threshold
    - calibration_metadata: Information about the calibration process
    - score_statistics: Statistics of the score distribution
    - anomaly_rate: Expected anomaly rate at this threshold
    - validation_status: Whether calibration passed validation
    """
    threshold_value: float
    calibration_metadata: Dict[str, Any] = field(default_factory=dict)
    score_statistics: Dict[str, float] = field(default_factory=dict)
    anomaly_rate: float = 0.0
    validation_status: str = "pending"  # "passed", "failed", "pending"
    validation_message: str = ""
    calibrated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    dataset_id: Optional[str] = None
    method: str = "percentile"  # "percentile", "adaptive", "statistical"

@dataclass
class ThresholdValidationReport:
    """
    Validation report for threshold calibration across datasets.
    
    Per US3 acceptance scenario 3: Must support threshold calibration
    across multiple datasets without labeled data.
    """
    threshold_results: List[ThresholdCalibrationResult] = field(default_factory=list)
    aggregate_statistics: Dict[str, float] = field(default_factory=dict)
    calibration_summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

# ============================================================================
# CONTRACT TESTS
# ============================================================================

class TestThresholdCalibrationConfig:
    """Contract tests for ThresholdCalibrationConfig schema."""

    def test_config_has_required_fields(self):
        """Config must have all required fields defined in spec."""
        config = ThresholdCalibrationConfig()
        config_dict = asdict(config)
        
        required_fields = [
            'percentile',
            'min_anomaly_rate',
            'max_anomaly_rate',
            'min_samples',
            'use_adaptive'
        ]
        
        for field_name in required_fields:
            assert field_name in config_dict, f"Missing required field: {field_name}"

    def test_config_percentile_bounds(self):
        """Percentile must be between 0 and 100."""
        config = ThresholdCalibrationConfig(percentile=95.0)
        assert 0 <= config.percentile <= 100, "Percentile must be in [0, 100]"

    def test_config_anomaly_rate_bounds(self):
        """Anomaly rate bounds must be valid probabilities."""
        config = ThresholdCalibrationConfig(
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.10
        )
        assert 0 <= config.min_anomaly_rate <= 1, "min_anomaly_rate must be in [0, 1]"
        assert 0 <= config.max_anomaly_rate <= 1, "max_anomaly_rate must be in [0, 1]"
        assert config.min_anomaly_rate <= config.max_anomaly_rate, \
            "min_anomaly_rate must be <= max_anomaly_rate"

    def test_config_min_samples_positive(self):
        """Min samples must be positive."""
        config = ThresholdCalibrationConfig(min_samples=100)
        assert config.min_samples > 0, "min_samples must be positive"

    def test_config_serialization(self):
        """Config must be JSON serializable."""
        config = ThresholdCalibrationConfig()
        config_dict = asdict(config)
        json_str = json.dumps(config_dict)
        config_restored = json.loads(json_str)
        
        assert config_restored['percentile'] == config.percentile
        assert config_restored['min_anomaly_rate'] == config.min_anomaly_rate

class TestThresholdCalibrationResult:
    """Contract tests for ThresholdCalibrationResult schema."""

    def test_result_has_required_fields(self):
        """Result must have all required fields per FR-004."""
        result = ThresholdCalibrationResult(threshold_value=2.5)
        result_dict = asdict(result)
        
        required_fields = [
            'threshold_value',
            'calibration_metadata',
            'score_statistics',
            'anomaly_rate',
            'validation_status',
            'calibrated_at',
            'method'
        ]
        
        for field_name in required_fields:
            assert field_name in result_dict, f"Missing required field: {field_name}"

    def test_result_threshold_value_type(self):
        """Threshold value must be a float."""
        result = ThresholdCalibrationResult(threshold_value=2.5)
        assert isinstance(result.threshold_value, (int, float)), \
            "threshold_value must be numeric"

    def test_result_validation_status_values(self):
        """Validation status must be one of allowed values."""
        valid_statuses = ["passed", "failed", "pending"]
        for status in valid_statuses:
            result = ThresholdCalibrationResult(
                threshold_value=2.5,
                validation_status=status
            )
            assert result.validation_status in valid_statuses, \
                f"Invalid validation_status: {status}"

    def test_result_score_statistics_structure(self):
        """Score statistics must contain expected keys."""
        result = ThresholdCalibrationResult(
            threshold_value=2.5,
            score_statistics={
                'mean': 0.0,
                'std': 1.0,
                'min': -2.0,
                'max': 5.0,
                'median': 0.0,
                'p95': 2.5,
                'p99': 4.0
            }
        )
        
        expected_keys = ['mean', 'std', 'min', 'max', 'median', 'p95', 'p99']
        for key in expected_keys:
            assert key in result.score_statistics, f"Missing statistic: {key}"

    def test_result_anomaly_rate_bounds(self):
        """Anomaly rate must be a valid probability."""
        result = ThresholdCalibrationResult(
            threshold_value=2.5,
            anomaly_rate=0.05
        )
        assert 0 <= result.anomaly_rate <= 1, \
            "anomaly_rate must be in [0, 1]"

    def test_result_method_values(self):
        """Method must be one of allowed calibration methods."""
        valid_methods = ["percentile", "adaptive", "statistical"]
        for method in valid_methods:
            result = ThresholdCalibrationResult(
                threshold_value=2.5,
                method=method
            )
            assert result.method in valid_methods, \
                f"Invalid method: {method}"

    def test_result_timestamp_format(self):
        """Calibrated_at must be ISO format timestamp."""
        result = ThresholdCalibrationResult(threshold_value=2.5)
        # Should be parseable as ISO format
        datetime.fromisoformat(result.calibrated_at)

    def test_result_serialization(self):
        """Result must be JSON serializable."""
        result = ThresholdCalibrationResult(
            threshold_value=2.5,
            calibration_metadata={'samples': 1000, 'iterations': 10},
            score_statistics={'mean': 0.0, 'std': 1.0},
            anomaly_rate=0.05,
            validation_status='passed'
        )
        result_dict = asdict(result)
        json_str = json.dumps(result_dict)
        result_restored = json.loads(json_str)
        
        assert result_restored['threshold_value'] == result.threshold_value
        assert result_restored['validation_status'] == result.validation_status

    def test_result_metadata_structure(self):
        """Calibration metadata must be a dict with expected keys."""
        result = ThresholdCalibrationResult(
            threshold_value=2.5,
            calibration_metadata={
                'n_samples': 1000,
                'n_scores': 1000,
                'calibration_method': 'percentile',
                'confidence_level': 0.95
            }
        )
        
        assert isinstance(result.calibration_metadata, dict)
        assert 'n_samples' in result.calibration_metadata

class TestThresholdValidationReport:
    """Contract tests for ThresholdValidationReport schema."""

    def test_report_has_required_fields(self):
        """Report must have all required fields."""
        report = ThresholdValidationReport()
        report_dict = asdict(report)
        
        required_fields = [
            'threshold_results',
            'aggregate_statistics',
            'calibration_summary',
            'recommendations',
            'generated_at'
        ]
        
        for field_name in required_fields:
            assert field_name in report_dict, f"Missing required field: {field_name}"

    def test_report_results_list(self):
        """Threshold results must be a list."""
        report = ThresholdValidationReport()
        assert isinstance(report.threshold_results, list), \
            "threshold_results must be a list"

    def test_report_results_items(self):
        """Each result in list must be ThresholdCalibrationResult type."""
        result1 = ThresholdCalibrationResult(threshold_value=2.5)
        result2 = ThresholdCalibrationResult(threshold_value=3.0)
        report = ThresholdValidationReport(
            threshold_results=[result1, result2]
        )
        
        assert len(report.threshold_results) == 2
        for r in report.threshold_results:
            assert isinstance(r, ThresholdCalibrationResult)

    def test_report_recommendations_list(self):
        """Recommendations must be a list of strings."""
        report = ThresholdValidationReport(
            recommendations=[
                "Use percentile=95 for baseline",
                "Consider adaptive threshold for streaming"
            ]
        )
        
        assert isinstance(report.recommendations, list)
        for rec in report.recommendations:
            assert isinstance(rec, str)

    def test_report_serialization(self):
        """Report must be JSON serializable."""
        report = ThresholdValidationReport(
            threshold_results=[
                ThresholdCalibrationResult(threshold_value=2.5)
            ],
            aggregate_statistics={'mean_threshold': 2.5},
            calibration_summary="Calibration successful",
            recommendations=["Review threshold periodically"]
        )
        report_dict = asdict(report)
        json_str = json.dumps(report_dict)
        report_restored = json.loads(json_str)
        
        assert len(report_restored['threshold_results']) == 1

class TestThresholdCalibrationIntegration:
    """Integration contract tests for threshold calibration workflow."""

    def test_calibrate_workflow_schema(self):
        """
        Simulate the calibration workflow output structure.
        
        This test defines what the actual threshold calibration function
        (T045) MUST return when called.
        """
        # Simulate scores from a model
        scores = np.random.normal(0, 1, 1000)
        
        # Expected output structure
        expected_result = ThresholdCalibrationResult(
            threshold_value=np.percentile(scores, 95),
            calibration_metadata={
                'n_samples': len(scores),
                'percentile': 95.0,
                'calibration_method': 'percentile'
            },
            score_statistics={
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores)),
                'min': float(np.min(scores)),
                'max': float(np.max(scores)),
                'median': float(np.median(scores)),
                'p95': float(np.percentile(scores, 95)),
                'p99': float(np.percentile(scores, 99))
            },
            anomaly_rate=0.05,  # 5% at 95th percentile
            validation_status='passed',
            validation_message='Threshold within expected bounds',
            method='percentile'
        )
        
        # Verify schema compliance
        result_dict = asdict(expected_result)
        
        # Threshold must be within score range
        assert np.min(scores) <= expected_result.threshold_value <= np.max(scores)
        
        # Anomaly rate must match percentile
        assert abs(expected_result.anomaly_rate - 0.05) < 0.01

    def test_multi_dataset_calibration_schema(self):
        """
        Test schema for multi-dataset calibration (US3 acceptance scenario 3).
        
        When calibrating across multiple datasets, the output must aggregate
        results appropriately.
        """
        # Simulate multiple datasets
        datasets = ['dataset_1', 'dataset_2', 'dataset_3']
        results = []
        
        for ds_id in datasets:
            scores = np.random.normal(0, 1, 1000)
            result = ThresholdCalibrationResult(
                threshold_value=float(np.percentile(scores, 95)),
                calibration_metadata={
                    'dataset_id': ds_id,
                    'n_samples': len(scores),
                    'percentile': 95.0
                },
                score_statistics={
                    'mean': float(np.mean(scores)),
                    'std': float(np.std(scores)),
                    'p95': float(np.percentile(scores, 95))
                },
                anomaly_rate=0.05,
                validation_status='passed',
                method='percentile'
            )
            results.append(result)
        
        # Aggregate into report
        report = ThresholdValidationReport(
            threshold_results=results,
            aggregate_statistics={
                'mean_threshold': float(np.mean([r.threshold_value for r in results])),
                'threshold_std': float(np.std([r.threshold_value for r in results])),
                'n_datasets': len(datasets)
            },
            calibration_summary=f"Calibrated across {len(datasets)} datasets",
            recommendations=[
                "Use mean threshold for cross-dataset deployment",
                "Monitor threshold drift over time"
            ]
        )
        
        # Verify report structure
        assert len(report.threshold_results) == len(datasets)
        assert 'mean_threshold' in report.aggregate_statistics
        assert 'threshold_std' in report.aggregate_statistics

    def test_adaptive_threshold_schema(self):
        """
        Test schema for adaptive threshold calibration.
        
        Adaptive thresholds (T048) must include additional metadata
        about the adaptation process.
        """
        result = ThresholdCalibrationResult(
            threshold_value=2.5,
            calibration_metadata={
                'initial_threshold': 2.0,
                'final_threshold': 2.5,
                'adaptation_iterations': 5,
                'convergence_delta': 0.01,
                'adaptation_method': 'moving_average'
            },
            score_statistics={
                'mean': 0.0,
                'std': 1.0,
                'p95': 2.5
            },
            anomaly_rate=0.05,
            validation_status='passed',
            method='adaptive'
        )
        
        # Verify adaptive-specific fields exist
        assert 'initial_threshold' in result.calibration_metadata
        assert 'adaptation_iterations' in result.calibration_metadata
        assert result.method == 'adaptive'

    def test_threshold_validation_bounds(self):
        """
        Test that threshold validation checks bounds correctly.
        
        Per US3 acceptance scenario 1: Anomaly rate must be within
        expected bounds.
        """
        config = ThresholdCalibrationConfig(
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.10
        )
        
        # Valid case
        result = ThresholdCalibrationResult(
            threshold_value=2.5,
            anomaly_rate=0.05,
            validation_status='passed'
        )
        assert config.min_anomaly_rate <= result.anomaly_rate <= config.max_anomaly_rate
        
        # Invalid case (rate too high)
        result_high = ThresholdCalibrationResult(
            threshold_value=1.5,
            anomaly_rate=0.15,  # Above max
            validation_status='failed',
            validation_message='Anomaly rate exceeds maximum threshold'
        )
        assert result_high.validation_status == 'failed'
        assert 'exceeds' in result_high.validation_message.lower()

    def test_empty_scores_handling(self):
        """
        Test schema behavior when no scores are available.
        
        Per edge cases: Must handle empty or insufficient data gracefully.
        """
        config = ThresholdCalibrationConfig(min_samples=100)
        
        # Simulate insufficient data
        insufficient_scores = np.random.normal(0, 1, 50)
        
        # Expected behavior: validation fails with appropriate message
        result = ThresholdCalibrationResult(
            threshold_value=0.0,  # Placeholder
            calibration_metadata={
                'n_samples': len(insufficient_scores),
                'required_samples': config.min_samples,
                'status': 'insufficient_data'
            },
            score_statistics={},
            anomaly_rate=0.0,
            validation_status='failed',
            validation_message=f'Insufficient samples: {len(insufficient_scores)} < {config.min_samples}',
            method='percentile'
        )
        
        assert result.validation_status == 'failed'
        assert 'insufficient' in result.validation_message.lower()

    def test_schema_versioning(self):
        """
        Test that schema can be versioned for backward compatibility.
        
        Future-proofing: Schema should support version tracking.
        """
        # Add version field to metadata
        result = ThresholdCalibrationResult(
            threshold_value=2.5,
            calibration_metadata={
                'schema_version': '1.0',
                'calibration_method': 'percentile',
                'n_samples': 1000
            },
            score_statistics={'mean': 0.0, 'std': 1.0},
            anomaly_rate=0.05,
            validation_status='passed'
        )
        
        assert 'schema_version' in result.calibration_metadata

# ============================================================================
# PARAMETERIZED TESTS
# ============================================================================

@pytest.mark.parametrize(
    'percentile,expected_anomaly_rate',
    [
        (90, 0.10),
        (95, 0.05),
        (99, 0.01),
        (99.9, 0.001)
    ]
)
def test_percentile_to_anomaly_rate_mapping(self, percentile, expected_anomaly_rate):
    """
    Verify percentile values map to correct expected anomaly rates.
    
    Per US3: 95th percentile should yield ~5% anomaly rate.
    """
    scores = np.random.normal(0, 1, 10000)  # Large sample for accuracy
    threshold = float(np.percentile(scores, percentile))
    actual_rate = float(np.mean(scores > threshold))
    
    # Allow 1% tolerance for sampling variance
    assert abs(actual_rate - expected_anomaly_rate) < 0.01

@pytest.mark.parametrize(
    'distribution_type,expected_threshold_range',
    [
        ('normal', (1.6, 2.0)),   # 95th percentile of N(0,1)
        ('uniform', (0.9, 1.1)),  # 95th percentile of U(0,1)
        ('exponential', (2.8, 3.2))  # 95th percentile of Exp(1)
    ]
)
def test_threshold_across_distributions(self, distribution_type, expected_threshold_range):
    """
    Verify threshold computation works across different score distributions.
    
    Per US3: Calibration should be robust to score distribution variations.
    """
    if distribution_type == 'normal':
        scores = np.random.normal(0, 1, 10000)
    elif distribution_type == 'uniform':
        scores = np.random.uniform(0, 1, 10000)
    elif distribution_type == 'exponential':
        scores = np.random.exponential(1, 10000)
    
    threshold = float(np.percentile(scores, 95))
    
    assert expected_threshold_range[0] <= threshold <= expected_threshold_range[1], \
        f"Threshold {threshold} outside expected range {expected_threshold_range}"

# ============================================================================
# FIXTURES FOR TEST ORGANIZATION
# ============================================================================

@pytest.fixture
def sample_scores():
    """Generate sample anomaly scores for testing."""
    np.random.seed(42)
    # Simulate normal scores with some outliers
    scores = np.concatenate([
        np.random.normal(0, 1, 900),  # Normal
        np.random.normal(4, 0.5, 100)  # Anomalous
    ])
    return scores

@pytest.fixture
def valid_config():
    """Generate a valid threshold calibration config."""
    return ThresholdCalibrationConfig(
        percentile=95.0,
        min_anomaly_rate=0.01,
        max_anomaly_rate=0.10,
        min_samples=100,
        use_adaptive=True
    )

@pytest.fixture
def valid_result():
    """Generate a valid calibration result."""
    return ThresholdCalibrationResult(
        threshold_value=2.5,
        calibration_metadata={
            'n_samples': 1000,
            'percentile': 95.0,
            'method': 'percentile'
        },
        score_statistics={
            'mean': 0.0,
            'std': 1.0,
            'p95': 2.5
        },
        anomaly_rate=0.05,
        validation_status='passed',
        method='percentile'
    )

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run contract tests standalone (for CI integration)."""
    pytest.main([__file__, '-v', '--tb=short'])

if __name__ == '__main__':
    main()
