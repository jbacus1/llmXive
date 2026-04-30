"""
Anomaly Detector Service Wrapper per plan.md Project Structure specification.
Provides a high-level interface for streaming anomaly detection.
"""
from pathlib import Path
from typing import Optional, List, Dict, Any, Generator
import numpy as np
import logging

from src.models.dp_gmm import DPGMMModel, DPGMMConfig
from src.models.anomaly_score import AnomalyScore
from src.utils.streaming import StreamingObservation
from src.utils.threshold import adaptive_threshold, calibrate_threshold

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnomalyDetectorService:
    """
    Service wrapper for DPGMM-based anomaly detection.
    
    Provides streaming observation processing with automatic
    threshold calibration and anomaly scoring.
    """
    
    def __init__(
        self,
        config: Optional[DPGMMConfig] = None,
        config_path: Optional[Path] = None,
    ):
        """
        Initialize the anomaly detector service.
        
        Args:
            config: DPGMM configuration parameters
            config_path: Path to YAML config file (alternative to config param)
        """
        if config_path:
            self.config = DPGMMConfig.from_yaml(config_path)
        else:
            self.config = config or DPGMMConfig()
        
        self.model = DPGMMModel(config=self.config)
        self.threshold: Optional[float] = None
        self.scores: List[AnomalyScore] = []
        self.is_calibrated = False
        
        logger.info(f"AnomalyDetectorService initialized with config: {self.config}")
    
    def process_observation(
        self,
        value: float,
        timestamp: Optional[np.datetime64] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AnomalyScore:
        """
        Process a single streaming observation.
        
        Args:
            value: The observed value
            timestamp: Optional timestamp for the observation
            metadata: Optional additional metadata
        
        Returns:
            AnomalyScore with negative log posterior probability
        """
        obs = StreamingObservation(
            value=value,
            timestamp=timestamp,
            metadata=metadata,
        )
        
        # Update model with new observation
        self.model.update(obs)
        
        # Compute anomaly score
        score = self.model.score(obs)
        self.scores.append(score)
        
        logger.debug(f"Processed observation: value={value}, score={score.score:.4f}")
        return score
    
    def process_stream(
        self,
        values: List[float],
        timestamps: Optional[List[np.datetime64]] = None,
    ) -> Generator[AnomalyScore, None, None]:
        """
        Process a batch of observations as a stream.
        
        Args:
            values: List of observed values
            timestamps: Optional list of timestamps
        
        Yields:
            AnomalyScore for each observation
        """
        for i, value in enumerate(values):
            timestamp = timestamps[i] if timestamps else None
            score = self.process_observation(value, timestamp)
            yield score
    
    def calibrate_threshold(
        self,
        method: str = "percentile",
        percentile: float = 95.0,
        min_anomaly_rate: float = 0.01,
        max_anomaly_rate: float = 0.10,
    ) -> float:
        """
        Calibrate anomaly threshold based on collected scores.
        
        Args:
            method: Calibration method ("percentile", "iqr", "mad")
            percentile: Percentile for percentile method (default 95)
            min_anomaly_rate: Minimum acceptable anomaly rate
            max_anomaly_rate: Maximum acceptable anomaly rate
        
        Returns:
            Calibrated threshold value
        """
        if not self.scores:
            raise ValueError("No scores collected for threshold calibration")
        
        score_values = np.array([s.score for s in self.scores])
        
        if method == "percentile":
            self.threshold = calibrate_threshold(
                score_values,
                method="percentile",
                percentile=percentile,
            )
        elif method == "iqr":
            self.threshold = calibrate_threshold(
                score_values,
                method="iqr",
            )
        elif method == "mad":
            self.threshold = calibrate_threshold(
                score_values,
                method="mad",
            )
        else:
            raise ValueError(f"Unknown calibration method: {method}")
        
        # Validate anomaly rate bounds
        anomaly_rate = np.mean(score_values >= self.threshold)
        if not (min_anomaly_rate <= anomaly_rate <= max_anomaly_rate):
            logger.warning(
                f"Anomaly rate {anomaly_rate:.2%} outside bounds "
                f"[{min_anomaly_rate:.2%}, {max_anomaly_rate:.2%}]"
            )
        
        self.is_calibrated = True
        logger.info(f"Threshold calibrated: {self.threshold:.4f} (anomaly rate: {anomaly_rate:.2%})")
        return self.threshold
    
    def is_anomaly(self, score: AnomalyScore) -> bool:
        """
        Check if an anomaly score indicates an anomaly.
        
        Args:
            score: AnomalyScore to evaluate
        
        Returns:
            True if score exceeds threshold, False otherwise
        """
        if not self.is_calibrated:
            raise ValueError("Threshold not calibrated. Call calibrate_threshold() first.")
        
        return score.score >= self.threshold
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get detection statistics.
        
        Returns:
            Dictionary with model and detection statistics
        """
        if not self.scores:
            return {
                "n_observations": 0,
                "n_components": 0,
                "threshold": None,
                "anomaly_rate": None,
            }
        
        score_values = np.array([s.score for s in self.scores])
        
        return {
            "n_observations": len(self.scores),
            "n_components": self.model.n_active_components,
            "threshold": self.threshold,
            "anomaly_rate": np.mean(score_values >= self.threshold) if self.threshold else None,
            "mean_score": float(np.mean(score_values)),
            "std_score": float(np.std(score_values)),
            "min_score": float(np.min(score_values)),
            "max_score": float(np.max(score_values)),
        }
    
    def reset(self):
        """Reset the detector state for new analysis."""
        self.model.reset()
        self.scores.clear()
        self.threshold = None
        self.is_calibrated = False
        logger.info("AnomalyDetectorService reset")
    
    def save_state(self, path: Path):
        """
        Save detector state to file.
        
        Args:
            path: Path to save state file
        """
        self.model.save_state(path)
        logger.info(f"Detector state saved to {path}")
    
    def load_state(self, path: Path):
        """
        Load detector state from file.
        
        Args:
            path: Path to load state file
        """
        self.model.load_state(path)
        self.is_calibrated = True  # Assume calibrated if state loaded
        logger.info(f"Detector state loaded from {path}")
    execute: false