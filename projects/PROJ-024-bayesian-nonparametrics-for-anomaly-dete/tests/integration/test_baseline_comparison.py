"""
Integration test for end-to-end baseline comparison pipeline (US2).

Tests the complete pipeline:
1. Synthetic data generation with known ground truth
2. Running DPGMM, ARIMA, and Moving Average baselines
3. Computing evaluation metrics (F1, precision, recall, AUC)
4. Generating comparison plots
5. Verifying output schemas

This test verifies US2 acceptance scenarios independently.
"""
import sys
import os
import pytest
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.synthetic_generator import (
    generate_synthetic_timeseries,
    save_synthetic_dataset,
    generate_validation_dataset,
)
from baselines.arima import ARIMABaseline, ARIMAConfig
from baselines.moving_average import MovingAverageBaseline, MovingAverageConfig
from models.dp_gmm import DPGMMModel
from models.anomaly_score import AnomalyScore
from evaluation.metrics import (
    EvaluationMetrics,
    compute_f1_score,
    compute_precision,
    compute_recall,
    compute_auc,
    compute_all_metrics,
    generate_confusion_matrix,
)
from evaluation.plots import (
    generate_pr_curve,
    save_pr_curve,
    generate_evaluation_plots,
    PRPlotConfig,
)
from utils.streaming import StreamingObservationProcessor, SlidingWindowBuffer
from utils.runtime_monitor import RuntimeMonitor, RuntimeBudget


@pytest.fixture
def synthetic_dataset():
    """Generate synthetic time series with known anomaly ground truth."""
    np.random.seed(42)
    data, ground_truth = generate_synthetic_timeseries(
        n_samples=500,
        anomaly_rate=0.05,
        anomaly_types=["point", "contextual"],
        seed=42,
    )
    return data, ground_truth


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory for test artifacts."""
    output_dir = tmp_path / "baseline_comparison_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def dpgmm_model():
    """Initialize DPGMM model with test configuration."""
    model = DPGMMModel(
        n_features=1,
        max_components=20,
        concentration_prior=1.0,
        random_state=42,
    )
    return model


@pytest.fixture
def arima_baseline():
    """Initialize ARIMA baseline with test configuration."""
    config = ARIMAConfig(
        order=(1, 1, 1),
        seasonal_order=(0, 0, 0, 0),
        trend="c",
        n_jobs=1,
    )
    baseline = ARIMABaseline(config=config)
    return baseline


@pytest.fixture
def moving_average_baseline():
    """Initialize Moving Average baseline with test configuration."""
    config = MovingAverageConfig(
        window_size=20,
        z_score_threshold=3.0,
        min_samples=30,
    )
    baseline = MovingAverageBaseline(config=config)
    return baseline


class TestBaselineComparisonPipeline:
    """Integration tests for the complete baseline comparison pipeline."""

    def test_synthetic_data_generation_with_ground_truth(
        self, synthetic_dataset
    ):
        """
        Verify synthetic data generation produces data with known anomalies.

        US2 Acceptance Scenario 1: Can generate test data with known ground truth
        for validation purposes.
        """
        data, ground_truth = synthetic_dataset

        # Verify data shape
        assert data.shape[0] > 0, "Data should have samples"
        assert data.shape[1] == 1, "Should be univariate"

        # Verify ground truth exists and has same length
        assert len(ground_truth) == len(data), \
            "Ground truth should match data length"

        # Verify ground truth contains anomalies
        anomaly_indices = np.where(ground_truth == 1)[0]
        assert len(anomaly_indices) > 0, \
            "Synthetic data should contain anomalies for testing"

        # Verify anomaly rate is approximately correct
        actual_rate = len(anomaly_indices) / len(ground_truth)
        expected_rate = 0.05
        assert abs(actual_rate - expected_rate) < 0.02, \
            f"Anomaly rate {actual_rate:.3f} should be close to {expected_rate}"

    def test_arima_baseline_detection(
        self, synthetic_dataset, arima_baseline, temp_output_dir
    ):
        """
        Verify ARIMA baseline can process data and produce anomaly scores.

        US2 Acceptance Scenario 1: ARIMA baseline should run on time series
        and produce anomaly predictions.
        """
        data, ground_truth = synthetic_dataset

        # Run ARIMA baseline
        predictions = arima_baseline.fit_predict(data)

        # Verify output schema
        assert predictions is not None, "ARIMA should produce predictions"
        assert len(predictions) == len(data), \
            "Predictions should match data length"

        # Verify predictions are numeric
        assert all(isinstance(p, (int, float, np.number)) for p in predictions), \
            "Predictions should be numeric scores"

        # Verify we can convert to binary anomalies using threshold
        threshold = np.percentile(predictions, 95)
        binary_predictions = (np.array(predictions) > threshold).astype(int)
        assert set(binary_predictions).issubset({0, 1}), \
            "Binary predictions should be 0 or 1"

    def test_moving_average_baseline_detection(
        self, synthetic_dataset, moving_average_baseline, temp_output_dir
    ):
        """
        Verify Moving Average baseline can process data and produce anomaly scores.

        US2 Acceptance Scenario 1: Moving average baseline should run on time series
        and produce anomaly predictions.
        """
        data, ground_truth = synthetic_dataset

        # Run Moving Average baseline
        predictions = moving_average_baseline.fit_predict(data)

        # Verify output schema
        assert predictions is not None, "Moving Average should produce predictions"
        assert len(predictions) == len(data), \
            "Predictions should match data length"

        # Verify predictions are numeric
        assert all(isinstance(p, (int, float, np.number)) for p in predictions), \
            "Predictions should be numeric scores"

    def test_dpgmm_model_streaming_detection(
        self, synthetic_dataset, dpgmm_model, temp_output_dir
    ):
        """
        Verify DPGMM model can process streaming observations and produce scores.

        US1 + US2: DPGMM should work in streaming mode and produce anomaly scores
        that can be compared against baselines.
        """
        data, ground_truth = synthetic_dataset

        # Process data in streaming mode
        scores = []
        for i, value in enumerate(data):
            observation = StreamingObservation(
                timestamp=datetime.now(),
                value=float(value),
                features=None,
            )
            dpgmm_model.update(observation)
            score = dpgmm_model.score(observation)
            scores.append(score.score_value)

        # Verify output schema
        assert len(scores) == len(data), \
            "Scores should match data length"

        # Verify scores are numeric
        assert all(isinstance(s, (int, float, np.number)) for s in scores), \
            "Scores should be numeric"

    def test_evaluation_metrics_computation(
        self, synthetic_dataset, temp_output_dir
    ):
        """
        Verify evaluation metrics can be computed from predictions and ground truth.

        US2 Acceptance Scenario 1: Should be able to compute F1, precision, recall,
        and AUC metrics for model comparison.
        """
        data, ground_truth = synthetic_dataset

        # Generate test predictions
        np.random.seed(42)
        test_predictions = np.random.random(len(data))

        # Compute metrics
        metrics = compute_all_metrics(
            y_true=ground_truth,
            y_pred=test_predictions,
            threshold=0.5,
        )

        # Verify metrics schema
        assert isinstance(metrics, EvaluationMetrics), \
            "Metrics should be EvaluationMetrics instance"

        assert hasattr(metrics, 'f1_score'), "Should have f1_score"
        assert hasattr(metrics, 'precision'), "Should have precision"
        assert hasattr(metrics, 'recall'), "Should have recall"
        assert hasattr(metrics, 'auc'), "Should have auc"

        # Verify metrics are in valid ranges
        assert 0 <= metrics.f1_score <= 1, "F1 should be in [0, 1]"
        assert 0 <= metrics.precision <= 1, "Precision should be in [0, 1]"
        assert 0 <= metrics.recall <= 1, "Recall should be in [0, 1]"
        assert 0.5 <= metrics.auc <= 1.0, "AUC should be in [0.5, 1.0]"

    def test_full_baseline_comparison_pipeline(
        self, synthetic_dataset, dpgmm_model, arima_baseline,
        moving_average_baseline, temp_output_dir
    ):
        """
        End-to-end test of complete baseline comparison pipeline.

        This is the main integration test that verifies all components work
        together to produce a complete comparison report.
        """
        data, ground_truth = synthetic_dataset

        # Run all models
        results = {}

        # DPGMM
        dpgmm_scores = []
        for value in data:
            observation = StreamingObservation(
                timestamp=datetime.now(),
                value=float(value),
                features=None,
            )
            dpgmm_model.update(observation)
            score = dpgmm_model.score(observation)
            dpgmm_scores.append(score.score_value)
        results['dpgmm'] = np.array(dpgmm_scores)

        # ARIMA
        arima_scores = arima_baseline.fit_predict(data)
        results['arima'] = np.array(arima_scores)

        # Moving Average
        ma_scores = moving_average_baseline.fit_predict(data)
        results['moving_average'] = np.array(ma_scores)

        # Compute metrics for each model
        metrics_results = {}
        for model_name, scores in results.items():
            # Find optimal threshold using percentile
            threshold = np.percentile(scores, 95)
            binary_preds = (scores > threshold).astype(int)

            metrics = compute_all_metrics(
                y_true=ground_truth,
                y_pred=scores,
                threshold=threshold,
            )
            metrics_results[model_name] = metrics

            # Verify metrics are valid
            assert metrics.f1_score > 0, \
                f"{model_name} should detect some anomalies"

        # Generate comparison plots
        plot_config = PRPlotConfig(
            title="Baseline Comparison PR Curves",
            xlabel="Recall",
            ylabel="Precision",
            figsize=(10, 8),
        )

        # Save PR curves for each model
        for model_name, scores in results.items():
            fig, ax = generate_pr_curve(
                y_true=ground_truth,
                y_scores=scores,
                config=plot_config,
            )
            save_pr_curve(
                fig=fig,
                path=temp_output_dir / f"{model_name}_pr_curve.png",
            )

        # Verify plots were created
        for model_name in results.keys():
            plot_path = temp_output_dir / f"{model_name}_pr_curve.png"
            assert plot_path.exists(), \
                f"Plot should be saved for {model_name}"

        # Verify all models produced detectable anomalies
        for model_name, metrics in metrics_results.items():
            assert metrics.f1_score >= 0, \
                f"{model_name} should have valid F1 score"

        return results, metrics_results

    def test_runtime_within_budget(
        self, synthetic_dataset, dpgmm_model, arima_baseline,
        moving_average_baseline, temp_output_dir
    ):
        """
        Verify the baseline comparison pipeline completes within time budget.

        SC-003: Runtime should be <30 minutes per dataset.
        """
        data, ground_truth = synthetic_dataset

        # Set runtime budget (60 seconds for this test)
        budget = RuntimeBudget(
            max_seconds=60,
            warning_threshold=0.8,
        )
        monitor = RuntimeMonitor(budget=budget)

        with monitor.track("baseline_comparison"):
            # Run DPGMM
            dpgmm_scores = []
            for value in data:
                observation = StreamingObservation(
                    timestamp=datetime.now(),
                    value=float(value),
                    features=None,
                )
                dpgmm_model.update(observation)
                score = dpgmm_model.score(observation)
                dpgmm_scores.append(score.score_value)

            # Run ARIMA
            arima_scores = arima_baseline.fit_predict(data)

            # Run Moving Average
            ma_scores = moving_average_baseline.fit_predict(data)

        # Verify runtime was within budget
        runtime_result = monitor.get_results()
        assert runtime_result['baseline_comparison']['elapsed_seconds'] < 60, \
            "Pipeline should complete within 60 seconds for test data"

    def test_metrics_schema_compliance(
        self, synthetic_dataset, temp_output_dir
    ):
        """
        Verify all metrics outputs comply with the EvaluationMetrics schema.

        T027 Contract Test integration: Verify metrics schema is consistent.
        """
        data, ground_truth = synthetic_dataset

        # Generate predictions
        np.random.seed(42)
        predictions = np.random.random(len(data))

        # Compute all metrics
        metrics = compute_all_metrics(
            y_true=ground_truth,
            y_pred=predictions,
            threshold=0.5,
        )

        # Verify schema fields
        required_fields = [
            'f1_score', 'precision', 'recall', 'auc',
            'true_positives', 'true_negatives',
            'false_positives', 'false_negatives',
            'threshold', 'model_name', 'timestamp'
        ]

        for field in required_fields:
            assert hasattr(metrics, field), \
                f"EvaluationMetrics should have {field} field"

    def test_confusion_matrix_generation(
        self, synthetic_dataset, temp_output_dir
    ):
        """
        Verify confusion matrix can be generated and saved.

        FR-006: Should be able to generate confusion matrix for model evaluation.
        """
        data, ground_truth = synthetic_dataset

        # Generate predictions
        np.random.seed(42)
        predictions = np.random.random(len(data))
        threshold = 0.5
        binary_preds = (predictions > threshold).astype(int)

        # Generate confusion matrix
        cm = generate_confusion_matrix(
            y_true=ground_truth,
            y_pred=binary_preds,
        )

        # Verify confusion matrix shape
        assert cm.shape == (2, 2), \
            "Confusion matrix should be 2x2"

        # Save confusion matrix plot
        fig = save_confusion_matrix_plot(
            confusion_matrix=cm,
            path=temp_output_dir / "confusion_matrix.png",
        )

        # Verify plot was saved
        assert (temp_output_dir / "confusion_matrix.png").exists(), \
            "Confusion matrix plot should be saved"

    def test_multiple_dataset_comparison(
        self, temp_output_dir
    ):
        """
        Verify pipeline can compare models across multiple datasets.

        US2 Acceptance Scenario 3: Should support comparison across multiple datasets.
        """
        datasets = []

        # Generate multiple synthetic datasets
        for i in range(3):
            np.random.seed(42 + i)
            data, ground_truth = generate_synthetic_timeseries(
                n_samples=200,
                anomaly_rate=0.05,
                anomaly_types=["point"],
                seed=42 + i,
            )
            datasets.append((data, ground_truth, f"dataset_{i}"))

        # Run comparison on each dataset
        all_metrics = {}
        for data, ground_truth, name in datasets:
            # Simple test predictions
            np.random.seed(42)
            predictions = np.random.random(len(data))

            metrics = compute_all_metrics(
                y_true=ground_truth,
                y_pred=predictions,
                threshold=0.5,
            )
            all_metrics[name] = metrics

            # Verify metrics are valid
            assert metrics.f1_score >= 0, \
                f"{name} should have valid F1 score"

        # Verify all datasets were processed
        assert len(all_metrics) == 3, \
            "Should process all 3 datasets"

    def test_pipeline_with_streaming_processor(
        self, synthetic_dataset, dpgmm_model, temp_output_dir
    ):
        """
        Verify pipeline works with streaming observation processor.

        T009 Integration: Should integrate with streaming utilities.
        """
        data, ground_truth = synthetic_dataset

        # Create streaming processor
        window_size = 20
        processor = StreamingObservationProcessor(
            window_size=window_size,
            buffer=SlidingWindowBuffer(size=window_size),
        )

        # Process data through pipeline
        scores = []
        for value in data:
            observation = StreamingObservation(
                timestamp=datetime.now(),
                value=float(value),
                features=None,
            )
            processor.add(observation)
            dpgmm_model.update(observation)
            score = dpgmm_model.score(observation)
            scores.append(score.score_value)

        # Verify streaming produced valid scores
        assert len(scores) == len(data), \
            "Should produce one score per observation"

        # Verify scores are numeric
        assert all(isinstance(s, (int, float, np.number)) for s in scores), \
            "Scores should be numeric"


class TestBaselineComparisonEdgeCases:
    """Edge case tests for baseline comparison pipeline."""

    def test_empty_dataset_handling(self, temp_output_dir):
        """Verify pipeline handles empty datasets gracefully."""
        empty_data = np.array([])
        empty_ground_truth = np.array([])

        # Should not crash on empty data
        with pytest.raises((ValueError, IndexError)):
            compute_all_metrics(
                y_true=empty_ground_truth,
                y_pred=np.array([]),
                threshold=0.5,
            )

    def test_all_anomalies_dataset(self, temp_output_dir):
        """Verify pipeline handles dataset where all points are anomalies."""
        data = np.random.random(100)
        ground_truth = np.ones(100)  # All anomalies

        np.random.seed(42)
        predictions = np.random.random(100)

        metrics = compute_all_metrics(
            y_true=ground_truth,
            y_pred=predictions,
            threshold=0.5,
        )

        # Should produce valid metrics even in edge case
        assert metrics.f1_score >= 0
        assert metrics.precision >= 0
        assert metrics.recall >= 0

    def test_no_anomalies_dataset(self, temp_output_dir):
        """Verify pipeline handles dataset with no anomalies."""
        data = np.random.random(100)
        ground_truth = np.zeros(100)  # No anomalies

        np.random.seed(42)
        predictions = np.random.random(100)

        metrics = compute_all_metrics(
            y_true=ground_truth,
            y_pred=predictions,
            threshold=0.5,
        )

        # Should produce valid metrics even in edge case
        assert metrics.f1_score >= 0
        assert metrics.precision >= 0
        assert metrics.recall >= 0


def main():
    """Run tests when executed directly."""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    main()
