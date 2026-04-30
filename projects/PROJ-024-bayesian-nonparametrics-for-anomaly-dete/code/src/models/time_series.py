"""
TimeSeries data model for streaming anomaly detection.

This module defines the core TimeSeries dataclass and iterator
for processing sequential observations in the DPGMM anomaly
detection pipeline.

Per Constitution Principle III, this entity definition is
documented in data-model.md (specs/001-bayesian-nonparametrics-
anomaly-detection/data-model.md).
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Iterator, Tuple
import numpy as np
import logging

# Import from sibling module - StreamingObservation defined in utils/streaming.py
# Per API surface: code/src/utils/streaming.py provides StreamingObservation
try:
    from ..utils.streaming import StreamingObservation
except ImportError:
    # Fallback for direct execution
    StreamingObservation = None

logger = logging.getLogger(__name__)


@dataclass
class TimeSeries:
    """
    Core TimeSeries entity for anomaly detection.

    Represents a time-ordered sequence of observations with
    metadata for provenance and processing state.

    Attributes:
        name: Human-readable identifier for this time series
        source: Origin of the data (file path, API endpoint, etc.)
        start_time: First observation timestamp
        end_time: Last observation timestamp
        observations: List of (timestamp, value) tuples
        metadata: Additional context (sensor_id, unit, etc.)
        processed: Whether this series has been processed by the model
        checksum: SHA256 hash of raw data for integrity verification (Constitution Principle III)

    Per data-model.md:
        - Entity: TimeSeries
        - Primary Key: (name, source, start_time)
        - Cardinality: One TimeSeries contains many Observations
    """
    name: str
    source: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    observations: List[Tuple[datetime, float]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processed: bool = False
    checksum: Optional[str] = None
    missing_count: int = 0
    total_count: int = 0

    def __post_init__(self):
        """Validate and compute derived fields."""
        if self.observations:
            self._update_time_bounds()
            self.total_count = len(self.observations)

    def _update_time_bounds(self) -> None:
        """Update start_time and end_time from observations."""
        if self.observations:
            timestamps = [ts for ts, _ in self.observations]
            self.start_time = min(timestamps)
            self.end_time = max(timestamps)

    def add_observation(self, timestamp: datetime, value: float, is_missing: bool = False) -> None:
        """
        Add a single observation to the time series.

        Args:
            timestamp: Observation timestamp
            value: Observed value (NaN if missing)
            is_missing: Whether this is a missing value
        """
        self.observations.append((timestamp, value))
        if is_missing:
            self.missing_count += 1
        self.total_count = len(self.observations)
        self._update_time_bounds()

    def add_observations(self, observations: List[Tuple[datetime, float]], 
                        missing_flags: Optional[List[bool]] = None) -> None:
        """
        Add multiple observations at once.

        Args:
            observations: List of (timestamp, value) tuples
            missing_flags: Optional list indicating which values are missing
        """
        if missing_flags is None:
            missing_flags = [False] * len(observations)

        for (ts, val), is_missing in zip(observations, missing_flags):
            self.add_observation(ts, val, is_missing)

    def get_values(self) -> np.ndarray:
        """Return observation values as numpy array."""
        return np.array([v for _, v in self.observations], dtype=np.float64)

    def get_timestamps(self) -> List[datetime]:
        """Return observation timestamps."""
        return [ts for ts, _ in self.observations]

    def get_observations(self) -> List[Tuple[datetime, float]]:
        """Return all observations as list of tuples."""
        return list(self.observations)

    def get_missing_mask(self) -> np.ndarray:
        """Return boolean mask indicating missing values."""
        return np.array([np.isnan(v) for _, v in self.observations])

    def get_valid_observations(self) -> List[Tuple[datetime, float]]:
        """Return only non-missing observations."""
        return [(ts, v) for ts, v in self.observations if not np.isnan(v)]

    def compute_statistics(self) -> Dict[str, float]:
        """
        Compute basic statistics for the time series.

        Returns:
            Dict with mean, std, min, max, count, missing_count
        """
        values = self.get_values()
        valid_values = self.get_valid_observations()

        return {
            'mean': float(np.nanmean(values)) if len(values) > 0 else 0.0,
            'std': float(np.nanstd(values)) if len(values) > 0 else 0.0,
            'min': float(np.nanmin(values)) if len(values) > 0 else 0.0,
            'max': float(np.nanmax(values)) if len(values) > 0 else 0.0,
            'count': self.total_count,
            'valid_count': len(valid_values),
            'missing_count': self.missing_count,
            'missing_ratio': self.missing_count / max(self.total_count, 1),
        }

    def get_observations_range(self, start: datetime, end: datetime) -> List[Tuple[datetime, float]]:
        """
        Get observations within a timestamp range (inclusive).

        Args:
            start: Start timestamp
            end: End timestamp

        Returns:
            List of observations within range
        """
        return [(ts, v) for ts, v in self.observations 
                if start <= ts <= end]

    def to_streaming_observations(self) -> Iterator['StreamingObservation']:
        """
        Convert to streaming observations for incremental processing.

        Yields:
            StreamingObservation objects for each timestamp
        """
        if StreamingObservation is None:
            logger.warning("StreamingObservation not available, skipping streaming conversion")
            return

        for ts, val in self.observations:
            yield StreamingObservation(
                timestamp=ts,
                value=val,
                is_missing=np.isnan(val)
            )

    def save_to_file(self, path: Union[str, Path]) -> None:
        """
        Save time series to CSV file.

        Args:
            path: Output file path
        """
        import pandas as pd

        path = Path(path)
        df = pd.DataFrame([
            {'timestamp': ts.isoformat(), 'value': v}
            for ts, v in self.observations
        ])
        df.to_csv(path, index=False)
        logger.info(f"Saved time series '{self.name}' to {path}")

    @classmethod
    def load_from_file(cls, path: Union[str, Path], name: str = None) -> 'TimeSeries':
        """
        Load time series from CSV file.

        Args:
            path: Input file path
            name: Optional name override

        Returns:
            TimeSeries instance
        """
        import pandas as pd

        path = Path(path)
        if name is None:
            name = path.stem

        df = pd.read_csv(path)
        observations = [
            (datetime.fromisoformat(str(ts)), float(v))
            for ts, v in zip(df['timestamp'], df['value'])
        ]

        return cls(
            name=name,
            source=str(path),
            observations=observations
        )

    def __len__(self) -> int:
        """Return number of observations."""
        return len(self.observations)

    def __repr__(self) -> str:
        """String representation."""
        return (f"TimeSeries(name='{self.name}', "
                f"observations={len(self.observations)}, "
                f"missing={self.missing_count}, "
                f"processed={self.processed})")


@dataclass
class TimeSeriesIterator:
    """
    Iterator wrapper for processing time series observations
    one at a time in streaming fashion.

    Per FR-005 (memory constraints), this enables incremental
    processing without loading entire series into memory.
    """
    time_series: TimeSeries
    start_index: int = 0
    end_index: Optional[int] = None

    def __post_init__(self):
        if self.end_index is None:
            self.end_index = len(self.time_series.observations)

    def __iter__(self) -> 'TimeSeriesIterator':
        return self

    def __next__(self) -> Tuple[datetime, float]:
        if self.start_index >= self.end_index:
            raise StopIteration

        ts, val = self.time_series.observations[self.start_index]
        self.start_index += 1
        return ts, val

    def get_remaining_count(self) -> int:
        """Return number of observations remaining."""
        return max(0, self.end_index - self.start_index)

    def reset(self) -> None:
        """Reset iterator to start."""
        self.start_index = 0

    def to_streaming(self) -> Iterator[StreamingObservation]:
        """
        Iterate as StreamingObservation objects.

        Yields:
            StreamingObservation for each remaining observation
        """
        if StreamingObservation is None:
            return

        for i in range(self.start_index, self.end_index):
            ts, val = self.time_series.observations[i]
            yield StreamingObservation(
                timestamp=ts,
                value=val,
                is_missing=np.isnan(val)
            )