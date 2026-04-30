"""
Time-ordered train/test split utilities to prevent temporal data leakage.

This module implements explicit time-ordered splitting for time series data,
ensuring that future observations never leak into training data. All splits
respect the temporal ordering of observations.
"""

import os
import sys
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List, Union
import numpy as np
import pandas as pd

from ..models.time_series import TimeSeries

logger = logging.getLogger(__name__)


@dataclass
class TimeSplitConfig:
    """Configuration for time-ordered train/test splitting."""
    # Split ratio (train portion of total data, e.g., 0.8 for 80% train)
    train_ratio: float = 0.8
    # Optional fixed cutoff timestamp (if provided, overrides train_ratio)
    cutoff_timestamp: Optional[datetime] = None
    # Minimum observations required in each split
    min_train_obs: int = 100
    min_test_obs: int = 50
    # Whether to include a validation set (0.1 of remaining after train)
    include_validation: bool = True
    # Random seed for reproducibility (not used in time-based split, but kept for API)
    random_seed: int = 42
    # Gap between train and test (observations to exclude as buffer)
    gap_observations: int = 0


@dataclass
class TimeSplitResult:
    """Result of a time-ordered train/test split operation."""
    # Training data (TimeSeries or array)
    train_data: Any
    # Test data (TimeSeries or array)
    test_data: Any
    # Validation data if included (None otherwise)
    validation_data: Optional[Any] = None
    # Timestamp of split boundary
    split_timestamp: Optional[datetime] = None
    # Number of observations in each split
    train_count: int = 0
    test_count: int = 0
    validation_count: int = 0
    # Total observations processed
    total_count: int = 0
    # Timestamps in train set (start, end)
    train_time_range: Tuple[Optional[datetime], Optional[datetime]] = (None, None)
    # Timestamps in test set (start, end)
    test_time_range: Tuple[Optional[datetime], Optional[datetime]] = (None, None)
    # Timestamps in validation set (start, end)
    validation_time_range: Optional[Tuple[Optional[datetime], Optional[datetime]]] = None


def _ensure_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure DataFrame has a datetime index."""
    if not isinstance(df.index, pd.DatetimeIndex):
        # Try to find a timestamp column
        timestamp_cols = []
        for col in df.columns:
            if 'time' in col.lower() or 'date' in col.lower() or 'timestamp' in col.lower():
                timestamp_cols.append(col)
        
        if timestamp_cols:
            # Use the first timestamp-like column
            df = df.set_index(timestamp_cols[0])
            df.index = pd.to_datetime(df.index)
        else:
            # Create synthetic datetime index
            logger.warning("No timestamp column found, creating synthetic datetime index")
            dates = pd.date_range(
                start='2020-01-01',
                periods=len(df),
                freq='H'  # Hourly frequency by default
            )
            df.index = dates
    
    # Ensure index is sorted
    df = df.sort_index()
    return df


def _validate_split_sizes(
    train_count: int,
    test_count: int,
    validation_count: int,
    config: TimeSplitConfig
) -> None:
    """Validate that split sizes meet minimum requirements."""
    if train_count < config.min_train_obs:
        raise ValueError(
            f"Training set has {train_count} observations, "
            f"but minimum required is {config.min_train_obs}"
        )
    if test_count < config.min_test_obs:
        raise ValueError(
            f"Test set has {test_count} observations, "
            f"but minimum required is {config.min_test_obs}"
        )


def split_by_ratio(
    data: Union[pd.DataFrame, TimeSeries, np.ndarray],
    config: TimeSplitConfig
) -> TimeSplitResult:
    """
    Split time series data by time-ordered ratio.

    This ensures that all training data comes before all test data in time,
    preventing any temporal data leakage.

    Args:
        data: Input time series data (DataFrame, TimeSeries, or numpy array)
        config: TimeSplitConfig with split parameters

    Returns:
        TimeSplitResult with train, test, and optional validation splits

    Raises:
        ValueError: If data cannot be split according to configuration
    """
    logger.info(f"Starting time-ordered split with ratio {config.train_ratio}")

    # Convert to DataFrame if needed
    if isinstance(data, TimeSeries):
        df = data.to_dataframe()
    elif isinstance(data, np.ndarray):
        if data.ndim == 1:
            df = pd.DataFrame({'value': data})
        else:
            df = pd.DataFrame(data)
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")

    # Ensure datetime index
    df = _ensure_datetime_index(df)

    total_count = len(df)
    logger.info(f"Total observations: {total_count}")

    # Calculate split point
    train_count = int(total_count * config.train_ratio)
    
    # Apply gap if specified
    if config.gap_observations > 0:
        train_count = min(train_count, total_count - config.min_test_obs - config.gap_observations)
        test_start = train_count + config.gap_observations
    else:
        test_start = train_count

    test_count = total_count - test_start

    # Apply validation split if requested
    if config.include_validation and test_count > config.min_test_obs:
        validation_count = int(test_count * 0.1)
        validation_count = max(validation_count, config.min_test_obs // 2)
        validation_count = min(validation_count, test_count - config.min_test_obs)
        test_count = test_count - validation_count
        test_end = test_start + test_count
        validation_end = total_count
    else:
        validation_count = 0
        test_end = total_count

    # Validate split sizes
    _validate_split_sizes(train_count, test_count, validation_count, config)

    # Perform split
    train_data = df.iloc[:train_count]
    test_data = df.iloc[test_start:test_end]
    validation_data = df.iloc[test_end:validation_end] if validation_count > 0 else None

    # Get timestamp ranges
    train_time_range = (
        train_data.index.min() if len(train_data) > 0 else None,
        train_data.index.max() if len(train_data) > 0 else None
    )
    test_time_range = (
        test_data.index.min() if len(test_data) > 0 else None,
        test_data.index.max() if len(test_data) > 0 else None
    )
    validation_time_range = (
        (validation_data.index.min() if len(validation_data) > 0 else None,
         validation_data.index.max() if len(validation_data) > 0 else None)
        if validation_data is not None and len(validation_data) > 0 else None
    )

    split_timestamp = train_data.index.max() if len(train_data) > 0 else None

    logger.info(f"Split complete: train={train_count}, test={test_count}, validation={validation_count}")

    return TimeSplitResult(
        train_data=train_data,
        test_data=test_data,
        validation_data=validation_data,
        split_timestamp=split_timestamp,
        train_count=train_count,
        test_count=test_count,
        validation_count=validation_count,
        total_count=total_count,
        train_time_range=train_time_range,
        test_time_range=test_time_range,
        validation_time_range=validation_time_range
    )


def split_by_timestamp(
    data: Union[pd.DataFrame, TimeSeries, np.ndarray],
    cutoff_timestamp: datetime,
    config: Optional[TimeSplitConfig] = None
) -> TimeSplitResult:
    """
    Split time series data by a fixed timestamp cutoff.

    All data before (and including) the cutoff goes to training,
    all data after goes to testing.

    Args:
        data: Input time series data
        cutoff_timestamp: The timestamp to use as split boundary
        config: Optional TimeSplitConfig for validation parameters

    Returns:
        TimeSplitResult with train and test splits

    Raises:
        ValueError: If cutoff timestamp is invalid or splits are too small
    """
    if config is None:
        config = TimeSplitConfig()

    logger.info(f"Starting time-ordered split at timestamp {cutoff_timestamp}")

    # Convert to DataFrame if needed
    if isinstance(data, TimeSeries):
        df = data.to_dataframe()
    elif isinstance(data, np.ndarray):
        if data.ndim == 1:
            df = pd.DataFrame({'value': data})
        else:
            df = pd.DataFrame(data)
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")

    # Ensure datetime index
    df = _ensure_datetime_index(df)

    total_count = len(df)
    logger.info(f"Total observations: {total_count}")

    # Find closest index at or before cutoff
    cutoff_idx = df.index.get_loc(df.index[df.index <= cutoff_timestamp][-1]) \
        if len(df.index[df.index <= cutoff_timestamp]) > 0 else 0

    train_count = cutoff_idx + 1
    test_count = total_count - train_count

    # Validate split sizes
    _validate_split_sizes(train_count, test_count, 0, config)

    # Perform split
    train_data = df.iloc[:train_count]
    test_data = df.iloc[train_count:]

    # Get timestamp ranges
    train_time_range = (
        train_data.index.min() if len(train_data) > 0 else None,
        train_data.index.max() if len(train_data) > 0 else None
    )
    test_time_range = (
        test_data.index.min() if len(test_data) > 0 else None,
        test_data.index.max() if len(test_data) > 0 else None
    )

    logger.info(f"Split complete: train={train_count}, test={test_count}")

    return TimeSplitResult(
        train_data=train_data,
        test_data=test_data,
        validation_data=None,
        split_timestamp=cutoff_timestamp,
        train_count=train_count,
        test_count=test_count,
        validation_count=0,
        total_count=total_count,
        train_time_range=train_time_range,
        test_time_range=test_time_range,
        validation_time_range=None
    )


def save_split_metadata(
    result: TimeSplitResult,
    output_path: Path,
    dataset_name: str
) -> None:
    """
    Save split metadata to JSON for reproducibility.

    Args:
        result: TimeSplitResult to save
        output_path: Path to save JSON metadata
        dataset_name: Name of the dataset for documentation
    """
    metadata = {
        'dataset_name': dataset_name,
        'split_method': 'time_ordered',
        'total_observations': result.total_count,
        'train_observations': result.train_count,
        'test_observations': result.test_count,
        'validation_observations': result.validation_count,
        'train_time_range': {
            'start': result.train_time_range[0].isoformat() if result.train_time_range[0] else None,
            'end': result.train_time_range[1].isoformat() if result.train_time_range[1] else None
        },
        'test_time_range': {
            'start': result.test_time_range[0].isoformat() if result.test_time_range[0] else None,
            'end': result.test_time_range[1].isoformat() if result.test_time_range[1] else None
        },
        'validation_time_range': {
            'start': result.validation_time_range[0].isoformat() if result.validation_time_range and result.validation_time_range[0] else None,
            'end': result.validation_time_range[1].isoformat() if result.validation_time_range and result.validation_time_range[1] else None
        } if result.validation_time_range else None,
        'split_timestamp': result.split_timestamp.isoformat() if result.split_timestamp else None,
        'generated_at': datetime.now().isoformat()
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved split metadata to {output_path}")


def load_split_metadata(metadata_path: Path) -> Dict[str, Any]:
    """Load split metadata from JSON file."""
    with open(metadata_path, 'r') as f:
        return json.load(f)


def main() -> None:
    """
    Main entry point for command-line usage.

    Demonstrates time-ordered split on synthetic data and saves metadata.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Generate synthetic time series for demonstration
    logger.info("Generating synthetic time series for demonstration")
    np.random.seed(42)
    n_observations = 1000
    timestamps = pd.date_range(start='2020-01-01', periods=n_observations, freq='H')
    values = np.sin(np.arange(n_observations) * 0.1) + np.random.normal(0, 0.1, n_observations)
    
    df = pd.DataFrame({'value': values}, index=timestamps)
    df.to_csv('data/processed/synthetic_demo.csv')
    logger.info("Saved synthetic data to data/processed/synthetic_demo.csv")

    # Configure split
    config = TimeSplitConfig(
        train_ratio=0.8,
        include_validation=True,
        min_train_obs=100,
        min_test_obs=50
    )

    # Perform split
    result = split_by_ratio(df, config)

    # Save splits
    output_dir = Path('data/processed/splits')
    output_dir.mkdir(parents=True, exist_ok=True)

    result.train_data.to_csv(output_dir / 'synthetic_demo_train.csv')
    result.test_data.to_csv(output_dir / 'synthetic_demo_test.csv')
    if result.validation_data is not None:
        result.validation_data.to_csv(output_dir / 'synthetic_demo_validation.csv')

    # Save metadata
    save_split_metadata(result, output_dir / 'synthetic_demo_split_metadata.json', 'synthetic_demo')

    # Print summary
    print(f"\n=== Time-Ordered Split Summary ===")
    print(f"Dataset: synthetic_demo")
    print(f"Total observations: {result.total_count}")
    print(f"Train: {result.train_count} observations")
    print(f"  Time range: {result.train_time_range[0]} to {result.train_time_range[1]}")
    print(f"Test: {result.test_count} observations")
    print(f"  Time range: {result.test_time_range[0]} to {result.test_time_range[1]}")
    if result.validation_count > 0:
        print(f"Validation: {result.validation_count} observations")
        print(f"  Time range: {result.validation_time_range[0]} to {result.validation_time_range[1]}")
    print(f"Split timestamp: {result.split_timestamp}")
    print(f"=====================================\n")

    logger.info("Time-ordered split demonstration complete")


if __name__ == '__main__':
    main()
