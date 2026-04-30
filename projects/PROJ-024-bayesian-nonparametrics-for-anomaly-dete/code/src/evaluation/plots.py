"""
Plot generation utilities for evaluation metrics.

This module provides functions to generate and save ROC and PR curves,
as well as other evaluation visualizations for anomaly detection models.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ROCPlotConfig:
    """Configuration for ROC curve plotting."""
    title: str = "ROC Curve"
    xlabel: str = "False Positive Rate"
    ylabel: str = "True Positive Rate"
    figsize: Tuple[int, int] = (10, 8)
    dpi: int = 150
    save_format: str = "png"
    show_diagonal: bool = True
    grid: bool = True
    legend: bool = True
    
@dataclass
class PRPlotConfig:
    """Configuration for Precision-Recall curve plotting."""
    title: str = "Precision-Recall Curve"
    xlabel: str = "Recall"
    ylabel: str = "Precision"
    figsize: Tuple[int, int] = (10, 8)
    dpi: int = 150
    save_format: str = "png"
    grid: bool = True
    legend: bool = True
    baseline: bool = True  # Show baseline (mean positive rate)
    
@dataclass
class EvaluationPlotConfig:
    """Configuration for combined evaluation plots."""
    output_dir: str = "paper/figures"
    prefix: str = ""
    roc_config: ROCPlotConfig = field(default_factory=ROCPlotConfig)
    pr_config: PRPlotConfig = field(default_factory=PRPlotConfig)
    

def generate_roc_curve(
    fpr: np.ndarray,
    tpr: np.ndarray,
    auc: float,
    config: Optional[ROCPlotConfig] = None
) -> plt.Figure:
    """
    Generate a ROC curve plot.
    
    Args:
        fpr: False positive rates array
        tpr: True positive rates array
        auc: Area under the curve value
        config: ROCPlotConfig instance or None for defaults
        
    Returns:
        matplotlib Figure object
    """
    if config is None:
        config = ROCPlotConfig()
        
    fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)
    
    # Plot ROC curve
    ax.plot(fpr, tpr, 'b-', linewidth=2, 
            label=f'ROC Curve (AUC = {auc:.4f})')
    
    # Plot diagonal line (random classifier)
    if config.show_diagonal:
        ax.plot([0, 1], [0, 1], 'r--', linewidth=1, 
                label='Random Classifier', alpha=0.5)
    
    # Configure axes
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel(config.xlabel, fontsize=12)
    ax.set_ylabel(config.ylabel, fontsize=12)
    ax.set_title(config.title, fontsize=14, fontweight='bold')
    
    if config.grid:
        ax.grid(True, alpha=0.3)
        
    if config.legend:
        ax.legend(loc='lower right', fontsize=10)
        
    return fig


def save_roc_curve(
    fpr: np.ndarray,
    tpr: np.ndarray,
    auc: float,
    output_path: Path,
    config: Optional[ROCPlotConfig] = None
) -> Path:
    """
    Generate and save a ROC curve to file.
    
    Args:
        fpr: False positive rates array
        tpr: True positive rates array
        auc: Area under the curve value
        output_path: Path to save the figure
        config: ROCPlotConfig instance or None for defaults
        
    Returns:
        Path to the saved file
    """
    if config is None:
        config = ROCPlotConfig()
        
    fig = generate_roc_curve(fpr, tpr, auc, config)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fig.savefig(output_path, format=config.save_format, 
               bbox_inches='tight', dpi=config.dpi)
    plt.close(fig)
    
    logger.info(f"ROC curve saved to {output_path}")
    return output_path


def generate_pr_curve(
    recall: np.ndarray,
    precision: np.ndarray,
    ap: float,
    positive_rate: float,
    config: Optional[PRPlotConfig] = None
) -> plt.Figure:
    """
    Generate a Precision-Recall curve plot.
    
    Args:
        recall: Recall values array (sorted ascending)
        precision: Precision values array (corresponding to recall)
        ap: Average precision score
        positive_rate: Fraction of positive samples in dataset (for baseline)
        config: PRPlotConfig instance or None for defaults
        
    Returns:
        matplotlib Figure object
        
    Notes:
        - PR curves are typically plotted with recall on x-axis and precision on y-axis
        - The curve should be monotonically non-increasing
        - Average Precision (AP) is the area under the PR curve
    """
    if config is None:
        config = PRPlotConfig()
        
    fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)
    
    # Sort by recall for proper plotting
    sort_idx = np.argsort(recall)
    recall_sorted = recall[sort_idx]
    precision_sorted = precision[sort_idx]
    
    # Plot PR curve
    ax.plot(recall_sorted, precision_sorted, 'b-', linewidth=2,
            label=f'PR Curve (AP = {ap:.4f})')
    
    # Fill area under curve for visualization
    ax.fill_between(recall_sorted, precision_sorted, alpha=0.15, color='blue')
    
    # Plot baseline (mean positive rate) if requested
    if config.baseline:
        ax.axhline(y=positive_rate, color='r', linestyle='--', 
                  linewidth=1, label=f'Baseline (Positive Rate = {positive_rate:.4f})',
                  alpha=0.7)
    
    # Configure axes
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel(config.xlabel, fontsize=12)
    ax.set_ylabel(config.ylabel, fontsize=12)
    ax.set_title(config.title, fontsize=14, fontweight='bold')
    
    if config.grid:
        ax.grid(True, alpha=0.3)
        
    if config.legend:
        ax.legend(loc='lower left', fontsize=10)
        
    return fig


def save_pr_curve(
    recall: np.ndarray,
    precision: np.ndarray,
    ap: float,
    positive_rate: float,
    output_path: Path,
    config: Optional[PRPlotConfig] = None
) -> Path:
    """
    Generate and save a Precision-Recall curve to file.
    
    Args:
        recall: Recall values array (sorted ascending)
        precision: Precision values array (corresponding to recall)
        ap: Average precision score
        positive_rate: Fraction of positive samples in dataset
        output_path: Path to save the figure
        config: PRPlotConfig instance or None for defaults
        
    Returns:
        Path to the saved file
        
    Example:
        >>> recall = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        >>> precision = np.array([0.5, 0.6, 0.7, 0.65, 0.6, 0.55])
        >>> ap = 0.62
        >>> positive_rate = 0.1
        >>> save_pr_curve(recall, precision, ap, positive_rate, 
        ...               Path('paper/figures/pr_curve.png'))
    """
    if config is None:
        config = PRPlotConfig()
        
    fig = generate_pr_curve(recall, precision, ap, positive_rate, config)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fig.savefig(output_path, format=config.save_format,
               bbox_inches='tight', dpi=config.dpi)
    plt.close(fig)
    
    logger.info(f"PR curve saved to {output_path}")
    return output_path


def compute_precision_recall_curve(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    threshold: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Compute precision and recall values for different thresholds.
    
    Args:
        y_true: True binary labels (0 or 1)
        y_scores: Anomaly scores (higher = more anomalous)
        threshold: Optional array of thresholds to evaluate
        
    Returns:
        Tuple of (precision, recall, average_precision)
        
    Notes:
        - This function computes the PR curve points manually
        - Average Precision is computed using trapezoidal rule
    """
    if threshold is None:
        # Use unique score values as thresholds
        threshold = np.unique(y_scores)
        # Add 0 and 1 for completeness
        threshold = np.concatenate([[0], threshold, [1 + np.max(y_scores)]])
        
    precision_list = []
    recall_list = []
    
    for thresh in threshold:
        y_pred = (y_scores >= thresh).astype(int)
        
        # True positives, false positives, false negatives
        tp = np.sum((y_pred == 1) & (y_true == 1))
        fp = np.sum((y_pred == 1) & (y_true == 0))
        fn = np.sum((y_pred == 0) & (y_true == 1))
        
        # Compute precision and recall
        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        precision_list.append(precision)
        recall_list.append(recall)
    
    precision_arr = np.array(precision_list)
    recall_arr = np.array(recall_list)
    
    # Compute Average Precision using trapezoidal rule
    # Sort by recall for proper integration
    sort_idx = np.argsort(recall_arr)
    recall_sorted = recall_arr[sort_idx]
    precision_sorted = precision_arr[sort_idx]
    
    # Compute AP
    ap = np.trapz(precision_sorted, recall_sorted)
    
    return precision_arr, recall_arr, ap


def generate_evaluation_plots(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    output_dir: Path,
    prefix: str = "",
    model_name: str = "Model"
) -> Dict[str, Path]:
    """
    Generate and save both ROC and PR curves for a model.
    
    Args:
        y_true: True binary labels (0 = normal, 1 = anomaly)
        y_scores: Anomaly scores from the model
        output_dir: Directory to save plots
        prefix: Prefix for output filenames
        model_name: Name of the model for plot titles
        
    Returns:
        Dictionary mapping plot type to saved file path
        
    Raises:
        ValueError: If input arrays have mismatched lengths
    """
    if len(y_true) != len(y_scores):
        raise ValueError("y_true and y_scores must have same length")
        
    # Compute ROC curve
    from sklearn.metrics import roc_curve, auc as roc_auc
    fpr, tpr, _ = roc_curve(y_true, y_scores)
    roc_auc_val = roc_auc(y_true, y_scores)
    
    # Compute PR curve
    precision, recall, ap = compute_precision_recall_curve(y_true, y_scores)
    positive_rate = np.mean(y_true)
    
    # Generate plots
    saved_files = {}
    
    # ROC curve
    roc_config = ROCPlotConfig(
        title=f"ROC Curve - {model_name}"
    )
    roc_path = output_dir / f"{prefix}roc_curve_{model_name}.png"
    save_roc_curve(fpr, tpr, roc_auc_val, roc_path, roc_config)
    saved_files['roc'] = roc_path
    
    # PR curve
    pr_config = PRPlotConfig(
        title=f"Precision-Recall Curve - {model_name}"
    )
    pr_path = output_dir / f"{prefix}pr_curve_{model_name}.png"
    save_pr_curve(recall, precision, ap, positive_rate, pr_path, pr_config)
    saved_files['pr'] = pr_path
    
    logger.info(f"Generated evaluation plots in {output_dir}")
    return saved_files


def main():
    """
    Main function for testing PR curve generation.
    
    This function generates synthetic anomaly scores and true labels,
    then creates and saves ROC and PR curves.
    """
    # Create output directory
    output_dir = Path("paper/figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate synthetic data for testing
    np.random.seed(42)
    n_samples = 1000
    n_anomalies = int(n_samples * 0.1)  # 10% anomaly rate
    
    # True labels: 0 = normal, 1 = anomaly
    y_true = np.zeros(n_samples, dtype=int)
    y_true[:n_anomalies] = 1
    
    # Anomaly scores: higher for anomalies
    y_scores = np.random.random(n_samples)
    y_scores[:n_anomalies] += 0.3  # Anomalies have higher scores
    y_scores = np.clip(y_scores, 0, 1)
    
    # Generate evaluation plots
    saved_files = generate_evaluation_plots(
        y_true=y_true,
        y_scores=y_scores,
        output_dir=output_dir,
        prefix="test_",
        model_name="DPGMM"
    )
    
    print(f"Generated files:")
    for plot_type, path in saved_files.items():
        print(f"  {plot_type}: {path}")
        
    return saved_files


if __name__ == "__main__":
    main()
