"""
ARIMA Baseline Model for Time Series Anomaly Detection.

Implements an ARIMA-based anomaly detection baseline that:
1. Fits an ARIMA(p,d,q) model to historical observations
2. Generates predictions for the next time step
3. Computes anomaly scores based on prediction residuals
4. Supports both batch and streaming (rolling window) modes

Per US2 acceptance scenario 1: Compare against DPGMM and Moving Average baselines.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Union
from datetime import datetime
from pathlib import Path
import sys
import logging

# Conditional import for ARIMA - statsmodels may not be available in all environments
try:
    from statsmodels.tsa.arima.model import ARIMA as StatsModelsARIMA
    ARIMA_AVAILABLE = True
except ImportError:
  ARIMA_AVAILABLE = False
  StatsModelsARIMA = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ARIMAConfig:
    """Configuration for ARIMA baseline model.

    Attributes:
        order: ARIMA order (p, d, q) tuple
        seasonal_order: Seasonal order (P, D, Q, s) tuple, or None for non-seasonal
        random_state: Random seed for reproducibility
        max_lag: Maximum lag for residual-based anomaly detection
        threshold_multiplier: Number of standard deviations for anomaly threshold
        rolling_window_size: Size of rolling window for streaming updates
        min_training_samples: Minimum samples required before making predictions
    """
    order: Tuple[int, int, int] = field(default=(5, 1, 0))
    seasonal_order: Optional[Tuple[int, int, int, int]] = field(default=None)
    random_state: int = field(default=42)
    max_lag: int = field(default=24)
    threshold_multiplier: float = field(default=3.0)
    rolling_window_size: int = field(default=100)
    min_training_samples: int = field(default=50)


@dataclass
class ARIMAPrediction:
    """Prediction output from ARIMA baseline.

    Attributes:
        timestamp: Timestamp of the prediction
        observed_value: The actual observed value
        predicted_value: The ARIMA prediction
        residual: observed - predicted
        anomaly_score: Absolute residual (higher = more anomalous)
        is_anomaly: Boolean flag based on threshold
        threshold: The threshold used for this prediction
        confidence_interval_lower: Lower bound of 95% CI
        confidence_interval_upper: Upper bound of 95% CI
        model_state: Serialized model state for checkpointing
    """
    timestamp: datetime
    observed_value: float
    predicted_value: float
    residual: float
    anomaly_score: float
    is_anomaly: bool
    threshold: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    model_state: Optional[Dict[str, Any]] = field(default=None)


@dataclass
class ARIMABaselineState:
    """Internal state for streaming ARIMA updates.

    Attributes:
        observation_history: List of recent observations for rolling window
        residual_history: List of recent residuals for threshold estimation
        fitted_model: The fitted ARIMA model (or None)
        last_prediction: The last prediction made
        n_predictions: Total number of predictions made
        n_anomalies: Total number of anomalies detected
    """
    observation_history: List[float] = field(default_factory=list)
    residual_history: List[float] = field(default_factory=list)
    fitted_model: Optional[Any] = field(default=None)
    last_prediction: Optional[ARIMAPrediction] = field(default=None)
    n_predictions: int = field(default=0)
    n_anomalies: int = field(default=0)


class ARIMABaseline:
    """ARIMA-based anomaly detection baseline.

    This baseline implements a standard ARIMA model for time series
    anomaly detection. Anomalies are flagged when the prediction
    residual exceeds a threshold based on historical residual statistics.

    Supports:
        - Batch fitting on historical data
        - Streaming updates with rolling window retraining
        - Configurable ARIMA orders
        - Confidence interval computation

    Per US2: Used for comparison against DPGMM and Moving Average baselines.
    """

    def __init__(self, config: Optional[ARIMAConfig] = None):
        """Initialize ARIMA baseline with configuration.

        Args:
            config: ARIMAConfig instance or None for defaults
        """
        if not ARIMA_AVAILABLE:
            raise ImportError(
                "statsmodels required for ARIMA baseline. "
                "Install with: pip install statsmodels"
            )

        self.config = config or ARIMAConfig()
        self.state = ARIMABaselineState()
        self._residual_std: float = 1.0  # Running estimate of residual std

        # Set random seed for reproducibility
        np.random.seed(self.config.random_state)

    def _compute_residual_threshold(self) -> float:
        """Compute anomaly threshold from residual history.

        Uses the configurable multiplier on the standard deviation
        of historical residuals.

        Returns:
            Threshold value for anomaly detection
        """
        if len(self.state.residual_history) < 10:
            # Not enough history, use default threshold
            return self.config.threshold_multiplier * self._residual_std

        residuals = np.array(self.state.residual_history)
        self._residual_std = np.std(residuals)
        return self.config.threshold_multiplier * self._residual_std

    def _fit_model(self, observations: List[float]) -> Any:
        """Fit ARIMA model to observations.

        Args:
            observations: List of historical observations

        Returns:
            Fitted ARIMA model
        """
        if len(observations) < self.config.min_training_samples:
            raise ValueError(
                f"Not enough observations ({len(observations)}) to fit ARIMA. "
                f"Minimum required: {self.config.min_training_samples}"
            )

        try:
            model = StatsModelsARIMA(
                observations,
                order=self.config.order,
                seasonal_order=self.config.seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            fitted = model.fit()
            return fitted
        except Exception as e:
            logger.warning(f"ARIMA fitting failed: {e}. Falling back to simple model.")
            # Fallback: use simpler order if complex order fails
            try:
                model = StatsModelsARIMA(
                    observations,
                    order=(1, 1, 0),
                    enforce_stationarity=False,
                    enforce_invertibility=False
                )
                fitted = model.fit()
                return fitted
            except Exception as e2:
                logger.error(f"ARIMA fallback also failed: {e2}")
                raise

    def fit(self, observations: List[float]) -> 'ARIMABaseline':
        """Fit the ARIMA model on historical observations.

        Args:
            observations: List of time series observations

        Returns:
            self for method chaining
        """
        logger.info(f"Fitting ARIMA model on {len(observations)} observations")

        self.state.observation_history = list(observations)
        self.state.fitted_model = self._fit_model(observations)

        # Initialize residual history with training data
        # We'll compute residuals during prediction phase
        logger.info("ARIMA model fitted successfully")
        return self

    def predict(self, observed_value: float) -> ARIMAPrediction:
        """Make a prediction for the current observation.

        This updates the model state and computes anomaly metrics.

        Args:
            observed_value: The current observed value

        Returns:
            ARIMAPrediction with anomaly metrics
        """
        timestamp = datetime.now()

        # Ensure we have enough training data
        if len(self.state.observation_history) < self.config.min_training_samples:
            # Not enough data, return placeholder
            return ARIMAPrediction(
                timestamp=timestamp,
                observed_value=observed_value,
                predicted_value=observed_value,  # No prediction possible
                residual=0.0,
                anomaly_score=0.0,
                is_anomaly=False,
                threshold=0.0,
                confidence_interval_lower=observed_value,
                confidence_interval_upper=observed_value,
                model_state=None
            )

        # If model not fitted or not enough history, fit/retrain
        if self.state.fitted_model is None or (
            len(self.state.observation_history) > self.config.rolling_window_size
        ):
            # Use rolling window for retraining
            window = self.state.observation_history[-self.config.rolling_window_size:]
            try:
                self.state.fitted_model = self._fit_model(window)
            except ValueError as e:
                logger.warning(f"Retraining failed: {e}. Keeping existing model.")

        # Get prediction
        try:
            # Use the fitted model to predict next value
            forecast = self.state.fitted_model.get_forecast(steps=1)
            predicted_value = forecast.predicted_mean[0]
            conf_int = forecast.conf_int(alpha=0.05)
            ci_lower = conf_int.iloc[0, 0]
            ci_upper = conf_int.iloc[0, 1]
        except Exception as e:
            logger.warning(f"Prediction failed: {e}. Using naive prediction.")
            predicted_value = self.state.observation_history[-1]
            ci_lower = predicted_value
            ci_upper = predicted_value

        # Compute metrics
        residual = observed_value - predicted_value
        anomaly_score = abs(residual)
        threshold = self._compute_residual_threshold()
        is_anomaly = anomaly_score > threshold

        # Update state
        self.state.residual_history.append(residual)
        # Keep residual history bounded
        if len(self.state.residual_history) > self.config.max_lag * 2:
            self.state.residual_history = self.state.residual_history[-self.config.max_lag:]

        self.state.observation_history.append(observed_value)
        if len(self.state.observation_history) > self.config.rolling_window_size:
            self.state.observation_history = self.state.observation_history[-self.config.rolling_window_size:]

        self.state.n_predictions += 1
        if is_anomaly:
            self.state.n_anomalies += 1

        # Create prediction object
        prediction = ARIMAPrediction(
            timestamp=timestamp,
            observed_value=observed_value,
            predicted_value=float(predicted_value),
            residual=float(residual),
            anomaly_score=float(anomaly_score),
            is_anomaly=is_anomaly,
            threshold=float(threshold),
            confidence_interval_lower=float(ci_lower),
            confidence_interval_upper=float(ci_upper),
            model_state=None  # Would need proper serialization for checkpointing
        )

        self.state.last_prediction = prediction
        return prediction

    def process_batch(self, observations: List[float]) -> List[ARIMAPrediction]:
        """Process a batch of observations.

        Args:
            observations: List of time series observations

        Returns:
            List of predictions for each observation
        """
        # First fit on all but the last observation
        if len(observations) < self.config.min_training_samples + 1:
            raise ValueError(
                f"Need at least {self.config.min_training_samples + 1} observations for batch processing"
            )

        train_data = observations[:-1]
        self.fit(train_data)

        # Process each observation
        predictions = []
        for obs in observations[-1:]:  # Process only the last one after fitting
            pred = self.predict(obs)
            predictions.append(pred)

        return predictions

    def get_statistics(self) -> Dict[str, Any]:
        """Get baseline statistics.

        Returns:
            Dictionary of baseline performance statistics
        """
        return {
            'n_predictions': self.state.n_predictions,
            'n_anomalies': self.state.n_anomalies,
            'anomaly_rate': (
                self.state.n_anomalies / self.state.n_predictions
                if self.state.n_predictions > 0 else 0.0
            ),
            'residual_std': self._residual_std,
            'observation_history_length': len(self.state.observation_history),
            'residual_history_length': len(self.state.residual_history)
        }

    def reset(self) -> None:
        """Reset the baseline state for fresh training."""
        self.state = ARIMABaselineState()
        self._residual_std = 1.0


def create_baseline(config: Optional[ARIMAConfig] = None) -> ARIMABaseline:
    """Factory function to create ARIMA baseline.

    Args:
        config: Optional ARIMAConfig instance

    Returns:
        Configured ARIMABaseline instance
    """
    return ARIMABaseline(config=config)


def main():
    """Main entry point for testing ARIMA baseline.

    Runs a simple demonstration with synthetic data.
    """
    if not ARIMA_AVAILABLE:
        logger.error("statsmodels not available. Skipping ARIMA baseline test.")
        return

    logger.info("Testing ARIMA Baseline")

    # Create synthetic time series with known anomalies
    np.random.seed(42)
    n_points = 200

    # Base signal: sinusoidal with noise
    t = np.arange(n_points)
    base_signal = 10 * np.sin(2 * np.pi * t / 50) + np.random.normal(0, 1, n_points)

    # Inject anomalies at known positions
    anomaly_indices = [50, 100, 150]
    for idx in anomaly_indices:
        base_signal[idx] += 10  # Large spike

    observations = base_signal.tolist()

    # Create and fit baseline
    config = ARIMAConfig(
        order=(2, 1, 1),
        threshold_multiplier=3.0,
        rolling_window_size=100,
        min_training_samples=30
    )
    baseline = create_baseline(config)

    # Process observations
    predictions = []
    for i, obs in enumerate(observations):
        pred = baseline.predict(obs)
        predictions.append(pred)

        if pred.is_anomaly:
            logger.info(f"Anomaly detected at index {i}: observed={obs:.2f}, "
                       f"predicted={pred.predicted_value:.2f}, score={pred.anomaly_score:.2f}")

    # Print summary
    stats = baseline.get_statistics()
    logger.info(f"ARIMA Baseline Statistics: {stats}")

    # Report detected anomalies
    detected_indices = [i for i, p in enumerate(predictions) if p.is_anomaly]
    logger.info(f"Detected anomalies at indices: {detected_indices}")
    logger.info(f"True anomaly indices: {anomaly_indices}")

    # Compute detection accuracy
    true_positives = len(set(detected_indices) & set(anomaly_indices))
    precision = true_positives / len(detected_indices) if detected_indices else 0.0
    recall = true_positives / len(anomaly_indices) if anomaly_indices else 0.0

    logger.info(f"Precision: {precision:.2f}, Recall: {recall:.2f}")


if __name__ == '__main__':
    main()
