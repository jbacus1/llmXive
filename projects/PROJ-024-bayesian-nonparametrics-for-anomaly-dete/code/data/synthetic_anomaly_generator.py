"""
Synthetic Anomaly Dataset Generator for DPGMM Validation

Generates controlled synthetic time series data with known ground truth anomalies
for validation of the Bayesian Nonparametrics anomaly detection system.

Supports multiple anomaly types:
- Point anomalies: isolated extreme values
- Contextual anomalies: values anomalous in local context
- Collective anomalies: sequences of anomalous values

Usage:
    python code/data/synthetic_anomaly_generator.py [--config path/to/config.yaml]

Output:
    data/synthetic/time_series_<id>.csv - Time series data
    data/synthetic/ground_truth_<id>.csv - Anomaly labels
    data/synthetic/metadata_<id>.json - Generation metadata
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logger import get_logger

logger = get_logger(__name__)


class SyntheticAnomalyGenerator:
    """
    Generates synthetic time series data with known ground truth anomalies.

    This class creates deterministic, reproducible datasets for testing and
    validating the DPGMM anomaly detection system. All random operations use
    seeded NumPy random generators for reproducibility.

    Attributes:
        config: Configuration dictionary with generation parameters
        rng: Seeded numpy random number generator
        output_dir: Directory to save generated artifacts
    """

    def __init__(self, config_path: str, seed: Optional[int] = None):
        """
        Initialize the synthetic data generator.

        Args:
            config_path: Path to config.yaml with generation parameters
            seed: Optional random seed (overrides config if provided)
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Use provided seed or from config
        if seed is not None:
            self.seed = seed
        else:
            self.seed = self.config.get('random', {}).get('seed', 42)

        self.rng = np.random.default_rng(self.seed)

        # Ensure synthetic data directory exists
        self.output_dir = Path('data/synthetic')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized SyntheticAnomalyGenerator with seed {self.seed}")

    def generate_base_timeseries(
        self,
        n_points: int,
        frequency: str = 'D',
        include_trend: bool = True,
        include_seasonality: bool = True,
        noise_level: float = 0.1
    ) -> pd.DataFrame:
        """
        Generate a base time series with configurable components.

        Args:
            n_points: Number of observations to generate
            frequency: Pandas frequency string (e.g., 'D' for daily)
        include_trend: Whether to include linear trend
            include_seasonality: Whether to include seasonal component
            noise_level: Standard deviation of Gaussian noise

        Returns:
            DataFrame with 'timestamp' and 'value' columns
        """
        logger.debug(f"Generating base time series: {n_points} points")

        # Generate timestamps
        timestamps = pd.date_range(
            start='2024-01-01',
            periods=n_points,
            freq=frequency
        )

        # Generate base components
        t = np.arange(n_points)

        # Linear trend
        trend = np.zeros(n_points)
        if include_trend:
            trend_slope = self.rng.uniform(0.01, 0.1)
            trend = trend_slope * t

        # Seasonal component
        seasonal = np.zeros(n_points)
        if include_seasonality:
            # Use a period between 7 and 30 days
            period = self.rng.integers(7, 31)
            amplitude = self.rng.uniform(0.5, 2.0)
            seasonal = amplitude * np.sin(2 * np.pi * t / period)

        # Gaussian noise
        noise = self.rng.normal(0, noise_level, n_points)

        # Combine components
        values = trend + seasonal + noise

        df = pd.DataFrame({
            'timestamp': timestamps,
            'value': values
        })

        logger.debug(f"Generated base time series with range [{values.min():.3f}, {values.max():.3f}]")
        return df

    def inject_point_anomalies(
        self,
        df: pd.DataFrame,
        n_anomalies: int,
        magnitude_range: Tuple[float, float] = (3.0, 6.0)
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Inject point anomalies (isolated extreme values).

        Args:
            df: Input time series DataFrame
            n_anomalies: Number of anomalies to inject
            magnitude_range: (min, max) multiplier of std dev for anomaly magnitude

        Returns:
            Tuple of (modified DataFrame, ground truth labels)
        """
        logger.debug(f"Injecting {n_anomalies} point anomalies")

        df = df.copy()
        n_points = len(df)

        # Select random indices for anomalies (avoid first/last 10%)
        min_idx = int(n_points * 0.1)
        max_idx = int(n_points * 0.9)
        anomaly_indices = self.rng.choice(
            range(min_idx, max_idx),
            size=n_anomalies,
            replace=False
        )

        # Calculate magnitude based on data statistics
        std_val = df['value'].std()
        ground_truth = pd.DataFrame({
            'timestamp': df['timestamp'],
            'is_anomaly': False
        })

        for idx in anomaly_indices:
            # Random direction (positive or negative)
            direction = self.rng.choice([-1, 1])
            magnitude = self.rng.uniform(*magnitude_range)
            anomaly_value = df.loc[idx, 'value'] + direction * magnitude * std_val
            df.loc[idx, 'value'] = anomaly_value
            ground_truth.loc[idx, 'is_anomaly'] = True

        logger.info(f"Injected {len(anomaly_indices)} point anomalies")
        return df, ground_truth

    def inject_contextual_anomalies(
        self,
        df: pd.DataFrame,
        n_anomalies: int,
        window_size: int = 10,
        deviation_factor: float = 2.5
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Inject contextual anomalies (values anomalous relative to local context).

        Args:
            df: Input time series DataFrame
            n_anomalies: Number of anomalies to inject
            window_size: Size of local window for context comparison
            deviation_factor: How many local std devs away to place anomaly

        Returns:
            Tuple of (modified DataFrame, ground truth labels)
        """
        logger.debug(f"Injecting {n_anomalies} contextual anomalies")

        df = df.copy()
        n_points = len(df)

        # Select random indices (avoid edges)
        min_idx = window_size
        max_idx = n_points - window_size
        anomaly_indices = self.rng.choice(
            range(min_idx, max_idx),
            size=n_anomalies,
            replace=False
        )

        ground_truth = pd.DataFrame({
            'timestamp': df['timestamp'],
            'is_anomaly': False
        })

        for idx in anomaly_indices:
            # Calculate local statistics
            start = max(0, idx - window_size)
            end = min(n_points, idx + window_size)
            local_values = df.loc[start:end, 'value'].values
            local_mean = np.mean(local_values)
            local_std = np.std(local_values)

            # Create anomaly that deviates from local context
            direction = self.rng.choice([-1, 1])
            anomaly_value = local_mean + direction * deviation_factor * local_std
            df.loc[idx, 'value'] = anomaly_value
            ground_truth.loc[idx, 'is_anomaly'] = True

        logger.info(f"Injected {len(anomaly_indices)} contextual anomalies")
        return df, ground_truth

    def inject_collective_anomalies(
        self,
        df: pd.DataFrame,
        n_sequences: int,
        sequence_length_range: Tuple[int, int] = (5, 15),
        shift_amount: float = 3.0
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Inject collective anomalies (sequences of anomalous values).

        Args:
            df: Input time series DataFrame
            n_sequences: Number of anomalous sequences to inject
            sequence_length_range: (min, max) length of anomalous sequences
            shift_amount: Amount to shift the sequence values

        Returns:
            Tuple of (modified DataFrame, ground truth labels)
        """
        logger.debug(f"Injecting {n_sequences} collective anomaly sequences")

        df = df.copy()
        n_points = len(df)

        # Calculate statistics for shift
        std_val = df['value'].std()

        ground_truth = pd.DataFrame({
            'timestamp': df['timestamp'],
            'is_anomaly': False
        })

        for _ in range(n_sequences):
            # Select random start position (avoid edges)
            min_idx = 10
            max_idx = n_points - 20
            start_idx = self.rng.integers(min_idx, max_idx)

            # Select random length
            length = self.rng.integers(*sequence_length_range)
            end_idx = min(start_idx + length, n_points - 1)

            # Determine shift direction
            direction = self.rng.choice([-1, 1])

            # Apply shift to entire sequence
            shift = direction * shift_amount * std_val
            df.loc[start_idx:end_idx, 'value'] += shift

            # Mark as anomalies
            ground_truth.loc[start_idx:end_idx, 'is_anomaly'] = True

            logger.debug(f"Injected sequence from {start_idx} to {end_idx}")

        logger.info(f"Injected {n_sequences} collective anomaly sequences")
        return df, ground_truth

    def generate_dataset(
        self,
        dataset_id: str,
        n_points: int = 1000,
        anomaly_config: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate a complete synthetic dataset with all anomaly types.

        Args:
            dataset_id: Unique identifier for this dataset
            n_points: Number of time series points
            anomaly_config: Optional override for anomaly injection config

        Returns:
            Dict with paths to generated artifacts
        """
        logger.info(f"Generating synthetic dataset: {dataset_id}")

        # Use config defaults if not overridden
        if anomaly_config is None:
          anomaly_config = self.config.get('synthetic_data', {}).get(
              'anomaly_config', {}
          )

        # Generate base time series
        df = self.generate_base_timeseries(
            n_points=n_points,
            frequency=anomaly_config.get('frequency', 'D'),
            include_trend=anomaly_config.get('include_trend', True),
            include_seasonality=anomaly_config.get('include_seasonality', True),
            noise_level=anomaly_config.get('noise_level', 0.1)
        )

        # Collect ground truth
        all_ground_truth = pd.DataFrame({
            'timestamp': df['timestamp'],
            'is_anomaly': False
        })

        # Inject point anomalies
        n_point = anomaly_config.get('n_point_anomalies', 5)
        if n_point > 0:
            df, point_gt = self.inject_point_anomalies(
                df,
                n_point,
                magnitude_range=anomaly_config.get(
                    'point_magnitude_range', (3.0, 6.0)
                )
            )
            all_ground_truth['is_anomaly'] |= point_gt['is_anomaly']

        # Inject contextual anomalies
        n_contextual = anomaly_config.get('n_contextual_anomalies', 3)
        if n_contextual > 0:
            df, contextual_gt = self.inject_contextual_anomalies(
                df,
                n_contextual,
                window_size=anomaly_config.get('contextual_window_size', 10),
                deviation_factor=anomaly_config.get('contextual_deviation', 2.5)
            )
            all_ground_truth['is_anomaly'] |= contextual_gt['is_anomaly']

        # Inject collective anomalies
        n_collective = anomaly_config.get('n_collective_anomalies', 2)
        if n_collective > 0:
            df, collective_gt = self.inject_collective_anomalies(
                df,
                n_collective,
                sequence_length_range=anomaly_config.get(
                    'collective_length_range', (5, 15)
                ),
                shift_amount=anomaly_config.get('collective_shift', 3.0)
            )
            all_ground_truth['is_anomaly'] |= collective_gt['is_anomaly']

        # Calculate anomaly statistics
        n_anomalies = all_ground_truth['is_anomaly'].sum()
        anomaly_rate = n_anomalies / n_points

        # Save artifacts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        time_series_path = self.output_dir / f'time_series_{dataset_id}_{timestamp}.csv'
        ground_truth_path = self.output_dir / f'ground_truth_{dataset_id}_{timestamp}.csv'
        metadata_path = self.output_dir / f'metadata_{dataset_id}_{timestamp}.json'

        df.to_csv(time_series_path, index=False)
        all_ground_truth.to_csv(ground_truth_path, index=False)

        # Create metadata
        metadata = {
            'dataset_id': dataset_id,
            'seed': self.seed,
            'n_points': n_points,
            'n_anomalies': int(n_anomalies),
            'anomaly_rate': float(anomaly_rate),
            'anomaly_types': {
                'point': n_point,
                'contextual': n_contextual,
                'collective': n_collective
            },
            'config': anomaly_config,
            'generated_at': timestamp
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(
            f"Generated dataset {dataset_id}: {n_anomalies} anomalies "
            f"({anomaly_rate:.2%} rate)"
        )

        return {
            'time_series': str(time_series_path),
            'ground_truth': str(ground_truth_path),
            'metadata': str(metadata_path)
        }


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Generate synthetic anomaly datasets for DPGMM validation'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection/code/config.yaml',
        help='Path to config.yaml'
    )
    parser.add_argument(
        '--dataset-id',
        type=str,
        default='test',
        help='Dataset identifier'
    )
    parser.add_argument(
        '--n-points',
        type=int,
        default=1000,
        help='Number of time series points'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed (overrides config)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel('DEBUG')

    # Generate dataset
    generator = SyntheticAnomalyGenerator(args.config, args.seed)
    artifacts = generator.generate_dataset(
        dataset_id=args.dataset_id,
        n_points=args.n_points
    )

    print(f"Generated artifacts:")
    for key, path in artifacts.items():
        print(f"  {key}: {path}")


if __name__ == '__main__':
    main()
