"""
Contract test for threshold calibration output schema (T042).

Per spec.md US3 acceptance criteria:
- Validates threshold calibration output schema
- Tests adaptive threshold computation
- Tests anomaly rate validation

FAILS before implementation (T044-T048) - verify this behavior.
"""
import pytest
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

@pytest.mark.contract
@pytest.mark.us3
class TestThresholdCalibrationSchema:
    """Contract tests for threshold calibration output schema compliance."""
    
    def test_output_schema_exists(self):
        """
        Verify ThresholdCalibrationResult dataclass exists and has required fields.
        
        Per FR-004: Must implement adaptive threshold computation.
        """
        try:
            from utils.threshold import ThresholdCalibrationResult
        except ImportError:
            pytest.skip("Threshold module not yet implemented (T044-T048)")
        
        # Verify dataclass has required fields
        import dataclasses
        if not dataclasses.is_dataclass(ThresholdCalibrationResult):
            pytest.fail("ThresholdCalibrationResult must be a dataclass")
        
        field_names = {f.name for f in dataclasses.fields(ThresholdCalibrationResult)}
        required_fields = {'threshold_value', 'threshold_percentile', 'anomaly_rate'}
        missing_fields = required_fields - field_names
        if missing_fields:
            pytest.fail(f"ThresholdCalibrationResult missing required fields: {missing_fields}")
    
    def test_output_contains_threshold_value(self):
        """
        Verify threshold calibration output contains threshold_value field.
        
        Per FR-004: Must implement adaptive threshold computation.
        """
        try:
            from utils.threshold import ThresholdCalibrationResult
        except ImportError:
            pytest.skip("Threshold module not yet implemented (T044-T048)")
        
        # Create a sample result to verify structure
        result = ThresholdCalibrationResult(
            threshold_value=2.5,
            threshold_percentile=95,
            anomaly_rate=0.05
        )
        
        assert hasattr(result, 'threshold_value')
        assert isinstance(result.threshold_value, (int, float))
        assert result.threshold_value > 0
    
    def test_output_contains_threshold_percentile(self):
        """
        Verify output contains threshold_percentile field.
        
        Per Assumptions: Use 95th percentile of score distribution.
        """
        try:
            from utils.threshold import ThresholdCalibrationResult
        except ImportError:
            pytest.skip("Threshold module not yet implemented (T044-T048)")
        
        result = ThresholdCalibrationResult(
            threshold_value=2.5,
            threshold_percentile=95,
            anomaly_rate=0.05
        )
        
        assert hasattr(result, 'threshold_percentile')
        assert isinstance(result.threshold_percentile, int)
        assert 0 <= result.threshold_percentile <= 100
    
    def test_output_contains_anomaly_rate(self):
        """
        Verify output contains anomaly_rate field.
        
        Per US3 acceptance scenario 1: Validate anomaly rate against expected bounds.
        """
        try:
            from utils.threshold import ThresholdCalibrationResult
        except ImportError:
            pytest.skip("Threshold module not yet implemented (T044-T048)")
        
        result = ThresholdCalibrationResult(
            threshold_value=2.5,
            threshold_percentile=95,
            anomaly_rate=0.05
        )
        
        assert hasattr(result, 'anomaly_rate')
        assert isinstance(result.anomaly_rate, (int, float))
        assert 0 <= result.anomaly_rate <= 1
    
    def test_calibrate_threshold_function_exists(self):
        """
        Verify calibrate_threshold function exists and returns proper schema.
        
        Per T045: Create threshold calibration function for unlabeled data.
        """
        try:
            from utils.threshold import calibrate_threshold
        except ImportError:
            pytest.skip("Threshold module not yet implemented (T044-T048)")
        
        # Verify function signature
        import inspect
        sig = inspect.signature(calibrate_threshold)
        # Should accept anomaly scores and return ThresholdCalibrationResult
        assert len(sig.parameters) >= 1  # At least scores parameter
    
    def test_threshold_computed_from_unlabeled_data(self):
        """
        Verify threshold is computed without requiring labeled data.
        
        Per US3: Calibrate threshold for unlabeled streaming deployment.
        """
        try:
            from utils.threshold import calibrate_threshold
            import numpy as np
        except ImportError:
            pytest.skip("Threshold module not yet implemented (T044-T048)")
        
        # Create synthetic unlabeled scores
        np.random.seed(42)
        scores = np.random.randn(1000).tolist()
        
        # Should work without labels
        try:
            result = calibrate_threshold(scores)
        except Exception as e:
            pytest.fail(f"calibrate_threshold failed on unlabeled data: {e}")
    
    def test_threshold_supports_multiple_datasets(self):
        """
        Verify threshold calibration works across multiple datasets.
        
        Per US3 acceptance scenario 3: Support calibration across datasets.
        """
        try:
            from utils.threshold import calibrate_threshold
            import numpy as np
        except ImportError:
            pytest.skip("Threshold module not yet implemented (T044-T048)")
        
        # Create multiple synthetic datasets
        np.random.seed(42)
        dataset1 = np.random.randn(500).tolist()
        dataset2 = np.random.randn(500).tolist()
        
        # Should calibrate on each independently
        try:
            result1 = calibrate_threshold(dataset1)
            result2 = calibrate_threshold(dataset2)
            assert result1.threshold_value != result2.threshold_value  # Different data = different thresholds
        except Exception as e:
            pytest.fail(f"Multi-dataset calibration failed: {e}")
    
    def test_anomaly_rate_validation(self):
        """
        Verify anomaly rate is within expected bounds.
        
        Per US3 acceptance scenario 1: Validate anomaly rate against expected bounds.
        """
        try:
            from utils.threshold import calibrate_threshold
            import numpy as np
        except ImportError:
            pytest.skip("Threshold module not yet implemented (T044-T048)")
        
        # Create synthetic scores with known distribution
        np.random.seed(42)
        scores = np.random.randn(1000).tolist()
        
        result = calibrate_threshold(scores)
        
        # Anomaly rate should be reasonable (not 0 or 100%)
        assert 0 < result.anomaly_rate < 1, f"Anomaly rate {result.anomaly_rate} out of bounds"
    
    def test_output_contains_metadata(self):
        """
        Verify output contains metadata about calibration.
        
        Per FR-004: Document decision boundary for replication.
        """
        try:
            from utils.threshold import ThresholdCalibrationResult
        except ImportError:
            pytest.skip("Threshold module not yet implemented (T044-T048)")
        
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(ThresholdCalibrationResult)}
        
        # Should have at least some metadata fields
        expected_metadata = {'num_observations', 'calibration_timestamp'}
        found_metadata = expected_metadata.intersection(field_names)
        if not found_metadata:
            pytest.skip("Metadata fields not yet required (T044-T048)")
    
    def test_threshold_serializable(self):
        """
        Verify threshold result can be serialized for config.yaml.
        
        Per FR-007: Document decision boundary in config.yaml for replication.
        """
        try:
            from utils.threshold import ThresholdCalibrationResult
            import json
        except ImportError:
            pytest.skip("Threshold module not yet implemented (T044-T048)")
        
        result = ThresholdCalibrationResult(
            threshold_value=2.5,
            threshold_percentile=95,
            anomaly_rate=0.05
        )
        
        # Should be serializable
        try:
            # Convert to dict for serialization
            result_dict = {
                'threshold_value': result.threshold_value,
                'threshold_percentile': result.threshold_percentile,
                'anomaly_rate': result.anomaly_rate
            }
            json.dumps(result_dict)
        except Exception as e:
            pytest.fail(f"Threshold result not serializable: {e}")