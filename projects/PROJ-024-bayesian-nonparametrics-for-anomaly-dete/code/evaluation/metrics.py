"""
Evaluation metrics module for Bayesian Nonparametrics Anomaly Detection.

This module provides:
- Precision, recall, F1-score, AUC calculations
- Confusion matrix generation
- Statistical significance testing with Bonferroni correction

Per Constitution Principle: Reproducibility (PR-001)
All random operations use seeded RNG from config.yaml
"""

import numpy as np
import scipy.stats as stats
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
import logging

from code.utils.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# Basic Metrics (existing implementation)
# ============================================================================

def precision(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate precision score."""
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    if tp + fp == 0:
        return 0.0
    return tp / (tp + fp)

def recall(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate recall score."""
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    if tp + fn == 0:
        return 0.0
    return tp / (tp + fn)

def f1_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate F1-score (harmonic mean of precision and recall)."""
    prec = precision(y_true, y_pred)
    rec = recall(y_true, y_pred)
    if prec + rec == 0:
        return 0.0
    return 2 * (prec * rec) / (prec + rec)

def auc_roc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """Calculate Area Under ROC Curve."""
    return stats.roc_auc_score(y_true, y_scores)

def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, int]:
    """Generate confusion matrix as dictionary."""
    return {
        'tp': int(np.sum((y_true == 1) & (y_pred == 1))),
        'tn': int(np.sum((y_true == 0) & (y_pred == 0))),
        'fp': int(np.sum((y_true == 0) & (y_pred == 1))),
        'fn': int(np.sum((y_true == 1) & (y_pred == 0))),
    }

# ============================================================================
# Statistical Significance Testing (T054 Implementation)
# ============================================================================

@dataclass
class StatisticalTestResult:
    """Container for statistical test results."""
    test_name: str
    statistic: float
    p_value: float
    corrected_p_value: float
    significant: bool
    alpha_level: float
    correction_method: str
    n_comparisons: int

@dataclass
class PairedComparison:
    """Container for paired model comparison data."""
    model_a_name: str
    model_b_name: str
    metric_name: str
    scores_a: np.ndarray  # Per-dataset scores for model A
    scores_b: np.ndarray  # Per-dataset scores for model B
    n_datasets: int

def paired_ttest(
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    alternative: str = 'two-sided'
) -> Tuple[float, float]:
    """
    Perform paired t-test between two sets of scores.
    
    This tests whether the mean difference between paired observations
    is significantly different from zero.
    
    Args:
        scores_a: Scores from model A (one score per dataset)
        scores_b: Scores from model B (one score per dataset)
        alternative: 'two-sided', 'less', or 'greater'
    
    Returns:
        Tuple of (t-statistic, p-value)
    
    Raises:
        ValueError: If arrays have different lengths or length < 2
        ValueError: If all differences are zero (perfect correlation)
    """
    scores_a = np.asarray(scores_a)
    scores_b = np.asarray(scores_b)
    
    if scores_a.shape != scores_b.shape:
        raise ValueError(
            f"Score arrays must have same shape: "
            f"{scores_a.shape} vs {scores_b.shape}"
        )
    
    n = len(scores_a)
    if n < 2:
        raise ValueError(
            f"Paired t-test requires at least 2 observations, got {n}"
        )
    
    # Calculate differences
    differences = scores_a - scores_b
    
    # Check for zero variance in differences
    if np.std(differences) == 0:
        # Perfect correlation - no significant difference
        return 0.0, 1.0
    
    # Perform paired t-test
    t_stat, p_val = stats.ttest_rel(
        scores_a, 
        scores_b, 
        alternative=alternative
    )
    
    return float(t_stat), float(p_val)

def bonferroni_correction(
    p_values: np.ndarray,
    alpha: float = 0.05
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    The Bonferroni correction multiplies each p-value by the number
    of comparisons and caps at 1.0. This is a conservative method
    that controls family-wise error rate (FWER).
    
    Args:
        p_values: Array of raw p-values from statistical tests
        alpha: Significance threshold (default 0.05)
    
    Returns:
        Tuple of (corrected_p_values, significant_flags)
        where significant_flags is boolean array
    """
    p_values = np.asarray(p_values)
    n_comparisons = len(p_values)
    
    if n_comparisons == 0:
        return np.array([]), np.array([], dtype=bool)
    
    # Bonferroni: multiply by n_comparisons, cap at 1.0
    corrected = np.minimum(p_values * n_comparisons, 1.0)
    
    # Determine significance
    significant = corrected < alpha
    
    return corrected, significant

def holm_bonferroni_correction(
    p_values: np.ndarray,
    alpha: float = 0.05
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Holm-Bonferroni correction (step-down method).
    
    This is less conservative than standard Bonferroni while
    still controlling FWER. It sorts p-values and applies
    progressively less stringent corrections.
    
    Args:
        p_values: Array of raw p-values
        alpha: Significance threshold
    
    Returns:
        Tuple of (corrected_p_values, significant_flags)
    """
    p_values = np.asarray(p_values)
    n = len(p_values)
    
    if n == 0:
        return np.array([]), np.array([], dtype=bool)
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate step-down corrected p-values
    corrected = np.zeros(n)
    for i in range(n):
        # Max of previous corrected and current adjusted
        adjusted = sorted_p[i] * (n - i)
        if i > 0:
            corrected[i] = max(corrected[i-1], adjusted)
        else:
            corrected[i] = adjusted
    
    # Cap at 1.0
    corrected = np.minimum(corrected, 1.0)
    
    # Restore original order
    corrected_restored = np.zeros(n)
    corrected_restored[sorted_indices] = corrected
    
    # Determine significance
    significant = corrected_restored < alpha
    
    return corrected_restored, significant

def compare_models_paired_ttest(
    comparison: PairedComparison,
    alpha: float = 0.05,
    correction_method: str = 'bonferroni'
) -> StatisticalTestResult:
    """
    Compare two models using paired t-test with multiple comparison correction.
    
    This function performs a paired t-test on per-dataset scores and applies
    the specified correction method for multiple comparisons.
    
    Args:
        comparison: PairedComparison object with model scores
        alpha: Significance threshold
        correction_method: 'bonferroni' or 'holm'
    
    Returns:
        StatisticalTestResult with test statistics and significance
    """
    if len(comparison.scores_a) != len(comparison.scores_b):
        raise ValueError(
            f"Score arrays must have same length: "
            f"{len(comparison.scores_a)} vs {len(comparison.scores_b)}"
        )
    
    # Perform paired t-test
    t_stat, p_val = paired_ttest(
        comparison.scores_a,
        comparison.scores_b,
        alternative='two-sided'
    )
    
    # Apply correction (single comparison, but include for consistency)
    if correction_method == 'bonferroni':
        corrected_p, significant = bonferroni_correction(
            np.array([p_val]), alpha
        )
    elif correction_method == 'holm':
        corrected_p, significant = holm_bonferroni_correction(
            np.array([p_val]), alpha
        )
    else:
        raise ValueError(f"Unknown correction method: {correction_method}")
    
    logger.debug(
        f"Paired t-test: {comparison.model_a_name} vs {comparison.model_b_name} "
        f"on {comparison.metric_name} - t={t_stat:.4f}, p={p_val:.4f}, "
        f"corrected_p={corrected_p[0]:.4f}, significant={significant[0]}"
    )
    
    return StatisticalTestResult(
        test_name=f"paired_ttest_{comparison.metric_name}",
        statistic=t_stat,
        p_value=p_val,
        corrected_p_value=corrected_p[0],
        significant=significant[0],
        alpha_level=alpha,
        correction_method=correction_method,
        n_comparisons=1
    )

def compare_multiple_models(
    model_scores: Dict[str, Dict[str, np.ndarray]],
    reference_model: str,
    alpha: float = 0.05,
    correction_method: str = 'bonferroni'
) -> List[StatisticalTestResult]:
    """
    Compare multiple models against a reference model with Bonferroni correction.
    
    This is useful for comparing DPGMM against multiple baselines across datasets.
    
    Args:
        model_scores: Dict mapping model_name -> {dataset_name -> scores}
        reference_model: Name of model to compare others against
        alpha: Significance threshold
        correction_method: 'bonferroni' or 'holm'
    
    Returns:
        List of StatisticalTestResult for each comparison
    
    Example:
        model_scores = {
            'dpgmm': {'dataset1': [0.85, 0.90, ...], 'dataset2': [...]},
            'arima': {'dataset1': [0.80, 0.85, ...], 'dataset2': [...]},
            'moving_avg': {'dataset1': [0.75, 0.78, ...], 'dataset2': [...]}
        }
        results = compare_multiple_models(model_scores, 'dpgmm')
    """
    if reference_model not in model_scores:
        raise ValueError(f"Reference model '{reference_model}' not in model_scores")
    
    reference_scores = model_scores[reference_model]
    results = []
    
    for model_name, scores_dict in model_scores.items():
        if model_name == reference_model:
            continue
        
        # Calculate mean score per model across datasets
        ref_mean = np.mean(list(reference_scores.values()))
        model_mean = np.mean(list(scores_dict.values()))
        
        # For proper paired test, we need per-dataset scores
        # Create paired arrays
        dataset_names = list(reference_scores.keys())
        ref_array = np.array([reference_scores[d] for d in dataset_names])
        model_array = np.array([scores_dict[d] for d in dataset_names])
        
        comparison = PairedComparison(
            model_a_name=model_name,
            model_b_name=reference_model,
            metric_name='mean_f1',
            scores_a=ref_array,
            scores_b=model_array,
            n_datasets=len(dataset_names)
        )
        
        result = compare_models_paired_ttest(
            comparison, alpha, correction_method
        )
        results.append(result)
    
    # Apply global Bonferroni correction across all comparisons
    if len(results) > 1:
        all_p_values = np.array([r.p_value for r in results])
        if correction_method == 'bonferroni':
            corrected, _ = bonferroni_correction(all_p_values, alpha)
        else:
            corrected, _ = holm_bonferroni_correction(all_p_values, alpha)
        
        for i, result in enumerate(results):
            result.corrected_p_value = corrected[i]
            result.significant = corrected[i] < alpha
            result.n_comparisons = len(results)
    
    return results

def summary_statistics(
    scores: np.ndarray,
    label: str = "scores"
) -> Dict[str, float]:
    """
    Calculate summary statistics for a set of scores.
    
    Args:
        scores: Array of scores
        label: Label for the scores (for logging)
    
    Returns:
        Dictionary with mean, std, min, max, median, n
    """
    scores = np.asarray(scores)
    return {
        'label': label,
        'n': int(len(scores)),
        'mean': float(np.mean(scores)),
        'std': float(np.std(scores)),
        'min': float(np.min(scores)),
        'max': float(np.max(scores)),
        'median': float(np.median(scores)),
        'q25': float(np.percentile(scores, 25)),
        'q75': float(np.percentile(scores, 75)),
    }

# ============================================================================
# Utility Functions for Reporting
# ============================================================================

def format_test_result(result: StatisticalTestResult) -> str:
    """Format a statistical test result for logging/reporting."""
    sig_marker = "***" if result.significant else "ns"
    return (
        f"{result.test_name}: "
        f"t={result.statistic:.4f}, "
        f"p={result.p_value:.4f}, "
        f"p_corr={result.corrected_p_value:.4f} {sig_marker} "
        f"({result.correction_method}, n={result.n_comparisons})"
    )

def format_comparison_summary(
    results: List[StatisticalTestResult],
    reference_model: str
) -> str:
    """Format a summary of multiple comparison results."""
    lines = [
        f"Statistical Comparison Summary (Reference: {reference_model})",
        f"Significance level: {results[0].alpha_level if results else 0.05}",
        f"Correction method: {results[0].correction_method if results else 'N/A'}",
        "-" * 60,
    ]
    
    for result in results:
        sig_marker = "***" if result.significant else "ns"
        lines.append(
            f"  {sig_marker} {result.test_name}: "
            f"p_corr={result.corrected_p_value:.4f}"
        )
    
    lines.append("-" * 60)
    significant_count = sum(1 for r in results if r.significant)
    lines.append(
        f"Significant differences: {significant_count}/{len(results)}"
    )
    
    return "\n".join(lines)

# ============================================================================
# Exported API
# ============================================================================

__all__ = [
    # Basic metrics
    'precision',
    'recall',
    'f1_score',
    'auc_roc',
    'confusion_matrix',
    # Statistical testing (T054)
    'StatisticalTestResult',
    'PairedComparison',
    'paired_ttest',
    'bonferroni_correction',
    'holm_bonferroni_correction',
    'compare_models_paired_ttest',
    'compare_multiple_models',
    'summary_statistics',
    # Reporting utilities
    'format_test_result',
    'format_comparison_summary',
]
