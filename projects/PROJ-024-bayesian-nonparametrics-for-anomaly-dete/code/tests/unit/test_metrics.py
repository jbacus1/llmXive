"""Unit tests for F1-score calculation in evaluation metrics.

Tests verify correct F1-score computation across standard cases,
edge cases (zero precision, zero recall, perfect prediction), and
array-based inputs. These tests should FAIL before T050 implementation
and PASS after code/evaluation/metrics.py is implemented.
"""

import pytest
import numpy as np

# Import the metrics module that will be implemented in T050
# This import will fail initially (expected - tests fail before impl)
try:
    from code.evaluation.metrics import (
        calculate_f1_score,
        calculate_precision,
        calculate_recall,
        calculate_confusion_matrix
    )
    MODULE_AVAILABLE = True
except ImportError:
    MODULE_AVAILABLE = False


@pytest.mark.skipif(not MODULE_AVAILABLE, reason="T050 metrics module not yet implemented")
class TestF1ScoreCalculation:
    """Test F1-score calculation functionality."""

    def test_f1_score_basic_case(self):
        """Test F1-score with standard values.

        Given: TP=80, FP=20, FN=10
        Expected: precision=0.8, recall=0.889, F1=0.842
        """
        tp, fp, fn = 80, 20, 10
        expected_precision = tp / (tp + fp)  # 0.8
        expected_recall = tp / (tp + fn)  # 0.889
        expected_f1 = 2 * (expected_precision * expected_recall) / (
            expected_precision + expected_recall
        )  # 0.842105

        result = calculate_f1_score(tp, fp, fn)
        assert np.isclose(result, expected_f1, rtol=1e-4)

    def test_f1_score_perfect_prediction(self):
        """Test F1-score when prediction is perfect (no false positives/negatives)."""
        tp, fp, fn = 100, 0, 0
        expected_f1 = 1.0

        result = calculate_f1_score(tp, fp, fn)
        assert np.isclose(result, expected_f1, rtol=1e-4)

    def test_f1_score_zero_precision(self):
        """Test F1-score when precision is zero (all predictions are false positives)."""
        tp, fp, fn = 0, 10, 5
        expected_f1 = 0.0

        result = calculate_f1_score(tp, fp, fn)
        assert np.isclose(result, expected_f1, rtol=1e-4)

    def test_f1_score_zero_recall(self):
        """Test F1-score when recall is zero (no true positives detected)."""
        tp, fp, fn = 0, 5, 10
        expected_f1 = 0.0

        result = calculate_f1_score(tp, fp, fn)
        assert np.isclose(result, expected_f1, rtol=1e-4)

    def test_f1_score_no_predictions(self):
        """Test F1-score when there are no predictions at all (all zeros)."""
        tp, fp, fn = 0, 0, 0
        # When all are zero, F1 should be 0.0 (not NaN)
        result = calculate_f1_score(tp, fp, fn)
        assert result == 0.0

    def test_f1_score_large_values(self):
        """Test F1-score with large observation counts."""
        tp, fp, fn = 10000, 2000, 1000
        expected_precision = tp / (tp + fp)
        expected_recall = tp / (tp + fn)
        expected_f1 = 2 * (expected_precision * expected_recall) / (
            expected_precision + expected_recall
        )

        result = calculate_f1_score(tp, fp, fn)
        assert np.isclose(result, expected_f1, rtol=1e-4)

    def test_f1_score_array_input(self):
        """Test F1-score with numpy array inputs (batch evaluation)."""
        tp = np.array([80, 90, 70])
        fp = np.array([20, 10, 30])
        fn = np.array([10, 5, 15])

        result = calculate_f1_score(tp, fp, fn)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert all(r >= 0.0 for r in result)
        assert all(r <= 1.0 for r in result)

    def test_precision_calculation(self):
        """Test precision calculation independently."""
        tp, fp = 80, 20
        expected_precision = tp / (tp + fp)  # 0.8

        result = calculate_precision(tp, fp)
        assert np.isclose(result, expected_precision, rtol=1e-4)

    def test_recall_calculation(self):
        """Test recall calculation independently."""
        tp, fn = 80, 10
        expected_recall = tp / (tp + fn)  # 0.889

        result = calculate_recall(tp, fn)
        assert np.isclose(result, expected_recall, rtol=1e-4)

    def test_confusion_matrix_from_arrays(self):
        """Test confusion matrix generation from true and predicted arrays."""
        y_true = np.array([1, 1, 0, 0, 1, 0, 1, 1])
        y_pred = np.array([1, 0, 0, 1, 1, 0, 1, 0])

        tp, fp, tn, fn = calculate_confusion_matrix(y_true, y_pred)

        # Manual calculation:
        # TP: indices where both are 1 -> [0, 4, 6] = 3
        # FP: where true=0, pred=1 -> [3, 7] = 2
        # TN: where both are 0 -> [2, 5] = 2
        # FN: where true=1, pred=0 -> [1] = 1
        assert tp == 3
        assert fp == 2
        assert tn == 2
        assert fn == 1

    def test_f1_score_binary_classification_scenario(self):
        """Test F1-score in a realistic binary classification scenario."""
        # Simulating anomaly detection: 100 samples, 10 actual anomalies
        # Model detects 8 correctly, 5 false alarms
        tp = 8  # True positives (anomalies correctly detected)
        fp = 5  # False positives (normal flagged as anomaly)
        fn = 2  # False negatives (anomalies missed)

        precision = tp / (tp + fp)  # 8/13 = 0.615
        recall = tp / (tp + fn)  # 8/10 = 0.8
        expected_f1 = 2 * (precision * recall) / (precision + recall)  # 0.696

        result = calculate_f1_score(tp, fp, fn)
        assert np.isclose(result, expected_f1, rtol=1e-4)

    def test_f1_score_symmetry(self):
        """Test that swapping precision and recall components maintains F1."""
        # Case 1: High precision, low recall
        tp1, fp1, fn1 = 90, 10, 90
        f1_case1 = calculate_f1_score(tp1, fp1, fn1)

        # Case 2: Low precision, high recall (swapped fp/fn)
        tp2, fp2, fn2 = 90, 90, 10
        f1_case2 = calculate_f1_score(tp2, fp2, fn2)

        # F1 should be the same (harmonic mean is symmetric)
        assert np.isclose(f1_case1, f1_case2, rtol=1e-4)

    def test_f1_score_monotonicity(self):
        """Test that F1 increases when TP increases (holding others constant)."""
        tp1, fp, fn = 50, 20, 10
        tp2, fp, fn = 60, 20, 10

        f1_1 = calculate_f1_score(tp1, fp, fn)
        f1_2 = calculate_f1_score(tp2, fp, fn)

        assert f1_2 > f1_1