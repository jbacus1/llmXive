"""
Evaluation metrics for anomaly detection models.

Implements F1-score, precision, recall, AUC computation and
confusion matrix generation with visualization.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Union, Sequence
import numpy as np
from pathlib import Path
import logging

# Conditional sklearn import for metrics
try:
    from sklearn.metrics import (
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
        confusion_matrix,
        roc_curve,
        precision_recall_curve,
    )
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("scikit-learn not available, using fallback implementations")

from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """Container for all evaluation metrics."""
    f1_score: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    auc_roc: float = 0.0
    auc_pr: float = 0.0
    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    total_samples: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'f1_score': self.f1_score,
            'precision': self.precision,
            'recall': self.recall,
            'auc_roc': self.auc_roc,
            'auc_pr': self.auc_pr,
            'true_positives': self.true_positives,
            'true_negatives': self.true_negatives,
            'false_positives': self.false_positives,
            'false_negatives': self.false_negatives,
            'total_samples': self.total_samples,
            'timestamp': self.timestamp.isoformat(),
        }


def compute_f1_score(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    average: str = 'binary',
    zero_division: int = 0
) -> float:
    """
    Compute F1 score between true and predicted labels.

    Args:
        y_true: Ground truth binary labels
        y_pred: Predicted binary labels
        average: Type of averaging ('binary', 'macro', 'micro')
        zero_division: Value to return when denominator is zero

    Returns:
        F1 score value
    """
    if SKLEARN_AVAILABLE:
        return float(f1_score(y_true, y_pred, average=average, zero_division=zero_division))

    # Fallback implementation
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))

    precision = tp / (tp + fp) if (tp + fp) > 0 else zero_division
    recall = tp / (tp + fn) if (tp + fn) > 0 else zero_division

    if precision + recall == 0:
        return zero_division

    return float(2 * precision * recall / (precision + recall))


def compute_precision(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    zero_division: int = 0
) -> float:
    """
    Compute precision score.

    Args:
        y_true: Ground truth binary labels
        y_pred: Predicted binary labels
        zero_division: Value to return when denominator is zero

    Returns:
        Precision score value
    """
    if SKLEARN_AVAILABLE:
        return float(precision_score(y_true, y_pred, zero_division=zero_division))

    # Fallback implementation
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))

    if tp + fp == 0:
        return zero_division

    return float(tp / (tp + fp))


def compute_recall(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    zero_division: int = 0
) -> float:
    """
    Compute recall score.

    Args:
        y_true: Ground truth binary labels
        y_pred: Predicted binary labels
        zero_division: Value to return when denominator is zero

    Returns:
        Recall score value
    """
    if SKLEARN_AVAILABLE:
        return float(recall_score(y_true, y_pred, zero_division=zero_division))

    # Fallback implementation
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    tp = np.sum((y_true == 1) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))

    if tp + fn == 0:
        return zero_division

    return float(tp / (tp + fn))


def compute_auc(
    y_true: Sequence[int],
    y_scores: Sequence[float],
    average: str = 'macro'
) -> float:
    """
    Compute Area Under the Curve (AUC) for ROC or PR curves.

    Args:
        y_true: Ground truth binary labels
        y_scores: Target scores (probability estimates)
        average: Averaging method ('macro', 'weighted', 'samples')

    Returns:
        AUC value
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn required for AUC computation")

    y_true = np.array(y_true)
    y_scores = np.array(y_scores)

    try:
        return float(roc_auc_score(y_true, y_scores, average=average))
    except ValueError as e:
        logger.warning(f"AUC computation failed: {e}")
        return 0.0


def generate_confusion_matrix(
    y_true: Sequence[int],
    y_pred: Sequence[int]
) -> np.ndarray:
    """
    Generate confusion matrix from true and predicted labels.

    Args:
        y_true: Ground truth binary labels
        y_pred: Predicted binary labels

    Returns:
        2x2 confusion matrix [[TN, FP], [FN, TP]]
    """
    if SKLEARN_AVAILABLE:
        return confusion_matrix(y_true, y_pred)

    # Fallback implementation
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    tn = np.sum((y_true == 0) & (y_pred == 0))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    tp = np.sum((y_true == 1) & (y_pred == 1))

    return np.array([[tn, fp], [fn, tp]])


def save_confusion_matrix_plot(
    cm: np.ndarray,
    labels: List[str] = None,
    output_path: Union[str, Path, None] = None
) -> Optional[str]:
    """
    Save confusion matrix as a visualization.

    Args:
        cm: Confusion matrix array
        labels: Optional label names for rows/columns
        output_path: Path to save the figure (optional)

    Returns:
        Path to saved figure, or None if not saved
    """
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        logger.warning("matplotlib/seaborn not available for plotting")
        return None

    if labels is None:
        labels = ['Negative', 'Positive']

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
               xticklabels=labels, yticklabels=labels, ax=ax)
    ax.set_xlabel('Predicted')
    ax.set_ylabel('True')
    ax.set_title('Confusion Matrix')

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return str(output_path)

    return str(fig)


def compute_all_metrics(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    y_scores: Optional[Sequence[float]] = None
) -> EvaluationMetrics:
    """
    Compute all evaluation metrics at once.

    Args:
        y_true: Ground truth binary labels
        y_pred: Predicted binary labels
        y_scores: Optional probability scores for AUC computation

    Returns:
        EvaluationMetrics object with all computed metrics
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    # Compute confusion matrix
    cm = generate_confusion_matrix(y_true, y_pred)
  tn, fp, fn, tp = cm.ravel()

  metrics = EvaluationMetrics(
      f1_score=compute_f1_score(y_true, y_pred),
      precision=compute_precision(y_true, y_pred),
      recall=compute_recall(y_true, y_pred),
      true_positives=int(tp),
      true_negatives=int(tn),
      false_positives=int(fp),
      false_negatives=int(fn),
      total_samples=int(len(y_true)),
  )

  # Compute AUC if scores provided
  if y_scores is not None:
      try:
          metrics.auc_roc = compute_auc(y_true, y_scores)
      except Exception as e:
          logger.warning(f"AUC computation failed: {e}")
          metrics.auc_roc = 0.0

  return metrics


def main() -> None:
    """Main entry point for standalone testing."""
    logging.basicConfig(level=logging.INFO)

    # Generate test data
    np.random.seed(42)
    n_samples = 1000
    y_true = np.random.randint(0, 2, n_samples)
    y_pred = np.random.randint(0, 2, n_samples)
    y_scores = np.random.rand(n_samples)

    # Compute metrics
    metrics = compute_all_metrics(y_true, y_pred, y_scores)

    logger.info(f"F1 Score: {metrics.f1_score:.4f}")
    logger.info(f"Precision: {metrics.precision:.4f}")
    logger.info(f"Recall: {metrics.recall:.4f}")
    logger.info(f"AUC-ROC: {metrics.auc_roc:.4f}")
    logger.info(f"Confusion Matrix: TP={metrics.true_positives}, "
               f"FP={metrics.false_positives}, "
               f"FN={metrics.false_negatives}, "
               f"TN={metrics.true_negatives}")
