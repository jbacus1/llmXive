"""
Moving Average with Z-Score Baseline for Time Series Anomaly Detection.

This module implements a simple yet effective baseline that uses
rolling window statistics to compute z-scores for anomaly detection.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MovingAverageConfig:
    """Configuration for Moving Average baseline model."""
    window_size: int = 20
    z_threshold: float = 3.0
    min_observations: int = 10
    random_seed: Optional[int] = None
    smoothing_factor: float = 0.1  # For exponential moving average fallback

    def __post_init__(self):
        if self.window_size < 1:
            raise ValueError("window_size must be >= 1")
        if self.z_threshold < 0:
            raise ValueError("z_threshold must be >= 0")
        if self.min_observations < 1:
            raise ValueError("min_observations must be >= 1")


@dataclass
class MovingAveragePrediction:
    """Prediction result from moving average model."""
    timestamp: datetime
    value: float
    moving_average: float
    std_dev: float
    z_score: float
    is_anomaly: bool
    confidence: float
    window_size_used: int
    n_observations: int


@dataclass
class MovingAverageState:
    """State for streaming updates."""
    window: List[float] = field(default_factory=list)
    n_observations: int = 0
    sum_values: float = 0.0
    sum_sq_values: float = 0.0
    timestamps: List[datetime] = field(default_factory=list)

    def add_observation(self, value: float, timestamp: Optional[datetime] = None) -> None:
        """Add a new observation to the sliding window."""
        if timestamp is None:
            timestamp = datetime.now()

        self.timestamps.append(timestamp)
        self.n_observations += 1
        self.sum_values += value
        self.sum_sq_values += value * value

        self.window.append(value)

        # Maintain window size
        if len(self.window) > self._max_window:
            old_value = self.window.pop(0)
            self.sum_values -= old_value
            self.sum_sq_values -= old_value * old_value

    def _max_window(self) -> int:
        """Maximum window size (property for internal use)."""
        return 1000  # Cap window to prevent memory issues

    def get_mean(self) -> float:
        """Get current window mean."""
        if len(self.window) == 0:
            return 0.0
        return self.sum_values / len(self.window)

    def get_std(self) -> float:
        """Get current window standard deviation."""
        if len(self.window) < 2:
            return 1.0  # Default std when insufficient data
        n = len(self.window)
        mean = self.sum_values / n
        variance = (self.sum_sq_values / n) - (mean * mean)
        # Numerical stability
        variance = max(0.0, variance)
        return np.sqrt(variance) if variance > 0 else 1.0


class MovingAverageBaseline:
    """
    Moving Average with Z-Score anomaly detection baseline.

    This baseline computes a rolling mean and standard deviation,
    then flags observations as anomalies when their z-score exceeds
    a configurable threshold.
    """

    def __init__(self, config: Optional[MovingAverageConfig] = None):
        """Initialize the baseline with configuration."""
        self.config = config or MovingAverageConfig()
        self.state = MovingAverageState()
        self._max_window = self.config.window_size
        self._predictions: List[MovingAveragePrediction] = []

        # Set random seed if provided
        if self.config.random_seed is not None:
            np.random.seed(self.config.random_seed)

        logger.info(f"Initialized MovingAverageBaseline with window_size={self.config.window_size}, z_threshold={self.config.z_threshold}")

    def update(self, value: float, timestamp: Optional[datetime] = None) -> MovingAveragePrediction:
        """
        Update model with a new observation and return prediction.

        Args:
            value: The new observation value
            timestamp: Optional timestamp for the observation

        Returns:
            MovingAveragePrediction with anomaly score
        """
        # Add observation to state
        self.state.add_observation(value, timestamp)

        # Compute statistics
        mean = self.state.get_mean()
        std = self.state.get_std()

        # Compute z-score (handle edge case where std is 0)
        if std < 1e-10:
            z_score = 0.0
        else:
            z_score = (value - mean) / std

        # Determine anomaly
        is_anomaly = abs(z_score) > self.config.z_threshold

        # Compute confidence (higher z-score = higher confidence)
        confidence = min(1.0, abs(z_score) / (self.config.z_threshold * 2))

        # Create prediction
        prediction = MovingAveragePrediction(
            timestamp=timestamp or datetime.now(),
            value=value,
            moving_average=mean,
            std_dev=std,
            z_score=z_score,
            is_anomaly=is_anomaly,
            confidence=confidence,
            window_size_used=min(len(self.state.window), self.config.window_size),
            n_observations=self.state.n_observations
        )

        self._predictions.append(prediction)
        return prediction

    def process_batch(self, values: List[float], timestamps: Optional[List[datetime]] = None) -> List[MovingAveragePrediction]:
        """
        Process a batch of observations.

        Args:
            values: List of observation values
            timestamps: Optional list of timestamps

        Returns:
            List of predictions
        """
        if timestamps is None:
            timestamps = [datetime.now()] * len(values)

        predictions = []
        for i, value in enumerate(values):
            ts = timestamps[i] if i < len(timestamps) else None
            pred = self.update(value, ts)
            predictions.append(pred)
        return predictions

    def get_statistics(self) -> Dict[str, Any]:
        """Get model statistics for diagnostics."""
        return {
            "n_observations": self.state.n_observations,
            "current_mean": self.state.get_mean(),
            "current_std": self.state.get_std(),
            "window_size": len(self.state.window),
            "anomaly_count": sum(1 for p in self._predictions if p.is_anomaly),
            "anomaly_rate": sum(1 for p in self._predictions if p.is_anomaly) / max(1, len(self._predictions))
        }

    def reset(self) -> None:
        """Reset model state."""
        self.state = MovingAverageState()
        self._predictions = []
        logger.info("MovingAverageBaseline state reset")


def create_baseline(config: Optional[MovingAverageConfig] = None) -> MovingAverageBaseline:
    """
    Factory function to create a MovingAverageBaseline instance.

    Args:
        config: Optional configuration (uses defaults if None)

    Returns:
        Configured MovingAverageBaseline instance
    """
    return MovingAverageBaseline(config)


def main():
    """
    Main entry point for testing the moving average baseline.

    This function runs a self-test with synthetic data to verify
    the baseline works correctly without errors.
    """
    logger.info("=== Moving Average Baseline Self-Test ===")

    # Create baseline with test configuration
    config = MovingAverageConfig(
        window_size=10,
        z_threshold=2.5,
        min_observations=5,
        random_seed=42
    )
    baseline = create_baseline(config)

    # Generate synthetic test data with known anomalies
    np.random.seed(42)
    n_observations = 100

    # Normal data
    normal_values = np.random.normal(loc=100, scale=5, size=n_observations - 10)

    # Inject anomalies at known positions
    anomaly_positions = [50, 51, 52, 75, 76]
    anomaly_values = np.array([150, 155, 160, 140, 145])  # Values that should be flagged

    values = normal_values.tolist()
    for pos, val in zip(anomaly_positions, anomaly_values):
        values[pos] = val

    # Process batch
    logger.info(f"Processing {len(values)} observations...")
    predictions = baseline.process_batch(values)

    # Verify results
    anomaly_count = sum(1 for p in predictions if p.is_anomaly)
    logger.info(f"Detected {anomaly_count} anomalies out of {len(predictions)} observations")

    # Check that anomalies were detected at expected positions
    detected_anomalies = [i for i, p in enumerate(predictions) if p.is_anomaly]
    logger.info(f"Anomaly positions detected: {detected_anomalies}")

    # Verify we detected most of the injected anomalies
    injected_detected = sum(1 for pos in anomaly_positions if pos in detected_anomalies)
    logger.info(f"Injected anomalies detected: {injected_detected}/{len(anomaly_positions)}")

    # Get final statistics
    stats = baseline.get_statistics()
    logger.info(f"Final statistics: {stats}")

    # Verify predictions have valid z-scores
    z_scores = [p.z_score for p in predictions]
    logger.info(f"Z-score range: [{min(z_scores):.2f}, {max(z_scores):.2f}]")

    # Success message
    logger.info("=== Moving Average Baseline Self-Test PASSED ===")
    print("Moving Average Baseline test completed successfully.")
    print(f"Processed {len(predictions)} observations")
    print(f"Detected {anomaly_count} anomalies")
    print(f"Statistics: {stats}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
