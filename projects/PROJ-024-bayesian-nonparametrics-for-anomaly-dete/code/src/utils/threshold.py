"""
Threshold Calibration Module for Anomaly Detection

Provides adaptive threshold computation for anomaly score calibration
without requiring labeled data. Supports both single-dataset and
multi-dataset calibration scenarios.

API Surface (public names):
- AdaptiveThresholdConfig
- ThresholdCalibrationResult
- MultiDatasetThresholdConfig
- MultiDatasetCalibrationResult
- compute_adaptive_threshold
- calibrate_threshold
- validate_anomaly_rate
- calibrate_thresholds_across_datasets
- aggregate_multi_dataset_statistics
- main
"""

import numpy as np
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AdaptiveThresholdConfig:
    """Configuration for adaptive threshold computation."""
    percentile: float = 95.0  # Default 95th percentile
    min_anomaly_rate: float = 0.01  # Minimum expected anomaly rate
    max_anomaly_rate: float = 0.10  # Maximum expected anomaly rate
    min_samples: int = 100  # Minimum samples required for calibration
    confidence_level: float = 0.95  # Confidence level for bounds
    smoothing_factor: float = 0.1  # For threshold smoothing across updates


@dataclass
class ThresholdCalibrationResult:
    """Result of single-dataset threshold calibration."""
    threshold: float
    anomaly_rate: float
    score_mean: float
    score_std: float
    num_samples: int
    calibration_date: str
    method: str = "percentile"
    bounds: Tuple[float, float] = field(default=(0.0, 1.0))


@dataclass
class MultiDatasetThresholdConfig:
    """Configuration for multi-dataset threshold calibration."""
    aggregation_method: str = "weighted_mean"  # weighted_mean, median, robust_mean
    weight_by_sample_size: bool = True
    min_datasets: int = 2  # Minimum datasets required
    outlier_removal: bool = True
    outlier_threshold: float = 3.0  # Standard deviations for outlier removal
    target_anomaly_rate: float = 0.05  # Target anomaly rate across datasets
    dataset_weights: Optional[Dict[str, float]] = None  # Manual weights per dataset


@dataclass
class MultiDatasetCalibrationResult:
    """Result of multi-dataset threshold calibration."""
    global_threshold: float
    per_dataset_thresholds: Dict[str, float]
    per_dataset_rates: Dict[str, float]
    aggregate_statistics: Dict[str, float]
    num_datasets: int
    calibration_date: str
    method: str
    validation_passed: bool
    validation_message: str = ""


def compute_adaptive_threshold(
    scores: np.ndarray,
    config: AdaptiveThresholdConfig
) -> Tuple[float, Dict[str, float]]:
    """
    Compute adaptive threshold using percentile-based method.

    Args:
        scores: Array of anomaly scores
        config: AdaptiveThresholdConfig with parameters

    Returns:
        Tuple of (threshold, statistics_dict)
    """
    if len(scores) < config.min_samples:
        logger.warning(
            f"Only {len(scores)} samples, minimum is {config.min_samples}. "
            "Proceeding with caution."
        )

    # Compute basic statistics
    score_mean = np.mean(scores)
    score_std = np.std(scores)
    score_min = np.min(scores)
    score_max = np.max(scores)

    # Compute percentile-based threshold
    threshold = np.percentile(scores, config.percentile)

    # Adjust threshold to maintain anomaly rate bounds
    anomaly_rate = np.mean(scores >= threshold)

    if anomaly_rate < config.min_anomaly_rate:
        # Lower threshold to increase anomaly rate
        target_percentile = 100 * (1 - config.min_anomaly_rate)
        threshold = np.percentile(scores, target_percentile)
        logger.info(
            f"Adjusted threshold to maintain min anomaly rate: "
            f"{config.min_anomaly_rate}"
        )
    elif anomaly_rate > config.max_anomaly_rate:
        # Raise threshold to decrease anomaly rate
        target_percentile = 100 * (1 - config.max_anomaly_rate)
        threshold = np.percentile(scores, target_percentile)
        logger.info(
            f"Adjusted threshold to maintain max anomaly rate: "
            f"{config.max_anomaly_rate}"
        )

    statistics = {
        'mean': score_mean,
        'std': score_std,
        'min': score_min,
        'max': score_max,
        'anomaly_rate': anomaly_rate,
        'num_samples': len(scores)
    }

    return threshold, statistics


def validate_anomaly_rate(
    anomaly_rate: float,
    config: AdaptiveThresholdConfig
) -> Tuple[bool, str]:
    """
    Validate that anomaly rate is within acceptable bounds.

    Args:
        anomaly_rate: Computed anomaly rate
        config: AdaptiveThresholdConfig

    Returns:
        Tuple of (is_valid, message)
    """
    if anomaly_rate < config.min_anomaly_rate:
        return False, (
            f"Anomaly rate {anomaly_rate:.4f} below minimum "
            f"{config.min_anomaly_rate}"
        )
    elif anomaly_rate > config.max_anomaly_rate:
        return False, (
            f"Anomaly rate {anomaly_rate:.4f} above maximum "
            f"{config.max_anomaly_rate}"
        )
    return True, f"Anomaly rate {anomaly_rate:.4f} within bounds"


def calibrate_threshold(
    scores: np.ndarray,
    config: AdaptiveThresholdConfig
) -> ThresholdCalibrationResult:
    """
    Full calibration workflow for single dataset.

    Args:
        scores: Array of anomaly scores
        config: AdaptiveThresholdConfig

    Returns:
        ThresholdCalibrationResult
    """
    threshold, stats = compute_adaptive_threshold(scores, config)
    is_valid, message = validate_anomaly_rate(stats['anomaly_rate'], config)

    return ThresholdCalibrationResult(
        threshold=threshold,
        anomaly_rate=stats['anomaly_rate'],
        score_mean=stats['mean'],
        score_std=stats['std'],
        num_samples=stats['num_samples'],
        calibration_date=datetime.now().isoformat(),
        method=config.percentile,
        bounds=(config.min_anomaly_rate, config.max_anomaly_rate)
    )


def aggregate_multi_dataset_statistics(
    dataset_results: Dict[str, ThresholdCalibrationResult],
    config: MultiDatasetThresholdConfig
) -> Dict[str, float]:
    """
    Aggregate statistics across multiple calibrated datasets.

    Args:
        dataset_results: Dict mapping dataset name to calibration result
        config: MultiDatasetThresholdConfig

    Returns:
        Dictionary of aggregate statistics
    """
    thresholds = [r.threshold for r in dataset_results.values()]
    anomaly_rates = [r.anomaly_rate for r in dataset_results.values()]
    sample_sizes = [r.num_samples for r in dataset_results.values()]

    # Compute weights based on sample size
    if config.weight_by_sample_size:
        weights = np.array(sample_sizes) / np.sum(sample_sizes)
    else:
        weights = np.ones(len(thresholds)) / len(thresholds)

    # Remove outliers if configured
    if config.outlier_removal and len(thresholds) > 2:
        mean_thresh = np.mean(thresholds)
        std_thresh = np.std(thresholds)
        if std_thresh > 0:
            z_scores = np.abs((np.array(thresholds) - mean_thresh) / std_thresh)
            valid_indices = z_scores < config.outlier_threshold
            thresholds = [t for t, valid in zip(thresholds, valid_indices) if valid]
            weights = np.array(sample_sizes) / np.sum(sample_sizes)

    # Aggregate threshold using configured method
    if config.aggregation_method == "weighted_mean":
        global_threshold = np.average(thresholds, weights=weights)
    elif config.aggregation_method == "median":
        global_threshold = np.median(thresholds)
    elif config.aggregation_method == "robust_mean":
        global_threshold = np.mean(thresholds)
    else:
        global_threshold = np.mean(thresholds)

    return {
        'global_threshold': float(global_threshold),
        'mean_threshold': float(np.mean(thresholds)),
        'std_threshold': float(np.std(thresholds)),
        'mean_anomaly_rate': float(np.mean(anomaly_rates)),
        'std_anomaly_rate': float(np.std(anomaly_rates)),
        'total_samples': int(np.sum(sample_sizes)),
        'num_datasets': len(dataset_results)
    }


def calibrate_thresholds_across_datasets(
    dataset_scores: Dict[str, np.ndarray],
    multi_config: MultiDatasetThresholdConfig,
    base_config: Optional[AdaptiveThresholdConfig] = None
) -> MultiDatasetCalibrationResult:
    """
    Calibrate thresholds across multiple datasets without labeled data.

    This function implements US3 acceptance scenario 3 by:
    1. Computing per-dataset adaptive thresholds
    2. Aggregating thresholds using configurable methods
    3. Validating that anomaly rates are within expected bounds
    4. Producing both global and per-dataset thresholds

    Args:
        dataset_scores: Dict mapping dataset name to anomaly score array
        multi_config: MultiDatasetThresholdConfig for cross-dataset calibration
        base_config: Optional AdaptiveThresholdConfig for per-dataset calibration

    Returns:
        MultiDatasetCalibrationResult with calibration results
    """
    if base_config is None:
        base_config = AdaptiveThresholdConfig()

    # Validate minimum datasets
    if len(dataset_scores) < multi_config.min_datasets:
        raise ValueError(
            f"Need at least {multi_config.min_datasets} datasets, "
            f"got {len(dataset_scores)}"
        )

    logger.info(
        f"Calibrating thresholds across {len(dataset_scores)} datasets"
    )

    # Step 1: Calibrate per-dataset thresholds
    per_dataset_results: Dict[str, ThresholdCalibrationResult] = {}
    per_dataset_thresholds: Dict[str, float] = {}
    per_dataset_rates: Dict[str, float] = {}

    for dataset_name, scores in dataset_scores.items():
        logger.info(f"Calibrating threshold for dataset: {dataset_name}")
        result = calibrate_threshold(scores, base_config)
        per_dataset_results[dataset_name] = result
        per_dataset_thresholds[dataset_name] = result.threshold
        per_dataset_rates[dataset_name] = result.anomaly_rate

    # Step 2: Aggregate statistics
    aggregate_stats = aggregate_multi_dataset_statistics(
        per_dataset_results, multi_config
    )

    # Step 3: Compute global threshold
    global_threshold = aggregate_stats['global_threshold']

    # Step 4: Validate anomaly rates
    all_rates = list(per_dataset_rates.values())
    mean_rate = np.mean(all_rates)
    rate_valid = (
        base_config.min_anomaly_rate <= mean_rate <= base_config.max_anomaly_rate
    )

    # Step 5: Generate validation message
    if rate_valid:
        validation_message = (
            f"All anomaly rates within bounds. Mean rate: {mean_rate:.4f}"
        )
    else:
        validation_message = (
            f"Anomaly rates outside bounds. Mean rate: {mean_rate:.4f}, "
            f"bounds: [{base_config.min_anomaly_rate}, {base_config.max_anomaly_rate}]"
        )

    return MultiDatasetCalibrationResult(
        global_threshold=float(global_threshold),
        per_dataset_thresholds=per_dataset_thresholds,
        per_dataset_rates=per_dataset_rates,
        aggregate_statistics=aggregate_stats,
        num_datasets=len(dataset_scores),
        calibration_date=datetime.now().isoformat(),
        method=multi_config.aggregation_method,
        validation_passed=rate_valid,
        validation_message=validation_message
    )


def save_multi_dataset_calibration(
    result: MultiDatasetCalibrationResult,
    output_path: Path
) -> None:
    """
    Save multi-dataset calibration results to JSON file.

    Args:
        result: MultiDatasetCalibrationResult to save
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    save_dict = {
        'global_threshold': result.global_threshold,
        'per_dataset_thresholds': result.per_dataset_thresholds,
        'per_dataset_rates': result.per_dataset_rates,
        'aggregate_statistics': result.aggregate_statistics,
        'num_datasets': result.num_datasets,
        'calibration_date': result.calibration_date,
        'method': result.method,
        'validation_passed': result.validation_passed,
        'validation_message': result.validation_message
    }

    with open(output_path, 'w') as f:
        json.dump(save_dict, f, indent=2)

    logger.info(f"Saved calibration results to {output_path}")


def load_multi_dataset_calibration(
    input_path: Path
) -> MultiDatasetCalibrationResult:
    """
    Load multi-dataset calibration results from JSON file.

    Args:
        input_path: Path to input file

    Returns:
        MultiDatasetCalibrationResult
    """
    with open(input_path, 'r') as f:
        data = json.load(f)

    return MultiDatasetCalibrationResult(
        global_threshold=data['global_threshold'],
        per_dataset_thresholds=data['per_dataset_thresholds'],
        per_dataset_rates=data['per_dataset_rates'],
        aggregate_statistics=data['aggregate_statistics'],
        num_datasets=data['num_datasets'],
        calibration_date=data['calibration_date'],
        method=data['method'],
        validation_passed=data['validation_passed'],
        validation_message=data.get('validation_message', '')
    )


def main() -> None:
    """
    Main function demonstrating multi-dataset threshold calibration.

    This script can be run standalone to test the multi-dataset
    calibration functionality with synthetic data.
    """
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    logger.info("Starting multi-dataset threshold calibration demo")

    # Generate synthetic test data for multiple datasets
    np.random.seed(42)

    # Simulate 3 datasets with different score distributions
    dataset_scores = {
        'dataset_electricity': np.random.normal(0, 1, 1000),
        'dataset_traffic': np.random.normal(0.5, 1.2, 1500),
        'dataset_synthetic': np.random.normal(-0.2, 0.8, 800)
    }

    # Convert to absolute values (scores should be non-negative)
    for name in dataset_scores:
        dataset_scores[name] = np.abs(dataset_scores[name])

    # Configure calibration
    multi_config = MultiDatasetThresholdConfig(
        aggregation_method="weighted_mean",
        weight_by_sample_size=True,
        min_datasets=2,
        outlier_removal=True,
        target_anomaly_rate=0.05
    )

    base_config = AdaptiveThresholdConfig(
        percentile=95.0,
        min_anomaly_rate=0.01,
        max_anomaly_rate=0.10,
        min_samples=100
    )

    # Run calibration
    result = calibrate_thresholds_across_datasets(
        dataset_scores,
        multi_config,
        base_config
    )

    # Print results
    print("\n" + "=" * 60)
    print("MULTI-DATASET THRESHOLD CALIBRATION RESULTS")
    print("=" * 60)
    print(f"Global Threshold: {result.global_threshold:.4f}")
    print(f"Number of Datasets: {result.num_datasets}")
    print(f"Method: {result.method}")
    print(f"Validation Passed: {result.validation_passed}")
    print(f"Validation Message: {result.validation_message}")
    print("\nPer-Dataset Thresholds:")
    for name, thresh in result.per_dataset_thresholds.items():
        print(f"  {name}: {thresh:.4f} (rate: {result.per_dataset_rates[name]:.4f})")
    print("\nAggregate Statistics:")
    for key, value in result.aggregate_statistics.items():
        print(f"  {key}: {value}")
    print("=" * 60 + "\n")

    # Save results
    output_path = Path("data/processed/multi_dataset_calibration.json")
    save_multi_dataset_calibration(result, output_path)
    logger.info(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()
