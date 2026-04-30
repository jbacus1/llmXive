"""
Threshold Calibrator Service for Anomaly Detection

Implements adaptive threshold calibration for anomaly flagging without
labeled data for real-world streaming deployment.

This module provides:
- 95th percentile threshold computation from validation split
- Anomaly rate validation against expected bounds
- Anomaly flagging logic based on calibrated thresholds
"""

import numpy as np
import logging
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ThresholdValidationResult:
    """Result of threshold validation against expected bounds."""
    passed: bool
    observed_rate: float
    expected_lower: float
    expected_upper: float
    threshold_value: float
    message: str

class ThresholdCalibrator:
    """
    Adaptive threshold calibrator for anomaly detection.
    
    Calibrates anomaly score thresholds without labeled data by using
    statistical properties of the score distribution (e.g., 95th percentile).
    
    Attributes:
        config: Configuration dictionary with threshold parameters
        validation_bounds: Expected anomaly rate bounds (lower, upper)
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the threshold calibrator.
        
        Args:
            config: Configuration dictionary containing:
                - threshold_lower_bound: Expected lower bound for anomaly rate
                - threshold_upper_bound: Expected upper bound for anomaly rate
                - percentile: Percentile for threshold computation (default 95)
                - min_validation_samples: Minimum samples required for validation
        """
        self.config = config
        self._percentile = config.get('threshold_percentile', 95)
        self._min_validation_samples = config.get('min_validation_samples', 50)
        
        # Default bounds: 0.5% to 15% anomaly rate (configurable)
        self.validation_bounds = (
            config.get('threshold_lower_bound', 0.005),
            config.get('threshold_upper_bound', 0.15)
        )
        
        logger.info(f"ThresholdCalibrator initialized with bounds: "
                   f"{self.validation_bounds[0]*100:.1f}% - {self.validation_bounds[1]*100:.1f}%")
    
    def compute_threshold(self, anomaly_scores: np.ndarray) -> float:
        """
        Compute the adaptive threshold from anomaly scores.
        
        Uses the specified percentile of the score distribution as the
        threshold for flagging anomalies.
        
        Args:
            anomaly_scores: 1D array of anomaly scores (higher = more anomalous)
        
        Returns:
            float: The computed threshold value
        
        Raises:
            ValueError: If insufficient samples or invalid scores
        """
        if len(anomaly_scores) < self._min_validation_samples:
            raise ValueError(
                f"Insufficient samples for threshold calibration: "
                f"got {len(anomaly_scores)}, need at least {self._min_validation_samples}"
            )
        
        if np.any(np.isnan(anomaly_scores)):
            logger.warning("NaN values detected in anomaly scores, will be masked")
            anomaly_scores = anomaly_scores[~np.isnan(anomaly_scores)]
        
        if len(anomaly_scores) < self._min_validation_samples:
            raise ValueError(
                f"After masking NaN: insufficient samples {len(anomaly_scores)}"
            )
        
        threshold = np.percentile(anomaly_scores, self._percentile)
        
        logger.info(f"Computed {self._percentile}th percentile threshold: {threshold:.6f} "
                   f"from {len(anomaly_scores)} scores")
        
        return float(threshold)
    
    def validate_anomaly_rate(self, 
                              anomaly_scores: np.ndarray,
                              threshold: float) -> ThresholdValidationResult:
        """
        Validate that the anomaly rate at the given threshold is within bounds.
        
        This is T066's primary responsibility: ensuring the calibrated threshold
        produces an anomaly rate that is reasonable for the use case.
        
        Args:
            anomaly_scores: 1D array of anomaly scores
            threshold: The threshold to validate against
        
        Returns:
            ThresholdValidationResult with validation status and diagnostics
        """
        if len(anomaly_scores) < self._min_validation_samples:
            return ThresholdValidationResult(
                passed=False,
                observed_rate=0.0,
                expected_lower=self.validation_bounds[0],
                expected_upper=self.validation_bounds[1],
                threshold_value=threshold,
                message=f"Insufficient samples: {len(anomaly_scores)} < {self._min_validation_samples}"
            )
        
        # Compute observed anomaly rate
        anomaly_flags = anomaly_scores >= threshold
        observed_rate = float(np.mean(anomaly_flags))
        
        # Check bounds
        lower_bound, upper_bound = self.validation_bounds
        passed = lower_bound <= observed_rate <= upper_bound
        
        # Generate validation message
        if passed:
            message = (
                f"Anomaly rate {observed_rate*100:.2f}% is within expected bounds "
                f"({lower_bound*100:.1f}% - {upper_bound*100:.1f}%)"
            )
        else:
            if observed_rate < lower_bound:
                message = (
                    f"Anomaly rate {observed_rate*100:.2f}% is BELOW expected lower bound "
                    f"({lower_bound*100:.1f}%). Consider lowering threshold percentile."
                )
            else:
                message = (
                    f"Anomaly rate {observed_rate*100:.2f}% is ABOVE expected upper bound "
                    f"({upper_bound*100:.1f}%). Consider raising threshold percentile."
                )
        
        logger.info(f"Threshold validation: {'PASSED' if passed else 'FAILED'} - {message}")
        
        return ThresholdValidationResult(
            passed=passed,
            observed_rate=observed_rate,
            expected_lower=lower_bound,
            expected_upper=upper_bound,
            threshold_value=threshold,
            message=message
        )
    
    def calibrate_and_validate(self, 
                               anomaly_scores: np.ndarray,
                               target_anomaly_rate: Optional[float] = None) -> Tuple[float, ThresholdValidationResult]:
        """
        Full calibration pipeline: compute threshold and validate rate.
        
        If target_anomaly_rate is provided, iteratively adjusts percentile
        to achieve the target rate (within reasonable bounds).
        
        Args:
            anomaly_scores: 1D array of anomaly scores
            target_anomaly_rate: Optional target rate (0.01-0.20) for iterative adjustment
        
        Returns:
            Tuple of (threshold, validation_result)
        """
        # Initial threshold computation
        threshold = self.compute_threshold(anomaly_scores)
        
        # Initial validation
        result = self.validate_anomaly_rate(anomaly_scores, threshold)
        
        # If target rate specified and validation failed, try to adjust
        if target_anomaly_rate is not None and not result.passed:
            logger.info(f"Attempting to adjust threshold for target rate: {target_anomaly_rate*100:.1f}%")
            threshold = self._adjust_threshold_for_target(
                anomaly_scores, target_anomaly_rate
            )
            result = self.validate_anomaly_rate(anomaly_scores, threshold)
        
        return threshold, result
    
    def _adjust_threshold_for_target(self, 
                                     anomaly_scores: np.ndarray,
                                     target_rate: float) -> float:
        """
        Iteratively adjust percentile to achieve target anomaly rate.
        
        Args:
            anomaly_scores: 1D array of anomaly scores
            target_rate: Target anomaly rate (e.g., 0.05 for 5%)
        
        Returns:
            float: Adjusted threshold
        """
        # Clamp target rate to reasonable bounds
        target_rate = np.clip(target_rate, 0.01, 0.50)
        
        # Binary search for appropriate percentile
        low_pct, high_pct = 50, 99.9
        best_threshold = np.percentile(anomaly_scores, 95)
        
        for _ in range(20):  # Max iterations
            mid_pct = (low_pct + high_pct) / 2
            threshold = np.percentile(anomaly_scores, mid_pct)
            rate = float(np.mean(anomaly_scores >= threshold))
            
            if abs(rate - target_rate) < 0.001:  # 0.1% tolerance
                best_threshold = threshold
                break
            elif rate < target_rate:
                low_pct = mid_pct
            else:
                high_pct = mid_pct
            best_threshold = threshold
        
        logger.info(f"Adjusted threshold to {best_threshold:.6f} for target rate {target_rate*100:.1f}%")
        return best_threshold
    
    def get_validation_report(self, 
                              anomaly_scores: np.ndarray,
                              threshold: float) -> Dict:
        """
        Generate a comprehensive validation report.
        
        Args:
            anomaly_scores: 1D array of anomaly scores
            threshold: Threshold to report on
        
        Returns:
            Dict with validation statistics and diagnostics
        """
        result = self.validate_anomaly_rate(anomaly_scores, threshold)
        
        return {
            'threshold': result.threshold_value,
            'observed_anomaly_rate': result.observed_rate,
            'expected_rate_lower_bound': result.expected_lower,
            'expected_rate_upper_bound': result.expected_upper,
            'validation_passed': result.passed,
            'validation_message': result.message,
            'score_statistics': {
                'min': float(np.min(anomaly_scores)),
                'max': float(np.max(anomaly_scores)),
                'mean': float(np.mean(anomaly_scores)),
                'median': float(np.median(anomaly_scores)),
                'std': float(np.std(anomaly_scores)),
                'count': int(len(anomaly_scores))
            }
        }

# Convenience function for quick validation
def validate_threshold_bounds(anomaly_scores: np.ndarray,
                              threshold: float,
                              expected_lower: float = 0.005,
                              expected_upper: float = 0.15) -> bool:
    """
    Quick validation that threshold produces acceptable anomaly rate.
    
    Args:
        anomaly_scores: 1D array of anomaly scores
        threshold: Threshold value to validate
        expected_lower: Lower bound for acceptable anomaly rate
        expected_upper: Upper bound for acceptable anomaly rate
    
    Returns:
        bool: True if rate is within bounds
    """
    if len(anomaly_scores) == 0:
        return False
    
    rate = float(np.mean(anomaly_scores >= threshold))
    return expected_lower <= rate <= expected_upper