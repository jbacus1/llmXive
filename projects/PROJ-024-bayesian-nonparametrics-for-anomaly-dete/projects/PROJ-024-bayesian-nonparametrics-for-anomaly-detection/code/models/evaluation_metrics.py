"""
EvaluationMetrics Entity Class

Implements the EvaluationMetrics entity per specs/001-bayesian-nonparametrics-anomaly-detection/data-model.md
and conforms to evaluation_metrics.schema.yaml contract.

Provides structured storage and computation for anomaly detection evaluation metrics
including precision, recall, F1-score, AUC, and confusion matrix data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import json
import numpy as np
from pathlib import Path

from code.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class EvaluationMetrics:
    """
    EvaluationMetrics entity class for anomaly detection model performance tracking.

    Attributes:
        model_name: Name identifier for the evaluated model
        dataset_name: Name of the dataset used for evaluation
        precision: Precision score (TP / (TP + FP))
        recall: Recall score (TP / (TP + FN))
        f1_score: F1 harmonic mean of precision and recall
        auc_roc: Area Under the ROC Curve
        auc_pr: Area Under the Precision-Recall Curve
        true_positives: Count of true positive predictions
        true_negatives: Count of true negative predictions
        false_positives: Count of false positive predictions
        false_negatives: Count of false negative predictions
        total_samples: Total number of samples evaluated
        anomaly_rate: Proportion of actual anomalies in the dataset
        threshold_used: The threshold value used for binary classification
        runtime_seconds: Wall-clock time for evaluation
        hyperparameter_count: Number of hyperparameters in the model
        metadata: Additional key-value pairs for experiment tracking
    """

    model_name: str
    dataset_name: str
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    auc_roc: float = 0.0
    auc_pr: float = 0.0
    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    total_samples: int = 0
    anomaly_rate: float = 0.0
    threshold_used: Optional[float] = None
    runtime_seconds: Optional[float] = None
    hyperparameter_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and compute derived metrics after initialization."""
        self._validate_confusion_matrix()
        self._compute_derived_metrics()

    def _validate_confusion_matrix(self) -> None:
        """
        Validate that confusion matrix components are non-negative integers.

        Raises:
            ValueError: If any confusion matrix component is negative or non-integer.
        """
        components = {
            'true_positives': self.true_positives,
            'true_negatives': self.true_negatives,
            'false_positives': self.false_positives,
            'false_negatives': self.false_negatives,
        }

        for name, value in components.items():
            if value < 0:
                raise ValueError(f"{name} cannot be negative: got {value}")
            if not isinstance(value, int):
                raise ValueError(f"{name} must be an integer: got {type(value).__name__}")

        # Validate total samples
        if self.total_samples < 0:
            raise ValueError(f"total_samples cannot be negative: got {self.total_samples}")

        # Validate that total matches confusion matrix sum if provided
        expected_total = (
            self.true_positives + self.true_negatives +
            self.false_positives + self.false_negatives
        )
        if self.total_samples > 0 and self.total_samples != expected_total:
            logger.warning(
                f"total_samples ({self.total_samples}) does not match "
                f"confusion matrix sum ({expected_total}). Using confusion matrix sum."
            )
            self.total_samples = expected_total

    def _compute_derived_metrics(self) -> None:
        """
        Compute derived metrics from confusion matrix values.

        Sets precision, recall, f1_score, and anomaly_rate based on
        confusion matrix components.
        """
        # Compute precision: TP / (TP + FP)
        tp_fp = self.true_positives + self.false_positives
        if tp_fp > 0:
            self.precision = self.true_positives / tp_fp
        else:
            self.precision = 0.0

        # Compute recall: TP / (TP + FN)
        tp_fn = self.true_positives + self.false_negatives
        if tp_fn > 0:
            self.recall = self.true_positives / tp_fn
        else:
            self.recall = 0.0

        # Compute F1 score: 2 * (precision * recall) / (precision + recall)
        if self.precision + self.recall > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)
        else:
            self.f1_score = 0.0

        # Compute anomaly rate: (TP + FN) / total
        if self.total_samples > 0:
            self.anomaly_rate = tp_fn / self.total_samples
        else:
            self.anomaly_rate = 0.0

    @classmethod
    def from_confusion_matrix(
        cls,
        model_name: str,
        dataset_name: str,
        true_positives: int,
        true_negatives: int,
        false_positives: int,
        false_negatives: int,
        threshold_used: Optional[float] = None,
        runtime_seconds: Optional[float] = None,
        hyperparameter_count: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EvaluationMetrics:
        """
        Factory method to create EvaluationMetrics from confusion matrix values.

        Args:
            model_name: Name of the model being evaluated
            dataset_name: Name of the dataset used
            true_positives: Count of true positive predictions
            true_negatives: Count of true negative predictions
            false_positives: Count of false positive predictions
            false_negatives: Count of false negative predictions
            threshold_used: The threshold value used for binary classification
            runtime_seconds: Wall-clock time for evaluation
            hyperparameter_count: Number of hyperparameters in the model
            metadata: Additional key-value pairs for experiment tracking

        Returns:
            EvaluationMetrics instance with computed metrics
        """
        total_samples = true_positives + true_negatives + false_positives + false_negatives

        return cls(
            model_name=model_name,
            dataset_name=dataset_name,
            true_positives=true_positives,
            true_negatives=true_negatives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            total_samples=total_samples,
            threshold_used=threshold_used,
            runtime_seconds=runtime_seconds,
            hyperparameter_count=hyperparameter_count,
            metadata=metadata or {},
        )

    @classmethod
    def from_predictions(
        cls,
        model_name: str,
        dataset_name: str,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_scores: Optional[np.ndarray] = None,
        threshold: Optional[float] = None,
        runtime_seconds: Optional[float] = None,
        hyperparameter_count: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EvaluationMetrics:
        """
        Factory method to create EvaluationMetrics from prediction arrays.

        Args:
            model_name: Name of the model being evaluated
            dataset_name: Name of the dataset used
            y_true: Array of true labels (0 or 1)
            y_pred: Array of predicted labels (0 or 1)
            y_scores: Array of anomaly scores (for AUC computation)
            threshold: Threshold used for binary classification
            runtime_seconds: Wall-clock time for evaluation
            hyperparameter_count: Number of hyperparameters in the model
            metadata: Additional key-value pairs for experiment tracking

        Returns:
            EvaluationMetrics instance with computed metrics
        """
        # Ensure inputs are numpy arrays
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)

        if y_true.shape != y_pred.shape:
            raise ValueError(
                f"y_true shape {y_true.shape} does not match y_pred shape {y_pred.shape}"
            )

        # Compute confusion matrix components
        true_positives = int(np.sum((y_true == 1) & (y_pred == 1)))
        true_negatives = int(np.sum((y_true == 0) & (y_pred == 0)))
        false_positives = int(np.sum((y_true == 0) & (y_pred == 1)))
        false_negatives = int(np.sum((y_true == 1) & (y_pred == 0)))

        metrics = cls.from_confusion_matrix(
            model_name=model_name,
            dataset_name=dataset_name,
            true_positives=true_positives,
            true_negatives=true_negatives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            threshold_used=threshold,
            runtime_seconds=runtime_seconds,
            hyperparameter_count=hyperparameter_count,
            metadata=metadata or {},
        )

        # Compute AUC metrics if scores are provided
        if y_scores is not None:
          y_scores = np.asarray(y_scores)
          metrics.auc_roc = cls._compute_auc_roc(y_true, y_scores)
          metrics.auc_pr = cls._compute_auc_pr(y_true, y_scores)

        return metrics

    @staticmethod
    def _compute_auc_roc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
        """
        Compute Area Under the ROC Curve.

        Uses trapezoidal rule for numerical integration.

        Args:
            y_true: Array of true binary labels
            y_scores: Array of anomaly scores

        Returns:
            AUC-ROC value between 0 and 1
        """
        try:
            # Import here to avoid hard dependency on scikit-learn
            from sklearn.metrics import roc_auc_score
            return float(roc_auc_score(y_true, y_scores))
        except ImportError:
            logger.warning("scikit-learn not available, using fallback AUC-ROC computation")
            return EvaluationMetrics._compute_auc_roc_fallback(y_true, y_scores)

    @staticmethod
    def _compute_auc_roc_fallback(y_true: np.ndarray, y_scores: np.ndarray) -> float:
        """
        Fallback AUC-ROC computation without scikit-learn.

        Uses trapezoidal integration over ROC curve points.
        """
        from collections import defaultdict

        # Sort by scores descending
        sorted_indices = np.argsort(-y_scores)
        y_true_sorted = y_true[sorted_indices]
        y_scores_sorted = y_scores[sorted_indices]

        # Compute TPR and FPR at each threshold
        total_positives = np.sum(y_true == 1)
        total_negatives = np.sum(y_true == 0)

        if total_positives == 0 or total_negatives == 0:
            return 0.5  # Undefined case

        tpr_values = [0.0]
        fpr_values = [0.0]

        tp = 0
        fp = 0

        for i, (y, _) in enumerate(zip(y_true_sorted, y_scores_sorted)):
            if y == 1:
                tp += 1
            else:
                fp += 1

            tpr = tp / total_positives
            fpr = fp / total_negatives

            # Only add unique FPR points
            if fpr > fpr_values[-1]:
                tpr_values.append(tpr)
                fpr_values.append(fpr)

        # Add endpoint
        tpr_values.append(1.0)
        fpr_values.append(1.0)

        # Trapezoidal integration
        auc = 0.0
        for i in range(1, len(fpr_values)):
            auc += (fpr_values[i] - fpr_values[i-1]) * (tpr_values[i] + tpr_values[i-1]) / 2

        return float(auc)

    @staticmethod
    def _compute_auc_pr(y_true: np.ndarray, y_scores: np.ndarray) -> float:
        """
        Compute Area Under the Precision-Recall Curve.

        Args:
            y_true: Array of true binary labels
            y_scores: Array of anomaly scores

        Returns:
            AUC-PR value between 0 and 1
        """
        try:
            from sklearn.metrics import average_precision_score
            return float(average_precision_score(y_true, y_scores))
        except ImportError:
            logger.warning("scikit-learn not available, using fallback AUC-PR computation")
            return EvaluationMetrics._compute_auc_pr_fallback(y_true, y_scores)

    @staticmethod
    def _compute_auc_pr_fallback(y_true: np.ndarray, y_scores: np.ndarray) -> float:
        """
        Fallback AUC-PR computation without scikit-learn.

        Uses trapezoidal integration over PR curve points.
        """
        # Sort by scores descending
        sorted_indices = np.argsort(-y_scores)
        y_true_sorted = y_true[sorted_indices]

        # Compute precision and recall at each threshold
        total_positives = np.sum(y_true == 1)

        if total_positives == 0:
            return 0.0

        precision_values = [1.0]  # Starting point
        recall_values = [0.0]

        tp = 0
        fp = 0

        for i, y in enumerate(y_true_sorted):
            if y == 1:
                tp += 1
            else:
                fp += 1

            precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
            recall = tp / total_positives

            # Only add unique recall points
            if recall > recall_values[-1]:
                precision_values.append(precision)
                recall_values.append(recall)

        # Add endpoint
        precision_values.append(precision_values[-1])
        recall_values.append(1.0)

        # Trapezoidal integration (recall is x-axis for PR curve)
        auc = 0.0
        for i in range(1, len(recall_values)):
            auc += (recall_values[i] - recall_values[i-1]) * (
                precision_values[i] + precision_values[i-1]
            ) / 2

        return float(auc)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert EvaluationMetrics to a dictionary.

        Returns:
            Dictionary representation of all metrics
        """
        return {
            'model_name': self.model_name,
            'dataset_name': self.dataset_name,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'auc_roc': self.auc_roc,
            'auc_pr': self.auc_pr,
            'true_positives': self.true_positives,
            'true_negatives': self.true_negatives,
            'false_positives': self.false_positives,
            'false_negatives': self.false_negatives,
            'total_samples': self.total_samples,
            'anomaly_rate': self.anomaly_rate,
            'threshold_used': self.threshold_used,
            'runtime_seconds': self.runtime_seconds,
            'hyperparameter_count': self.hyperparameter_count,
            'metadata': self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        """
        Convert EvaluationMetrics to JSON string.

        Args:
            indent: JSON indentation level

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvaluationMetrics:
        """
        Create EvaluationMetrics from a dictionary.

        Args:
            data: Dictionary with metric values

        Returns:
            EvaluationMetrics instance
        """
        return cls(
            model_name=data['model_name'],
            dataset_name=data['dataset_name'],
            precision=data.get('precision', 0.0),
            recall=data.get('recall', 0.0),
            f1_score=data.get('f1_score', 0.0),
            auc_roc=data.get('auc_roc', 0.0),
            auc_pr=data.get('auc_pr', 0.0),
            true_positives=data.get('true_positives', 0),
            true_negatives=data.get('true_negatives', 0),
            false_positives=data.get('false_positives', 0),
            false_negatives=data.get('false_negatives', 0),
            total_samples=data.get('total_samples', 0),
            anomaly_rate=data.get('anomaly_rate', 0.0),
            threshold_used=data.get('threshold_used'),
            runtime_seconds=data.get('runtime_seconds'),
            hyperparameter_count=data.get('hyperparameter_count'),
            metadata=data.get('metadata', {}),
        )

    @classmethod
    def load_from_file(cls, filepath: str) -> EvaluationMetrics:
        """
        Load EvaluationMetrics from a JSON file.

        Args:
            filepath: Path to the JSON file

        Returns:
            EvaluationMetrics instance
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save_to_file(self, filepath: str) -> None:
        """
        Save EvaluationMetrics to a JSON file.

        Args:
            filepath: Path to save the JSON file
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(self.to_json())

    def compare_with(self, other: EvaluationMetrics) -> Dict[str, float]:
        """
        Compare this EvaluationMetrics instance with another.

        Args:
            other: Another EvaluationMetrics instance to compare against

        Returns:
            Dictionary of differences for each metric
        """
        metrics_to_compare = [
            'precision', 'recall', 'f1_score', 'auc_roc', 'auc_pr',
            'true_positives', 'true_negatives', 'false_positives',
            'false_negatives', 'anomaly_rate', 'runtime_seconds'
        ]

        differences = {}
        for metric in metrics_to_compare:
            my_value = getattr(self, metric, 0)
            other_value = getattr(other, metric, 0)
            differences[metric] = float(my_value - other_value)

        return differences

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return (
            f"EvaluationMetrics(\n"
            f"  model={self.model_name},\n"
            f"  dataset={self.dataset_name},\n"
            f"  precision={self.precision:.4f},\n"
            f"  recall={self.recall:.4f},\n"
            f"  f1_score={self.f1_score:.4f},\n"
            f"  auc_roc={self.auc_roc:.4f},\n"
            f"  auc_pr={self.auc_pr:.4f},\n"
            f"  confusion_matrix=[TP={self.true_positives}, "
            f"TN={self.true_negatives}, FP={self.false_positives}, "
            f"FN={self.false_negatives}],\n"
            f"  total_samples={self.total_samples},\n"
            f"  anomaly_rate={self.anomaly_rate:.4f}"
            f")"
        )

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        return self.__str__()
