"""
Evaluation Module for Bayesian Nonparametric Anomaly Detection

This package provides evaluation metrics and utilities for comparing
the DPGMM-based anomaly detector against baseline methods.

Exports:
- Metrics computation functions (precision, recall, F1, AUC)
- Statistical comparison utilities
- Validation against success criteria
"""

from .metrics import (
    compute_confusion_matrix,
    compute_precision,
    compute_recall,
    compute_f1_score,
    compute_auc_roc,
    compute_auc_pr,
    compute_metrics_all,
    paired_ttest_with_correction,
    validate_metrics_against_thresholds,
)

__all__ = [
    "compute_confusion_matrix",
    "compute_precision",
    "compute_recall",
    "compute_f1_score",
    "compute_auc_roc",
    "compute_auc_pr",
    "compute_metrics_all",
    "paired_ttest_with_correction",
    "validate_metrics_against_thresholds",
]
