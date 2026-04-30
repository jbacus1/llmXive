"""Integration tests for state tracking workflow."""
import pytest
import yaml
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from services.state_tracker import StateTracker


class TestStateTrackingIntegration:
    """Test complete state tracking workflow."""
    
    @pytest.fixture
    def tracker(self, tmp_path):
        """Create a temporary StateTracker."""
        tracker = StateTracker(project_root=str(tmp_path))
        return tracker
    
    def test_full_experiment_workflow(self, tracker):
        """Test complete experiment lifecycle."""
        # 1. Generate initial metadata
        metadata = tracker.generate_experiment_metadata(
            experiment_name="integration_test",
            dataset_name="synthetic_anomaly",
            model_type="DPGMM",
            custom_params={
                "concentration": 1.0,
                "max_clusters": 10
            }
        )
        
        # 2. Save metadata
        filepath = tracker.save_metadata(metadata)
        assert filepath.exists()
        
        # 3. Update metrics after "experiment"
        metrics = {
            "precision": 0.85,
            "recall": 0.90,
            "f1_score": 0.87,
            "runtime_seconds": 120.5
        }
        tracker.update_metrics("integration_test", metrics)
        
        # 4. Register artifacts
        tracker.add_artifact(
            "integration_test",
            "paper/figures/fig1.png",
            "plot"
        )
        tracker.add_artifact(
            "integration_test",
            "data/processed/results.csv",
            "data"
        )
        
        # 5. Verify final state
        loaded = tracker.load_experiment("integration_test")
        
        assert loaded["metrics"]["precision"] == 0.85
        assert loaded["metrics"]["f1_score"] == 0.87
        assert len(loaded["artifacts"]) == 2
        assert loaded["parameters"]["concentration"] == 1.0
    
    def test_multiple_experiments_isolation(self, tracker):
        """Test that multiple experiments don't interfere."""
        # Create two experiments
        for i in range(2):
            metadata = tracker.generate_experiment_metadata(
                experiment_name=f"exp_{i}",
                dataset_name="dataset",
                custom_params={"index": i}
            )
            tracker.save_metadata(metadata)
            tracker.update_metrics(f"exp_{i}", {"score": i * 10})
        
        # Verify isolation
        exp0 = tracker.load_experiment("exp_0")
        exp1 = tracker.load_experiment("exp_1")
        
        assert exp0["metrics"]["score"] == 0
        assert exp1["metrics"]["score"] == 10
        assert exp0["parameters"]["index"] == 0
        assert exp1["parameters"]["index"] == 1
    
    def test_state_persistence(self, tracker):
        """Test state survives between tracker instances."""
        # Create and save
        metadata = tracker.generate_experiment_metadata(
            experiment_name="persist_test",
            dataset_name="test"
        )
        tracker.save_metadata(metadata)
        tracker.update_metrics("persist_test", {"metric": 42})
        
        # Create new tracker instance
        new_tracker = StateTracker(project_root=tracker.project_root)
        
        # Load should work
        loaded = new_tracker.load_experiment("persist_test")
        
        assert loaded is not None
        assert loaded["metrics"]["metric"] == 42
    
    def test_checksum_verification_workflow(self, tracker, tmp_path):
        """Test checksum in verification workflow."""
        # Create an artifact
        artifact_path = tmp_path / "artifact.txt"
        artifact_path.write_text("experiment data")
        
        # Generate checksum
        checksum = tracker.generate_checksum(str(artifact_path))
        
        # Verify checksum is reproducible
        assert checksum == tracker.generate_checksum(str(artifact_path))
        
        # Modify and verify different
        artifact_path.write_text("modified data")
        assert checksum != tracker.generate_checksum(str(artifact_path))
