"""
TimeSeries entity class for Bayesian Nonparametrics Anomaly Detection.

This module defines the core TimeSeries data structure used throughout
the DPGMM implementation. It provides validation, normalization, and
utility methods for time series data handling.

Based on data model documented in:
specs/001-bayesian-nonparametrics-anomaly-detection/data-model.md
"""

from dataclasses import dataclass, field
from typing import Optional, List, Union
import numpy as np
from numpy.typing import NDArray


@dataclass
class TimeSeries:
    """
    Entity class representing a time series for anomaly detection.
    
    Attributes:
        values: Core time series values as numpy array (float64)
        timestamps: Optional timestamps corresponding to values
        metadata: Optional dictionary for additional context
        is_normalized: Flag indicating if values have been normalized
        missing_mask: Boolean mask indicating missing values (True = missing)
    """
    
    values: NDArray[np.float64]
    timestamps: Optional[NDArray[np.float64]] = None
    metadata: dict = field(default_factory=dict)
    is_normalized: bool = False
    _missing_mask: Optional[NDArray[np.bool_]] = None
    
    def __post_init__(self):
        """Validate and initialize the TimeSeries instance."""
        self._validate_values()
        self._validate_timestamps()
        self._initialize_missing_mask()
    
    def _validate_values(self) -> None:
        """Validate that values array is proper 1D float64 array."""
        if not isinstance(self.values, np.ndarray):
            raise TypeError("values must be a numpy.ndarray")
        
        if self.values.ndim != 1:
            raise ValueError(f"values must be 1D array, got {self.values.ndim}D")
        
        if self.values.dtype != np.float64:
            self.values = self.values.astype(np.float64)
        
        if len(self.values) == 0:
            raise ValueError("values array cannot be empty")
    
    def _validate_timestamps(self) -> None:
        """Validate timestamps if provided."""
        if self.timestamps is not None:
            if not isinstance(self.timestamps, np.ndarray):
                raise TypeError("timestamps must be a numpy.ndarray or None")
            
            if self.timestamps.ndim != 1:
                raise ValueError(f"timestamps must be 1D array, got {self.timestamps.ndim}D")
            
            if len(self.timestamps) != len(self.values):
                raise ValueError(
                    f"timestamps length ({len(self.timestamps)}) must match "
                    f"values length ({len(self.values)})"
                )
    
    def _initialize_missing_mask(self) -> None:
        """Initialize missing values mask based on NaN detection."""
        self._missing_mask = np.isnan(self.values)
    
    @property
    def length(self) -> int:
        """Return the number of observations in the time series."""
        return len(self.values)
    
    @property
    def missing_count(self) -> int:
        """Return the count of missing (NaN) values."""
        return int(np.sum(self._missing_mask))
    
    @property
    def missing_ratio(self) -> float:
        """Return the ratio of missing values (0.0 to 1.0)."""
        return float(np.mean(self._missing_mask))
    
    @property
    def valid_values(self) -> NDArray[np.float64]:
        """Return array of non-missing values only."""
        return self.values[~self._missing_mask]
    
    @property
    def valid_indices(self) -> List[int]:
        """Return indices of non-missing values."""
        return list(np.where(~self._missing_mask)[0])
    
    def get_value(self, index: int) -> float:
        """
        Get value at specific index.
        
        Args:
            index: Index position in the time series
        
        Returns:
            Value at the given index
        
        Raises:
            IndexError: If index is out of bounds
        """
        if index < 0 or index >= self.length:
            raise IndexError(f"Index {index} out of bounds for length {self.length}")
        return self.values[index]
    
    def get_window(self, start: int, end: int) -> 'TimeSeries':
        """
        Extract a sub-segment of the time series.
        
        Args:
            start: Start index (inclusive)
            end: End index (exclusive)
        
        Returns:
            New TimeSeries with the specified window
        
        Raises:
            ValueError: If start >= end or indices out of bounds
        """
        if start < 0 or end > self.length:
            raise ValueError(
                f"Window indices ({start}, {end}) out of bounds for length {self.length}"
            )
        if start >= end:
            raise ValueError(f"Start index {start} must be less than end index {end}")
        
        return TimeSeries(
            values=self.values[start:end].copy(),
            timestamps=self.timestamps[start:end].copy() if self.timestamps is not None else None,
            metadata=self.metadata.copy(),
            is_normalized=self.is_normalized
        )
    
    def append(self, value: float, timestamp: Optional[float] = None) -> None:
        """
        Append a new observation to the time series (streaming update).
        
        Args:
            value: New value to append
            timestamp: Optional timestamp for the new value
        
        Note:
            This modifies the instance in place. For immutable updates,
            use copy() first.
        """
        self.values = np.append(self.values, float(value))
        if timestamp is not None:
            if self.timestamps is None:
                self.timestamps = np.array([timestamp], dtype=np.float64)
            else:
                self.timestamps = np.append(self.timestamps, float(timestamp))
        # Re-initialize missing mask after modification
        self._initialize_missing_mask()
    
    def normalize(self, method: str = 'zscore') -> None:
        """
        Normalize the time series values in place.
        
        Args:
            method: Normalization method ('zscore' or 'minmax')
        
        Raises:
            ValueError: If method is not supported
            RuntimeError: If all values are missing
        """
        valid = self.valid_values
        
        if len(valid) == 0:
            raise RuntimeError("Cannot normalize: all values are missing")
        
        if method == 'zscore':
            mean = np.mean(valid)
            std = np.std(valid)
            if std < 1e-10:  # Handle near-constant variance edge case
                self.values = np.zeros_like(self.values)
            else:
                self.values = (self.values - mean) / std
        elif method == 'minmax':
            min_val = np.min(valid)
            max_val = np.max(valid)
            if max_val - min_val < 1e-10:  # Handle near-constant variance
                self.values = np.zeros_like(self.values)
            else:
                self.values = (self.values - min_val) / (max_val - min_val)
        else:
            raise ValueError(f"Unknown normalization method: {method}")
        
        self.is_normalized = True
    
    def denormalize(self, mean: float, std: float) -> None:
        """
        Denormalize values using stored statistics.
        
        Args:
            mean: Mean used for zscore normalization
            std: Standard deviation used for zscore normalization
        
        Raises:
            RuntimeError: If values were not normalized
        """
        if not self.is_normalized:
            raise RuntimeError("Cannot denormalize: values were not normalized")
        self.values = self.values * std + mean
        self.is_normalized = False
    
    def fill_missing(self, method: str = 'linear') -> None:
        """
        Fill missing values using specified interpolation method.
        
        Args:
            method: Interpolation method ('linear', 'forward', 'backward', 'mean')
        
        Raises:
            ValueError: If method is not supported
        """
        if self.missing_count == 0:
            return  # No missing values to fill
        
        if method == 'linear':
            valid_idx = self.valid_indices
            if len(valid_idx) < 2:
                raise ValueError(
                    "Linear interpolation requires at least 2 valid values"
                )
            self.values = np.interp(
                np.arange(self.length),
                valid_idx,
                self.values[valid_idx]
            )
        elif method == 'forward':
            self.values = np.nan_to_num(self.values, nan=np.nan)
            for i in range(1, self.length):
                if np.isnan(self.values[i]):
                    self.values[i] = self.values[i-1]
        elif method == 'backward':
            self.values = np.nan_to_num(self.values, nan=np.nan)
            for i in range(self.length - 2, -1, -1):
                if np.isnan(self.values[i]):
                    self.values[i] = self.values[i+1]
        elif method == 'mean':
            mean_val = np.nanmean(self.values)
            self.values = np.nan_to_num(self.values, nan=mean_val)
        else:
            raise ValueError(f"Unknown fill method: {method}")
        
        # Re-initialize missing mask after filling
        self._initialize_missing_mask()
    
    def get_statistics(self) -> dict:
        """
        Compute and return basic statistics for the time series.
        
        Returns:
            Dictionary with mean, std, min, max, count, missing_count
        """
        valid = self.valid_values
        return {
            'mean': float(np.mean(valid)) if len(valid) > 0 else None,
            'std': float(np.std(valid)) if len(valid) > 0 else None,
            'min': float(np.min(valid)) if len(valid) > 0 else None,
            'max': float(np.max(valid)) if len(valid) > 0 else None,
            'count': int(len(valid)),
            'missing_count': self.missing_count,
            'missing_ratio': self.missing_ratio
        }
    
    def copy(self) -> 'TimeSeries':
        """
        Create a deep copy of the TimeSeries.
        
        Returns:
            Independent copy of this TimeSeries instance
        """
        return TimeSeries(
            values=self.values.copy(),
            timestamps=self.timestamps.copy() if self.timestamps is not None else None,
            metadata=self.metadata.copy(),
            is_normalized=self.is_normalized
        )
    
    def __len__(self) -> int:
        """Return the length of the time series."""
        return self.length
    
    def __repr__(self) -> str:
        """String representation of the TimeSeries."""
        return (
            f"TimeSeries(length={self.length}, "
            f"missing={self.missing_count}, "
            f"normalized={self.is_normalized})"
        )
    
    @classmethod
    def from_list(
        cls,
        values: List[Union[float, int, None]],
        timestamps: Optional[List[float]] = None,
        metadata: Optional[dict] = None
    ) -> 'TimeSeries':
        """
        Factory method to create TimeSeries from Python list.
        
        Args:
            values: List of numeric values (None treated as missing)
            timestamps: Optional list of timestamps
            metadata: Optional metadata dictionary
        
        Returns:
            TimeSeries instance
        """
        # Convert None to np.nan for missing values
        np_values = np.array([
            float(v) if v is not None else np.nan
            for v in values
        ], dtype=np.float64)
        
        np_timestamps = None
        if timestamps is not None:
            np_timestamps = np.array(timestamps, dtype=np.float64)
        
        return cls(
            values=np_values,
            timestamps=np_timestamps,
            metadata=metadata or {},
            is_normalized=False
        )