"""
AnomalyScore dataclass for storing negative log posterior probability scores.

This module provides the AnomalyScore dataclass that encapsulates anomaly
scoring results from the DPGMM model, including the negative log posterior
probability and associated metadata for each observation.

Per FR-003: Anomaly scoring function computing negative log posterior
per observation with probabilistic uncertainty estimates.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import numpy as np


@dataclass
class AnomalyScore:
    """
    Dataclass representing an anomaly score for a single observation.
    
    Attributes:
        observation_index: Index of the observation in the time series
        timestamp: Timestamp when the observation was processed
        negative_log_posterior: Negative log posterior probability (anomaly score)
        log_likelihood: Log likelihood of the observation under the model
        log_prior: Log prior probability of the observation
        component_assignment: Assigned mixture component (0-indexed)
        component_weights: Mixture weights at time of scoring
        uncertainty_estimate: Standard deviation of the score (if available)
        is_anomaly: Boolean flag if score exceeds threshold
        threshold: Threshold used for anomaly flagging
        metadata: Additional diagnostic information
    """
    observation_index: int
    timestamp: datetime
    negative_log_posterior: float
    log_likelihood: float
    log_prior: float
    component_assignment: Optional[int] = None
    component_weights: Optional[np.ndarray] = None
    uncertainty_estimate: Optional[float] = None
    is_anomaly: bool = False
    threshold: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'observation_index': self.observation_index,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'negative_log_posterior': float(self.negative_log_posterior),
            'log_likelihood': float(self.log_likelihood),
            'log_prior': float(self.log_prior),
            'component_assignment': self.component_assignment,
            'component_weights': self.component_weights.tolist() if self.component_weights is not None else None,
            'uncertainty_estimate': float(self.uncertainty_estimate) if self.uncertainty_estimate is not None else None,
            'is_anomaly': self.is_anomaly,
            'threshold': float(self.threshold) if self.threshold is not None else None,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnomalyScore':
        """Create AnomalyScore from dictionary representation."""
        timestamp = None
        if data.get('timestamp'):
            timestamp = datetime.fromisoformat(data['timestamp'])
        
        component_weights = None
        if data.get('component_weights'):
            component_weights = np.array(data['component_weights'])
        
        return cls(
            observation_index=data['observation_index'],
            timestamp=timestamp,
            negative_log_posterior=data['negative_log_posterior'],
            log_likelihood=data['log_likelihood'],
            log_prior=data['log_prior'],
            component_assignment=data.get('component_assignment'),
            component_weights=component_weights,
            uncertainty_estimate=data.get('uncertainty_estimate'),
            is_anomaly=data.get('is_anomaly', False),
            threshold=data.get('threshold'),
            metadata=data.get('metadata', {})
        )

    def __post_init__(self):
        """Validate and normalize fields after initialization."""
        # Ensure negative_log_posterior is finite
        if not np.isfinite(self.negative_log_posterior):
            raise ValueError(f"negative_log_posterior must be finite, got {self.negative_log_posterior}")
        
        # Ensure log_likelihood is finite
        if not np.isfinite(self.log_likelihood):
            raise ValueError(f"log_likelihood must be finite, got {self.log_likelihood}")
        
        # Ensure log_prior is finite
        if not np.isfinite(self.log_prior):
            raise ValueError(f"log_prior must be finite, got {self.log_prior}")
        
        # Validate component_weights if provided
        if self.component_weights is not None:
            if not np.all(np.isfinite(self.component_weights)):
                raise ValueError("component_weights must contain only finite values")
            if not np.isclose(np.sum(self.component_weights), 1.0, atol=1e-6):
                raise ValueError(f"component_weights must sum to 1, got {np.sum(self.component_weights)}")
            if np.any(self.component_weights < 0):
                raise ValueError("component_weights must be non-negative")

    def score(self) -> float:
        """Return the anomaly score (negative log posterior)."""
        return self.negative_log_posterior

    def apply_threshold(self, threshold: float) -> 'AnomalyScore':
        """
        Apply a threshold to determine if this observation is an anomaly.
        
        Args:
            threshold: The anomaly threshold (lower scores = more anomalous)
        
        Returns:
            A new AnomalyScore with updated is_anomaly flag
        """
        return AnomalyScore(
            observation_index=self.observation_index,
            timestamp=self.timestamp,
            negative_log_posterior=self.negative_log_posterior,
            log_likelihood=self.log_likelihood,
            log_prior=self.log_prior,
            component_assignment=self.component_assignment,
            component_weights=self.component_weights.copy() if self.component_weights is not None else None,
            uncertainty_estimate=self.uncertainty_estimate,
            is_anomaly=self.negative_log_posterior > threshold,
            threshold=threshold,
            metadata=self.metadata.copy()
        )

    def with_uncertainty(self, std: float) -> 'AnomalyScore':
        """
        Create a copy with updated uncertainty estimate.
        
        Args:
            std: Standard deviation of the score estimate
        
        Returns:
            New AnomalyScore with uncertainty_estimate set
        """
        return AnomalyScore(
            observation_index=self.observation_index,
            timestamp=self.timestamp,
            negative_log_posterior=self.negative_log_posterior,
            log_likelihood=self.log_likelihood,
            log_prior=self.log_prior,
            component_assignment=self.component_assignment,
            component_weights=self.component_weights.copy() if self.component_weights is not None else None,
            uncertainty_estimate=float(std),
            is_anomaly=self.is_anomaly,
            threshold=self.threshold,
            metadata=self.metadata.copy()
        )

    def with_metadata(self, key: str, value: Any) -> 'AnomalyScore':
        """
        Create a copy with updated metadata.
        
        Args:
            key: Metadata key
            value: Metadata value
        
        Returns:
            New AnomalyScore with updated metadata
        """
        new_metadata = self.metadata.copy()
        new_metadata[key] = value
        return AnomalyScore(
            observation_index=self.observation_index,
            timestamp=self.timestamp,
            negative_log_posterior=self.negative_log_posterior,
            log_likelihood=self.log_likelihood,
            log_prior=self.log_prior,
            component_assignment=self.component_assignment,
            component_weights=self.component_weights.copy() if self.component_weights is not None else None,
            uncertainty_estimate=self.uncertainty_estimate,
            is_anomaly=self.is_anomaly,
            threshold=self.threshold,
            metadata=new_metadata
        )


# API surface exports
__all__ = ['AnomalyScore']
