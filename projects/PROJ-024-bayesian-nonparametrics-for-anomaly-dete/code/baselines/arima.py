"""
ARIMA Baseline Model for Anomaly Detection in Time Series

Implements an ARIMA-based anomaly detector that:
- Fits ARIMA(p,d,q) model to training data
- Generates predictions and calculates residuals
- Flags anomalies when residuals exceed statistical thresholds
- Supports both batch and streaming observation processing

Per US2 acceptance scenario 1: Compare DPGMM detector against ARIMA
baseline on public benchmarks with F1-score validation.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Union
from datetime import datetime
from pathlib import Path

try:
    from statsmodels.tsa.arima.model import ARIMA as StatsmodelsARIMA
    from statsmodels.tsa.stattools import adfuller
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

# Import project utilities
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.anomaly_score import AnomalyScore
from models.time_series import TimeSeries
from utils.streaming import StreamingObservation, StreamingObservationProcessor


@dataclass
class ARIMAConfig:
    """Configuration for ARIMA baseline model."""
    order: Tuple[int, int, int] = field(default=(1, 1, 1))
    """ARIMA(p,d,q) order parameters"""
    
    seasonal_order: Optional[Tuple[int, int, int, int]] = field(default=None)
    """Seasonal ARIMA order (P,D,Q,s) - None for non-seasonal"""
    
    trend: Optional[str] = field(default="c")
    """Trend term: 'c' for constant, 't' for linear, 'ct' for both"""
    
    max_p: int = 5
    """Maximum AR order for automatic order selection"""
    
    max_q: int = 5
    """Maximum MA order for automatic order selection"""
    
    seasonal_period: int = 24
    """Seasonal period for automatic detection"""
    
    anomaly_threshold_std: float = 3.0
    """Number of standard deviations for anomaly threshold"""
    
    min_train_observations: int = 50
    """Minimum observations required before anomaly detection"""
    
    window_size: int = 100
    """Sliding window size for streaming mode"""
    
    random_state: Optional[int] = field(default=42)
    """Random seed for reproducibility"""
    
    enforce_stationarity: bool = True
    """Force stationarity constraint during fitting"""
    
    enforce_invertibility: bool = True
    """Force invertibility constraint during fitting"""

@dataclass
class ARIMAPrediction:
    """Container for ARIMA prediction results."""
    timestamp: datetime
    actual: float
    predicted: float
    residual: float
    standardized_residual: float
    is_anomaly: bool
    anomaly_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'actual': float(self.actual),
            'predicted': float(self.predicted),
            'residual': float(self.residual),
            'standardized_residual': float(self.standardized_residual),
            'is_anomaly': bool(self.is_anomaly),
            'anomaly_score': float(self.anomaly_score)
        }

class ARIMABaseline:
    """
    ARIMA-based anomaly detection baseline model.
    
    This baseline fits an ARIMA model to time series data and flags
    anomalies based on prediction residuals. It provides a standard
    comparison point for the DPGMM model in User Story 2.
    
    Features:
    - Automatic order selection (optional)
    - Streaming observation support
    - Residual-based anomaly scoring
    - Statistical threshold calibration
    """
    
    def __init__(self, config: Optional[ARIMAConfig] = None):
        """
        Initialize ARIMA baseline model.
        
        Args:
            config: ARIMAConfig instance. Defaults to ARIMAConfig()
        """
        if not HAS_STATSMODELS:
            raise ImportError(
                "statsmodels is required for ARIMA baseline. "
                "Install with: pip install statsmodels"
            )
        
        self.config = config or ARIMAConfig()
        self._model: Optional[StatsmodelsARIMA] = None
        self._residuals: List[float] = []
        self._predictions: List[float] = []
        self._actuals: List[float] = []
        self._timestamps: List[datetime] = []
        self._is_fitted: bool = False
        self._residual_mean: float = 0.0
        self._residual_std: float = 1.0
        self._streaming_buffer: List[float] = []
        self._streaming_predictions: List[float] = []
        
    def fit(self, observations: Union[List[float], np.ndarray],
            timestamps: Optional[List[datetime]] = None) -> 'ARIMABaseline':
        """
        Fit ARIMA model to training observations.
        
        Args:
            observations: Time series observations (1D array/list)
            timestamps: Optional timestamps for each observation
        
        Returns:
            self for method chaining
        
        Raises:
            ValueError: If observations are empty or too few
        """
        observations = np.asarray(observations, dtype=np.float64)
        
        if len(observations) < self.config.min_train_observations:
            raise ValueError(
                f"Need at least {self.config.min_train_observations} "
                f"observations for ARIMA fitting, got {len(observations)}"
            )
        
        # Handle missing values by forward filling
        mask = ~np.isnan(observations)
        if not np.all(mask):
            valid_obs = observations[mask]
            # Use last valid observation for missing values
            last_valid = valid_obs[-1] if len(valid_obs) > 0 else 0.0
            observations = np.where(np.isnan(observations), last_valid, observations)
        
        # Store training data
        self._actuals = observations.tolist()
        self._timestamps = timestamps or [
            datetime.now() for _ in range(len(observations))
        ]
        
        # Fit ARIMA model
        try:
            self._model = StatsmodelsARIMA(
                observations,
                order=self.config.order,
                seasonal_order=self.config.seasonal_order,
                trend=self.config.trend,
                enforce_stationarity=self.config.enforce_stationarity,
                enforce_invertibility=self.config.enforce_invertibility
            )
            
            self._fitted_model = self._model.fit()
            self._is_fitted = True
            
            # Calculate training residuals for threshold calibration
            train_fitted = self._fitted_model.fittedvalues
            self._residuals = (observations - train_fitted).tolist()
            
            # Calibrate residual statistics
            self._calibrate_residual_stats()
            
        except Exception as e:
            raise RuntimeError(f"ARIMA model fitting failed: {str(e)}")
        
        return self

    def _calibrate_residual_stats(self) -> None:
        """Calculate mean and std of residuals for standardization."""
        if len(self._residuals) > 0:
            residuals_arr = np.array(self._residuals)
            self._residual_mean = float(np.mean(residuals_arr))
            self._residual_std = float(np.std(residuals_arr))
            
            # Prevent division by zero
            if self._residual_std < 1e-8:
                self._residual_std = 1.0

    def predict(self, observations: Union[List[float], np.ndarray]) -> List[ARIMAPrediction]:
        """
        Generate predictions and anomaly scores for observations.
        
        Args:
            observations: Time series observations to predict on
        
        Returns:
            List of ARIMAPrediction objects
        
        Raises:
            RuntimeError: If model is not fitted
        """
        if not self._is_fitted:
            raise RuntimeError("Model must be fitted before prediction")
        
        observations = np.asarray(observations, dtype=np.float64)
        predictions = []
        
        for i, obs in enumerate(observations):
            # Get timestamp
            if i < len(self._timestamps):
                timestamp = self._timestamps[i]
            else:
                timestamp = datetime.now()
            
            # Generate prediction (one-step ahead)
            try:
                if i == 0:
                    # First observation - use training mean as prediction
                    pred = np.mean(self._actuals)
                else:
                    # Use model to predict this observation based on history
                    historical = self._actuals[:i] + [obs]
                    if len(historical) > len(self._actuals):
                        historical = historical[-len(self._actuals):]
                    
                    # Fit temporary model for prediction
                    temp_model = StatsmodelsARIMA(
                        historical,
                        order=self.config.order,
                        seasonal_order=self.config.seasonal_order,
                        trend=self.config.trend
                    )
                    temp_fitted = temp_model.fit()
                    pred = float(temp_fitted.forecast(steps=1)[0])
                
                # Calculate residual
                residual = float(obs - pred)
                
                # Standardize residual
                if self._residual_std > 1e-8:
                    standardized_residual = residual / self._residual_std
                else:
                    standardized_residual = residual
                
                # Determine anomaly status
                is_anomaly = abs(standardized_residual) > self.config.anomaly_threshold_std
                
                # Calculate anomaly score (negative log probability approximation)
                # Using Gaussian assumption on residuals
                anomaly_score = float(0.5 * (standardized_residual ** 2))
                
                pred_result = ARIMAPrediction(
                    timestamp=timestamp,
                    actual=float(obs),
                    predicted=pred,
                    residual=residual,
                    standardized_residual=standardized_residual,
                    is_anomaly=is_anomaly,
                    anomaly_score=anomaly_score
                )
                
                predictions.append(pred_result)
                
            except Exception as e:
                # Fallback for prediction errors
                pred_result = ARIMAPrediction(
                    timestamp=timestamp,
                    actual=float(obs),
                    predicted=float(obs),
                    residual=0.0,
                    standardized_residual=0.0,
                    is_anomaly=False,
                    anomaly_score=0.0
                )
                predictions.append(pred_result)
        
        return predictions

    def score(self, observations: Union[List[float], np.ndarray]) -> List[AnomalyScore]:
        """
        Generate anomaly scores for observations.
        
        Args:
            observations: Time series observations to score
        
        Returns:
            List of AnomalyScore objects compatible with DPGMM output
        
        Raises:
            RuntimeError: If model is not fitted
        """
        predictions = self.predict(observations)
        
        scores = []
        for pred in predictions:
            score = AnomalyScore(
                timestamp=pred.timestamp,
                value=pred.actual,
                anomaly_score=pred.anomaly_score,
                is_anomaly=pred.is_anomaly,
                uncertainty=pred.standardized_residual / 3.0,  # Normalize to [0,1] range
                model_type="ARIMA",
                metadata={
                    'residual': pred.residual,
                    'standardized_residual': pred.standardized_residual,
                    'predicted': pred.predicted
                }
            )
            scores.append(score)
        
        return scores

    def process_streaming(self, observation: StreamingObservation) -> AnomalyScore:
        """
        Process a single streaming observation.
        
        Args:
            observation: StreamingObservation with value and timestamp
        
        Returns:
            AnomalyScore for this observation
        
        Raises:
            RuntimeError: If model is not fitted
        """
        if not self._is_fitted:
            raise RuntimeError("Model must be fitted before streaming")
        
        value = observation.value
        timestamp = observation.timestamp or datetime.now()
        
        # Add to streaming buffer
        self._streaming_buffer.append(value)
        self._streaming_predictions.append(value)
        
        # Keep buffer size manageable
        if len(self._streaming_buffer) > self.config.window_size:
            self._streaming_buffer = self._streaming_buffer[-self.config.window_size:]
        
        # Generate prediction using recent history
        try:
            if len(self._streaming_buffer) < self.config.min_train_observations:
                # Not enough data for prediction
                pred = float(np.mean(self._streaming_buffer))
            else:
                # Use recent observations for prediction
                recent = self._streaming_buffer[-self.config.window_size:]
                temp_model = StatsmodelsARIMA(
                    recent,
                    order=self.config.order,
                    seasonal_order=self.config.seasonal_order,
                    trend=self.config.trend
                )
                temp_fitted = temp_model.fit()
                pred = float(temp_fitted.forecast(steps=1)[0])
            
            residual = float(value - pred)
            
            # Standardize
            if self._residual_std > 1e-8:
                standardized_residual = residual / self._residual_std
            else:
                standardized_residual = residual
            
            is_anomaly = abs(standardized_residual) > self.config.anomaly_threshold_std
            anomaly_score = float(0.5 * (standardized_residual ** 2))
            
        except Exception:
            # Fallback on prediction error
            pred = float(value)
            residual = 0.0
            standardized_residual = 0.0
            is_anomaly = False
            anomaly_score = 0.0
        
        return AnomalyScore(
            timestamp=timestamp,
            value=value,
            anomaly_score=anomaly_score,
            is_anomaly=is_anomaly,
            uncertainty=abs(standardized_residual) / 3.0,
            model_type="ARIMA",
            metadata={
                'residual': residual,
                'standardized_residual': standardized_residual,
                'predicted': pred
            }
        )

    def get_model_summary(self) -> Dict[str, Any]:
        """
        Get summary of fitted model parameters.
        
        Returns:
            Dictionary with model configuration and fit statistics
        """
        if not self._is_fitted:
            return {
                'is_fitted': False,
                'config': self.config.__dict__
            }
        
        try:
            summary_dict = {
                'is_fitted': True,
                'config': self.config.__dict__,
                'residual_stats': {
                    'mean': self._residual_mean,
                    'std': self._residual_std,
                    'count': len(self._residuals)
                },
                'training_observations': len(self._actuals)
            }
            
            # Add ARIMA-specific stats if available
            if hasattr(self._fitted_model, 'aic'):
                summary_dict['aic'] = float(self._fitted_model.aic)
            if hasattr(self._fitted_model, 'bic'):
                summary_dict['bic'] = float(self._fitted_model.bic)
            if hasattr(self._fitted_model, 'llf'):
                summary_dict['log_likelihood'] = float(self._fitted_model.llf)
            
            return summary_dict
            
        except Exception:
            return {
                'is_fitted': True,
                'config': self.config.__dict__,
                'error': 'Could not extract model summary'
            }

    def reset(self) -> 'ARIMABaseline':
        """
        Reset model to unfitted state.
        
        Returns:
            self for method chaining
        """
        self._model = None
        self._fitted_model = None
        self._residuals = []
        self._predictions = []
        self._actuals = []
        self._timestamps = []
        self._is_fitted = False
        self._residual_mean = 0.0
        self._residual_std = 1.0
        self._streaming_buffer = []
        self._streaming_predictions = []
        return self

    @classmethod
    def from_timeseries(cls, timeseries: TimeSeries,
                        config: Optional[ARIMAConfig] = None) -> 'ARIMABaseline':
        """
        Create ARIMA baseline from TimeSeries entity.
        
        Args:
            timeseries: TimeSeries entity with observations
            config: Optional ARIMAConfig
        
        Returns:
            Fitted ARIMABaseline instance
        """
        model = cls(config)
        observations = timeseries.values
        timestamps = timeseries.timestamps
        model.fit(observations, timestamps)
        return model

    @classmethod
    def auto_order_select(cls, observations: Union[List[float], np.ndarray],
                          config: Optional[ARIMAConfig] = None) -> 'ARIMABaseline':
        """
        Fit ARIMA with automatic order selection.
        
        Args:
            observations: Time series observations
            config: Optional ARIMAConfig (order will be auto-selected)
        
        Returns:
            Fitted ARIMABaseline with optimized order
        """
        observations = np.asarray(observations, dtype=np.float64)
        
        # Test different orders and select best by AIC
        best_order = (1, 1, 1)
        best_aic = float('inf')
        
        for p in range(0, config.max_p + 1 if config else 6):
            for d in range(0, 2):
                for q in range(0, config.max_q + 1 if config else 6):
                    try:
                        temp_model = StatsmodelsARIMA(
                            observations,
                            order=(p, d, q),
                            trend='c'
                        )
                        temp_fitted = temp_model.fit()
                        
                        if temp_fitted.aic < best_aic:
                            best_aic = temp_fitted.aic
                            best_order = (p, d, q)
                    
                    except Exception:
                        continue
        
        # Create config with selected order
        auto_config = (config or ARIMAConfig()).__dict__.copy()
        auto_config['order'] = best_order
        
        return cls(ARIMAConfig(**auto_config)).fit(observations)

    def __repr__(self) -> str:
        status = "fitted" if self._is_fitted else "unfitted"
        return f"ARIMABaseline(order={self.config.order}, status={status})"