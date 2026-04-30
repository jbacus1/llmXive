"""
Synthetic Anomaly Dataset Generator for DPGMM Validation

Generates time series with known ground truth anomalies for testing
and validating the DPGMM anomaly detection model. Supports three
anomaly types: point, contextual, and collective anomalies.

Per US1 Assumptions: Synthetic data with known ground truth enables
independent testing without labeled real-world datasets.
"""

import os
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Tuple, Dict, List, Optional, Any, Literal

# Set random seed for reproducibility
np.random.seed(42)

@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection parameters."""
    anomaly_rate: float = 0.05  # Expected percentage of anomalous points
    point_anomaly_magnitude: float = 3.0  # Standard deviations from mean
    contextual_anomaly_duration: int = 10  # Number of points for contextual
    contextual_anomaly_shift: float = 2.0  # Mean shift for contextual
    collective_anomaly_length: int = 20  # Length of collective anomaly segments
    collective_anomaly_type: Literal['level_shift', 'variance_change', 'trend'] = 'level_shift'
    seed: int = 42
    
@dataclass
class SignalConfig:
    """Configuration for base signal generation parameters."""
    length: int = 1000  # Number of observations
    frequency: float = 1.0  # Signal frequency (cycles per 100 points)
    amplitude: float = 1.0  # Signal amplitude
    noise_std: float = 0.1  # Gaussian noise standard deviation
    trend_slope: float = 0.0  # Linear trend slope
    seed: int = 42
    
@dataclass
class SyntheticDataset:
    """Container for synthetic dataset with ground truth."""
    timestamps: List[float]
    values: List[float]
    ground_truth: List[Literal[0, 1]]  # 0 = normal, 1 = anomaly
    anomaly_type: List[str]  # 'normal', 'point', 'contextual', 'collective'
    config: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamps': self.timestamps,
            'values': self.values,
            'ground_truth': self.ground_truth,
            'anomaly_type': self.anomaly_type,
            'config': self.config,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyntheticDataset':
        """Create from dictionary."""
        return cls(
            timestamps=data['timestamps'],
            values=data['values'],
            ground_truth=data['ground_truth'],
            anomaly_type=data['anomaly_type'],
            config=data['config'],
            metadata=data['metadata']
        )

def generate_base_signal(config: SignalConfig) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a base time series signal with optional trend and noise.
    
    Args:
        config: Signal configuration parameters
        
    Returns:
        Tuple of (timestamps, values) arrays
    """
    np.random.seed(config.seed)
    
    n_points = config.length
    timestamps = np.arange(n_points)
    
    # Generate sinusoidal base signal
    signal = config.amplitude * np.sin(2 * np.pi * config.frequency * timestamps / 100)
    
    # Add linear trend
    signal += config.trend_slope * timestamps
    
    # Add Gaussian noise
    noise = np.random.normal(0, config.noise_std, n_points)
    signal += noise
    
    return timestamps, signal

def inject_point_anomalies(
    values: np.ndarray,
    anomaly_rate: float,
    magnitude: float,
    seed: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Inject point anomalies (isolated outliers) into the signal.
    
    Args:
        values: Base signal values
        anomaly_rate: Fraction of points to make anomalous
        magnitude: Number of standard deviations for outlier magnitude
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (modified_values, anomaly_indices)
    """
    np.random.seed(seed)
    n_points = len(values)
    n_anomalies = int(n_points * anomaly_rate)
    
    # Select random indices for point anomalies
    anomaly_indices = np.random.choice(n_points, size=n_anomalies, replace=False)
    
    # Calculate local statistics for magnitude calculation
    mean_val = np.mean(values)
    std_val = np.std(values)
    
    # Create copy and inject anomalies
    modified = values.copy()
    anomaly_signs = np.random.choice([-1, 1], size=n_anomalies)
    modified[anomaly_indices] = mean_val + anomaly_signs * magnitude * std_val
    
    return modified, anomaly_indices

def inject_contextual_anomalies(
    values: np.ndarray,
    anomaly_rate: float,
    duration: int,
    shift: float,
    seed: int
) -> Tuple[np.ndarray, List[int]]:
    """
    Inject contextual anomalies (values normal in isolation but anomalous
    given context) into the signal.
    
    Args:
        values: Base signal values
        anomaly_rate: Fraction of points to make anomalous
        duration: Number of consecutive points per anomaly segment
        shift: Mean shift for contextual anomaly
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (modified_values, anomaly_ranges) where ranges are (start, end)
    """
    np.random.seed(seed)
    n_points = len(values)
    n_anomalies = int(n_points * anomaly_rate)
    n_segments = max(1, n_anomalies // duration)
    
    modified = values.copy()
    anomaly_ranges = []
    used_indices = set()
    
    # Inject contextual anomaly segments
    attempts = 0
    while len(anomaly_ranges) < n_segments and attempts < n_segments * 10:
        start = np.random.randint(0, n_points - duration)
        end = start + duration
        
        # Check for overlap
        if not any(i in used_indices for i in range(start, end)):
            anomaly_ranges.append((start, end))
            mean_val = np.mean(values[start:end])
            modified[start:end] = mean_val + shift * np.std(values)
            used_indices.update(range(start, end))
        
        attempts += 1
    
    return modified, anomaly_ranges

def inject_collective_anomalies(
    values: np.ndarray,
    anomaly_rate: float,
    length: int,
    anomaly_type: Literal['level_shift', 'variance_change', 'trend'],
    seed: int
) -> Tuple[np.ndarray, List[Tuple[int, int]]]:
    """
    Inject collective anomalies (groups of points with anomalous behavior)
    into the signal.
    
    Args:
        values: Base signal values
        anomaly_rate: Fraction of points to make anomalous
        length: Length of each collective anomaly segment
        anomaly_type: Type of collective anomaly
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (modified_values, anomaly_ranges)
    """
    np.random.seed(seed)
    n_points = len(values)
    n_anomalies = int(n_points * anomaly_rate)
    n_segments = max(1, n_anomalies // length)
    
    modified = values.copy()
    anomaly_ranges = []
    used_indices = set()
    
    # Calculate base statistics
    base_mean = np.mean(values)
    base_std = np.std(values)
    
    # Inject collective anomaly segments
    attempts = 0
    while len(anomaly_ranges) < n_segments and attempts < n_segments * 10:
        start = np.random.randint(0, n_points - length)
        end = start + length
        
        # Check for overlap
        if not any(i in used_indices for i in range(start, end)):
            anomaly_ranges.append((start, end))
            
            if anomaly_type == 'level_shift':
                # Sudden shift in mean level
                shift = 3 * base_std
                modified[start:end] += np.random.choice([-1, 1]) * shift
            
            elif anomaly_type == 'variance_change':
                # Sudden increase in variance
                scale = 3.0
                center = np.mean(values[start:end])
                modified[start:end] = center + (values[start:end] - center) * scale
            
            elif anomaly_type == 'trend':
                # Sudden trend change within segment
                trend = np.linspace(-2 * base_std, 2 * base_std, length)
                modified[start:end] += trend
            
            used_indices.update(range(start, end))
        
        attempts += 1
    
    return modified, anomaly_ranges

def generate_synthetic_timeseries(
    signal_config: SignalConfig,
    anomaly_config: AnomalyConfig
) -> SyntheticDataset:
    """
    Generate a complete synthetic time series dataset with ground truth.
    
    Args:
        signal_config: Base signal configuration
        anomaly_config: Anomaly injection configuration
        
    Returns:
        SyntheticDataset with values and ground truth labels
    """
    # Generate base signal
    timestamps, values = generate_base_signal(signal_config)
    
    # Initialize ground truth (all normal)
    ground_truth = [0] * len(values)
    anomaly_type = ['normal'] * len(values)
    
    # Inject point anomalies
    values, point_indices = inject_point_anomalies(
        values,
        anomaly_config.anomaly_rate / 3,  # Divide rate among types
        anomaly_config.point_anomaly_magnitude,
        anomaly_config.seed
    )
    for idx in point_indices:
        ground_truth[idx] = 1
        anomaly_type[idx] = 'point'
    
    # Inject contextual anomalies
    values, contextual_ranges = inject_contextual_anomalies(
        values,
        anomaly_config.anomaly_rate / 3,
        anomaly_config.contextual_anomaly_duration,
        anomaly_config.contextual_anomaly_shift,
        anomaly_config.seed + 1
    )
    for start, end in contextual_ranges:
        for i in range(start, end):
            if i < len(ground_truth):
                ground_truth[i] = 1
                anomaly_type[i] = 'contextual'
    
    # Inject collective anomalies
    values, collective_ranges = inject_collective_anomalies(
        values,
        anomaly_config.anomaly_rate / 3,
        anomaly_config.collective_anomaly_length,
        anomaly_config.collective_anomaly_type,
        anomaly_config.seed + 2
    )
    for start, end in collective_ranges:
        for i in range(start, end):
            if i < len(ground_truth):
                ground_truth[i] = 1
                anomaly_type[i] = 'collective'
    
    # Compile metadata
    metadata = {
        'n_points': len(values),
        'n_anomalies': sum(ground_truth),
        'anomaly_rate': sum(ground_truth) / len(ground_truth),
        'point_anomalies': len(point_indices),
        'contextual_segments': len(contextual_ranges),
        'collective_segments': len(collective_ranges),
        'generated_at': str(np.datetime64('now'))
    }
    
    return SyntheticDataset(
        timestamps=timestamps.tolist(),
        values=values.tolist(),
        ground_truth=ground_truth,
        anomaly_type=anomaly_type,
        config={
            'signal': asdict(signal_config),
            'anomaly': asdict(anomaly_config)
        },
        metadata=metadata
    )

def save_synthetic_dataset(
    dataset: SyntheticDataset,
    output_path: str
) -> Path:
    """
    Save synthetic dataset to JSON file.
    
    Args:
        dataset: Synthetic dataset to save
        output_path: Path for output JSON file
        
    Returns:
        Path object for saved file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(dataset.to_dict(), f, indent=2)
    
    return output_path

def load_synthetic_dataset(input_path: str) -> SyntheticDataset:
    """
    Load synthetic dataset from JSON file.
    
    Args:
        input_path: Path to JSON file
        
    Returns:
        Loaded SyntheticDataset
    """
    input_path = Path(input_path)
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    return SyntheticDataset.from_dict(data)

def generate_validation_dataset(
    n_datasets: int = 3,
    length: int = 1000,
    anomaly_rate: float = 0.05,
    output_dir: str = 'data/processed/synthetic/'
) -> List[Path]:
    """
    Generate multiple validation datasets with varying parameters.
    
    Args:
        n_datasets: Number of datasets to generate
        length: Length of each time series
        anomaly_rate: Expected anomaly rate
        output_dir: Directory to save datasets
        
    Returns:
        List of paths to generated dataset files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    for i in range(n_datasets):
        # Vary parameters for diversity
        signal_config = SignalConfig(
            length=length,
            frequency=1.0 + 0.5 * i,
            amplitude=1.0,
            noise_std=0.1 + 0.05 * i,
            trend_slope=0.001 * i,
            seed=42 + i
        )
        
        anomaly_config = AnomalyConfig(
            anomaly_rate=anomaly_rate,
            point_anomaly_magnitude=3.0 + 0.5 * i,
            contextual_anomaly_duration=10,
            contextual_anomaly_shift=2.0 + 0.3 * i,
            collective_anomaly_length=20,
            collective_anomaly_type=['level_shift', 'variance_change', 'trend'][i % 3],
            seed=100 + i
        )
        
        dataset = generate_synthetic_timeseries(signal_config, anomaly_config)
        
        # Save dataset
        filename = f'synthetic_validation_{i+1:03d}.json'
        filepath = output_path / filename
        save_synthetic_dataset(dataset, str(filepath))
        
        generated_files.append(filepath)
    
    return generated_files

def main():
    """
    Main function to generate synthetic datasets for validation.
    
    This script generates synthetic time series with known ground truth
    anomalies for testing the DPGMM model.
    """
    # Output directory
    output_dir = 'projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/processed/synthetic/'
    
    print("Generating synthetic validation datasets...")
    
    # Generate 3 validation datasets
    files = generate_validation_dataset(
        n_datasets=3,
        length=1000,
        anomaly_rate=0.05,
        output_dir=output_dir
    )
    
    print(f"Generated {len(files)} synthetic datasets:")
    for f in files:
        dataset = load_synthetic_dataset(str(f))
        print(f"  {f.name}: {dataset.metadata['n_points']} points, "
              f"{dataset.metadata['n_anomalies']} anomalies "
              f"({dataset.metadata['anomaly_rate']:.2%})")
    
    print("\nSynthetic dataset generation complete.")
    print(f"Datasets saved to: {output_dir}")

if __name__ == '__main__':
    main()
