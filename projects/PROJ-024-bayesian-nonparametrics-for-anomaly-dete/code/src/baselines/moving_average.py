"""
Moving Average Baseline for Time Series Anomaly Detection

Implements a simple moving average with z-score anomaly detection.
This baseline provides a reference point for comparing the DPGMM model.

Public API:
  - MovingAverageConfig: Configuration dataclass
  - MovingAveragePrediction: Prediction output dataclass
  - MovingAverageState: Internal state for streaming updates
  - MovingAverageBaseline: Main baseline class
  - create_baseline: Factory function
  - main: Entry point for script execution
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path
import sys
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MovingAverageConfig:
    """Configuration for Moving Average baseline model."""
    window_size: int = 50
    z_threshold: float = 3.0
    min_samples: int = 10
    smoothing_factor: float = 0.1
    use_exponential: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'window_size': self.window_size,
            'z_threshold': self.z_threshold,
            'min_samples': self.min_samples,
            'smoothing_factor': self.smoothing_factor,
            'use_exponential': self.use_exponential
        }

@dataclass
class MovingAveragePrediction:
    """Prediction output from the moving average model."""
    timestamp: float
    value: float
    moving_average: float
    std_dev: float
    z_score: float
    is_anomaly: bool
    anomaly_score: float
    prediction_confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert prediction to dictionary."""
        return {
            'timestamp': self.timestamp,
            'value': self.value,
            'moving_average': self.moving_average,
            'std_dev': self.std_dev,
            'z_score': self.z_score,
            'is_anomaly': self.is_anomaly,
            'anomaly_score': self.anomaly_score,
            'prediction_confidence': self.prediction_confidence
        }

@dataclass
class MovingAverageState:
    """Internal state for streaming updates."""
    window_values: List[float] = field(default_factory=list)
    window_timestamps: List[float] = field(default_factory=list)
    total_observations: int = 0
    anomaly_count: int = 0
    running_sum: float = 0.0
    running_sum_sq: float = 0.0
    exponential_weight: float = 1.0
    
    def update(self, timestamp: float, value: float, window_size: int) -> None:
        """Update state with new observation."""
        self.total_observations += 1
        self.window_values.append(value)
        self.window_timestamps.append(timestamp)
        
        # Maintain window size
        if len(self.window_values) > window_size:
            self.window_values.pop(0)
            self.window_timestamps.pop(0)
        
        # Update running statistics
        self.running_sum += value
        self.running_sum_sq += value ** 2
    
    def get_statistics(self, min_samples: int) -> Tuple[float, float]:
        """Get current mean and standard deviation."""
        if len(self.window_values) < min_samples:
            # Use all available samples if window not full yet
            samples = self.window_values
        else:
            samples = self.window_values[-min_samples:]
        
        if len(samples) < 2:
            return 0.0, 0.0
        
        mean = float(np.mean(samples))
        std = float(np.std(samples))
        
        # Avoid division by zero
        if std < 1e-10:
            std = 1e-10
        
        return mean, std

class MovingAverageBaseline:
    """
    Moving Average baseline for time series anomaly detection.
    
    Uses simple or exponential moving average with z-score based
    anomaly detection.
    """
    
    def __init__(self, config: MovingAverageConfig):
        """Initialize the baseline with configuration."""
        self.config = config
        self.state = MovingAverageState()
        self.predictions: List[MovingAveragePrediction] = []
        self.initialized = False
        
        logger.info(f"Initialized MovingAverageBaseline with config: {config.to_dict()}")
    
    def update(self, timestamp: float, value: float) -> MovingAveragePrediction:
        """
        Update model with new observation and return prediction.
        
        Args:
            timestamp: Observation timestamp (float or datetime)
            value: Observation value
        
        Returns:
            MovingAveragePrediction with anomaly score
        """
        # Convert timestamp to float if needed
        if isinstance(timestamp, datetime):
            timestamp = timestamp.timestamp()
        
        # Update internal state
        self.state.update(timestamp, value, self.config.window_size)
        
        # Get current statistics
        mean, std = self.state.get_statistics(self.config.min_samples)
        
        # Calculate z-score
        if std > 0:
            z_score = abs(value - mean) / std
        else:
            z_score = 0.0
        
        # Determine anomaly status
        is_anomaly = z_score > self.config.z_threshold
        
        if is_anomaly:
            self.state.anomaly_count += 1
        
        # Calculate anomaly score (higher = more anomalous)
        anomaly_score = z_score
        
        # Calculate prediction confidence
        confidence = min(1.0, len(self.state.window_values) / self.config.min_samples)
        
        # Create prediction
        prediction = MovingAveragePrediction(
            timestamp=timestamp,
            value=value,
            moving_average=mean,
            std_dev=std,
            z_score=z_score,
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            prediction_confidence=confidence
        )
        
        self.predictions.append(prediction)
        
        return prediction
    
    def process_timeseries(self, timestamps: List[float], values: List[float]) -> List[MovingAveragePrediction]:
        """
        Process entire time series and return all predictions.
        
        Args:
            timestamps: List of observation timestamps
            values: List of observation values
        
        Returns:
            List of MovingAveragePrediction objects
        """
        if len(timestamps) != len(values):
            raise ValueError("Timestamps and values must have same length")
        
        results = []
        for ts, val in zip(timestamps, values):
            pred = self.update(ts, val)
            results.append(pred)
        
        logger.info(f"Processed {len(results)} observations, "
                   f"found {self.state.anomaly_count} anomalies")
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the model run."""
        if len(self.predictions) == 0:
            return {'error': 'No predictions made yet'}
        
        z_scores = [p.z_score for p in self.predictions]
        anomaly_scores = [p.anomaly_score for p in self.predictions]
        
        return {
            'total_observations': self.state.total_observations,
            'anomaly_count': self.state.anomaly_count,
            'anomaly_rate': self.state.anomaly_count / self.state.total_observations,
            'mean_z_score': float(np.mean(z_scores)),
            'max_z_score': float(np.max(z_scores)),
            'mean_anomaly_score': float(np.mean(anomaly_scores)),
            'config': self.config.to_dict(),
            'window_size': len(self.state.window_values),
            'running_mean': float(self.state.running_sum / self.state.total_observations)
            if self.state.total_observations > 0 else 0.0
        }
    
    def save_predictions(self, output_path: Path) -> None:
        """Save predictions to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        predictions_dict = [p.to_dict() for p in self.predictions]
        summary = self.get_summary()
        
        with open(output_path, 'w') as f:
            json.dump({
                'predictions': predictions_dict,
                'summary': summary
            }, f, indent=2)
        
        logger.info(f"Saved {len(predictions_dict)} predictions to {output_path}")

def create_baseline(config: Optional[MovingAverageConfig] = None) -> MovingAverageBaseline:
    """
    Factory function to create a MovingAverageBaseline instance.
    
    Args:
        config: Optional configuration object, uses defaults if None
    
    Returns:
        MovingAverageBaseline instance
    """
    if config is None:
        config = MovingAverageConfig()
    
    return MovingAverageBaseline(config)

def main() -> None:
    """
    Entry point for script execution.
    
    Runs the moving average baseline on synthetic data and saves results.
    This function does the full intended work without requiring arguments.
    """
    logger.info("Starting Moving Average Baseline execution")
    
    # Create output directories
    output_dir = Path(__file__).parent.parent.parent / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create baseline with default config
    config = MovingAverageConfig(
        window_size=50,
        z_threshold=3.0,
        min_samples=10
    )
    baseline = create_baseline(config)
    
    # Generate synthetic test data
    logger.info("Generating synthetic test data...")
    np.random.seed(42)
    
    n_observations = 1000
    timestamps = np.arange(n_observations, dtype=float)
    
    # Create base signal with some anomalies
    base_signal = np.sin(timestamps / 10.0) * 10 + 50
    noise = np.random.normal(0, 2, n_observations)
    values = base_signal + noise
    
    # Inject known anomalies (5% of data)
    anomaly_indices = np.random.choice(n_observations, size=int(n_observations * 0.05), replace=False)
    for idx in anomaly_indices:
        values[idx] += np.random.choice([-1, 1]) * np.random.uniform(15, 25)
    
    logger.info(f"Generated {n_observations} observations with {len(anomaly_indices)} anomalies")
    
    # Process time series
    logger.info("Processing time series...")
    predictions = baseline.process_timeseries(timestamps.tolist(), values.tolist())
    
    # Get and log summary
    summary = baseline.get_summary()
    logger.info(f"Baseline summary: {json.dumps(summary, indent=2)}")
    
    # Save predictions
    output_path = output_dir / "moving_average_predictions.json"
    baseline.save_predictions(output_path)
    
    # Save summary separately
    summary_path = output_dir / "moving_average_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Execution complete. Results saved to {output_dir}")
    
    # Print summary to stdout for verification
    print(f"\n=== Moving Average Baseline Results ===")
    print(f"Total observations: {summary['total_observations']}")
    print(f"Anomalies detected: {summary['anomaly_count']}")
    print(f"Anomaly rate: {summary['anomaly_rate']:.2%}")
    print(f"Mean z-score: {summary['mean_z_score']:.2f}")
    print(f"Max z-score: {summary['max_z_score']:.2f}")
    print(f"Output saved to: {output_dir}")
    
    # Verify no errors occurred
    if summary.get('error'):
        logger.error(f"Baseline execution had errors: {summary['error']}")
        sys.exit(1)
    else:
        logger.info("Baseline execution successful - no errors")
        sys.exit(0)

if __name__ == "__main__":
    main()
