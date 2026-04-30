"""
Precision-Recall (PR) Curve Generation for Anomaly Detection Evaluation

This module provides functionality to generate and export Precision-Recall
curves as PNG files for evaluating anomaly detection models against baselines.

Per FR-006: Generate confusion matrices, ROC curves, PR curves for evaluation.
"""

import os
import json
import logging
from typing import Tuple, Optional, Dict, List

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve, auc

logger = logging.getLogger(__name__)

# Default output path for PR curve figures
DEFAULT_OUTPUT_DIR = "paper/figures"
DEFAULT_OUTPUT_FILENAME = "pr_curve.png"

def compute_precision_recall_curve(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    anomaly_threshold: Optional[float] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute precision-recall curve from ground truth labels and anomaly scores.
    
    Args:
        y_true: Binary ground truth labels (1 = anomaly, 0 = normal)
        y_scores: Anomaly scores (higher = more anomalous)
        anomaly_threshold: Optional threshold for binary predictions
    
    Returns:
        Tuple of (precision, recall, thresholds) arrays
    """
    precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
    return precision, recall, thresholds


def calculate_average_precision(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """
    Calculate Average Precision (AP) from precision-recall curve.
    
    AP is the area under the PR curve and provides a single-number summary
    of the precision-recall tradeoff across all thresholds.
    
    Args:
        y_true: Binary ground truth labels
        y_scores: Anomaly scores
    
    Returns:
        Average Precision score (area under PR curve)
    """
    precision, recall, _ = compute_precision_recall_curve(y_true, y_scores)
    # Use trapezoidal rule for PR curve (recall is x-axis, precision is y-axis)
    ap = auc(recall, precision)
    return ap


def plot_precision_recall_curve(
    precision: np.ndarray,
    recall: np.ndarray,
    output_path: str,
    title: str = "Precision-Recall Curve",
    show_ap: bool = True,
    ap_value: Optional[float] = None,
    figsize: Tuple[int, int] = (10, 8),
    color: str = "blue",
    linewidth: int = 2
) -> None:
    """
    Plot and save PR curve to PNG file.
    
    Args:
        precision: Precision values from precision_recall_curve
        recall: Recall values from precision_recall_curve
        output_path: Path to save PNG file (must end in .png)
        title: Plot title
        show_ap: Whether to display Average Precision on plot
        ap_value: Pre-computed AP value (if None, will be calculated from curve)
        figsize: Figure size tuple (width, height)
        color: Line color for the PR curve
        linewidth: Line width for the PR curve
    """
    # Create output directory if needed
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot PR curve
    ax.plot(recall, precision, color=color, linewidth=linewidth, 
            label='PR Curve', alpha=0.8)
    ax.fill_between(recall, precision, alpha=0.15, color=color)
    
    # Add reference line at random classifier (precision = prevalence)
    # For imbalanced datasets, this is typically low
    prevalence = np.mean(np.array([1 if p > 0 else 0 for p in precision]))
    ax.axhline(y=prevalence, color='gray', linestyle='--', alpha=0.5, 
               label=f'Random (prevalence={prevalence:.2f})')
    
    # Set labels and title
    ax.set_xlabel('Recall', fontsize=12, fontweight='bold')
    ax.set_ylabel('Precision', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Set axis limits
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    
    # Calculate and display Average Precision
    if show_ap:
        if ap_value is None:
            ap_value = auc(recall, precision)
        ax.text(0.05, 0.95, f'AP = {ap_value:.3f}', transform=ax.transAxes,
                fontsize=12, verticalalignment='top', fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Add legend and grid
    ax.legend(loc='lower left', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle=':')
    
    # Save figure with high DPI for publication quality
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    
    logger.info(f"PR curve saved to {output_path}")


def generate_pr_curve_from_scores(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    output_path: str,
    title: str = "Precision-Recall Curve",
    show_ap: bool = True,
    figsize: Tuple[int, int] = (10, 8)
) -> float:
    """
    Generate PR curve directly from ground truth labels and anomaly scores.
    
    This is a convenience function that combines curve computation and plotting.
    
    Args:
        y_true: Binary ground truth labels (1 = anomaly, 0 = normal)
        y_scores: Anomaly scores (higher = more anomalous)
        output_path: Path to save PNG file
        title: Plot title
        show_ap: Whether to display Average Precision on plot
        figsize: Figure size tuple
    
    Returns:
        Average Precision score
    """
    precision, recall, _ = compute_precision_recall_curve(y_true, y_scores)
    ap = calculate_average_precision(y_true, y_scores)
    
    plot_precision_recall_curve(
        precision=precision,
        recall=recall,
        output_path=output_path,
        title=title,
        show_ap=show_ap,
        ap_value=ap,
        figsize=figsize
    )
    
    return ap


def plot_multiple_pr_curves(
    curves: Dict[str, Tuple[np.ndarray, np.ndarray, float]],
    output_path: str,
    title: str = "Precision-Recall Curves Comparison",
    figsize: Tuple[int, int] = (10, 8)
) -> None:
    """
    Plot multiple PR curves on the same figure for comparison.
    
    Args:
        curves: Dict mapping model names to (precision, recall, ap) tuples
        output_path: Path to save PNG file
        title: Plot title
        figsize: Figure size tuple
    """
    # Create output directory if needed
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(curves)))
    
    for idx, (model_name, (precision, recall, ap)) in enumerate(curves.items()):
        ax.plot(recall, precision, color=colors[idx], linewidth=2, 
                label=f'{model_name} (AP={ap:.3f})', alpha=0.8)
        ax.fill_between(recall, precision, alpha=0.1, color=colors[idx])
    
    # Set labels and title
    ax.set_xlabel('Recall', fontsize=12, fontweight='bold')
    ax.set_ylabel('Precision', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Set axis limits
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    
    # Add legend and grid
    ax.legend(loc='lower left', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle=':')
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    
    logger.info(f"Multiple PR curves saved to {output_path}")

def generate_pr_curves_from_evaluation_data(
    evaluation_data_path: str,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    output_filename: str = "pr_curves_comparison.png"
) -> Dict[str, float]:
    """
    Generate PR curves from evaluation data JSON file.
    
    Expected JSON format:
    {
        "datasets": {
            "dataset_name": {
                "y_true": [0, 1, 0, ...],
                "y_scores": [0.1, 0.9, 0.2, ...]
            },
            ...
        }
    }
    
    Args:
        evaluation_data_path: Path to JSON file with evaluation data
        output_dir: Directory to save output PNG files
        output_filename: Name for the comparison figure
    
    Returns:
        Dict mapping dataset names to their AP scores
    """
    # Load evaluation data
    with open(evaluation_data_path, 'r') as f:
        data = json.load(f)
    
    datasets = data.get('datasets', {})
    curves = {}
    ap_scores = {}
    
    for dataset_name, dataset_data in datasets.items():
        y_true = np.array(dataset_data['y_true'])
        y_scores = np.array(dataset_data['y_scores'])
        
        precision, recall, _ = compute_precision_recall_curve(y_true, y_scores)
        ap = calculate_average_precision(y_true, y_scores)
        
        curves[dataset_name] = (precision, recall, ap)
        ap_scores[dataset_name] = ap
        
        # Also save individual PR curve for each dataset
        individual_output = os.path.join(output_dir, f"pr_curve_{dataset_name}.png")
        plot_precision_recall_curve(
            precision=precision,
            recall=recall,
            output_path=individual_output,
            title=f"PR Curve - {dataset_name}",
            show_ap=True,
            ap_value=ap
        )
    
    # Save comparison figure
    comparison_output = os.path.join(output_dir, output_filename)
    plot_multiple_pr_curves(curves, comparison_output)
    
    return ap_scores


# ============================================================================
# Main execution for standalone testing and demonstration
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create output directory
    os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
    
    # Demo mode: Generate sample PR curve
    print("=" * 60)
    print("PR Curve Generation - Demonstration")
    print("=" * 60)
    
    # Generate synthetic data for demonstration
    np.random.seed(42)
    n_samples = 1000
    n_anomalies = 50  # 5% anomaly rate
    
    # Create ground truth: 1 = anomaly, 0 = normal
    y_true = np.zeros(n_samples, dtype=int)
    anomaly_indices = np.random.choice(n_samples, n_anomalies, replace=False)
    y_true[anomaly_indices] = 1
    
    # Create anomaly scores: higher for anomalies, lower for normal
    y_scores = np.random.uniform(0.2, 0.5, n_samples)  # Normal samples
    y_scores[anomaly_indices] = np.random.uniform(0.7, 1.0, n_anomalies)  # Anomalies
    
    # Generate PR curve
    output_path = os.path.join(DEFAULT_OUTPUT_DIR, "pr_curve_demo.png")
    ap = generate_pr_curve_from_scores(
        y_true=y_true,
        y_scores=y_scores,
        output_path=output_path,
        title="Precision-Recall Curve - Demo Dataset",
        show_ap=True
    )
    
    print(f"\nAverage Precision (AP): {ap:.4f}")
    print(f"PR curve saved to: {output_path}")
    print(f"Anomaly rate: {n_anomalies/n_samples*100:.1f}%")
    print("\n" + "=" * 60)
    print("PR curve generation complete!")
    print("=" * 60)
