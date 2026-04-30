"""
Unit tests for ROC and PR curve generation.

Tests the evaluation/plots.py module for:
- ROC curve generation
- Precision-Recall curve generation
- PNG export functionality
- Edge cases (perfect classifier, random classifier, etc.)

Per plan.md requirements: Write tests FIRST, verify they fail before implementation.
"""

import os
import tempfile
from pathlib import Path

import numpy as np
import pytest
from sklearn.metrics import roc_curve, precision_recall_curve, auc

# Import the plots module under test
# This will fail until code/evaluation/plots.py is implemented (T052, T053)
from code.evaluation.plots import (
    generate_roc_curve,
    generate_pr_curve,
    save_roc_curve_to_png,
    save_pr_curve_to_png,
)


class TestROCCurveGeneration:
    """Unit tests for ROC curve generation functionality."""

    def test_roc_curve_basic(self):
        """Test basic ROC curve generation with known data."""
        # Ground truth and predictions
        y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])
        y_scores = np.array([0.1, 0.4, 0.35, 0.8, 0.9, 0.2, 0.7, 0.15, 0.95, 0.85])

        fpr, tpr, thresholds = generate_roc_curve(y_true, y_scores)

        # Verify outputs are numpy arrays
        assert isinstance(fpr, np.ndarray)
        assert isinstance(tpr, np.ndarray)
        assert isinstance(thresholds, np.ndarray)

        # Verify FPR is monotonically increasing
        assert np.all(np.diff(fpr) >= 0)

        # Verify TPR is monotonically increasing
        assert np.all(np.diff(tpr) >= 0)

        # Verify first point is (0, 0)
        assert fpr[0] == 0.0
        assert tpr[0] == 0.0

    def test_roc_curve_perfect_classifier(self):
        """Test ROC curve with perfect classifier."""
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_scores = np.array([0.1, 0.2, 0.3, 0.8, 0.9, 1.0])

        fpr, tpr, thresholds = generate_roc_curve(y_true, y_scores)

        # Perfect classifier should have AUC = 1.0
        roc_auc = auc(fpr, tpr)
        assert np.isclose(roc_auc, 1.0, atol=1e-6)

    def test_roc_curve_random_classifier(self):
        """Test ROC curve with random classifier (diagonal)."""
        np.random.seed(42)
        y_true = np.random.randint(0, 2, 100)
        y_scores = np.random.random(100)

        fpr, tpr, thresholds = generate_roc_curve(y_true, y_scores)

        # Random classifier should have AUC around 0.5
        roc_auc = auc(fpr, tpr)
        assert 0.4 < roc_auc < 0.6, f"Expected AUC around 0.5, got {roc_auc}"

    def test_roc_curve_empty_input(self):
        """Test ROC curve with empty arrays."""
        with pytest.raises((ValueError, IndexError)):
            generate_roc_curve(np.array([]), np.array([]))

    def test_roc_curve_single_class(self):
        """Test ROC curve with only one class present."""
        y_true = np.array([1, 1, 1, 1, 1])
        y_scores = np.array([0.1, 0.2, 0.3, 0.4, 0.5])

        # Should raise an error when only one class is present
        with pytest.raises(ValueError):
            generate_roc_curve(y_true, y_scores)

    def test_roc_curve_mismatched_lengths(self):
        """Test ROC curve with mismatched array lengths."""
        y_true = np.array([0, 1, 1, 0, 1])
        y_scores = np.array([0.1, 0.5, 0.9])

        with pytest.raises(ValueError):
            generate_roc_curve(y_true, y_scores)


class TestPRCurveGeneration:
    """Unit tests for Precision-Recall curve generation functionality."""

    def test_pr_curve_basic(self):
        """Test basic PR curve generation with known data."""
        y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])
        y_scores = np.array([0.1, 0.4, 0.35, 0.8, 0.9, 0.2, 0.7, 0.15, 0.95, 0.85])

        precision, recall, thresholds = generate_pr_curve(y_true, y_scores)

        # Verify outputs are numpy arrays
        assert isinstance(precision, np.ndarray)
        assert isinstance(recall, np.ndarray)
        assert isinstance(thresholds, np.ndarray)

        # Verify recall is monotonically decreasing
        assert np.all(np.diff(recall) <= 0)

        # Verify precision values are in [0, 1]
        assert np.all(precision >= 0) and np.all(precision <= 1)

    def test_pr_curve_imbalanced_data(self):
        """Test PR curve with highly imbalanced data."""
        # 95% negative, 5% positive
        y_true = np.array([0] * 95 + [1] * 5)
        y_scores = np.random.random(100)

        precision, recall, thresholds = generate_pr_curve(y_true, y_scores)

        # Should handle imbalanced data without error
        assert len(precision) > 0
        assert len(recall) > 0

    def test_pr_curve_perfect_classifier(self):
        """Test PR curve with perfect classifier."""
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_scores = np.array([0.1, 0.2, 0.3, 0.8, 0.9, 1.0])

        precision, recall, thresholds = generate_pr_curve(y_true, y_scores)

        # Perfect classifier should have high average precision
        from sklearn.metrics import average_precision_score
        ap = average_precision_score(y_true, y_scores)
        assert np.isclose(ap, 1.0, atol=1e-6)

    def test_pr_curve_empty_input(self):
        """Test PR curve with empty arrays."""
        with pytest.raises((ValueError, IndexError)):
            generate_pr_curve(np.array([]), np.array([]))

    def test_pr_curve_single_class(self):
        """Test PR curve with only one class present."""
        y_true = np.array([1, 1, 1, 1, 1])
        y_scores = np.array([0.1, 0.2, 0.3, 0.4, 0.5])

        with pytest.raises(ValueError):
            generate_pr_curve(y_true, y_scores)


class TestPNGExport:
    """Unit tests for PNG export functionality."""

    def test_save_roc_curve_to_png(self):
        """Test ROC curve PNG export to temporary file."""
        y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])
        y_scores = np.array([0.1, 0.4, 0.35, 0.8, 0.9, 0.2, 0.7, 0.15, 0.95, 0.85])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "roc_curve.png")
            save_roc_curve_to_png(y_true, y_scores, output_path)

            # Verify file was created
            assert os.path.exists(output_path)
            assert output_path.endswith(".png")
            assert os.path.getsize(output_path) > 0

    def test_save_pr_curve_to_png(self):
        """Test PR curve PNG export to temporary file."""
        y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])
        y_scores = np.array([0.1, 0.4, 0.35, 0.8, 0.9, 0.2, 0.7, 0.15, 0.95, 0.85])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "pr_curve.png")
            save_pr_curve_to_png(y_true, y_scores, output_path)

            # Verify file was created
            assert os.path.exists(output_path)
            assert output_path.endswith(".png")
            assert os.path.getsize(output_path) > 0

    def test_save_curve_to_nonexistent_directory(self):
        """Test PNG export to non-existent directory fails gracefully."""
        y_true = np.array([0, 1, 1, 0, 1])
        y_scores = np.array([0.1, 0.5, 0.9, 0.2, 0.7])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "nonexistent", "curve.png")
            with pytest.raises((FileNotFoundError, OSError)):
                save_roc_curve_to_png(y_true, y_scores, output_path)

    def test_save_curve_with_custom_title(self):
        """Test PNG export with custom title."""
        y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])
        y_scores = np.array([0.1, 0.4, 0.35, 0.8, 0.9, 0.2, 0.7, 0.15, 0.95, 0.85])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "custom_title.png")
            save_roc_curve_to_png(
                y_true, y_scores, output_path, title="Custom ROC Curve"
            )

            assert os.path.exists(output_path)


class TestEdgeCases:
    """Unit tests for edge cases in curve generation."""

    def test_roc_curve_with_ties(self):
        """Test ROC curve with tied scores."""
        y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])
        y_scores = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])

        # Should handle tied scores without error
        fpr, tpr, thresholds = generate_roc_curve(y_true, y_scores)
        assert len(fpr) > 0
        assert len(tpr) > 0

    def test_pr_curve_with_ties(self):
        """Test PR curve with tied scores."""
        y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])
        y_scores = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])

        # Should handle tied scores without error
        precision, recall, thresholds = generate_pr_curve(y_true, y_scores)
        assert len(precision) > 0
        assert len(recall) > 0

    def test_roc_curve_large_dataset(self):
        """Test ROC curve with larger dataset."""
        np.random.seed(42)
        n_samples = 10000
        y_true = np.random.randint(0, 2, n_samples)
        y_scores = np.random.random(n_samples)

        fpr, tpr, thresholds = generate_roc_curve(y_true, y_scores)

        # Should complete without error
        assert len(fpr) > 0
        assert len(tpr) > 0
        assert len(thresholds) > 0

    def test_pr_curve_small_dataset(self):
        """Test PR curve with very small dataset."""
        y_true = np.array([0, 1])
        y_scores = np.array([0.2, 0.8])

        precision, recall, thresholds = generate_pr_curve(y_true, y_scores)

        # Should handle minimal data
        assert len(precision) > 0
        assert len(recall) > 0


class TestIntegrationWithMetrics:
    """Integration tests with sklearn metrics for validation."""

    def test_roc_curve_matches_sklearn(self):
        """Verify our ROC curve matches sklearn implementation."""
        np.random.seed(42)
        y_true = np.random.randint(0, 2, 1000)
        y_scores = np.random.random(1000)

        fpr, tpr, thresholds = generate_roc_curve(y_true, y_scores)
        fpr_sklearn, tpr_sklearn, thresholds_sklearn = roc_curve(y_true, y_scores)

        # Should match sklearn implementation
        assert np.allclose(fpr, fpr_sklearn, rtol=1e-5)
        assert np.allclose(tpr, tpr_sklearn, rtol=1e-5)

    def test_pr_curve_matches_sklearn(self):
        """Verify our PR curve matches sklearn implementation."""
        np.random.seed(42)
        y_true = np.random.randint(0, 2, 1000)
        y_scores = np.random.random(1000)

        precision, recall, thresholds = generate_pr_curve(y_true, y_scores)
        precision_sklearn, recall_sklearn, thresholds_sklearn = precision_recall_curve(
            y_true, y_scores
        )

        # Should match sklearn implementation
        assert np.allclose(precision, precision_sklearn, rtol=1e-5)
        assert np.allclose(recall, recall_sklearn, rtol=1e-5)
