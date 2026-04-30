"""Unit tests for state tracker functionality."""
import pytest
import yaml
import tempfile
from pathlib import Path
from datetime import datetime

# Import the state tracker
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from services.state_tracker import StateTracker


class TestStateTracker:
    """Test StateTracker class functionality."""
    
    @pytest.fixture
    def tracker(self, tmp_path):
        """Create a temporary StateTracker."""
        tracker = StateTracker(project_root=str(tmp_path))
        return tracker
    
    def test_initialization(self, tracker):
        """Test StateTracker initializes correctly."""
        assert tracker.state_dir.exists()
        assert tracker.project_root is not None
    
    def test_generate_git_info(self, tracker):
        """Test git information extraction."""
        git_info = tracker._get_git_info()
        assert "commit" in git_info
        assert "branch" in git_info
        assert "timestamp" in git_info
    
    def test_generate_environment_info(self, tracker):
        """Test environment information extraction."""
        env_info = tracker._get_environment_info()
        assert "python_version" in env_info
        assert "platform" in env_info
        assert "numpy_version" in env_info
    
    def test_generate_experiment_metadata(self, tracker):
        """Test complete metadata generation."""
        metadata = tracker.generate_experiment_metadata(
            experiment_name="test_exp",
            dataset_name="test_dataset",
            model_type="DPGMM"
        )
        
        assert metadata["experiment_id"] == "test_exp"
        assert metadata["dataset"] == "test_dataset"
        assert metadata["model_type"] == "DPGMM"
        assert "created_at" in metadata
        assert "git" in metadata
        assert "environment" in metadata
        assert "config" in metadata
        assert "metrics" in metadata
        assert "artifacts" in metadata
    
    def test_save_metadata(self, tracker):
        """Test metadata persistence."""
        metadata = tracker.generate_experiment_metadata(
            experiment_name="test_exp",
            dataset_name="test_dataset"
        )
        
        filepath = tracker.save_metadata(metadata)
        
        assert filepath.exists()
        assert filepath.suffix == ".yaml"
        
        # Verify content can be loaded
        with open(filepath, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded["experiment_id"] == metadata["experiment_id"]
    
    def test_update_metrics(self, tracker):
        """Test metrics update functionality."""
        metadata = tracker.generate_experiment_metadata(
            experiment_name="test_exp",
            dataset_name="test_dataset"
        )
        tracker.save_metadata(metadata)
        
        metrics = {
            "precision": 0.85,
            "recall": 0.90,
            "f1_score": 0.87
        }
        
        filepath = tracker.update_metrics("test_exp", metrics)
        
        with open(filepath, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded["metrics"]["precision"] == 0.85
        assert loaded["metrics"]["recall"] == 0.90
        assert loaded["metrics"]["f1_score"] == 0.87
    
    def test_add_artifact(self, tracker):
        """Test artifact registration."""
        metadata = tracker.generate_experiment_metadata(
            experiment_name="test_exp",
            dataset_name="test_dataset"
        )
        tracker.save_metadata(metadata)
        
        filepath = tracker.add_artifact(
            "test_exp",
            "paper/figures/fig1.png",
            "plot"
        )
        
        with open(filepath, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert len(loaded["artifacts"]) == 1
        assert loaded["artifacts"][0]["path"] == "paper/figures/fig1.png"
        assert loaded["artifacts"][0]["type"] == "plot"
    
    def test_load_experiment(self, tracker):
        """Test experiment retrieval."""
        metadata = tracker.generate_experiment_metadata(
            experiment_name="test_exp",
            dataset_name="test_dataset"
        )
        tracker.save_metadata(metadata)
        
        loaded = tracker.load_experiment("test_exp")
        
        assert loaded is not None
        assert loaded["experiment_id"] == "test_exp"
    
    def test_load_nonexistent_experiment(self, tracker):
        """Test loading nonexistent experiment returns None."""
        loaded = tracker.load_experiment("nonexistent")
        assert loaded is None
    
    def test_list_experiments(self, tracker):
        """Test experiment listing."""
        # Create multiple experiments
        for i in range(3):
            metadata = tracker.generate_experiment_metadata(
                experiment_name=f"test_exp_{i}",
                dataset_name="test_dataset"
            )
            tracker.save_metadata(metadata)
        
        experiments = tracker.list_experiments()
        
        assert len(experiments) == 3
        assert all("filename" in exp for exp in experiments)
        assert all("created" in exp for exp in experiments)
    
    def test_generate_checksum(self, tracker, tmp_path):
        """Test file checksum generation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        checksum = tracker.generate_checksum(str(test_file))
        
        assert len(checksum) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)
    
    def test_checksum_deterministic(self, tracker, tmp_path):
        """Test checksum is deterministic."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        checksum1 = tracker.generate_checksum(str(test_file))
        checksum2 = tracker.generate_checksum(str(test_file))
        
        assert checksum1 == checksum2
    
    def test_checksum_changes_with_content(self, tracker, tmp_path):
        """Test checksum changes when content changes."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content 1")
        checksum1 = tracker.generate_checksum(str(test_file))
        
        test_file.write_text("content 2")
        checksum2 = tracker.generate_checksum(str(test_file))
        
        assert checksum1 != checksum2
