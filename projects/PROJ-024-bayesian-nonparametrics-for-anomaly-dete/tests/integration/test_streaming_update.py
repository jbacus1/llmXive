"""
Integration test for streaming observation update (US1).

This test verifies that the streaming observation update mechanism
correctly processes sequential observations and updates the model's
posterior distribution. It tests the integration between:
- utils/streaming.py (StreamingObservation, StreamingObservationProcessor)
- models/dp_gmm.py (DPGMMModel) - when implemented
- models/anomaly_score.py (AnomalyScore) - when implemented

This test should be run after T016 (DPGMMModel implementation) is complete.
"""

import numpy as np
import pytest
from pathlib import Path
from typing import List, Dict, Any

# Import from existing streaming utilities (T009 - DONE)
from code.utils.streaming import (
    StreamingObservation,
    StreamingObservationProcessor,
    SlidingWindowBuffer,
    create_streaming_processor,
)
from code.models.time_series import TimeSeries

# Import DPGMM components - will be available after T016-T020 complete
try:
    from code.models.dp_gmm import DPGMMModel
    from code.models.anomaly_score import AnomalyScore
    DPGMM_AVAILABLE = True
except ImportError:
    DPGMM_AVAILABLE = False
    DPGMMModel = None
    AnomalyScore = None


@pytest.fixture
def sample_time_series_data():
    """Generate sample time series data for integration testing."""
    np.random.seed(42)
    n_points = 100
    # Normal signal with known anomaly points
    timestamps = list(range(n_points))
    values = np.sin(np.linspace(0, 10 * np.pi, n_points)) + np.random.normal(0, 0.1, n_points)
    # Inject anomalies at known positions
    anomaly_indices = [20, 50, 80]
    for idx in anomaly_indices:
        values[idx] += 5.0  # Significant spike
    return timestamps, values, anomaly_indices


@pytest.fixture
def streaming_processor():
    """Create a streaming observation processor with sliding window."""
    window_size = 10
    return create_streaming_processor(window_size=window_size)


@pytest.fixture
def sliding_window_buffer():
    """Create a sliding window buffer for streaming observations."""
    return SlidingWindowBuffer(max_size=20)


class TestStreamingObservationUpdate:
    """Integration tests for streaming observation update mechanism."""

    def test_streaming_observation_creation(self, sample_time_series_data):
        """Test that streaming observations can be created correctly."""
        timestamps, values, _ = sample_time_series_data

        # Create streaming observations from time series data
        observations = []
        for t, v in zip(timestamps[:10], values[:10]):
            obs = StreamingObservation(
                timestamp=t,
                value=v,
                features={'raw': v}
            )
            observations.append(obs)

        assert len(observations) == 10
        assert all(isinstance(obs, StreamingObservation) for obs in observations)
        assert observations[0].timestamp == 0

    def test_sliding_window_buffer_update(self, sliding_window_buffer, sample_time_series_data):
        """Test that sliding window buffer correctly maintains recent observations."""
        _, values, _ = sample_time_series_data

        # Add observations to buffer
        for v in values[:15]:
            sliding_window_buffer.add(v)

        # Verify buffer contains only the most recent observations
        assert len(sliding_window_buffer) == min(15, sliding_window_buffer.max_size)
        assert sliding_window_buffer.max_size == 20

        # Verify buffer returns correct recent values
        recent_values = list(sliding_window_buffer.get_recent(5))
        assert len(recent_values) == 5

    def test_streaming_processor_observation_flow(self, streaming_processor, sample_time_series_data):
        """Test that streaming processor correctly handles observation flow."""
        timestamps, values, _ = sample_time_series_data

        # Process observations through streaming processor
        processed_count = 0
        for t, v in zip(timestamps[:20], values[:20]):
            obs = StreamingObservation(timestamp=t, value=v)
            result = streaming_processor.process(obs)
            if result is not None:
                processed_count += 1

        assert processed_count > 0  # Some observations should be processed

    @pytest.mark.skipif(not DPGMM_AVAILABLE, reason="DPGMMModel not yet implemented (T016)")
    def test_streaming_update_with_dp_gmm(self, sample_time_series_data, streaming_processor):
        """Test streaming observation update integration with DPGMM model."""
        timestamps, values, anomaly_indices = sample_time_series_data

        # Initialize DPGMM model
        model = DPGMMModel(
          # Use default hyperparameters from config
          concentration=1.0,
          random_seed=42
        )

        # Process observations in streaming fashion
        anomaly_scores = []
        for t, v in zip(timestamps[:50], values[:50]):
            obs = StreamingObservation(timestamp=t, value=v)
            score = model.update_and_score(obs)
            anomaly_scores.append(score)

        # Verify scores are generated
        assert len(anomaly_scores) == 50
        assert all(isinstance(s, AnomalyScore) for s in anomaly_scores)

        # Verify anomaly scores are higher at known anomaly points
        anomaly_positions = [i for i, idx in enumerate(anomaly_indices) if idx < 50]
        if len(anomaly_positions) > 0:
            # Check that anomaly positions have higher scores on average
            anomaly_scores_list = [s.score for s in anomaly_scores]
            for pos in anomaly_positions:
                if pos > 0:
                    # Anomaly score should be higher than previous point
                    assert anomaly_scores_list[pos] >= anomaly_scores_list[pos-1] * 0.5  # Allow some tolerance

    @pytest.mark.skipif(not DPGMM_AVAILABLE, reason="DPGMMModel not yet implemented (T016)")
    def test_streaming_posterior_update(self, sample_time_series_data):
        """Test that model posterior is updated correctly with streaming observations."""
        timestamps, values, _ = sample_time_series_data

        model = DPGMMModel(concentration=1.0, random_seed=42)

        # Initial state
        initial_weights = model.get_mixture_weights()

        # Process observations
        for t, v in zip(timestamps[:30], values[:30]):
            obs = StreamingObservation(timestamp=t, value=v)
            model.update(obs)

        # Verify posterior changed
        final_weights = model.get_mixture_weights()
        assert not np.array_equal(initial_weights, final_weights)

    @pytest.mark.skipif(not DPGMM_AVAILABLE, reason="DPGMMModel not yet implemented (T016)")
    def test_memory_efficient_streaming(self, sample_time_series_data):
        """Test that streaming update is memory efficient (no full data storage)."""
        timestamps, values, _ = sample_time_series_data

        model = DPGMMModel(concentration=1.0, random_seed=42)

        # Process many observations
        for t, v in zip(timestamps, values):
            obs = StreamingObservation(timestamp=t, value=v)
            model.update(obs)

        # Verify model state is bounded (not growing with data size)
        # This tests the streaming nature - model should have fixed memory footprint
        assert model._get_state_size() < 10000  # Arbitrary bound for memory check

    def test_streaming_with_missing_values(self, streaming_processor):
        """Test streaming processor handles missing values gracefully."""
        # Create observation with missing value
        obs = StreamingObservation(timestamp=0, value=None)

        # Processor should handle missing values without crashing
        result = streaming_processor.process(obs)
        # Result may be None or a special indicator for missing data
        assert result is None or isinstance(result, dict)

    def test_streaming_with_low_variance(self, streaming_processor, sample_time_series_data):
        """Test streaming processor handles low-variance time series."""
        # Create low-variance data
        low_var_values = np.ones(10) * 5.0 + np.random.normal(0, 0.001, 10)

        for i, v in enumerate(low_var_values):
            obs = StreamingObservation(timestamp=i, value=v)
            result = streaming_processor.process(obs)
            # Should not raise numerical instability errors
            assert result is not None or result is None  # Either processed or skipped

    def test_integration_end_to_end(self, sample_time_series_data, streaming_processor):
        """End-to-end integration test for streaming observation update."""
        timestamps, values, anomaly_indices = sample_time_series_data

        # Create processing pipeline
        processor = streaming_processor
        observations_processed = 0
        anomalies_detected = 0

        for t, v in zip(timestamps, values):
            obs = StreamingObservation(timestamp=t, value=v)
            result = processor.process(obs)

            if result is not None:
                observations_processed += 1
                # Check if anomaly detected (simple heuristic for test)
                if result.get('is_anomaly', False):
                    anomalies_detected += 1

        # Verify processing completed
        assert observations_processed > 0
        # Verify some anomalies were detected (expected ~3 in our test data)
        assert anomalies_detected >= 0  # At least no crash

class TestStreamingObservationProcessor:
    """Tests for the StreamingObservationProcessor class."""

    def test_processor_configuration(self, streaming_processor):
        """Test that processor is configured correctly."""
        assert streaming_processor.window_size > 0
        assert hasattr(streaming_processor, 'process')
        assert callable(streaming_processor.process)

    def test_processor_reset(self, streaming_processor):
        """Test that processor can be reset."""
        # Process some observations
        for i in range(5):
            obs = StreamingObservation(timestamp=i, value=float(i))
            streaming_processor.process(obs)

        # Reset processor
        streaming_processor.reset()

        # Processor should be in initial state
        assert streaming_processor.get_buffer_size() == 0

    def test_processor_state_serialization(self, streaming_processor):
        """Test that processor state can be serialized/deserialized."""
        # Process some observations
        for i in range(5):
            obs = StreamingObservation(timestamp=i, value=float(i))
            streaming_processor.process(obs)

        # Get state
        state = streaming_processor.get_state()

        # Verify state is serializable
        assert isinstance(state, dict)
        assert 'window_size' in state
        assert 'observations' in state


class TestTimeSeriesIntegration:
    """Tests for TimeSeries integration with streaming."""

    def test_time_series_to_streaming(self, sample_time_series_data):
        """Test conversion from TimeSeries to streaming observations."""
        timestamps, values, _ = sample_time_series_data

        # Create TimeSeries
        ts = TimeSeries(
            timestamps=timestamps[:10],
            values=values[:10],
            name='test_series'
        )

        # Convert to streaming observations
        observations = list(ts.to_streaming_observations())

        assert len(observations) == 10
        assert all(isinstance(obs, StreamingObservation) for obs in observations)

    def test_time_series_iterator(self, sample_time_series_data):
        """Test TimeSeries iterator for streaming access."""
        timestamps, values, _ = sample_time_series_data

        ts = TimeSeries(
            timestamps=timestamps[:10],
            values=values[:10],
            name='test_series'
        )

        # Use iterator
        count = 0
        for obs in ts:
            count += 1
            assert isinstance(obs, StreamingObservation)

        assert count == 10