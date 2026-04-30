"""
Evaluation metrics for anomaly detection models.

Implements F1-score, precision, recall, AUC, and confusion matrix generation
for model comparison and performance evaluation.

Per FR-006: Evaluation metrics must include F1-scores, precision, recall, AUC.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Union, Sequence
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, precision_recall_curve, auc as compute_auc_sklearn

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class EvaluationMetrics:
    """
    Container for all evaluation metrics computed during model evaluation.

    Attributes:
        f1_score: F1-score (harmonic mean of precision and recall)
        precision: Precision (true positives / (true positives + false positives))
        recall: Recall (true positives / (true positives + false negatives))
        auc: Area under ROC curve
        accuracy: Overall accuracy
        confusion_matrix: 2x2 confusion matrix [[TN, FP], [FN, TP]]
        thresholds: Array of thresholds used for evaluation
        precision_at_thresholds: Precision at each threshold
        recall_at_thresholds: Recall at each threshold
    """
    f1_score: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    auc: float = 0.0
    accuracy: float = 0.0
    confusion_matrix: Optional[np.ndarray] = None
    thresholds: Optional[np.ndarray] = None
    precision_at_thresholds: Optional[np.ndarray] = None
    recall_at_thresholds: Optional[np.ndarray] = None
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            'f1_score': self.f1_score,
            'precision': self.precision,
            'recall': self.recall,
            'auc': self.auc,
            'accuracy': self.accuracy,
            'true_positives': self.true_positives,
            'false_positives': self.false_positives,
            'true_negatives': self.true_negatives,
            'false_negatives': self.false_negatives,
            'timestamp': self.timestamp
        }

    def __repr__(self) -> str:
        return (f"EvaluationMetrics(f1={self.f1_score:.4f}, "
                f"precision={self.precision:.4f}, "
                f"recall={self.recall:.4f}, "
                f"auc={self.auc:.4f})")


def compute_f1_score(precision: float, recall: float, epsilon: float = 1e-10) -> float:
    """
    Compute F1-score as harmonic mean of precision and recall.

    Args:
        precision: Precision value (0-1)
        recall: Recall value (0-1)
        epsilon: Small constant to avoid division by zero

    Returns:
        F1-score value (0-1)
    """
    if precision + recall < epsilon:
        return 0.0
    return 2 * (precision * recall) / (precision + recall + epsilon)


def compute_precision(tp: int, fp: int, epsilon: float = 1e-10) -> float:
    """
    Compute precision from confusion matrix values.

    Args:
        tp: True positives count
        fp: False positives count
        epsilon: Small constant to avoid division by zero

    Returns:
        Precision value (0-1)
    """
    denominator = tp + fp
    if denominator < epsilon:
        return 0.0
    return tp / denominator


def compute_recall(tp: int, fn: int, epsilon: float = 1e-10) -> float:
    """
    Compute recall from confusion matrix values.

    Args:
        tp: True positives count
        fn: False negatives count
        epsilon: Small constant to avoid division by zero

    Returns:
        Recall value (0-1)
    """
    denominator = tp + fn
    if denominator < epsilon:
        return 0.0
    return tp / denominator


def compute_auc_from_pr_curve(precision: np.ndarray, recall: np.ndarray) -> float:
    """
    Compute area under PR curve.

    Args:
        precision: Precision values at different thresholds
        recall: Recall values at different thresholds

    Returns:
        AUC value (0-1)
    """
    if len(precision) < 2 or len(recall) < 2:
        return 0.0
    return compute_auc_sklearn(recall, precision)


def compute_auc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """
    Compute Area Under ROC Curve.

    Args:
        y_true: Ground truth binary labels (0 or 1)
        y_scores: Anomaly scores or predicted probabilities

    Returns:
        AUC value (0-1)
    """
    try:
        return compute_auc_sklearn(y_true, y_scores)
    except Exception as e:
        logger.warning(f"AUC computation failed: {e}, returning 0.0")
        return 0.0


def generate_confusion_matrix(
    y_true: Union[np.ndarray, List[int]],
    y_pred: Union[np.ndarray, List[int]],
    normalize: bool = False
) -> np.ndarray:
    """
    Generate confusion matrix from true and predicted labels.

    Creates a 2x2 confusion matrix for binary anomaly detection:
    [[TN, FP],
     [FN, TP]]

    Args:
        y_true: Ground truth binary labels (0=normal, 1=anomaly)
        y_pred: Predicted binary labels (0=normal, 1=anomaly)
        normalize: If True, return normalized matrix (proportions)

    Returns:
        2x2 numpy array confusion matrix [[TN, FP], [FN, TP]]

    Raises:
        ValueError: If input arrays have different lengths
        ValueError: If labels are not binary (0 or 1)
    """
    # Convert to numpy arrays
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    # Validate inputs
    if len(y_true) != len(y_pred):
        raise ValueError(
            f"Input arrays must have same length: "
            f"y_true={len(y_true)}, y_pred={len(y_pred)}"
        )

    # Validate binary labels
    unique_true = np.unique(y_true)
    unique_pred = np.unique(y_pred)

    if not set(unique_true).issubset({0, 1}):
        raise ValueError(
            f"y_true must contain only 0 and 1, got: {unique_true}"
        )
    if not set(unique_pred).issubset({0, 1}):
        raise ValueError(
            f"y_pred must contain only 0 and 1, got: {unique_pred}"
        )

    # Compute confusion matrix using sklearn
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1, keepdims=True)
        cm = np.nan_to_num(cm, nan=0.0)

    return cm


def extract_confusion_matrix_values(
    confusion_matrix: np.ndarray
) -> Tuple[int, int, int, int]:
    """
    Extract TP, TN, FP, FN from confusion matrix.

    Args:
        confusion_matrix: 2x2 confusion matrix [[TN, FP], [FN, TP]]

    Returns:
        Tuple of (true_negatives, false_positives, false_negatives, true_positives)
    """
    if confusion_matrix.shape != (2, 2):
        raise ValueError(
            f"Confusion matrix must be 2x2, got shape: {confusion_matrix.shape}"
        )

    tn = int(confusion_matrix[0, 0])
    fp = int(confusion_matrix[0, 1])
    fn = int(confusion_matrix[1, 0])
    tp = int(confusion_matrix[1, 1])

    return tn, fp, fn, tp


def save_confusion_matrix_plot(
    confusion_matrix: np.ndarray,
    output_path: Union[str, Path],
    title: str = "Confusion Matrix",
    normalize: bool = False,
    cmap: str = "Blues",
    figsize: Tuple[int, int] = (8, 6),
    annot: bool = True,
    fmt: str = ".2f" if normalize else "d"
) -> Path:
    """
    Save confusion matrix visualization as PNG file.

    Creates a heatmap visualization of the confusion matrix using seaborn.

    Args:
        confusion_matrix: 2x2 confusion matrix
        output_path: Path to save the PNG file
        title: Plot title
        normalize: If True, show normalized values (proportions)
        cmap: Matplotlib colormap name
        figsize: Figure size (width, height) in inches
        annot: If True, annotate cells with values
        fmt: Format string for annotations

    Returns:
        Path to saved file

    Raises:
        ValueError: If confusion matrix is not 2x2
        IOError: If file cannot be saved
    """
    # Validate input
    if confusion_matrix.shape != (2, 2):
        raise ValueError(
            f"Confusion matrix must be 2x2, got shape: {confusion_matrix.shape}"
        )

    # Ensure output path is Path object
    output_path = Path(output_path)

    # Create parent directories if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare labels
    labels = [['TN', 'FP'], ['FN', 'TP']]

    # Create figure
    plt.figure(figsize=figsize)

    # Create heatmap
    ax = sns.heatmap(
        confusion_matrix,
        annot=annot,
        fmt=fmt,
        cmap=cmap,
        cbar=True,
        xticklabels=['Normal', 'Anomaly'],
        yticklabels=['Normal', 'Anomaly'],
        linewidths=0.5
    )

    # Set title and labels
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel('Predicted Label', fontsize=12)
    plt.ylabel('True Label', fontsize=12)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)

    # Adjust layout
    plt.tight_layout()

    # Save figure
    try:
        plt.savefig(
            output_path,
            dpi=150,
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )
        plt.close()
        logger.info(f"Confusion matrix plot saved to: {output_path}")
        return output_path
    except Exception as e:
        plt.close()
        logger.error(f"Failed to save confusion matrix plot: {e}")
        raise IOError(f"Could not save confusion matrix plot: {e}")


def compute_all_metrics(
    y_true: Union[np.ndarray, List[int]],
    y_pred: Union[np.ndarray, List[int]],
    y_scores: Optional[Union[np.ndarray, List[float]]] = None
) -> EvaluationMetrics:
    """
    Compute all evaluation metrics from true and predicted labels.

    This is the main entry point for model evaluation, computing:
    - Confusion matrix (TN, FP, FN, TP)
    - Precision, Recall, F1-score
    - AUC (if scores provided)
    - Accuracy

    Args:
        y_true: Ground truth binary labels (0=normal, 1=anomaly)
        y_pred: Predicted binary labels (0=normal, 1=anomaly)
        y_scores: Optional anomaly scores for AUC computation

    Returns:
        EvaluationMetrics object containing all computed metrics
    """
    # Convert inputs
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    # Generate confusion matrix
    cm = generate_confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = extract_confusion_matrix_values(cm)

    # Compute precision, recall, f1
    precision = compute_precision(tp, fp)
    recall = compute_recall(tp, fn)
    f1 = compute_f1_score(precision, recall)

    # Compute accuracy
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total > 0 else 0.0

    # Compute AUC if scores provided
    auc = 0.0
    if y_scores is not None:
        y_scores = np.asarray(y_scores)
        auc = compute_auc(y_true, y_scores)

    # Create metrics object
    metrics = EvaluationMetrics(
        f1_score=f1,
        precision=precision,
        recall=recall,
        auc=auc,
        accuracy=accuracy,
        confusion_matrix=cm,
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn
    )

    logger.info(
        f"Computed metrics: F1={f1:.4f}, Precision={precision:.4f}, "
        f"Recall={recall:.4f}, AUC={auc:.4f}"
    )

    return metrics


def generate_confusion_matrix_with_thresholds(
    y_true: Union[np.ndarray, List[int]],
    y_scores: Union[np.ndarray, List[float]],
    thresholds: Optional[List[float]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    base_name: str = "confusion_matrix"
) -> Dict[float, EvaluationMetrics]:
    """
    Generate confusion matrices across multiple thresholds.

    Useful for threshold calibration and analysis.

    Args:
        y_true: Ground truth binary labels
        y_scores: Anomaly scores (higher = more anomalous)
        thresholds: List of thresholds to evaluate (default: 10 evenly spaced)
        output_dir: Optional directory to save confusion matrix plots
        base_name: Base name for output files

    Returns:
        Dictionary mapping threshold to EvaluationMetrics
    """
    y_true = np.asarray(y_true)
    y_scores = np.asarray(y_scores)

    # Default thresholds if not provided
    if thresholds is None:
        thresholds = np.linspace(
            np.percentile(y_scores, 10),
            np.percentile(y_scores, 90),
            10
        ).tolist()

    results = {}

    for threshold in thresholds:
        # Apply threshold to get binary predictions
        y_pred = (y_scores >= threshold).astype(int)

        # Compute metrics
        metrics = compute_all_metrics(y_true, y_pred)

        # Save confusion matrix plot if output_dir provided
        if output_dir is not None:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            plot_path = output_dir / f"{base_name}_threshold_{threshold:.3f}.png"
            try:
                save_confusion_matrix_plot(
                    metrics.confusion_matrix,
                    plot_path,
                    title=f"Confusion Matrix (Threshold={threshold:.3f})"
                )
            except Exception as e:
                logger.warning(f"Failed to save plot for threshold {threshold}: {e}")

        results[threshold] = metrics

    logger.info(
        f"Generated confusion matrices for {len(thresholds)} thresholds"
    )

    return results


def main():
    """
    Main function for testing confusion matrix functionality.

    Runs self-test with synthetic data to verify all functions work correctly.
    """
    print("=" * 60)
    print("Confusion Matrix Generator - Self Test")
    print("=" * 60)

    # Create synthetic test data
    np.random.seed(42)
    n_samples = 1000
    n_anomalies = 100

    # Generate ground truth (10% anomalies)
    y_true = np.zeros(n_samples, dtype=int)
    anomaly_indices = np.random.choice(n_samples, n_anomalies, replace=False)
    y_true[anomaly_indices] = 1

    # Generate predictions (80% accuracy on anomalies, 95% on normal)
    y_pred = y_true.copy()
    # Miss some anomalies (false negatives)
    fn_count = int(n_anomalies * 0.2)
    fn_indices = np.random.choice(anomaly_indices, fn_count, replace=False)
    y_pred[fn_indices] = 0
    # Add some false positives
    normal_indices = np.setdiff1d(np.arange(n_samples), anomaly_indices)
    fp_count = int(len(normal_indices) * 0.05)
    fp_indices = np.random.choice(normal_indices, fp_count, replace=False)
    y_pred[fp_indices] = 1

    # Generate scores (for AUC)
    y_scores = np.random.random(n_samples)
    y_scores[anomaly_indices] += np.random.uniform(0.3, 0.5, n_anomalies)
    y_scores = np.clip(y_scores, 0, 1)

    print(f"\nTest data: {n_samples} samples, {n_anomalies} anomalies")

    # Test confusion matrix generation
    print("\n1. Testing confusion matrix generation...")
    cm = generate_confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = extract_confusion_matrix_values(cm)
    print(f"   Confusion Matrix:\n{cm}")
    print(f"   TN={tn}, FP={fp}, FN={fn}, TP={tp}")

    # Test metrics computation
    print("\n2. Testing metrics computation...")
    metrics = compute_all_metrics(y_true, y_pred, y_scores)
    print(f"   F1-score: {metrics.f1_score:.4f}")
    print(f"   Precision: {metrics.precision:.4f}")
    print(f"   Recall: {metrics.recall:.4f}")
    print(f"   AUC: {metrics.auc:.4f}")
    print(f"   Accuracy: {metrics.accuracy:.4f}")

    # Test plot saving
    print("\n3. Testing plot saving...")
    output_path = Path("data/evaluation/confusion_matrix_test.png")
    try:
        saved_path = save_confusion_matrix_plot(
            cm,
            output_path,
            title="Test Confusion Matrix"
        )
        print(f"   Saved to: {saved_path}")
    except Exception as e:
        print(f"   Plot save skipped (no matplotlib): {e}")

    # Test multi-threshold analysis
    print("\n4. Testing multi-threshold analysis...")
    threshold_results = generate_confusion_matrix_with_thresholds(
        y_true, y_scores,
        thresholds=[0.3, 0.5, 0.7],
        output_dir="data/evaluation/threshold_analysis"
    )
    for threshold, m in threshold_results.items():
        print(f"   Threshold {threshold:.2f}: F1={m.f1_score:.4f}, "
              f"Precision={m.precision:.4f}, Recall={m.recall:.4f}")

    print("\n" + "=" * 60)
    print("Self Test Complete")
    print("=" * 60)

    return metrics


if __name__ == "__main__":
    main()
