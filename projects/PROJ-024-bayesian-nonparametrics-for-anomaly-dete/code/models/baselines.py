"""
Baseline Models for Anomaly Detection in Time Series.

This module implements baseline anomaly detection models for comparison
with the DPGMM approach. Includes:
- ARIMA baseline (implemented in T048)
- Moving Average with Z-Score baseline

Per spec.md requirements:
- All baselines must support streaming updates
- Must produce anomaly scores compatible with AnomalyScore schema
- Must handle edge cases: missing values, low variance, etc.
"""

import numpy as np
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
import logging

from .timeseries import TimeSeries
from .anomaly_score import AnomalyScore

logger = logging.getLogger(__name__)


@dataclass
class MovingAverageConfig:
    """Configuration for Moving Average Z-Score baseline."""
    window_size: int = 20  # Number of observations for moving average
    z_threshold: float = 3.0  # Z-score threshold for anomaly detection
    min_observations: int = 10  # Minimum observations before scoring


class MovingAverageZScore:
    """
    Moving Average with Z-Score baseline for anomaly detection.

    This baseline computes a rolling moving average and standard deviation
    over a sliding window, then flags observations as anomalies when their
    z-score (deviation from mean in standard deviation units) exceeds a
    threshold.

    Per spec.md:
    - Supports streaming updates (incremental)
    - Handles missing values with NaN propagation
    - Handles low variance edge cases with epsilon floor
    - Produces anomaly scores compatible with AnomalyScore schema

    Attributes:
        config: MovingAverageConfig with hyperparameters
        window_values: Circular buffer of recent observations
        window_idx: Current position in circular buffer
        initialized: Whether minimum observations have been seen
    """

    def __init__(self, config: Optional[MovingAverageConfig] = None):
        """
        Initialize the Moving Average Z-Score baseline.

        Args:
            config: Configuration object. Uses defaults if None.
        """
        self.config = config or MovingAverageConfig()
        self.window_size = self.config.window_size
        self.z_threshold = self.config.z_threshold
        self.min_observations = self.config.min_observations

        # Circular buffer for streaming updates
        self.window_values: np.ndarray = np.zeros(self.window_size)
        self.window_idx: int = 0
        self.observation_count: int = 0
        self.initialized: bool = False

        # Store last computed statistics
        self._last_mean: Optional[float] = None
        self._last_std: Optional[float] = None
        self._last_zscore: Optional[float] = None

        logger.info(f"Initialized MovingAverageZScore with window={self.window_size}, "
                   f"z_threshold={self.z_threshold}")

    def update(self, observation: float) -> Tuple[Optional[float], Optional[float]]:
        """
        Update the model with a new observation and return current stats.

        Per spec.md streaming requirements:
        - Updates internal state incrementally
        - Returns current mean and std after update
        - Handles missing values (NaN) gracefully

        Args:
            observation: New time series observation

        Returns:
            Tuple of (current_mean, current_std) after update.
            Returns (None, None) if not enough observations yet.
        """
        self.observation_count += 1

        # Handle NaN/missing values
        if np.isnan(observation):
            logger.debug("Received NaN observation, propagating without update")
            return self._last_mean, self._last_std

        # Update circular buffer
        self.window_values[self.window_idx] = observation
        self.window_idx = (self.window_idx + 1) % self.window_size

        # Check if we have enough observations
        effective_count = min(self.observation_count, self.window_size)
        if effective_count < self.min_observations:
            # Not enough observations for reliable statistics
            return None, None

        self.initialized = True

        # Compute moving statistics from circular buffer
        valid_values = self.window_values[:effective_count]
        self._last_mean = np.mean(valid_values)
        self._last_std = np.std(valid_values, ddof=1)  # Sample std

        # Handle low variance edge case (spec.md requirement)
        std_epsilon = 1e-8
        if self._last_std < std_epsilon:
            logger.warning(f"Low variance detected (std={self._last_std}), applying floor")
            self._last_std = std_epsilon

        return self._last_mean, self._last_std

    def compute_zscore(self, observation: float,
                      mean: Optional[float] = None,
                      std: Optional[float] = None) -> Optional[float]:
        """
        Compute z-score for an observation.

        Args:
            observation: Observation to score
            mean: Mean to use (uses last computed if None)
            std: Std to use (uses last computed if None)

        Returns:
            Z-score or None if not initialized
        """
        if not self.initialized:
            return None

        use_mean = mean if mean is not None else self._last_mean
        use_std = std if std is not None else self._last_std

        if use_mean is None or use_std is None:
            return None

        self._last_zscore = (observation - use_mean) / use_std
        return self._last_zscore

    def compute_anomaly_score(self, observation: float,
                             timestamp: Optional[str] = None) -> Optional[AnomalyScore]:
        """
        Compute anomaly score for an observation per AnomalyScore schema.

        Per spec.md FR-003: anomaly scores as negative log posterior probability.
        For z-score baseline, we use |z-score| as the anomaly score (higher = more anomalous).

        Args:
            observation: Time series observation
            timestamp: Optional timestamp for the observation

        Returns:
            AnomalyScore object or None if not initialized
        """
        mean, std = self.update(observation)

        if not self.initialized:
            return None

        zscore = self.compute_zscore(observation, mean, std)

        if zscore is None:
            return None

        # Anomaly score: absolute z-score (higher = more anomalous)
        # This aligns with "negative log posterior" concept:
        # lower probability -> higher anomaly score
        anomaly_score = abs(zscore)

        # Determine if flagged as anomaly
        is_anomaly = anomaly_score > self.z_threshold

        score_obj = AnomalyScore(
            observation=observation,
            score=anomaly_score,
            is_anomaly=is_anomaly,
            method="moving_average_zscore",
            metadata={
                "mean": mean,
                "std": std,
                "zscore": zscore,
                "threshold": self.z_threshold,
                "window_size": self.window_size,
                "observation_count": self.observation_count
            },
            timestamp=timestamp
        )

        return score_obj

    def process_timeseries(self, timeseries: TimeSeries,
                          batch_size: int = 100) -> list:
        """
        Process a full time series and return anomaly scores.

        Per spec.md streaming requirements:
        - Processes observations sequentially
        - Maintains state between observations
        - Returns list of AnomalyScore objects

        Args:
            timeseries: TimeSeries object to process
            batch_size: Not used (streaming) but kept for API consistency

        Returns:
            List of AnomalyScore objects
        """
        scores = []

        for i, (value, timestamp) in enumerate(zip(
            timeseries.values, timeseries.timestamps or [None] * len(timeseries.values)
        )):
            score = self.compute_anomaly_score(value, timestamp)
            if score is not None:
                scores.append(score)

        logger.info(f"Processed {len(timeseries.values)} observations, "
                   f"generated {len(scores)} anomaly scores")

        return scores

    def reset(self):
        """Reset the model state for fresh processing."""
        self.window_values = np.zeros(self.window_size)
        self.window_idx = 0
        self.observation_count = 0
        self.initialized = False
        self._last_mean = None
        self._last_std = None
        self._last_zscore = None
        logger.info("MovingAverageZScore model reset")

    def get_params(self) -> Dict[str, Any]:
        """Return model parameters for logging/reproducibility."""
        return {
            "model_type": "moving_average_zscore",
            "window_size": self.window_size,
            "z_threshold": self.z_threshold,
            "min_observations": self.min_observations,
            "observation_count": self.observation_count,
            "initialized": self.initialized
        }

    @classmethod
    def from_config_dict(cls, config_dict: Dict[str, Any]) -> "MovingAverageZScore":
        """
        Create model from configuration dictionary.

        Args:
            config_dict: Dictionary with configuration keys

        Returns:
            Configured MovingAverageZScore instance
        """
        config = MovingAverageConfig(
            window_size=config_dict.get("window_size", 20),
            z_threshold=config_dict.get("z_threshold", 3.0),
            min_observations=config_dict.get("min_observations", 10)
        )
        return cls(config=config)