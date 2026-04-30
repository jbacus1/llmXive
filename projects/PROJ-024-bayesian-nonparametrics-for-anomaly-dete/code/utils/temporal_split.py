"""
Temporal train/test split utilities for time series anomaly detection.

This module implements explicit time-ordered splitting to prevent temporal
data leakage. All splits are performed chronologically, never randomly,
ensuring that future observations never appear in the training set.

Per Constitution Principle III: All data splits must be documented with
exact timestamps for reproducibility.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List, Union
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


@dataclass
class TemporalSplitConfig:
    """Configuration for temporal train/test splitting."""
    train_ratio: float = 0.8
    test_ratio: float = 0.2
    min_train_observations: int = 1000
    min_test_observations: int = 200
    timestamp_column: str = 'timestamp'
    value_column: str = 'value'
    validate_timestamps: bool = True


@dataclass
class TemporalSplitResult:
    """Result of a temporal train/test split operation."""
    train_data: pd.DataFrame
    test_data: pd.DataFrame
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    train_observations: int
    test_observations: int
    split_timestamp: datetime
    config: TemporalSplitConfig
    metadata: Dict[str, Any] = field(default_factory=dict)


def load_timeseries_data(
    data_path: Union[str, Path],
    timestamp_column: str = 'timestamp',
    value_column: str = 'value',
    date_format: Optional[str] = None
) -> pd.DataFrame:
    """
    Load time series data from CSV or similar format.

    Args:
        data_path: Path to the data file
        timestamp_column: Name of the timestamp column
        value_column: Name of the value column
        date_format: Optional datetime format string for parsing

    Returns:
        DataFrame with timestamp and value columns, sorted chronologically
    """
    data_path = Path(data_path)

    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    logger.info(f"Loading time series data from {data_path}")

    # Handle different file formats
    if data_path.suffix == '.csv':
        df = pd.read_csv(data_path)
    elif data_path.suffix == '.json':
        df = pd.read_json(data_path)
    elif data_path.suffix in ['.parquet', '.pkl', '.pickle']:
        df = pd.read_parquet(data_path) if data_path.suffix == '.parquet' else pd.read_pickle(data_path)
    else:
        # Default to CSV
        df = pd.read_csv(data_path)

    # Validate required columns
    required_cols = [timestamp_column, value_column]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in {data_path}. "
                           f"Available columns: {list(df.columns)}")

    # Parse timestamps
    if date_format:
        df[timestamp_column] = pd.to_datetime(df[timestamp_column], format=date_format)
    else:
        df[timestamp_column] = pd.to_datetime(df[timestamp_column])

    # Sort by timestamp to ensure chronological order
    df = df.sort_values(timestamp_column).reset_index(drop=True)

    # Validate monotonic timestamps (no backwards time travel)
    timestamps = df[timestamp_column].values
    if np.any(np.diff(timestamps) < 0):
        logger.warning("Non-monotonic timestamps detected. Data will be sorted.")
        df = df.sort_values(timestamp_column).reset_index(drop=True)

    logger.info(f"Loaded {len(df)} observations from {df[timestamp_column].min()} to {df[timestamp_column].max()}")

    return df


def compute_split_timestamp(
    df: pd.DataFrame,
    timestamp_column: str,
    train_ratio: float
) -> datetime:
    """
    Compute the split timestamp based on observation count ratio.

    Args:
        df: Time series DataFrame
        timestamp_column: Name of timestamp column
        train_ratio: Fraction of data to use for training (0-1)

    Returns:
        Timestamp that divides train and test sets
    """
    n_total = len(df)
    n_train = max(int(n_total * train_ratio), 1)

    # Split timestamp is the timestamp of the last training observation
    split_timestamp = df.iloc[n_train - 1][timestamp_column]

    logger.info(f"Splitting at observation {n_train}/{n_total} (timestamp: {split_timestamp})")

    return split_timestamp


def apply_temporal_split(
    df: pd.DataFrame,
    timestamp_column: str,
    value_column: str,
    train_ratio: float = 0.8,
    min_train_observations: int = 1000,
    min_test_observations: int = 200
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Apply temporal train/test split to time series data.

    CRITICAL: This function ensures temporal ordering is preserved.
    Future observations never leak into the training set.

    Args:
        df: Time series DataFrame with timestamp column
        timestamp_column: Name of timestamp column
        value_column: Name of value column
        train_ratio: Fraction for training set (0-1)
        min_train_observations: Minimum training observations required
        min_test_observations: Minimum test observations required

    Returns:
        Tuple of (train_df, test_df) split chronologically

    Raises:
        ValueError: If dataset is too small for the requested split
    """
    n_total = len(df)
    n_train = max(int(n_total * train_ratio), 1)

    # Validate minimum sizes
    if n_train < min_train_observations:
        raise ValueError(
            f"Dataset too small for training: {n_train} observations < {min_train_observations} minimum. "
            f"Total observations: {n_total}"
        )

    n_test = n_total - n_train
    if n_test < min_test_observations:
        raise ValueError(
            f"Dataset too small for test set: {n_test} observations < {min_test_observations} minimum. "
            f"Total observations: {n_total}"
        )

    # Perform chronological split
    train_df = df.iloc[:n_train].copy()
    test_df = df.iloc[n_train:].copy()

    # Verify no temporal overlap
    train_end = train_df[timestamp_column].max()
    test_start = test_df[timestamp_column].min()

    if train_end >= test_start:
        logger.warning(
            f"Temporal overlap detected: train_end={train_end}, test_start={test_start}"
        )

    logger.info(f"Temporal split complete: train={len(train_df)}, test={len(test_df)}")

    return train_df, test_df


def perform_temporal_split_with_metadata(
    data_path: Union[str, Path],
    config: Optional[TemporalSplitConfig] = None
) -> TemporalSplitResult:
    """
    Perform complete temporal split with full metadata documentation.

    This is the recommended entry point for production use as it provides
    complete provenance documentation per Constitution Principle III.

    Args:
        data_path: Path to time series data file
        config: Optional TemporalSplitConfig (uses defaults if None)

    Returns:
        TemporalSplitResult with all split metadata documented
    """
    if config is None:
        config = TemporalSplitConfig()

    # Load data
    df = load_timeseries_data(
        data_path=data_path,
        timestamp_column=config.timestamp_column,
        value_column=config.value_column,
        date_format=None  # Auto-detect
    )

    # Compute split
    split_timestamp = compute_split_timestamp(
        df=df,
        timestamp_column=config.timestamp_column,
        train_ratio=config.train_ratio
    )

    # Apply split
    train_df, test_df = apply_temporal_split(
        df=df,
        timestamp_column=config.timestamp_column,
        value_column=config.value_column,
        train_ratio=config.train_ratio,
        min_train_observations=config.min_train_observations,
        min_test_observations=config.min_test_observations
    )

    # Extract metadata
    result = TemporalSplitResult(
        train_data=train_df,
        test_data=test_df,
        train_start=train_df[config.timestamp_column].min(),
        train_end=train_df[config.timestamp_column].max(),
        test_start=test_df[config.timestamp_column].min(),
        test_end=test_df[config.timestamp_column].max(),
        train_observations=len(train_df),
        test_observations=len(test_df),
        split_timestamp=split_timestamp,
        config=config,
        metadata={
            'total_observations': len(df),
            'data_source': str(data_path),
            'split_ratio': f"{config.train_ratio:.1f}/{config.test_ratio:.1f}",
            'split_method': 'temporal_chronological',
            'leakage_prevention': 'future_data_excluded_from_training',
            'timestamp_column': config.timestamp_column,
            'value_column': config.value_column,
            'generated_at': datetime.now().isoformat()
        }
    )

    logger.info(f"Temporal split complete with full metadata documentation")

    return result


def save_split_metadata(
    result: TemporalSplitResult,
    output_path: Union[str, Path]
) -> None:
    """
    Save temporal split metadata to a file for reproducibility.

    Args:
        result: TemporalSplitResult from perform_temporal_split_with_metadata
        output_path: Path to save metadata JSON
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    metadata = {
        'train_start': result.train_start.isoformat(),
        'train_end': result.train_end.isoformat(),
        'test_start': result.test_start.isoformat(),
        'test_end': result.test_end.isoformat(),
        'split_timestamp': result.split_timestamp.isoformat(),
        'train_observations': result.train_observations,
        'test_observations': result.test_observations,
        'total_observations': result.train_observations + result.test_observations,
        'train_ratio': result.config.train_ratio,
        'test_ratio': result.config.test_ratio,
        'timestamp_column': result.config.timestamp_column,
        'value_column': result.config.value_column,
        'data_source': result.metadata.get('data_source', 'unknown'),
        'generated_at': result.metadata.get('generated_at', datetime.now().isoformat()),
        'leakage_prevention': 'temporal_ordering_maintained'
    }

    import json
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Split metadata saved to {output_path}")


def validate_no_temporal_leakage(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    timestamp_column: str
) -> bool:
    """
    Validate that no temporal leakage exists between train and test sets.

    Args:
        train_df: Training DataFrame
        test_df: Test DataFrame
        timestamp_column: Name of timestamp column

    Returns:
        True if no leakage detected, False otherwise
    """
    train_max = train_df[timestamp_column].max()
    test_min = test_df[timestamp_column].min()

    no_leakage = train_max < test_min

    if not no_leakage:
        logger.error(
            f"TEMPORAL LEAKAGE DETECTED: train_max={train_max}, test_min={test_min}"
        )

    return no_leakage


def main():
    """
    Command-line entry point for temporal split utility.

    Usage:
        python temporal_split.py --data data/raw/electricity.csv --output data/processed/split_metadata.json
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Temporal train/test split for time series')
    parser.add_argument('--data', required=True, help='Path to time series CSV file')
    parser.add_argument('--output', required=True, help='Path to save split metadata JSON')
    parser.add_argument('--train-ratio', type=float, default=0.8, help='Training set ratio (0-1)')
    parser.add_argument('--timestamp-col', default='timestamp', help='Timestamp column name')
    parser.add_argument('--value-col', default='value', help='Value column name')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    try:
        config = TemporalSplitConfig(
            train_ratio=args.train_ratio,
            timestamp_column=args.timestamp_col,
            value_column=args.value_col
        )

        result = perform_temporal_split_with_metadata(args.data, config)

        # Save metadata
        save_split_metadata(result, args.output)

        # Validate no leakage
        if validate_no_temporal_leakage(
            result.train_data,
            result.test_data,
            args.timestamp_col
        ):
            print(f"✓ Temporal split validated: no leakage detected")
            print(f"  Train: {result.train_observations} obs from {result.train_start} to {result.train_end}")
            print(f"  Test:  {result.test_observations} obs from {result.test_start} to {result.test_end}")
        else:
            print(f"✗ TEMPORAL LEAKAGE DETECTED - ABORTING")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Temporal split failed: {e}")
        raise


if __name__ == '__main__':
    main()
