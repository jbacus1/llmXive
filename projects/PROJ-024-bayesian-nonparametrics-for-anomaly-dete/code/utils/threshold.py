"""
Threshold calibration utilities for anomaly detection.

Implements adaptive threshold computation using statistical properties
of anomaly scores without requiring labeled data. Supports calibration
across multiple datasets for robust deployment.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import logging
import json
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ThresholdConfig:
    """Configuration for adaptive threshold computation."""
    percentile: float = 95.0  # Default percentile for threshold
    min_anomaly_rate: float = 0.01  # Minimum expected anomaly rate
    max_anomaly_rate: float = 0.10  # Maximum expected anomaly rate
    min_samples: int = 100  # Minimum samples required for calibration
    alpha: float = 0.05  # Significance level for statistical tests
    use_interquartile: bool = True  # Use IQR-based method as fallback
    robust_scaling: bool = True  # Use median and MAD for robustness
    cross_dataset_weight: float = 0.7  # Weight for cross-dataset calibration
    min_datasets: int = 2  # Minimum datasets for cross-calibration
    calibration_save_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'percentile': self.percentile,
            'min_anomaly_rate': self.min_anomaly_rate,
            'max_anomaly_rate': self.max_anomaly_rate,
            'min_samples': self.min_samples,
            'alpha': self.alpha,
            'use_interquartile': self.use_interquartile,
            'robust_scaling': self.robust_scaling,
            'cross_dataset_weight': self.cross_dataset_weight,
            'min_datasets': self.min_datasets,
            'calibration_save_path': self.calibration_save_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThresholdConfig':
        """Load config from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AnomalyRateValidationResult:
    """Result of anomaly rate validation against expected bounds."""
    dataset_id: str
    anomaly_rate: float
    within_bounds: bool
    min_expected: float
    max_expected: float
    threshold_used: float
    n_observations: int
    n_anomalies: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'dataset_id': self.dataset_id,
            'anomaly_rate': self.anomaly_rate,
            'within_bounds': self.within_bounds,
            'min_expected': self.min_expected,
            'max_expected': self.max_expected,
            'threshold_used': self.threshold_used,
            'n_observations': self.n_observations,
            'n_anomalies': self.n_anomalies
        }


@dataclass
class ThresholdResult:
    """Result of adaptive threshold computation for a single dataset."""
    dataset_id: str
    threshold: float
    percentile_used: float
    n_observations: int
    n_anomalies: int
    anomaly_rate: float
    score_mean: float
    score_std: float
    score_median: float
    score_iqr: float
    method: str  # 'percentile', 'iqr', or 'robust'
    calibration_weights: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'dataset_id': self.dataset_id,
            'threshold': self.threshold,
            'percentile_used': self.percentile_used,
            'n_observations': self.n_observations,
            'n_anomalies': self.n_anomalies,
            'anomaly_rate': self.anomaly_rate,
            'score_mean': self.score_mean,
            'score_std': self.score_std,
            'score_median': self.score_median,
            'score_iqr': self.score_iqr,
            'method': self.method,
            'calibration_weights': self.calibration_weights
        }


@dataclass
class AdaptiveThresholdState:
    """State for tracking adaptive threshold across streaming updates."""
    dataset_id: str
    n_observations: int = 0
    n_anomalies: int = 0
    score_sum: float = 0.0
    score_sq_sum: float = 0.0
    score_min: float = float('inf')
    score_max: float = float('-inf')
    current_threshold: float = 0.0
    percentile: float = 95.0
    last_update_time: Optional[str] = None
    history: List[float] = field(default_factory=list)
    max_history_size: int = 10000
    
    def update(self, score: float, timestamp: str) -> None:
        """Update state with new score observation."""
        self.n_observations += 1
        self.score_sum += score
        self.score_sq_sum += score ** 2
        self.score_min = min(self.score_min, score)
        self.score_max = max(self.score_max, score)
        
        # Maintain bounded history for percentile calculation
        if len(self.history) >= self.max_history_size:
            self.history = self.history[-self.max_history_size + 1:]
        self.history.append(score)
        self.last_update_time = timestamp
    
    def get_mean(self) -> float:
        """Calculate running mean."""
        if self.n_observations == 0:
            return 0.0
        return self.score_sum / self.n_observations
    
    def get_std(self) -> float:
        """Calculate running standard deviation."""
        if self.n_observations < 2:
            return 0.0
        variance = (self.score_sq_sum / self.n_observations) - (self.get_mean() ** 2)
        return np.sqrt(max(0, variance))
    
    def get_percentile(self, p: float) -> float:
        """Calculate percentile from history."""
        if len(self.history) == 0:
            return 0.0
        return float(np.percentile(self.history, p))
    
    def get_iqr(self) -> float:
        """Calculate interquartile range."""
        if len(self.history) < 4:
            return 0.0
        q1 = np.percentile(self.history, 25)
        q3 = np.percentile(self.history, 75)
        return float(q3 - q1)
    
    def get_median(self) -> float:
        """Calculate median from history."""
        if len(self.history) == 0:
            return 0.0
        return float(np.median(self.history))
    
    def get_mad(self) -> float:
        """Calculate median absolute deviation."""
        if len(self.history) < 2:
            return 0.0
        median = self.get_median()
        return float(np.median(np.abs(np.array(self.history) - median)))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'dataset_id': self.dataset_id,
            'n_observations': self.n_observations,
            'n_anomalies': self.n_anomalies,
            'score_sum': self.score_sum,
            'score_sq_sum': self.score_sq_sum,
            'score_min': self.score_min if self.score_min != float('inf') else None,
            'score_max': self.score_max if self.score_max != float('-inf') else None,
            'current_threshold': self.current_threshold,
            'percentile': self.percentile,
            'last_update_time': self.last_update_time,
            'history_length': len(self.history)
        }


class AdaptiveThresholdCalculator:
    """
    Adaptive threshold calculator for streaming anomaly detection.
    
    Supports both single-dataset and cross-dataset threshold calibration
    without requiring labeled data.
    """
    
    def __init__(self, config: Optional[ThresholdConfig] = None):
        """Initialize with optional configuration."""
        self.config = config or ThresholdConfig()
        self.states: Dict[str, AdaptiveThresholdState] = {}
        self.results: Dict[str, ThresholdResult] = {}
        self.calibration_history: List[Dict[str, Any]] = []
    
    def update_state(self, dataset_id: str, score: float, timestamp: str) -> None:
        """Update state for a dataset with a new score observation."""
        if dataset_id not in self.states:
            self.states[dataset_id] = AdaptiveThresholdState(dataset_id=dataset_id)
        self.states[dataset_id].update(score, timestamp)
    
    def compute_adaptive_threshold(
        self,
        dataset_id: str,
        scores: Optional[np.ndarray] = None,
        override_percentile: Optional[float] = None
    ) -> ThresholdResult:
        """
        Compute adaptive threshold for a single dataset.
        
        Args:
            dataset_id: Identifier for the dataset
            scores: Optional array of scores (uses stored history if None)
            override_percentile: Optional override for percentile threshold
        
        Returns:
            ThresholdResult with computed threshold and statistics
        """
        percentile = override_percentile or self.config.percentile
        
        # Get scores from array or history
        if scores is not None:
            score_array = np.array(scores)
        elif dataset_id in self.states:
            score_array = np.array(self.states[dataset_id].history)
        else:
            raise ValueError(f"No scores available for dataset {dataset_id}")
        
        n_observations = len(score_array)
        if n_observations < self.config.min_samples:
            logger.warning(
                f"Dataset {dataset_id} has only {n_observations} samples "
                f"(min required: {self.config.min_samples})"
            )
        
        # Determine method based on configuration
        if self.config.robust_scaling and len(score_array) > 0:
            # Use robust method (median + MAD)
            median = np.median(score_array)
            mad = np.median(np.abs(score_array - median))
            # Threshold at median + k*MAD where k is chosen for desired percentile
            k = self._percentile_to_mad_multiplier(percentile)
            threshold = median + k * mad
            method = 'robust'
        elif self.config.use_interquartile and len(score_array) > 3:
            # Use IQR method
            q1 = np.percentile(score_array, 25)
            q3 = np.percentile(score_array, 75)
            iqr = q3 - q1
            # Upper fence at Q3 + k*IQR
            k = self._percentile_to_iqr_multiplier(percentile)
            threshold = q3 + k * iqr
            method = 'iqr'
        else:
            # Use direct percentile
            threshold = float(np.percentile(score_array, percentile))
            method = 'percentile'
        
        # Calculate statistics
        anomaly_rate = self._estimate_anomaly_rate(score_array, threshold)
        n_anomalies = int(anomaly_rate * n_observations)
        
        result = ThresholdResult(
            dataset_id=dataset_id,
            threshold=threshold,
            percentile_used=percentile,
            n_observations=n_observations,
            n_anomalies=n_anomalies,
            anomaly_rate=anomaly_rate,
            score_mean=float(np.mean(score_array)),
            score_std=float(np.std(score_array)),
            score_median=float(np.median(score_array)),
            score_iqr=float(np.percentile(score_array, 75) - np.percentile(score_array, 25)) if len(score_array) > 3 else 0.0,
            method=method
        )
        
        self.results[dataset_id] = result
        return result
    
    def _percentile_to_mad_multiplier(self, percentile: float) -> float:
        """Convert percentile to MAD multiplier for normal distribution."""
        # For normal distribution, MAD ≈ 0.6745 * std
        # Percentile p corresponds to z-score z
        z = np.percentile(np.random.normal(0, 1, 10000), percentile)
        return z / 0.6745
    
    def _percentile_to_iqr_multiplier(self, percentile: float) -> float:
        """Convert percentile to IQR multiplier for normal distribution."""
        # IQR ≈ 1.349 * std for normal distribution
        z = np.percentile(np.random.normal(0, 1, 10000), percentile)
        return z / 1.349
    
    def _estimate_anomaly_rate(self, scores: np.ndarray, threshold: float) -> float:
        """Estimate anomaly rate given threshold."""
        if len(scores) == 0:
            return 0.0
        n_anomalies = np.sum(scores >= threshold)
        return float(n_anomalies / len(scores))
    
    def validate_anomaly_rate(
        self,
        dataset_id: str,
        threshold: Optional[float] = None
    ) -> AnomalyRateValidationResult:
        """
        Validate that anomaly rate is within expected bounds.
        
        Args:
            dataset_id: Identifier for the dataset
            threshold: Optional threshold to use (uses computed if None)
        
        Returns:
            AnomalyRateValidationResult with validation status
        """
        if dataset_id not in self.results:
            raise ValueError(f"No threshold result for dataset {dataset_id}")
        
        result = self.results[dataset_id]
        threshold_used = threshold if threshold is not None else result.threshold
        
        anomaly_rate = self._estimate_anomaly_rate(
            np.array(self.states[dataset_id].history),
            threshold_used
        )
        
        within_bounds = (
            self.config.min_anomaly_rate <= anomaly_rate <= self.config.max_anomaly_rate
        )
        
        return AnomalyRateValidationResult(
            dataset_id=dataset_id,
            anomaly_rate=anomaly_rate,
            within_bounds=within_bounds,
            min_expected=self.config.min_anomaly_rate,
            max_expected=self.config.max_anomaly_rate,
            threshold_used=threshold_used,
            n_observations=result.n_observations,
            n_anomalies=result.n_anomalies
        )
    
    def calibrate_thresholds_across_datasets(
        self,
        dataset_ids: List[str],
        scores_dict: Optional[Dict[str, np.ndarray]] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, ThresholdResult]:
        """
        Calibrate thresholds across multiple datasets without labeled data.
        
        This implements US3 acceptance scenario 3: threshold calibration
        across multiple datasets using statistical aggregation of score
        distributions.
        
        Args:
            dataset_ids: List of dataset identifiers to calibrate
            scores_dict: Optional dict mapping dataset_id to score arrays
            weights: Optional dict mapping dataset_id to calibration weights
        
        Returns:
            Dict mapping dataset_id to ThresholdResult
        """
        if len(dataset_ids) < self.config.min_datasets:
            logger.warning(
                f"Only {len(dataset_ids)} datasets provided, "
                f"minimum is {self.config.min_datasets} for cross-dataset calibration"
            )
        
        # Collect all score statistics
        all_stats = {}
        for dataset_id in dataset_ids:
            if scores_dict is not None and dataset_id in scores_dict:
                scores = np.array(scores_dict[dataset_id])
            elif dataset_id in self.states:
                scores = np.array(self.states[dataset_id].history)
            else:
                logger.warning(f"No scores available for dataset {dataset_id}, skipping")
                continue
            
            all_stats[dataset_id] = {
                'scores': scores,
                'median': np.median(scores),
                'mean': np.mean(scores),
                'std': np.std(scores),
                'percentile_95': np.percentile(scores, 95),
                'percentile_99': np.percentile(scores, 99),
                'n_observations': len(scores)
            }
        
        if len(all_stats) < self.config.min_datasets:
            raise ValueError(
                f"Only {len(all_stats)} datasets have scores, "
                f"minimum is {self.config.min_datasets}"
            )
        
        # Compute global statistics for cross-dataset calibration
        all_medians = np.array([s['median'] for s in all_stats.values()])
        all_means = np.array([s['mean'] for s in all_stats.values()])
        all_stds = np.array([s['std'] for s in all_stats.values()])
        all_p95s = np.array([s['percentile_95'] for s in all_stats.values()])
        
        # Global robust statistics
        global_median = np.median(all_medians)
        global_mad = np.median(np.abs(all_medians - global_median))
        
        # Compute per-dataset thresholds with cross-dataset adjustment
        calibration_weights = weights or {
            ds_id: 1.0 / len(dataset_ids) for ds_id in dataset_ids
        }
        
        # Normalize weights
        weight_sum = sum(calibration_weights.values())
        calibration_weights = {k: v / weight_sum for k, v in calibration_weights.items()}
        
        final_results = {}
        for dataset_id in dataset_ids:
            if dataset_id not in all_stats:
                continue
            
            stats = all_stats[dataset_id]
            local_p95 = stats['percentile_95']
            
            # Cross-dataset adjusted threshold
            # Blend local percentile with global robust estimate
            global_threshold = global_median + 3 * global_mad  # 3-MAD rule
            adjusted_threshold = (
                self.config.cross_dataset_weight * global_threshold +
                (1 - self.config.cross_dataset_weight) * local_p95
            )
            
            # Ensure threshold is reasonable (not too low)
            adjusted_threshold = max(adjusted_threshold, stats['mean'] + 2 * stats['std'])
            
            # Calculate anomaly rate with adjusted threshold
            scores = stats['scores']
            anomaly_rate = float(np.sum(scores >= adjusted_threshold) / len(scores))
            
            # Adjust threshold if anomaly rate is out of bounds
            if anomaly_rate < self.config.min_anomaly_rate:
                # Lower threshold to increase anomaly rate
                target_p = self._rate_to_percentile(anomaly_rate, self.config.min_anomaly_rate)
                adjusted_threshold = float(np.percentile(scores, target_p))
            elif anomaly_rate > self.config.max_anomaly_rate:
                # Raise threshold to decrease anomaly rate
                target_p = self._rate_to_percentile(anomaly_rate, self.config.max_anomaly_rate)
                adjusted_threshold = float(np.percentile(scores, target_p))
            
            result = ThresholdResult(
                dataset_id=dataset_id,
                threshold=adjusted_threshold,
                percentile_used=self.config.percentile,
                n_observations=stats['n_observations'],
                n_anomalies=int(anomaly_rate * stats['n_observations']),
                anomaly_rate=anomaly_rate,
                score_mean=float(stats['mean']),
                score_std=float(stats['std']),
                score_median=float(stats['median']),
                score_iqr=float(np.percentile(scores, 75) - np.percentile(scores, 25)),
                method='cross_dataset',
                calibration_weights=calibration_weights
            )
            
            final_results[dataset_id] = result
            self.results[dataset_id] = result
        
        # Record calibration history
        self.calibration_history.append({
            'datasets': dataset_ids,
            'global_median': float(global_median),
            'global_mad': float(global_mad),
            'results': {k: v.to_dict() for k, v in final_results.items()}
        })
        
        return final_results
    
    def _rate_to_percentile(self, current_rate: float, target_rate: float) -> float:
        """Convert anomaly rate change to percentile adjustment."""
        # Simple linear approximation
        if current_rate == target_rate:
            return 100 - 100 * target_rate
        
        # Adjust percentile to move rate toward target
        adjustment = (target_rate - current_rate) * 100
        current_percentile = 100 - 100 * current_rate
        new_percentile = current_percentile + adjustment
        return max(50, min(99, new_percentile))
    
    def save_threshold_calibration(
        self,
        output_path: Optional[str] = None
    ) -> Path:
        """
        Save threshold calibration results to file.
        
        Args:
            output_path: Optional path for output file (uses config if None)
        
        Returns:
            Path to saved file
        """
        path = Path(output_path or self.config.calibration_save_path or 'threshold_calibration.yaml')
        
        data = {
            'config': self.config.to_dict(),
            'calibration_history': self.calibration_history,
            'results': {k: v.to_dict() for k, v in self.results.items()},
            'states': {k: v.to_dict() for k, v in self.states.items()}
        }
        
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
        
        logger.info(f"Saved threshold calibration to {path}")
        return path
    
    def load_threshold_config(
        self,
        input_path: str
    ) -> None:
        """
        Load threshold calibration from file.
        
        Args:
            input_path: Path to calibration file
        """
        with open(input_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if 'config' in data:
            self.config = ThresholdConfig.from_dict(data['config'])
        
        if 'results' in data:
            self.results = {
                k: ThresholdResult(**v) for k, v in data['results'].items()
            }
        
        if 'states' in data:
            self.states = {
                k: AdaptiveThresholdState(**{
                    kk: vv for kk, vv in v.items()
                    if kk in AdaptiveThresholdState.__dataclass_fields__
                })
                for k, v in data['states'].items()
            }
        
        if 'calibration_history' in data:
            self.calibration_history = data['calibration_history']
        
        logger.info(f"Loaded threshold calibration from {input_path}")


def compute_adaptive_threshold(
    scores: np.ndarray,
    percentile: float = 95.0,
    method: str = 'robust'
) -> Tuple[float, Dict[str, float]]:
    """
    Convenience function to compute adaptive threshold for a single dataset.
    
    Args:
        scores: Array of anomaly scores
        percentile: Percentile for threshold (default 95)
        method: Method to use ('percentile', 'iqr', or 'robust')
    
    Returns:
        Tuple of (threshold, statistics dict)
    """
    stats = {
        'mean': float(np.mean(scores)),
        'std': float(np.std(scores)),
        'median': float(np.median(scores)),
        'min': float(np.min(scores)),
        'max': float(np.max(scores))
    }
    
    if method == 'robust':
        median = np.median(scores)
        mad = np.median(np.abs(scores - median))
        k = 3.0  # 3-MAD rule approximates 99.7% for normal
        threshold = median + k * mad
        stats['method'] = 'robust'
    elif method == 'iqr':
        q1 = np.percentile(scores, 25)
        q3 = np.percentile(scores, 75)
        iqr = q3 - q1
        threshold = q3 + 1.5 * iqr
        stats['method'] = 'iqr'
    else:
        threshold = float(np.percentile(scores, percentile))
        stats['method'] = 'percentile'
    
    return threshold, stats


def calibrate_thresholds_across_datasets(
    scores_dict: Dict[str, np.ndarray],
    config: Optional[ThresholdConfig] = None
) -> Dict[str, ThresholdResult]:
    """
    Convenience function for cross-dataset threshold calibration.
    
    Args:
        scores_dict: Dict mapping dataset_id to score arrays
        config: Optional ThresholdConfig (uses defaults if None)
    
    Returns:
        Dict mapping dataset_id to ThresholdResult
    """
    calculator = AdaptiveThresholdCalculator(config)
    dataset_ids = list(scores_dict.keys())
    return calculator.calibrate_thresholds_across_datasets(dataset_ids, scores_dict)


def main() -> None:
    """Main entry point for threshold calibration CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Threshold calibration utility')
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--scores', type=str, help='Path to scores JSON file')
    parser.add_argument('--output', type=str, help='Path to output file')
    parser.add_argument('--percentile', type=float, default=95.0, help='Percentile threshold')
    parser.add_argument('--method', type=str, default='robust', help='Method: percentile, iqr, robust')
    
    args = parser.parse_args()
    
    # Load config if provided
    config = None
    if args.config:
        with open(args.config, 'r') as f:
            config = ThresholdConfig.from_dict(json.load(f))
    
    config = config or ThresholdConfig(percentile=args.percentile)
    
    # Load scores if provided
    if args.scores:
        with open(args.scores, 'r') as f:
            scores_data = json.load(f)
        
        calculator = AdaptiveThresholdCalculator(config)
        
        if isinstance(scores_data, dict):
            # Multi-dataset format
            dataset_ids = list(scores_data.keys())
            scores_array = {k: np.array(v) for k, v in scores_data.items()}
            
            results = calculator.calibrate_thresholds_across_datasets(dataset_ids, scores_array)
            logger.info(f"Calibrated thresholds for {len(results)} datasets")
        else:
            # Single dataset format
            scores = np.array(scores_data)
            result = calculator.compute_adaptive_threshold('single', scores)
            results = {'single': result}
            logger.info(f"Computed threshold: {result.threshold}")
        
        # Save results
        output_path = args.output or 'threshold_results.json'
        with open(output_path, 'w') as f:
            json.dump({k: v.to_dict() for k, v in results.items()}, f, indent=2)
        logger.info(f"Saved results to {output_path}")
    else:
        print("Usage: Provide --scores file with anomaly scores")
        print("Format: JSON array for single dataset, or JSON object for multiple datasets")


if __name__ == '__main__':
    main()
