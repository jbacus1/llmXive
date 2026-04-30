"""
Contract tests for evaluation metrics output schema.

These tests validate that the evaluation metrics module produces
outputs matching the expected schema defined in spec.md.

Tests are REQUIRED per spec.md Independent Test scenarios for US2.
"""

import pytest
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import asdict, is_dataclass

# Import from existing API surface - MUST match code/evaluation/metrics.py
from code.evaluation.metrics import (
    EvaluationMetrics,
    compute_f1_score,
    compute_precision,
    compute_recall,
    compute_auc,
    generate_confusion_matrix,
    save_confusion_matrix_plot,
    compute_all_metrics,
    main,
)

# Import from plots API surface
from code.evaluation.plots import (
    ROCPlotConfig,
    PRPlotConfig,
    EvaluationPlotConfig,
    generate_roc_curve,
    save_roc_curve,
    generate_pr_curve,
    save_pr_curve,
    generate_evaluation_plots,
)

# Import from statistical tests API surface
from code.evaluation.statistical_tests import (
    StatisticalTestResult,
    ComparisonSummary,
    paired_ttest_with_bonferroni,
    apply_bonferroni_correction,
    compare_all_models,
    format_comparison_summary,
    save_comparison_results,
)


# ============================================================================
# Fixtures for test data
# ============================================================================

@pytest.fixture
def sample_predictions() -> Tuple[np.ndarray, np.ndarray]:
    """Sample ground truth and predictions for testing."""
    y_true = np.array([0, 1, 0, 1, 1, 0, 1, 0, 1, 1])
    y_pred = np.array([0, 1, 0, 0, 1, 1, 1, 0, 1, 0])
    return y_true, y_pred

@pytest.fixture
def sample_scores() -> Tuple[np.ndarray, np.ndarray]:
    """Sample ground truth and anomaly scores for AUC testing."""
    y_true = np.array([0, 1, 0, 1, 1, 0, 1, 0, 1, 1])
    scores = np.array([0.1, 0.9, 0.2, 0.8, 0.7, 0.3, 0.6, 0.25, 0.75, 0.85])
    return y_true, scores

@pytest.fixture
def sample_metrics() -> EvaluationMetrics:
    """Sample EvaluationMetrics object for schema testing."""
    return EvaluationMetrics(
        f1_score=0.85,
        precision=0.80,
        recall=0.90,
        auc=0.92,
        tp=8,
        fp=2,
        tn=7,
        fn=3,
        total_samples=20,
        anomaly_rate=0.55,
        dataset_name="test_dataset",
        timestamp="2024-01-15T10:30:00Z",
        model_name="DPGMM",
    )

@pytest.fixture
def sample_confusion_matrix() -> np.ndarray:
    """Sample 2x2 confusion matrix."""
    return np.array([[7, 2], [3, 8]])

# ============================================================================
# EvaluationMetrics Dataclass Schema Tests
# ============================================================================

class TestEvaluationMetricsSchema:
    """Test that EvaluationMetrics dataclass has expected schema."""

    def test_evaluation_metrics_is_dataclass(self, sample_metrics):
        """Verify EvaluationMetrics is a dataclass."""
        assert is_dataclass(EvaluationMetrics), \
            "EvaluationMetrics must be a dataclass for schema validation"

    def test_evaluation_metrics_required_fields(self, sample_metrics):
        """Verify EvaluationMetrics has all required fields per spec.md."""
        required_fields = [
            'f1_score', 'precision', 'recall', 'auc',
            'tp', 'fp', 'tn', 'fn',
            'total_samples', 'anomaly_rate',
            'dataset_name', 'timestamp', 'model_name'
        ]
        metrics_dict = asdict(sample_metrics)
        for field in required_fields:
            assert field in metrics_dict, \
                f"EvaluationMetrics missing required field: {field}"

    def test_evaluation_metrics_numeric_fields_type(self, sample_metrics):
        """Verify numeric fields are float or int."""
        numeric_fields = ['f1_score', 'precision', 'recall', 'auc',
                         'tp', 'fp', 'tn', 'fn', 'total_samples']
        metrics_dict = asdict(sample_metrics)
        for field in numeric_fields:
            value = metrics_dict[field]
            assert isinstance(value, (int, float, np.integer, np.floating)), \
                f"Field {field} must be numeric, got {type(value)}"

    def test_evaluation_metrics_string_fields_type(self, sample_metrics):
        """Verify string fields are strings."""
        string_fields = ['dataset_name', 'timestamp', 'model_name']
        metrics_dict = asdict(sample_metrics)
        for field in string_fields:
            value = metrics_dict[field]
            assert isinstance(value, str), \
                f"Field {field} must be string, got {type(value)}"

    def test_evaluation_metrics_f1_range(self, sample_metrics):
        """Verify f1_score is in valid range [0, 1]."""
        assert 0 <= sample_metrics.f1_score <= 1, \
            f"f1_score must be in [0, 1], got {sample_metrics.f1_score}"

    def test_evaluation_metrics_precision_range(self, sample_metrics):
        """Verify precision is in valid range [0, 1]."""
        assert 0 <= sample_metrics.precision <= 1, \
            f"precision must be in [0, 1], got {sample_metrics.precision}"

    def test_evaluation_metrics_recall_range(self, sample_metrics):
        """Verify recall is in valid range [0, 1]."""
        assert 0 <= sample_metrics.recall <= 1, \
            f"recall must be in [0, 1], got {sample_metrics.recall}"

    def test_evaluation_metrics_auc_range(self, sample_metrics):
        """Verify AUC is in valid range [0, 1]."""
        assert 0 <= sample_metrics.auc <= 1, \
            f"AUC must be in [0, 1], got {sample_metrics.auc}"

    def test_evaluation_metrics_confusion_matrix_sum(self, sample_metrics):
        """Verify confusion matrix components sum to total_samples."""
        expected_total = sample_metrics.tp + sample_metrics.fp + \
                        sample_metrics.tn + sample_metrics.fn
        assert expected_total == sample_metrics.total_samples, \
            f"Confusion matrix sum {expected_total} != total_samples {sample_metrics.total_samples}"

    def test_evaluation_metrics_anomaly_rate_calculation(self, sample_metrics):
        """Verify anomaly_rate matches (tp + fn) / total."""
        expected_rate = (sample_metrics.tp + sample_metrics.fn) / sample_metrics.total_samples
        assert abs(sample_metrics.anomaly_rate - expected_rate) < 1e-6, \
            f"anomaly_rate {sample_metrics.anomaly_rate} != calculated {expected_rate}"

# ============================================================================
# Metric Computation Function Tests
# ============================================================================

class TestMetricComputationFunctions:
    """Test that metric computation functions return correct schema."""

    def test_compute_f1_score_returns_float(self, sample_predictions):
        """Verify compute_f1_score returns a float."""
        y_true, y_pred = sample_predictions
        result = compute_f1_score(y_true, y_pred)
        assert isinstance(result, (float, np.floating)), \
            f"compute_f1_score must return float, got {type(result)}"
        assert 0 <= result <= 1, \
            f"f1_score must be in [0, 1], got {result}"

    def test_compute_precision_returns_float(self, sample_predictions):
        """Verify compute_precision returns a float."""
        y_true, y_pred = sample_predictions
        result = compute_precision(y_true, y_pred)
        assert isinstance(result, (float, np.floating)), \
            f"compute_precision must return float, got {type(result)}"
        assert 0 <= result <= 1, \
            f"precision must be in [0, 1], got {result}"

    def test_compute_recall_returns_float(self, sample_predictions):
        """Verify compute_recall returns a float."""
        y_true, y_pred = sample_predictions
        result = compute_recall(y_true, y_pred)
        assert isinstance(result, (float, np.floating)), \
            f"compute_recall must return float, got {type(result)}"
        assert 0 <= result <= 1, \
            f"recall must be in [0, 1], got {result}"

    def test_compute_auc_returns_float(self, sample_scores):
        """Verify compute_auc returns a float."""
        y_true, scores = sample_scores
        result = compute_auc(y_true, scores)
        assert isinstance(result, (float, np.floating)), \
            f"compute_auc must return float, got {type(result)}"
        assert 0 <= result <= 1, \
            f"AUC must be in [0, 1], got {result}"

    def test_compute_all_metrics_returns_evaluation_metrics(self, sample_predictions, sample_scores):
        """Verify compute_all_metrics returns EvaluationMetrics dataclass."""
        y_true, y_pred = sample_predictions
        y_true_scores, scores = sample_scores
        result = compute_all_metrics(y_true, y_pred, scores)
        assert isinstance(result, EvaluationMetrics), \
            f"compute_all_metrics must return EvaluationMetrics, got {type(result)}"

    def test_compute_all_metrics_has_all_fields(self, sample_predictions, sample_scores):
        """Verify compute_all_metrics output has all required fields."""
        y_true, y_pred = sample_predictions
        y_true_scores, scores = sample_scores
        result = compute_all_metrics(y_true, y_pred, scores)
        required_fields = ['f1_score', 'precision', 'recall', 'auc',
                         'tp', 'fp', 'tn', 'fn', 'total_samples',
                         'anomaly_rate', 'dataset_name', 'timestamp', 'model_name']
        result_dict = asdict(result)
        for field in required_fields:
            assert field in result_dict, \
                f"compute_all_metrics missing field: {field}"

# ============================================================================
# Confusion Matrix Tests
# ============================================================================

class TestConfusionMatrix:
    """Test confusion matrix generation and schema."""

    def test_generate_confusion_matrix_returns_2x2_array(self, sample_predictions):
        """Verify generate_confusion_matrix returns 2x2 numpy array."""
        y_true, y_pred = sample_predictions
        result = generate_confusion_matrix(y_true, y_pred)
        assert isinstance(result, np.ndarray), \
            f"generate_confusion_matrix must return numpy array, got {type(result)}"
        assert result.shape == (2, 2), \
            f"Confusion matrix must be 2x2, got shape {result.shape}"

    def test_generate_confusion_matrix_values_non_negative(self, sample_predictions):
        """Verify confusion matrix values are non-negative."""
        y_true, y_pred = sample_predictions
        result = generate_confusion_matrix(y_true, y_pred)
        assert np.all(result >= 0), \
            "Confusion matrix values must be non-negative"

    def test_generate_confusion_matrix_sums_to_total(self, sample_predictions):
        """Verify confusion matrix sums equal total samples."""
        y_true, y_pred = sample_predictions
        result = generate_confusion_matrix(y_true, y_pred)
        total_samples = len(y_true)
        assert result.sum() == total_samples, \
            f"Confusion matrix sum {result.sum()} != total samples {total_samples}"

    def test_save_confusion_matrix_plot_creates_file(self, sample_predictions, tmp_path):
        """Verify save_confusion_matrix_plot creates output file."""
        y_true, y_pred = sample_predictions
        output_path = tmp_path / "confusion_matrix.png"
        result = save_confusion_matrix_plot(y_true, y_pred, output_path)
        assert output_path.exists(), \
            "save_confusion_matrix_plot must create output file"
        assert output_path.stat().st_size > 0, \
            "Output file must not be empty"

# ============================================================================
# ROC/PR Curve Tests
# ============================================================================

class TestROCPRCurves:
    """Test ROC and PR curve generation schema."""

    def test_generate_roc_curve_returns_tuple(self, sample_scores):
        """Verify generate_roc_curve returns (fpr, tpr, thresholds) tuple."""
        y_true, scores = sample_scores
        result = generate_roc_curve(y_true, scores)
        assert isinstance(result, tuple), \
            f"generate_roc_curve must return tuple, got {type(result)}"
        assert len(result) == 3, \
            f"generate_roc_curve must return 3 elements, got {len(result)}"
        fpr, tpr, thresholds = result
        assert isinstance(fpr, np.ndarray), "fpr must be numpy array"
        assert isinstance(tpr, np.ndarray), "tpr must be numpy array"
        assert isinstance(thresholds, np.ndarray), "thresholds must be numpy array"

    def test_generate_pr_curve_returns_tuple(self, sample_scores):
        """Verify generate_pr_curve returns (precision, recall, thresholds) tuple."""
        y_true, scores = sample_scores
        result = generate_pr_curve(y_true, scores)
        assert isinstance(result, tuple), \
            f"generate_pr_curve must return tuple, got {type(result)}"
        assert len(result) == 3, \
            f"generate_pr_curve must return 3 elements, got {len(result)}"
        precision, recall, thresholds = result
        assert isinstance(precision, np.ndarray), "precision must be numpy array"
        assert isinstance(recall, np.ndarray), "recall must be numpy array"
        assert isinstance(thresholds, np.ndarray), "thresholds must be numpy array"

    def test_save_roc_curve_creates_file(self, sample_scores, tmp_path):
        """Verify save_roc_curve creates output file."""
        y_true, scores = sample_scores
        output_path = tmp_path / "roc_curve.png"
        result = save_roc_curve(y_true, scores, output_path)
        assert output_path.exists(), \
            "save_roc_curve must create output file"
        assert output_path.stat().st_size > 0, \
            "Output file must not be empty"

    def test_save_pr_curve_creates_file(self, sample_scores, tmp_path):
        """Verify save_pr_curve creates output file."""
        y_true, scores = sample_scores
        output_path = tmp_path / "pr_curve.png"
        result = save_pr_curve(y_true, scores, output_path)
        assert output_path.exists(), \
            "save_pr_curve must create output file"
        assert output_path.stat().st_size > 0, \
            "Output file must not be empty"

# ============================================================================
# Statistical Tests Schema Tests
# ============================================================================

class TestStatisticalTestsSchema:
    """Test statistical test output schema."""

    def test_statistical_test_result_is_dataclass(self):
        """Verify StatisticalTestResult is a dataclass."""
        assert is_dataclass(StatisticalTestResult), \
            "StatisticalTestResult must be a dataclass"

    def test_statistical_test_result_required_fields(self):
        """Verify StatisticalTestResult has required fields."""
        required_fields = ['test_name', 'statistic', 'p_value',
                         'significant', 'correction_applied']
        # Create a sample instance to check fields
        sample = StatisticalTestResult(
            test_name="t-test",
            statistic=2.5,
            p_value=0.03,
            significant=True,
            correction_applied="bonferroni"
        )
        result_dict = asdict(sample)
        for field in required_fields:
            assert field in result_dict, \
                f"StatisticalTestResult missing field: {field}"

    def test_comparison_summary_is_dataclass(self):
        """Verify ComparisonSummary is a dataclass."""
        assert is_dataclass(ComparisonSummary), \
            "ComparisonSummary must be a dataclass"

    def test_comparison_summary_required_fields(self):
        """Verify ComparisonSummary has required fields."""
        required_fields = ['models_compared', 'datasets_tested',
                         'best_model', 'significance_level',
                         'summary_text']
        sample = ComparisonSummary(
            models_compared=["DPGMM", "ARIMA"],
            datasets_tested=3,
            best_model="DPGMM",
            significance_level=0.05,
            summary_text="DPGMM outperforms baselines"
        )
        result_dict = asdict(sample)
        for field in required_fields:
            assert field in result_dict, \
                f"ComparisonSummary missing field: {field}"

    def test_paired_ttest_with_bonferroni_returns_statistical_test_result(self):
        """Verify paired_ttest_with_bonferroni returns StatisticalTestResult."""
        scores_a = np.array([0.8, 0.85, 0.9, 0.88, 0.92])
        scores_b = np.array([0.7, 0.75, 0.8, 0.78, 0.82])
        result = paired_ttest_with_bonferroni(scores_a, scores_b, alpha=0.05)
        assert isinstance(result, StatisticalTestResult), \
            f"paired_ttest_with_bonferroni must return StatisticalTestResult, got {type(result)}"

    def test_compare_all_models_returns_comparison_summary(self):
        """Verify compare_all_models returns ComparisonSummary."""
        models_scores = {
            "DPGMM": [0.85, 0.88, 0.90],
            "ARIMA": [0.75, 0.78, 0.80],
            "MA": [0.70, 0.72, 0.75]
        }
        result = compare_all_models(models_scores, alpha=0.05)
        assert isinstance(result, ComparisonSummary), \
            f"compare_all_models must return ComparisonSummary, got {type(result)}"

# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_compute_metrics_with_perfect_prediction(self):
        """Test metrics with perfect predictions."""
        y_true = np.array([0, 1, 0, 1, 1])
        y_pred = np.array([0, 1, 0, 1, 1])
        f1 = compute_f1_score(y_true, y_pred)
        assert f1 == 1.0, f"Perfect prediction should give f1=1.0, got {f1}"

    def test_compute_metrics_with_zero_predictions(self):
        """Test metrics when model predicts all zeros."""
        y_true = np.array([0, 1, 0, 1, 1])
        y_pred = np.array([0, 0, 0, 0, 0])
        precision = compute_precision(y_true, y_pred)
        recall = compute_recall(y_true, y_pred)
        # Precision should be undefined (0/0), recall should be 0
        assert recall == 0.0, f"Recall should be 0.0, got {recall}"

    def test_compute_metrics_with_all_predictions(self):
        """Test metrics when model predicts all ones."""
        y_true = np.array([0, 1, 0, 1, 1])
        y_pred = np.array([1, 1, 1, 1, 1])
        recall = compute_recall(y_true, y_pred)
        assert recall == 1.0, f"Recall should be 1.0, got {recall}"

    def test_compute_auc_with_constant_scores(self):
        """Test AUC with constant scores (should give 0.5)."""
        y_true = np.array([0, 1, 0, 1, 1])
        scores = np.array([0.5, 0.5, 0.5, 0.5, 0.5])
        auc = compute_auc(y_true, scores)
        assert abs(auc - 0.5) < 0.01, f"AUC with constant scores should be ~0.5, got {auc}"

    def test_empty_input_handling(self):
        """Test handling of empty inputs."""
        y_true = np.array([])
        y_pred = np.array([])
        with pytest.raises((ValueError, IndexError)):
            compute_f1_score(y_true, y_pred)

# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for full evaluation pipeline."""

    def test_full_evaluation_pipeline(self, sample_predictions, sample_scores, tmp_path):
        """Test complete evaluation pipeline produces valid outputs."""
        y_true, y_pred = sample_predictions
        y_true_scores, scores = sample_scores

        # Compute all metrics
        metrics = compute_all_metrics(y_true, y_pred, scores)
        assert isinstance(metrics, EvaluationMetrics)

        # Generate confusion matrix
        cm = generate_confusion_matrix(y_true, y_pred)
        assert cm.shape == (2, 2)

        # Generate ROC/PR curves
        roc_result = generate_roc_curve(y_true_scores, scores)
        pr_result = generate_pr_curve(y_true_scores, scores)
        assert len(roc_result) == 3
        assert len(pr_result) == 3

        # Save plots
        roc_path = tmp_path / "roc.png"
        pr_path = tmp_path / "pr.png"
        save_roc_curve(y_true_scores, scores, roc_path)
        save_pr_curve(y_true_scores, scores, pr_path)
        assert roc_path.exists()
        assert pr_path.exists()

    def test_metrics_consistency_across_functions(self, sample_predictions, sample_scores):
        """Verify metrics are consistent when computed via different functions."""
        y_true, y_pred = sample_predictions
        y_true_scores, scores = sample_scores

        # Direct computation
        f1_direct = compute_f1_score(y_true, y_pred)
        precision_direct = compute_precision(y_true, y_pred)
        recall_direct = compute_recall(y_true, y_pred)
        auc_direct = compute_auc(y_true_scores, scores)

        # Via compute_all_metrics
        all_metrics = compute_all_metrics(y_true, y_pred, scores)

        # Verify consistency
        assert abs(all_metrics.f1_score - f1_direct) < 1e-6, \
            f"f1_score inconsistent: {all_metrics.f1_score} vs {f1_direct}"
        assert abs(all_metrics.precision - precision_direct) < 1e-6, \
            f"precision inconsistent: {all_metrics.precision} vs {precision_direct}"
        assert abs(all_metrics.recall - recall_direct) < 1e-6, \
            f"recall inconsistent: {all_metrics.recall} vs {recall_direct}"
        assert abs(all_metrics.auc - auc_direct) < 1e-6, \
            f"AUC inconsistent: {all_metrics.auc} vs {auc_direct}"

# ============================================================================
# Main entry point for standalone testing
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
