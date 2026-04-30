"""
ARIMA baseline for time series anomaly detection.

Implements Autoregressive Integrated Moving Average model
for comparison with DPGMM.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Union
from datetime import datetime
from pathlib import Path
import sys
import logging

# Conditional statsmodels import
try:
    from statsmodels.tsa.arima.model import ARIMA as StatsModelsARIMA
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("statsmodels not available, using fallback")

# Configure logger
logger = logging.getLogger(__name__)


@dataclass
class ARIMAConfig:
    """Configuration for ARIMA baseline model."""
    order: Tuple[int, int, int] = (1, 1, 1)
    seasonal_order: Tuple[int, int, int, int] = (0, 0, 0, 0)
    trend: Optional[str] = 'c'
    enforce_stationarity: bool = True
    enforce_invertibility: bool = True
    maxiter: int = 100
    random_state: Optional[int] = 42

    def validate(self) -> None:
        """Validate configuration parameters."""
        if len(self.order) != 3:
            raise ValueError("order must be a tuple of 3 integers (p, d, q)")
        if self.order[0] < 0 or self.order[1] < 0 or self.order[2] < 0:
            raise ValueError("ARIMA order parameters must be non-negative")


@dataclass
class ARIMAPrediction:
    """Container for ARIMA prediction results."""
    predicted_value: float
    lower_bound: float
    upper_bound: float
    timestamp: datetime = field(default_factory=datetime.now)
    is_anomaly: bool = False
    residual: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'predicted_value': self.predicted_value,
            'lower_bound': self.lower_bound,
            'upper_bound': self.upper_bound,
            'timestamp': self