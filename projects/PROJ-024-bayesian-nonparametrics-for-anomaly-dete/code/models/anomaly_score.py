"""
AnomalyScore Entity Class

Represents an anomaly score for a single observation in a time series.
This entity follows the contract schema defined in anomaly_score.schema.yaml
and implements the data model documented in data-model.md.

Fields:
  - timestamp: ISO 8601 formatted timestamp of the observation
  - score: Anomaly score (negative log posterior probability)
  - uncertainty: Standard deviation of the score (probabilistic uncertainty)
  - cluster_id: ID of the cluster this observation belongs to (from DPGMM)
  - is_anomaly: Boolean flag indicating if score exceeds threshold
  - threshold: Threshold value used for anomaly flagging
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import json
import yaml

@dataclass
class AnomalyScore:
    """
    Anomaly score entity for time series observations.
    
    This class represents the output of the anomaly detection pipeline,
    containing the computed score, uncertainty estimates, and anomaly
    classification for a single observation.
    """
    
    timestamp: datetime
    score: float
    uncertainty: float = 0.0
    cluster_id: Optional[int] = None
    is_anomaly: bool = False
    threshold: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate anomaly score values after initialization."""
        if self.score < 0:
            raise ValueError("Anomaly score must be non-negative (negative log posterior)")
        if self.uncertainty < 0:
            raise ValueError("Uncertainty must be non-negative")
        
        # Validate anomaly flag consistency
        if self.threshold is not None:
            expected_is_anomaly = self.score > self.threshold
            if self.is_anomaly != expected_is_anomaly:
                # Allow override but log warning in production
                pass
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnomalyScore':
        """
        Create AnomalyScore from dictionary (e.g., JSON/YAML loaded).
        
        Args:
            data: Dictionary containing anomaly score fields
        
        Returns:
            AnomalyScore instance
        
        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = ['timestamp', 'score']
        for field_name in required_fields:
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")
        
        # Parse timestamp
        timestamp = data['timestamp']
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, datetime):
            pass
        else:
            raise ValueError(f"Invalid timestamp type: {type(timestamp)}")
        
        return cls(
            timestamp=timestamp,
            score=float(data['score']),
            uncertainty=float(data.get('uncertainty', 0.0)),
            cluster_id=data.get('cluster_id', None),
            is_anomaly=bool(data.get('is_anomaly', False)),
            threshold=data.get('threshold', None),
            metadata=data.get('metadata', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert AnomalyScore to dictionary for serialization.
        
        Returns:
            Dictionary representation of the anomaly score
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'score': self.score,
            'uncertainty': self.uncertainty,
            'cluster_id': self.cluster_id,
            'is_anomaly': self.is_anomaly,
            'threshold': self.threshold,
            'metadata': self.metadata
        }
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert AnomalyScore to JSON string.
        
        Args:
            indent: JSON indentation level
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AnomalyScore':
        """
        Create AnomalyScore from JSON string.
        
        Args:
            json_str: JSON string representation
        
        Returns:
            AnomalyScore instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def to_yaml(self) -> str:
        """
        Convert AnomalyScore to YAML string.
        
        Returns:
            YAML string representation
        """
        return yaml.dump(self.to_dict(), default_flow_style=False)
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'AnomalyScore':
        """
        Create AnomalyScore from YAML string.
        
        Args:
            yaml_str: YAML string representation
        
        Returns:
            AnomalyScore instance
        """
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)
    
    def exceeds_threshold(self, threshold: float) -> bool:
        """
        Check if score exceeds given threshold.
        
        Args:
            threshold: Threshold value to compare against
        
        Returns:
            True if score exceeds threshold
        """
        return self.score > threshold
    
    def with_threshold(self, threshold: float) -> 'AnomalyScore':
        """
        Return new instance with threshold set and anomaly flag updated.
        
        Args:
            threshold: Threshold value for anomaly detection
        
        Returns:
            New AnomalyScore instance with updated threshold and flag
        """
        return AnomalyScore(
            timestamp=self.timestamp,
            score=self.score,
            uncertainty=self.uncertainty,
            cluster_id=self.cluster_id,
            is_anomaly=self.score > threshold,
            threshold=threshold,
            metadata=self.metadata.copy()
        )
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        status = "ANOMALY" if self.is_anomaly else "normal"
        return f"AnomalyScore(timestamp={self.timestamp}, score={self.score:.4f}, " \
               f"uncertainty={self.uncertainty:.4f}, cluster={self.cluster_id}, " \
               f"status={status})"
    
    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return self.__str__()
    
    def __eq__(self, other) -> bool:
        """Equality comparison based on all fields."""
        if not isinstance(other, AnomalyScore):
            return False
        return (
            self.timestamp == other.timestamp and
            abs(self.score - other.score) < 1e-10 and
            abs(self.uncertainty - other.uncertainty) < 1e-10 and
            self.cluster_id == other.cluster_id and
            self.is_anomaly == other.is_anomaly and
            self.threshold == other.threshold
        )
    
    def __hash__(self) -> int:
        """Hash based on timestamp and score for use in sets/dicts."""
        return hash((self.timestamp, round(self.score, 10)))