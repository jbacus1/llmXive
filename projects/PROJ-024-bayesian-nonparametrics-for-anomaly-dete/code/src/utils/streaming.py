"""
Streaming utilities for sequential observation processing in time series anomaly detection.

Supports memory-efficient processing of observations one at a time,
enabling real-time streaming inference for DPGMM models.

This module provides:
- StreamingObservation: dataclass for individual time series observations
- ObservationBuffer: sliding window buffer for local statistics
- StreamingStats: running statistics using Welford's algorithm
- Helper functions for stream processing and validation
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Union, Generator, Callable
import numpy as np
from pathlib import Path


@dataclass
class StreamingObservation:
    """
    Represents a single observation in a time series stream.
    
    Attributes:
        timestamp: Time of observation
        value: Observed value (scalar or vector)
        metadata: Optional metadata about the observation
        is_missing: Whether this observation is missing/NaN
    """
    timestamp: datetime
    value: Union[float, np.ndarray]
    metadata: Optional[Dict[str, Any]] = None
    is_missing: bool = False
    
    def __post_init__(self) -> None:
        """Validate and normalize the observation."""
        if self.metadata is None:
            self.metadata = {}
        
        # Check if value is missing
        if isinstance(self.value, (float, int)):
            self.is_missing = np.isnan(float(self.value))
            self.value = np.array([float(self.value)])
        elif isinstance(self.value, np.ndarray):
            self.is_missing = np.any(np.isnan(self.value))
            if self.value.ndim == 0:
                self.value = np.array([float(self.value)])
        else:
            self.value = np.array(self.value, dtype=float)
            self.is_missing = np.any(np.isnan(self.value))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert observation to dictionary representation."""
        return {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'value': self.value.tolist() if isinstance(self.value, np.ndarray) else self.value,
            'metadata': self.metadata,
            'is_missing': self.is_missing
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamingObservation':
        """Create observation from dictionary representation."""
        timestamp = datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None
        value = np.array(data['value']) if isinstance(data.get('value'), list) else data.get('value', 0.0)
        
        return cls(
            timestamp=timestamp,
            value=value,
            metadata=data.get('metadata', {}),
            is_missing=data.get('is_missing', False)
        )

@dataclass
class ObservationBuffer:
    """
    Sliding window buffer for streaming observations.
    
    Maintains a fixed-size window of recent observations for
    local statistics computation and anomaly scoring.
    
    Attributes:
        window_size: Maximum number of observations to retain
        observations: List of observations in the buffer
    """
    window_size: int
    observations: List[StreamingObservation] = field(default_factory=list)
    
    def add(self, observation: StreamingObservation) -> None:
        """Add observation to buffer, removing oldest if full."""
        self.observations.append(observation)
        if len(self.observations) > self.window_size:
            self.observations.pop(0)
    
    def get_values(self) -> np.ndarray:
        """Get array of values from current buffer."""
        return np.array([obs.value[0] if obs.value.ndim == 1 else obs.value 
                        for obs in self.observations])
    
    def get_timestamps(self) -> List[datetime]:
        """Get list of timestamps from current buffer."""
        return [obs.timestamp for obs in self.observations]
    
    def get_missing_mask(self) -> np.ndarray:
        """Get boolean mask indicating missing values."""
        return np.array([obs.is_missing for obs in self.observations])
    
    def is_ready(self) -> bool:
        """Check if buffer has reached minimum size for processing."""
        return len(self.observations) >= self.window_size
    
    def clear(self) -> None:
        """Clear all observations from buffer."""
        self.observations = []
    
    def __len__(self) -> int:
        """Return current number of observations in buffer."""
        return len(self.observations)

@dataclass
class StreamingStats:
    """
    Running statistics for streaming observations.
    
    Computes mean, variance, and other statistics incrementally
    without storing all historical values using Welford's algorithm.
    
    Attributes:
        n: Number of observations processed
        mean: Running mean
        M2: Running sum of squared differences from mean
        min_value: Minimum value seen
        max_value: Maximum value seen
    """
    n: int = 0
    mean: float = 0.0
    M2: float = 0.0
    min_value: float = float('inf')
    max_value: float = float('-inf')
    
    def update(self, value: float) -> None:
        """Update statistics with new observation using Welford's algorithm."""
        if np.isnan(value):
            return
        
        self.n += 1
        delta = value - self.mean
        self.mean += delta / self.n
        delta2 = value - self.mean
        self.M2 += delta * delta2
        self.min_value = min(self.min_value, value)
        self.max_value = max(self.max_value, value)
    
    @property
    def variance(self) -> float:
        """Calculate unbiased variance from running statistics."""
        if self.n < 2:
            return 0.0
        return self.M2 / (self.n - 1)
    
    @property
    def std(self) -> float:
        """Calculate standard deviation from running statistics."""
        return np.sqrt(self.variance)
    
    @property
    def coefficient_of_variation(self) -> float:
        """Calculate coefficient of variation (std/mean)."""
        if self.mean == 0:
            return 0.0
        return self.std / abs(self.mean)
    
    def reset(self) -> None:
        """Reset all statistics."""
        self.n = 0
        self.mean = 0.0
        self.M2 = 0.0
        self.min_value = float('inf')
        self.max_value = float('-inf')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary."""
        return {
            'n': self.n,
            'mean': self.mean,
            'variance': self.variance,
            'std': self.std,
            'min': self.min_value,
            'max': self.max_value,
            'coefficient_of_variation': self.coefficient_of_variation
        }

def create_streaming_observation(
    value: Union[float, np.ndarray],
    timestamp: Optional[datetime] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> StreamingObservation:
    """
    Factory function to create a StreamingObservation.
    
    Args:
        value: Observed value (scalar or vector)
        timestamp: Optional timestamp (defaults to current time)
        metadata: Optional metadata dictionary
    
    Returns:
        StreamingObservation instance
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    return StreamingObservation(
        timestamp=timestamp,
        value=value,
        metadata=metadata,
        is_missing=False
    )

def stream_from_file(
    file_path: Path,
    timestamp_column: Optional[str] = None,
    value_column: str = 'value'
) -> Generator[StreamingObservation, None, None]:
    """
    Generate StreamingObservations from a CSV file.
    
    Args:
        file_path: Path to CSV file with time series data
        timestamp_column: Column name for timestamps (optional)
        value_column: Column name for values
    
    Yields:
        StreamingObservation for each row
    """
    import pandas as pd
    
    df = pd.read_csv(file_path)
    
    for _, row in df.iterrows():
        timestamp = row[timestamp_column] if timestamp_column else datetime.now()
        value = row[value_column]
        
        yield create_streaming_observation(
            value=value,
            timestamp=timestamp,
            metadata={'source': str(file_path)}
        )

def process_stream(
    observations: Generator[StreamingObservation, None, None],
    callback: Callable[[StreamingObservation], None],
    buffer_size: int = 100
) -> StreamingStats:
    """
    Process a stream of observations with a callback function.
    
    Args:
        observations: Generator of StreamingObservations
        callback: Function to call for each observation
        buffer_size: Size of observation buffer
    
    Returns:
        StreamingStats for the processed observations
    """
    buffer = ObservationBuffer(window_size=buffer_size)
    stats = StreamingStats()
    
    for obs in observations:
        buffer.add(obs)
        
        if not obs.is_missing and obs.value.size > 0:
            value = obs.value[0] if obs.value.ndim == 1 else obs.value
            if isinstance(value, np.ndarray):
                value = value[0]
            stats.update(float(value))
        
        callback(obs)
    
    return stats

def validate_streaming_observations(
    observations: List[StreamingObservation]
) -> Dict[str, Any]:
    """
    Validate a list of streaming observations.
    
    Args:
        observations: List of StreamingObservations to validate
    
    Returns:
        Dictionary with validation results
    """
    result = {
        'valid': True,
        'total_count': len(observations),
        'missing_count': 0,
        'issues': []
    }
    
    for i, obs in enumerate(observations):
        if obs.is_missing:
            result['missing_count'] += 1
        
        if not isinstance(obs.timestamp, datetime):
            result['valid'] = False
            result['issues'].append(f"Observation {i}: Invalid timestamp type")
        
        if not isinstance(obs.value, (float, int, np.ndarray)):
            result['valid'] = False
            result['issues'].append(f"Observation {i}: Invalid value type")
    
    return result

def compute_zscore(
    value: float,
    mean: float,
    std: float,
    epsilon: float = 1e-8
) -> float:
    """
    Compute z-score for anomaly detection.
    
    Args:
        value: Observed value
        mean: Reference mean
        std: Reference standard deviation
        epsilon: Small constant to avoid division by zero
    
    Returns:
        Z-score value
    """
    if std < epsilon:
        return 0.0
    return (value - mean) / (std + epsilon)

def normalize_observation(
    value: float,
    min_val: float,
    max_val: float,
    epsilon: float = 1e-8
) -> float:
    """
    Normalize value to [0, 1] range.
    
    Args:
        value: Observed value
        min_val: Minimum reference value
        max_val: Maximum reference value
        epsilon: Small constant to avoid division by zero
    
    Returns:
        Normalized value in [0, 1]
    """
    range_val = max_val - min_val
    if range_val < epsilon:
        return 0.5
    return (value - min_val) / (range_val + epsilon)

def main() -> None:
    """Main function for testing streaming utilities."""
    print("Streaming utilities module loaded successfully")
    print("Available classes:")
    print("  - StreamingObservation")
    print("  - ObservationBuffer")
    print("  - StreamingStats")
    print("Available functions:")
    print("  - create_streaming_observation")
    print("  - stream_from_file")
    print("  - process_stream")
    print("  - validate_streaming_observations")
    print("  - compute_zscore")
    print("  - normalize_observation")

if __name__ == "__main__":
    main()
