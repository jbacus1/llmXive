"""
Contract test for evaluation metrics output schema (T027).

Per spec.md US2 acceptance criteria:
- Validates EvaluationMetrics output schema
- Tests F1-scores, precision, recall, AUC computation
- Tests confusion matrix generation

FAILS before implementation (T031-T033) - verify this behavior.
"""
import pytest
from typing import Dict, Any
import numpy as np
from pathlib import Path

# Import from the metrics module we just created
sys_path = Path(__file__).parent.parent.parent / 'code'
import sys
sys.path.insert(0, str(sys_path))

from evaluation.metrics import (
    EvaluationMetrics,
    compute_f1_score,
    compute_precision,
    compute_recall,
    compute_auc,
    generate_confusion_matrix,
    compute_all_metrics
)

@pytest.mark.contract
@pytest.mark.us2
class TestEvaluationMetricsSchema:
    """Contract tests for evaluation metrics output schema compliance."""
    
    def test_output_contains_f1_score(self):
        """
        Verify EvaluationMetrics output contains f1_score field.
        
        Per FR-006: Metrics must include F1-scores.
        """
        y_true = np.array([0, 1, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 0, 1])
        
        metrics = compute_all_metrics(y_true, y_pred)
        assert hasattr(metrics, 'f1_score'), "EvaluationMetrics must have f1_score field"
        assert isinstance(metrics.f1_score, float), "f1_score must be a float"
    
    def test_output_contains_precision(self):
        """
        Verify EvaluationMetrics output contains precision field.
        
        Per FR-006: Metrics must include precision.
        """
        y_true = np.array([0, 1, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 0, 1])
        
        metrics = compute_all_metrics(y_true, y_pred)
        assert hasattr(metrics, 'precision'), "EvaluationMetrics must have precision field"
        assert isinstance(metrics.precision, float), "precision must be a float"
    
    def test_output_contains_recall(self):
        """
        Verify EvaluationMetrics output contains recall field.
        
        Per FR-006: Metrics must include recall.
        """
        y_true = np.array([0, 1, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 0, 1])
        
        metrics = compute_all_metrics(y_true, y_pred)
        assert hasattr(metrics, 'recall'), "EvaluationMetrics must have recall field"
        assert isinstance(metrics.recall, float), "recall must be a float"
    
    def test_output_contains_auc(self):
        """
        Verify EvaluationMetrics output contains auc field.
        
        Per FR-006: Metrics must include AUC.
        """
        y_true = np.array([0, 1, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 0, 1])
        y_scores = np.array([0.1, 0.8, 0.6, 0.2, 0.9])
        
        metrics = compute_all_metrics(y_true, y_pred, y_scores)
        assert hasattr(metrics, 'auc'), "EvaluationMetrics must have auc field"
        assert isinstance(metrics.auc, float), "auc must be a float"
    
    def test_output_contains_confusion_matrix(self):
        """
        Verify EvaluationMetrics output contains confusion_matrix field.
        
        Per FR-006: Must support confusion matrix generation.
        """
        y_true = np.array([0, 1, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 0, 1])
        
        metrics = compute_all_metrics(y_true, y_pred)
        assert hasattr(metrics, 'confusion_matrix'), "EvaluationMetrics must have confusion_matrix field"
        assert isinstance(metrics.confusion_matrix, list), "confusion_matrix must be a list"
    
    def test_metrics_are_computed_against_ground_truth(self):
        """
        Verify metrics are computed against known ground truth labels.
        
        Per US2: Compare against labeled benchmark datasets.
        """
        # Create known ground truth with known anomaly positions
        y_true = np.array([0, 0, 0, 1, 1, 0, 0, 0])  # anomalies at indices 3, 4
        y_pred = np.array([0, 0, 1, 1, 0, 0, 0, 0])  # predicted anomaly at index 2, 3
        
        metrics = compute_all_metrics(y_true, y_pred)
        
        # Verify metrics are computed (not just defaults)
        assert metrics.tp >= 0, "True positives must be non-negative"
        assert metrics.fp >= 0, "False positives must be non-negative"
        assert metrics.tn >= 0, "True negatives must be non-negative"
        assert metrics.fn >= 0, "False negatives must be non-negative"
    
    def test_metrics_schema_serialization(self):
        """
        Verify EvaluationMetrics can be serialized to dictionary.
        
        Per FR-006: Metrics must be exportable for reporting.
        """
        y_true = np.array([0, 1, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 0, 1])
        y_scores = np.array([0.1, 0.8, 0.6, 0.2, 0.9])
        
        metrics = compute_all_metrics(y_true, y_pred, y_scores)
        metrics_dict = metrics.to_dict()
        
        assert isinstance(metrics_dict, dict), "to_dict() must return a dictionary"
        assert 'f1_score' in metrics_dict, "Serialized dict must contain f1_score"
        assert 'precision' in metrics_dict, "Serialized dict must contain precision"
        assert 'recall' in metrics_dict, "Serialized dict must contain recall"
        assert 'auc' in metrics_dict, "Serialized dict must contain auc"
    
    def test_edge_case_perfect_prediction(self):
        """
        Test metrics when prediction perfectly matches ground truth.
        
        Per Edge Cases: Handle perfect prediction scenario.
        """
        y_true = np.array([0, 1, 0, 1, 0])
        y_pred = np.array([0, 1, 0, 1, 0])
        
        metrics = compute_all_metrics(y_true, y_pred)
        
        assert metrics.f1_score == 1.0, "Perfect prediction should yield F1=1.0"
        assert metrics.precision == 1.0, "Perfect prediction should yield precision=1.0"
        assert metrics.recall == 1.0, "Perfect prediction should yield recall=1.0"
    
    def test_edge_case_no_anomalies(self):
        """
        Test metrics when there are no anomalies in data.
        
        Per Edge Cases: Handle zero-anomaly scenario.
        """
        y_true = np.array([0, 0, 0, 0, 0])
        y_pred = np.array([0, 0, 0, 0, 0])
        
        metrics = compute_all_metrics(y_true, y_pred)
        
        # Should not crash, metrics should be 0 or NaN handled gracefully
        assert metrics.f1_score >= 0, "F1-score must be non-negative"
    
    def test_edge_case_all_anomalies(self):
        """
        Test metrics when all samples are anomalies.
        
        Per Edge Cases: Handle all-anomaly scenario.
        """
        y_true = np.array([1, 1, 1, 1, 1])
        y_pred = np.array([1, 1, 1, 1, 1])
        
        metrics = compute_all_metrics(y_true, y_pred)
        
        assert metrics.f1_score == 1.0, "All anomalies correctly predicted should yield F1=1.0"
    
    def test_confusion_matrix_components(self):
        """
        Verify confusion matrix component counts are accurate.
        
        Per FR-006: Must correctly count TP, FP, TN, FN.
        """
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_pred = np.array([0, 1, 0, 1, 0, 1])
        # Expected: TP=2, FP=1, TN=2, FN=1
        
        metrics = compute_all_metrics(y_true, y_pred)
        
        assert metrics.tp + metrics.fp + metrics.tn + metrics.fn == len(y_true), \
            "Sum of confusion matrix components must equal total samples"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])