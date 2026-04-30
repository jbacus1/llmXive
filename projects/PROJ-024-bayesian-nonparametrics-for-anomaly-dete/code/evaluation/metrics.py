"""
Evaluation metrics module for US2 baseline comparison.

Defines EvaluationMetrics schema and computation functions for
F1-score, precision, recall, AUC, and confusion matrix generation.

Per FR-006: Metrics must include F1-scores, precision, recall, AUC.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
from sklearn.metrics import (
    f1_score, precision_score, recall_score, roc_auc_score,
    confusion_matrix, roc_curve, precision_recall_curve
)

@dataclass
class EvaluationMetrics:
    """
    Container for evaluation metrics output schema.
    
    Per FR-006: Must include F1-scores, precision, recall, AUC.
    Per US2: Used for baseline comparison with DPGMM.
    """
    f1_score: float = field(default=0.0)
    precision: float = field(default=0.0)
    recall: float = field(default=0.0)
    auc: float = field(default=0.0)
    confusion_matrix: List[List[int]] = field(default_factory=list)
    tp: int = field(default=0)
    fp: int = field(default=0)
    tn: int = field(default=0)
    fn: int = field(default=0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            'f1_score': self.f1_score,
            'precision': self.precision,
            'recall': self.recall,
            'auc': self.auc,
            'confusion_matrix': self.confusion_matrix,
            'tp': self.tp,
            'fp': self.fp,
            'tn': self.tn,
            'fn': self.fn
        }

def compute_f1_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute F1-score from true and predicted labels.
    
    Args:
        y_true: Ground truth binary labels (0 or 1)
        y_pred: Predicted binary labels (0 or 1)
    
    Returns:
        F1-score as float
    """
    return f1_score(y_true, y_pred, zero_division=0.0)

def compute_precision(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute precision from true and predicted labels.
    
    Args:
        y_true: Ground truth binary labels (0 or 1)
        y_pred: Predicted binary labels (0 or 1)
    
    Returns:
        Precision as float
    """
    return precision_score(y_true, y_pred, zero_division=0.0)

def compute_recall(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute recall from true and predicted labels.
    
    Args:
        y_true: Ground truth binary labels (0 or 1)
        y_pred: Predicted binary labels (0 or 1)
    
    Returns:
        Recall as float
    """
    return recall_score(y_true, y_pred, zero_division=0.0)

def compute_auc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """
    Compute AUC-ROC from true labels and anomaly scores.
    
    Args:
        y_true: Ground truth binary labels (0 or 1)
        y_scores: Anomaly scores (higher = more anomalous)
    
    Returns:
        AUC-ROC as float
    """
    return roc_auc_score(y_true, y_scores)

def generate_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> Tuple[np.ndarray, Dict[str, int]]:
    """
    Generate confusion matrix and component counts.
    
    Args:
        y_true: Ground truth binary labels (0 or 1)
        y_pred: Predicted binary labels (0 or 1)
    
    Returns:
        Tuple of (confusion matrix array, dict with tp/fp/tn/fn)
    """
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
    return cm, {'tp': int(tp), 'fp': int(fp), 'tn': int(tn), 'fn': int(fn)}

def save_confusion_matrix_plot(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    output_path: str,
    title: str = "Confusion Matrix"
) -> Tuple[np.ndarray, Dict[str, int]]:
    """
    Generate and save confusion matrix visualization as PNG file.
    
    Args:
        y_true: Ground truth binary labels (0 or 1)
        y_pred: Predicted binary labels (0 or 1)
        output_path: Path to save the PNG file (must end with .png)
        title: Title for the plot
    
    Returns:
        Tuple of (confusion matrix array, dict with tp/fp/tn/fn)
    
    Raises:
        ValueError: If output_path doesn't end with .png
    """
    if not output_path.endswith('.png'):
        raise ValueError("output_path must end with .png")
    
    cm, counts = generate_confusion_matrix(y_true, y_pred)
    
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
               xticklabels=['Normal', 'Anomaly'],
               yticklabels=['Normal', 'Anomaly'])
    plt.title(title)
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    return cm, counts

def compute_all_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_scores: Optional[np.ndarray] = None
) -> EvaluationMetrics:
    """
    Compute all evaluation metrics at once.
    
    Args:
        y_true: Ground truth binary labels (0 or 1)
        y_pred: Predicted binary labels (0 or 1)
        y_scores: Optional anomaly scores for AUC computation
    
    Returns:
        EvaluationMetrics object with all computed values
    """
    cm, counts = generate_confusion_matrix(y_true, y_pred)
    
    metrics = EvaluationMetrics(
        f1_score=compute_f1_score(y_true, y_pred),
        precision=compute_precision(y_true, y_pred),
        recall=compute_recall(y_true, y_pred),
        confusion_matrix=cm.tolist(),
        tp=counts['tp'],
        fp=counts['fp'],
        tn=counts['tn'],
        fn=counts['fn']
    )
    
    if y_scores is not None:
        metrics.auc = compute_auc(y_true, y_scores)
    
    return metrics
