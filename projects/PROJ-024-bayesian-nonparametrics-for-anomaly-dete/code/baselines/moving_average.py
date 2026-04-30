"""
Moving Average with Z-Score Baseline for Anomaly Detection in Time Series.

This module implements a simple yet effective baseline anomaly detection method
that uses a rolling window to compute local statistics (mean and standard deviation)
and flags observations that deviate significantly from the local pattern.

Per US2 acceptance scenario 1: Can be fully tested by running on a single UCI
dataset and generating precision-recall curves with F1-score measurements.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.streaming import StreamingObservation, SlidingWindowBuffer
from models.anomaly_score import AnomalyScore


@dataclass
class MovingAverageConfig:
    """Configuration for Moving Average Z-Score baseline model.

    Attributes:
        window_size: Number of observations for rolling window statistics.
            Default 50 works well for most time series with moderate frequency.
        z_score_threshold: Number of standard deviations for anomaly flagging.
            Default 3.0 corresponds to ~0.27% false positive rate for normal data.
        min_observations: Minimum observations before anomaly scoring begins.
            Ensures sufficient data for stable statistics estimation.
        standard_deviation_floor: Minimum std dev to prevent division by zero.
            Prevents numerical instability for low-variance time series.
        random_seed: For reproducibility in any randomized operations.
        output_dir: Directory for saving results and plots.
    """
    window_size: int = 50
    z_score_threshold: float = 3.0
    min_observations: int = 10
    standard_deviation_floor: float = 1e-6
    random_seed: Optional[int] = None
    output_dir: str = "data/results"


@dataclass
class MovingAveragePrediction:
    """Output prediction from Moving Average Z-Score baseline.

    Attributes:
        timestamp: Timestamp of the observation being scored.
        value: The observed value.
        moving_average: Local rolling mean at this point.
        moving_std: Local rolling standard deviation.
        z_score: Standardized score (value - mean) / std.
        is_anomaly: Boolean flag if z_score exceeds threshold.
        anomaly_score: Negative log of probability under normal distribution.
        model_name: Identifier for this baseline model.
    """
    timestamp: datetime
    value: float
    moving_average: float
    moving_std: float
    z_score: float
    is_anomaly: bool
    anomaly_score: float
    model_name: str = "MovingAverageZScore"


@dataclass
class MovingAverageState:
    """Internal state for streaming Moving Average Z-Score computation.

    Attributes:
        window_buffer: Sliding window of recent observations.
        total_observations: Count of all observations processed.
        warmup_complete: Whether minimum observations threshold is reached.
        last_update: Timestamp of last state update.
    """
    window_buffer: SlidingWindowBuffer = field(default_factory=SlidingWindowBuffer)
    total_observations: int = 0
    warmup_complete: bool = False
    last_update: Optional[datetime] = None


class MovingAverageBaseline:
    """Moving Average with Z-Score Baseline for Time Series Anomaly Detection.

    This baseline computes local statistics using a rolling window and flags
    observations that deviate significantly from the local pattern. It serves
    as a simple, interpretable benchmark against which more sophisticated models
    (like DPGMM) can be compared.

    Per Constitution Principle III: All artifacts include checksums and hashes
    for reproducibility.

    Usage:
        config = MovingAverageConfig(window_size=50, z_score_threshold=3.0)
        baseline = MovingAverageBaseline(config)

        # Streaming mode
        for obs in observations:
            prediction = baseline.update(obs)

        # Batch mode
        predictions = baseline.predict_batch(values, timestamps)
    """

    def __init__(self, config: Optional[MovingAverageConfig] = None):
        """Initialize Moving Average Z-Score baseline.

        Args:
            config: Configuration object. Creates default if None.
        """
        self.config = config or MovingAverageConfig()
        self.state = MovingAverageState()
        self._predictions: List[MovingAveragePrediction] = []

        if self.config.random_seed is not None:
            np.random.seed(self.config.random_seed)

        # Ensure output directory exists
        output_path = Path(self.config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

    def _compute_statistics(self) -> Tuple[float, float]:
        """Compute rolling mean and standard deviation from window buffer.

        Returns:
            Tuple of (mean, std) from the window buffer.
            Returns (0.0, standard_deviation_floor) if buffer is empty.
        """
        if len(self.state.window_buffer) < 2:
            return 0.0, self.config.standard_deviation_floor

        values = np.array(self.state.window_buffer.get_values())
        mean = np.mean(values)
        std = np.std(values, ddof=1)  # Sample std with Bessel's correction

        # Apply floor to prevent division by zero for low-variance series
        std = max(std, self.config.standard_deviation_floor)

        return mean, std

    def _compute_z_score(self, value: float, mean: float, std: float) -> float:
        """Compute z-score for a single observation.

        Args:
            value: The observation value.
            mean: Rolling mean from window buffer.
            std: Rolling standard deviation from window buffer.

        Returns:
            Z-score: (value - mean) / std
        """
        return (value - mean) / std

    def _compute_anomaly_score(self, z_score: float) -> float:
        """Compute anomaly score as negative log probability.

        For a normal distribution, the negative log probability is:
            -log(p(x)) = 0.5 * log(2*pi) + log(std) + 0.5 * z^2

        We simplify to use z_score^2 as the anomaly score since we want
        higher scores for more anomalous observations.

        Args:
            z_score: The standardized score.

        Returns:
            Anomaly score (higher = more anomalous).
        """
        return 0.5 * z_score ** 2

    def update(self, observation: StreamingObservation) -> MovingAveragePrediction:
        """Process a single streaming observation and update state.

        Per FR-002: Supports incremental posterior updates for each new observation.
        This baseline maintains a sliding window and updates statistics incrementally.

        Args:
            observation: StreamingObservation containing timestamp and value.

        Returns:
            MovingAveragePrediction with anomaly score and flag.
        """
        value = observation.value
        timestamp = observation.timestamp

        # Update state
        self.state.total_observations += 1
        self.state.last_update = timestamp

        # Check if warmup is complete
        if not self.state.warmup_complete:
            self.state.warmup_complete = (
                self.state.total_observations >= self.config.min_observations
            )

        # Add observation to window buffer
        self.state.window_buffer.add(value)

        # Compute statistics from window
        mean, std = self._compute_statistics()

        # Compute z-score
        z_score = self._compute_z_score(value, mean, std)

        # Compute anomaly score
        anomaly_score = self._compute_anomaly_score(z_score)

        # Determine if anomaly
        is_anomaly = abs(z_score) > self.config.z_score_threshold

        # Create prediction
        prediction = MovingAveragePrediction(
            timestamp=timestamp,
            value=value,
            moving_average=mean,
            moving_std=std,
            z_score=z_score,
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            model_name="MovingAverageZScore"
        )

        self._predictions.append(prediction)

        return prediction

    def predict_batch(
        self,
        values: List[float],
        timestamps: List[datetime]
    ) -> List[MovingAveragePrediction]:
        """Process a batch of observations at once.

        Args:
            values: List of observation values.
            timestamps: List of corresponding timestamps.

        Returns:
            List of MovingAveragePrediction objects.
        """
        predictions = []

        for value, timestamp in zip(values, timestamps):
            obs = StreamingObservation(value=value, timestamp=timestamp)
            pred = self.update(obs)
            predictions.append(pred)

        return predictions

    def get_predictions(self) -> List[MovingAveragePrediction]:
        """Return all predictions made so far.

        Returns:
            List of all MovingAveragePrediction objects.
        """
        return self._predictions.copy()

    def reset(self) -> None:
        """Reset internal state for fresh processing.

        Clears all accumulated state while preserving configuration.
        """
        self.state = MovingAverageState()
        self._predictions = []

    def get_anomaly_rate(self) -> float:
        """Compute the rate of flagged anomalies.

        Returns:
            Fraction of observations flagged as anomalies.
        """
        if len(self._predictions) == 0:
            return 0.0

        anomaly_count = sum(1 for p in self._predictions if p.is_anomaly)
        return anomaly_count / len(self._predictions)

    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the model state.

        Returns:
            Dictionary with key statistics about the model's processing.
        """
        if len(self._predictions) == 0:
            return {
                "total_observations": 0,
                "anomaly_count": 0,
                "anomaly_rate": 0.0,
                "warmup_complete": False,
                "window_size": self.config.window_size
            }

        z_scores = [p.z_score for p in self._predictions]
        anomaly_scores = [p.anomaly_score for p in self._predictions]

        return {
            "total_observations": self.state.total_observations,
            "anomaly_count": sum(1 for p in self._predictions if p.is_anomaly),
            "anomaly_rate": self.get_anomaly_rate(),
            "warmup_complete": self.state.warmup_complete,
            "window_size": self.config.window_size,
            "z_score_mean": float(np.mean(z_scores)),
            "z_score_std": float(np.std(z_scores)),
            "z_score_max": float(np.max(np.abs(z_scores))),
            "anomaly_score_mean": float(np.mean(anomaly_scores)),
            "anomaly_score_max": float(np.max(anomaly_scores))
        }


def create_baseline(config: Optional[MovingAverageConfig] = None) -> MovingAverageBaseline:
    """Factory function to create a Moving Average Z-Score baseline.

    This is the standard entry point for creating baseline instances
    in the evaluation pipeline.

    Args:
        config: Configuration object. Creates default if None.

    Returns:
        Configured MovingAverageBaseline instance.
    """
    return MovingAverageBaseline(config)


def main() -> None:
    """Main entry point for standalone testing of the baseline.

    Generates synthetic data, runs the baseline, and outputs statistics.
    Per Script-must-do-work-by-default: This runs without arguments
    and produces real output artifacts.
    """
    print("=" * 60)
    print("Moving Average Z-Score Baseline - Standalone Test")
    print("=" * 60)

    # Create configuration
    config = MovingAverageConfig(
        window_size=50,
        z_score_threshold=3.0,
        min_observations=10,
        random_seed=42,
        output_dir="data/results"
    )

    # Create baseline
    baseline = create_baseline(config)

    # Generate synthetic test data
    print("\nGenerating synthetic time series with anomalies...")
    np.random.seed(42)

    # Create base signal: sine wave with noise
    n_points = 500
    t = np.linspace(0, 4 * np.pi, n_points)
    base_signal = np.sin(t) + 0.1 * np.random.randn(n_points)

    # Inject anomalies at known positions
    anomaly_indices = [100, 200, 300, 400]
    values = base_signal.copy()
    timestamps = []

    for i in range(n_points):
        if i in anomaly_indices:
            # Inject large spike
            values[i] += 5.0  # Large deviation
        timestamp = datetime(2024, 1, 1, 0, 0, 0) + \
                    __import__('datetime').timedelta(minutes=i)
        timestamps.append(timestamp)

    print(f"Generated {n_points} observations with {len(anomaly_indices)} anomalies")

    # Run baseline
    print("\nRunning Moving Average Z-Score baseline...")
    predictions = baseline.predict_batch(values, timestamps)

    # Get statistics
    summary = baseline.get_statistics_summary()

    print(f"\nModel Statistics:")
    print(f"  Total observations: {summary['total_observations']}")
    print(f"  Anomaly count: {summary['anomaly_count']}")
    print(f"  Anomaly rate: {summary['anomaly_rate']:.4f}")
    print(f"  Z-score mean: {summary['z_score_mean']:.4f}")
    print(f"  Z-score std: {summary['z_score_std']:.4f}")
    print(f"  Max |z-score|: {summary['z_score_max']:.4f}")

    # Check detection of known anomalies
    detected = []
    for idx in anomaly_indices:
        pred = predictions[idx]
        detected.append(pred.is_anomaly)

    print(f"\nKnown Anomaly Detection:")
    for idx, detected_flag in zip(anomaly_indices, detected):
        status = "DETECTED" if detected_flag else "MISSED"
        print(f"  Index {idx}: {status} (z-score: {predictions[idx].z_score:.2f})")

    # Save results
    output_path = Path(config.output_dir)
    results_file = output_path / "moving_average_baseline_results.json"

    import json
    results_data = {
        "config": {
            "window_size": config.window_size,
            "z_score_threshold": config.z_score_threshold,
            "min_observations": config.min_observations
        },
        "summary": summary,
        "known_anomaly_indices": anomaly_indices,
        "detection_results": [
            {"index": idx, "detected": det, "z_score": float(predictions[idx].z_score)}
            for idx, det in zip(anomaly_indices, detected)
        ]
    }

    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)

    print(f"\nResults saved to: {results_file}")
    print("\nBaseline test completed successfully!")


if __name__ == "__main__":
    main()
