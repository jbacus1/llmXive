"""
Unit tests for anomaly cluster vs isolated point edge case handling.

These tests verify that the AnomalyDetector correctly distinguishes between:
- Isolated anomalies (single outlier points)
- Clustered anomalies (groups forming new clusters)
- Regime shifts (new clusters with high anomaly rates)
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock

from code.services.anomaly_detector import (
    AnomalyDetector,
    AnomalyClassification,
    ClusterContext
)


class TestAnomalyClusterEdgeCase:
    """Tests for cluster vs isolated point handling."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock DPGMM model for testing."""
        model = Mock()
        model.compute_anomaly_score = Mock(return_value=(2.5, 0.3, 0))
        return model

    @pytest.fixture
    def detector_config(self):
        """Default configuration for detector."""
        return {
            'cluster_min_size': 3,
            'cluster_max_age': 50,
            'isolated_anomaly_threshold': 2.0,
            'clustered_anomaly_threshold': 1.5,
            'regime_shift_anomaly_rate': 0.3
        }

    @pytest.fixture
    def detector(self, mock_model, detector_config):
        """Create a detector with mock model."""
        return AnomalyDetector(mock_model, detector_config)

    def test_isolated_anomaly_classification(self, detector, mock_model):
        """Test that points without cluster membership are classified as isolated."""
        # Mock model returns no cluster (None)
        mock_model.compute_anomaly_score = Mock(return_value=(2.5, 0.3, None))

        obs = np.array([1.0, 2.0, 3.0])
        classification = detector.process_observation(obs, observation_idx=0)

        assert classification.classification == 'isolated'
        assert classification.is_anomaly == True
        assert classification.cluster_context is None

    def test_clustered_anomaly_classification(self, detector, mock_model):
        """Test that points with cluster membership are classified as clustered."""
        # Mock model returns cluster ID
        mock_model.compute_anomaly_score = Mock(return_value=(2.0, 0.3, 0))

        # Process multiple points to build cluster
        for i in range(5):
            obs = np.array([1.0 + i * 0.1, 2.0, 3.0])
            classification = detector.process_observation(obs, observation_idx=i)

        # Second point should be clustered
        classification = detector.process_observation(obs, observation_idx=5)

        assert classification.classification == 'clustered'
        assert classification.is_anomaly == True
        assert classification.cluster_context is not None
        assert classification.cluster_context.cluster_id == 0

    def test_regime_shift_detection(self, detector, mock_model):
        """Test detection of regime shift (new cluster with high anomaly rate)."""
        # Mock model returns high score and cluster ID
        mock_model.compute_anomaly_score = Mock(return_value=(3.0, 0.3, 1))

        # Create a new cluster with high anomaly rate
        for i in range(10):
            obs = np.array([10.0, 20.0, 30.0])  # Different from normal
            classification = detector.process_observation(obs, observation_idx=i)

        # Check that cluster statistics show high anomaly rate
        stats = detector.get_cluster_statistics()
        cluster_stats = stats['clusters'].get(1, {})

        assert cluster_stats.get('anomaly_rate', 0) > 0.3

    def test_cluster_context_creation(self, detector):
        """Test that cluster context is properly created."""
        context = detector._get_cluster_context(cluster_id=0, observation_idx=100)

        assert context is None  # No clusters yet

        # Create a cluster
        detector._cluster_observations[0] = [(0, True), (1, True), (2, False)]
        detector._cluster_total_counts[0] = 3
        detector._cluster_anomaly_counts[0] = 2
        detector._cluster_formed_at[0] = 0

        context = detector._get_cluster_context(cluster_id=0, observation_idx=100)

        assert context.cluster_id == 0
        assert context.cluster_size == 3
        assert context.cluster_age == 100
        assert context.anomaly_rate_in_cluster == pytest.approx(2/3, rel=0.1)

    def test_confidence_computation(self, detector):
        """Test that confidence scores are computed correctly."""
        # Isolated anomaly confidence
        isolated_conf = detector._compute_isolated_confidence(3.0, 0.2)
        assert 0.0 <= isolated_conf <= 1.0

        # Regime shift confidence
        context = ClusterContext(
            cluster_id=0,
            cluster_size=5,
            cluster_density=0.5,
            is_new_cluster=True,
            cluster_age=10,
            anomaly_rate_in_cluster=0.8
        )
        regime_conf = detector._compute_regime_confidence(context, 3.0)
        assert 0.0 <= regime_conf <= 1.0

        # Cluster confidence
        cluster_conf = detector._compute_cluster_confidence(context, 3.0)
        assert 0.0 <= cluster_conf <= 1.0

    def test_cluster_state_update(self, detector, mock_model):
        """Test that cluster state is properly updated."""
        mock_model.compute_anomaly_score = Mock(return_value=(2.0, 0.3, 0))

        # Process observations
        for i in range(5):
            obs = np.array([1.0, 2.0, 3.0])
            detector.process_observation(obs, observation_idx=i)

        # Check state
        assert 0 in detector._cluster_observations
        assert detector._cluster_total_counts[0] == 5
        assert len(detector._cluster_observations[0]) == 5

    def test_cluster_state_reset(self, detector, mock_model):
        """Test that cluster state can be reset."""
        # Create some state
        mock_model.compute_anomaly_score = Mock(return_value=(2.0, 0.3, 0))
        obs = np.array([1.0, 2.0, 3.0])
        detector.process_observation(obs, observation_idx=0)

        assert len(detector._cluster_observations) > 0

        # Reset
        detector.reset_cluster_state()

        assert len(detector._cluster_observations) == 0
        assert detector._observation_count == 0

    def test_batch_classification(self, detector, mock_model):
        """Test batch processing of observations."""
        mock_model.compute_anomaly_score = Mock(return_value=(2.0, 0.3, 0))

        observations = np.array([
            [1.0, 2.0, 3.0],
            [1.1, 2.1, 3.1],
            [1.2, 2.2, 3.2]
        ])

        classifications = detector.classify_batch(observations, start_idx=0)

        assert len(classifications) == 3
        assert all(isinstance(c, AnomalyClassification) for c in classifications)

    def test_recommendation_generation(self, detector, mock_model):
        """Test that appropriate recommendations are generated."""
        mock_model.compute_anomaly_score = Mock(return_value=(2.5, 0.3, None))

        obs = np.array([1.0, 2.0, 3.0])
        classification = detector.process_observation(obs, observation_idx=0)

        assert classification.recommendation is not None
        assert len(classification.recommendation) > 0
        assert 'isolated' in classification.recommendation.lower()

    def test_cluster_pruning(self, detector, mock_model):
        """Test that old cluster data is pruned to save memory."""
        mock_model.compute_anomaly_score = Mock(return_value=(2.0, 0.3, 0))

        # Create many observations
        for i in range(150):
            obs = np.array([1.0, 2.0, 3.0])
            detector.process_observation(obs, observation_idx=i)

        # Should be pruned to last 100
        assert len(detector._cluster_observations[0]) <= 100

    def test_normal_classification(self, detector, mock_model):
        """Test that normal points are classified correctly."""
        # Low score = normal
        mock_model.compute_anomaly_score = Mock(return_value=(1.0, 0.1, 0))

        obs = np.array([1.0, 2.0, 3.0])
        classification = detector.process_observation(obs, observation_idx=0)

        assert classification.classification == 'normal'
        assert classification.is_anomaly == False

    def test_low_variance_edge_case(self, detector, mock_model):
        """Test handling of low variance time series."""
        # Very low variance observations
        mock_model.compute_anomaly_score = Mock(return_value=(2.5, 0.01, 0))

        obs = np.array([1.000, 1.001, 1.002])
        classification = detector.process_observation(obs, observation_idx=0)

        # Should still classify based on score threshold
        assert classification.confidence > 0

    def test_missing_cluster_id_handling(self, detector, mock_model):
        """Test handling when cluster_id is None."""
        mock_model.compute_anomaly_score = Mock(return_value=(2.5, 0.3, None))

        obs = np.array([1.0, 2.0, 3.0])
        classification = detector.process_observation(obs, observation_idx=0)

        assert classification.cluster_context is None
        assert classification.classification == 'isolated'

    def test_cluster_age_computation(self, detector, mock_model):
        """Test that cluster age is computed correctly."""
        mock_model.compute_anomaly_score = Mock(return_value=(2.0, 0.3, 0))

        # Create cluster at observation 10
        for i in range(10):
            obs = np.array([1.0, 2.0, 3.0])
            detector.process_observation(obs, observation_idx=i)

        # Check age at observation 50
        obs = np.array([1.0, 2.0, 3.0])
        classification = detector.process_observation(obs, observation_idx=50)

        assert classification.cluster_context.cluster_age == 40

    def test_serialization(self, detector):
        """Test that detector can be serialized to dict."""
        state = detector.to_dict()

        assert 'config' in state
        assert 'observation_count' in state
        assert 'num_clusters' in state
        assert 'cluster_statistics' in state
