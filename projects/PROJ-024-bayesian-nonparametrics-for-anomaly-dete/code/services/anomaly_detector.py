"""
Anomaly Detector Service for DPGMM-based Time Series Anomaly Detection.

This service integrates the DPGMM model with threshold calibration
to provide streaming anomaly detection with flagging logic.

Per FR-004: Flag observations when scores exceed adaptive threshold.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from code.models.anomaly_score import AnomalyScore
from code.models.timeseries import TimeSeries
from code.models.dpgmm import DPGMMModel
from code.services.threshold_calibrator import ThresholdCalibrator

logger = logging.getLogger(__name__)


@dataclass
class AnomalyFlag:
    """Represents a flagged anomaly observation."""
    timestamp: float
    value: float
    score: float
    threshold: float
    is_anomaly: bool
    uncertainty: Optional[float] = None
    cluster_id: Optional[int] = None


class AnomalyDetector:
    """
    Streaming anomaly detector that combines DPGMM scoring with
    adaptive threshold-based flagging per FR-004.

    FR-004: Flag observations when anomaly scores exceed the adaptive
    threshold computed by the ThresholdCalibrator.

    Attributes:
        dpgmm_model: The DPGMM model for computing anomaly scores.
        calibrator: The threshold calibrator for adaptive thresholds.
        current_threshold: The active anomaly threshold.
        flagged_observations: List of all flagged anomalies.
    """

    def __init__(
        self,
        dpgmm_model: DPGMMModel,
        calibrator: ThresholdCalibrator,
        default_threshold: float = 0.95,
    ):
        """
        Initialize the anomaly detector.

        Args:
            dpgmm_model: DPGMM model instance for score computation.
            calibrator: Threshold calibrator for adaptive thresholding.
            default_threshold: Default threshold if calibration not available.
        """
        self.dpgmm_model = dpgmm_model
        self.calibrator = calibrator
        self._default_threshold = default_threshold
        self._current_threshold = default_threshold
        self._flagged_observations: List[AnomalyFlag] = []
        self._score_history: List[float] = []

        logger.info(
            "AnomalyDetector initialized with default threshold=%.4f",
            self._current_threshold,
        )

    @property
    def current_threshold(self) -> float:
        """Return the current active threshold."""
        return self._current_threshold

    @property
    def flagged_observations(self) -> List[AnomalyFlag]:
        """Return list of all flagged anomalies."""
        return self._flagged_observations.copy()

    def update_threshold(self, threshold: float) -> None:
        """
        Update the anomaly threshold.

        Per FR-004, this threshold is used to flag observations
        exceeding the decision boundary.

        Args:
            threshold: New threshold value (0.0 to 1.0 for probabilities,
                      or raw score threshold depending on configuration).
        """
        if not 0.0 <= threshold <= 1.0:
            logger.warning(
                "Threshold %.4f outside [0,1] range, clamping", threshold
            )
            threshold = np.clip(threshold, 0.0, 1.0)

        old_threshold = self._current_threshold
        self._current_threshold = threshold
        logger.info(
            "Threshold updated: %.4f -> %.4f", old_threshold, threshold
        )

    def process_observation(
        self,
        observation: float,
        timestamp: Optional[float] = None,
        uncertainty: Optional[float] = None,
    ) -> AnomalyFlag:
        """
        Process a single streaming observation and flag if anomalous.

        Per FR-004: Flag observations when anomaly scores exceed the
        adaptive threshold.

        Args:
            observation: The time series observation value.
            timestamp: Optional timestamp for the observation.
            uncertainty: Optional uncertainty estimate from the model.

        Returns:
            AnomalyFlag with the score, threshold, and anomaly decision.
        """
        # Update DPGMM model with new observation (streaming)
        self.dpgmm_model.update(observation)

        # Compute anomaly score (negative log posterior probability)
        score_result = self.dpgmm_model.compute_anomaly_score(observation)
        score = score_result["score"]
        cluster_id = score_result.get("cluster_id")

        # Normalize score to [0, 1] range for threshold comparison
        # (assuming higher score = more anomalous)
        normalized_score = self._normalize_score(score)

        # Determine if this observation is anomalous per FR-004
        is_anomaly = normalized_score >= self._current_threshold

        # Create the flag record
        flag = AnomalyFlag(
            timestamp=timestamp or self.dpgmm_model.observation_count,
            value=observation,
            score=normalized_score,
            threshold=self._current_threshold,
            is_anomaly=is_anomaly,
            uncertainty=uncertainty,
            cluster_id=cluster_id,
        )

        # Track flagged observations
        if is_anomaly:
            self._flagged_observations.append(flag)
            logger.debug(
                "Anomaly flagged: timestamp=%.2f, value=%.4f, "
                "score=%.4f, threshold=%.4f",
                flag.timestamp,
                flag.value,
                flag.score,
                flag.threshold,
            )
        else:
            logger.debug(
                "Normal observation: timestamp=%.2f, value=%.4f, "
                "score=%.4f, threshold=%.4f",
                flag.timestamp,
                flag.value,
                flag.score,
                flag.threshold,
            )

        # Store score for potential threshold calibration
        self._score_history.append(normalized_score)

        return flag

    def process_time_series(
        self,
        timeseries: TimeSeries,
    ) -> List[AnomalyFlag]:
        """
        Process an entire time series in streaming fashion.

        Args:
            timeseries: TimeSeries object with observations and timestamps.

        Returns:
            List of AnomalyFlag records for all observations.
        """
        flags = []
        for i, (value, timestamp) in enumerate(
            zip(timeseries.values, timeseries.timestamps)
        ):
            if not np.isnan(value):
                flag = self.process_observation(
                    observation=value,
                    timestamp=timestamp,
                )
                flags.append(flag)
            else:
                # Handle missing values - create placeholder flag
                flag = AnomalyFlag(
                    timestamp=timestamp,
                    value=np.nan,
                    score=np.nan,
                    threshold=self._current_threshold,
                    is_anomaly=False,
                )
                flags.append(flag)
                logger.debug("Missing value at timestamp=%.2f", timestamp)

        logger.info(
            "Processed %d observations, flagged %d anomalies (%.2f%%)",
            len(flags),
            len(self._flagged_observations),
            100.0 * len(self._flagged_observations) / len(flags) if flags else 0,
        )

        return flags

    def _normalize_score(self, score: float) -> float:
        """
        Normalize raw anomaly score to [0, 1] range.

        Uses exponential normalization: 1 - exp(-score / scale)
        where scale is based on observed score statistics.

        Args:
            score: Raw anomaly score (higher = more anomalous).

        Returns:
            Normalized score in [0, 1].
        """
        if not self._score_history:
            # No history yet, use identity for first observation
            return min(max(score, 0.0), 1.0)

        # Compute scale from score history (robust to outliers)
        history_array = np.array(self._score_history)
        q75 = np.percentile(history_array, 75)
        q25 = np.percentile(history_array, 25)
        iqr = q75 - q25
        scale = max(iqr, 0.1)  # Avoid division by zero

        # Exponential normalization
        normalized = 1.0 - np.exp(-score / (scale + 1e-10))
        return float(np.clip(normalized, 0.0, 1.0))

    def calibrate_threshold_from_history(
        self,
        percentile: float = 95.0,
    ) -> float:
        """
        Calibrate threshold from score history using percentile method.

        Per FR-004, this provides an adaptive threshold without labeled data.

        Args:
            percentile: Percentile of score distribution to use as threshold.

        Returns:
            Calibrated threshold value.
        """
        if len(self._score_history) < 10:
            logger.warning(
                "Insufficient score history (%d points), using default",
                len(self._score_history),
            )
            return self._default_threshold

        threshold = float(np.percentile(self._score_history, percentile))
        self.update_threshold(threshold)
        logger.info(
            "Calibrated threshold to %.4f (%.0f percentile of %d scores)",
            threshold,
            percentile,
            len(self._score_history),
        )
        return threshold

    def get_statistics(self) -> Dict:
        """
        Get detector statistics for monitoring.

        Returns:
            Dictionary with anomaly rate, threshold, and score stats.
        """
        if not self._score_history:
            return {
                "threshold": self._current_threshold,
                "anomaly_rate": 0.0,
                "total_observations": 0,
                "flagged_anomalies": 0,
            }

        history_array = np.array(self._score_history)
        anomaly_rate = len(self._flagged_observations) / len(history_array)

        return {
            "threshold": self._current_threshold,
            "anomaly_rate": anomaly_rate,
            "total_observations": len(history_array),
            "flagged_anomalies": len(self._flagged_observations),
            "mean_score": float(np.mean(history_array)),
            "std_score": float(np.std(history_array)),
            "max_score": float(np.max(history_array)),
            "min_score": float(np.min(history_array)),
        }

    def reset(self) -> None:
        """Reset detector state for new time series processing."""
        self._flagged_observations.clear()
        self._score_history.clear()
        self._current_threshold = self._default_threshold
        logger.info("AnomalyDetector reset")
