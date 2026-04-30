"""
State tracking service for experiment metadata.

Tracks experiment parameters, runtime metrics, and version information
to ensure reproducibility and traceability per Constitution Principle 1
(Reproducibility) and Principle 6 (Single Source of Truth).
"""
import os
import yaml
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import platform
import git
import numpy as np


class StateTracker:
    """
    Tracks experiment state including parameters, metrics, and environment.
    
    All state is stored in state/ directory with ISO-8601 timestamped files.
    """
    
    def __init__(self, project_root: str = "projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection"):
        self.project_root = Path(project_root)
        self.state_dir = self.project_root / "state"
        self.state_dir.mkdir(exist_ok=True)
        
    def _get_git_info(self) -> Dict[str, Any]:
        """Extract current git commit and branch information."""
        try:
            repo = git.Repo(self.project_root)
            return {
                "commit": repo.head.commit.hexsha,
                "branch": repo.active_branch.name,
                "dirty": repo.is_dirty(),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except Exception:
            return {
                "commit": "unknown",
                "branch": "unknown",
                "dirty": False,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    def _get_environment_info(self) -> Dict[str, Any]:
        """Capture Python and system environment."""
        return {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "numpy_version": np.__version__,
            "hostname": platform.node(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.yaml."""
        config_path = self.project_root / "code" / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def generate_experiment_metadata(
        self,
        experiment_name: str,
        dataset_name: str,
        model_type: str = "DPGMM",
        custom_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete experiment metadata for tracking.
        
        Args:
            experiment_name: Unique identifier for this experiment run
            dataset_name: Name of dataset being used
            model_type: Type of model (DPGMM, ARIMA, MA, etc.)
            custom_params: Additional parameters to track
        
        Returns:
            Complete metadata dictionary
        """
        config = self._load_config()
        
        metadata = {
            "experiment_id": experiment_name,
            "dataset": dataset_name,
            "model_type": model_type,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "git": self._get_git_info(),
            "environment": self._get_environment_info(),
            "config": {
                "random_seed": config.get("random_seed", 42),
                "hyperparameters": config.get("hyperparameters", {}),
                "dataset_paths": config.get("dataset_paths", {})
            },
            "parameters": custom_params or {},
            "metrics": {},
            "artifacts": []
        }
        
        return metadata
    
    def save_metadata(self, metadata: Dict[str, Any]) -> Path:
        """
        Save metadata to state directory with timestamp.
        
        Args:
            metadata: Complete metadata dictionary
        
        Returns:
            Path to saved metadata file
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"experiment_{metadata['experiment_id']}_{timestamp}.yaml"
        filepath = self.state_dir / filename
        
        with open(filepath, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
        
        return filepath
    
    def update_metrics(self, experiment_id: str, metrics: Dict[str, float]) -> Path:
        """
        Update metrics for an existing experiment.
        
        Args:
            experiment_id: Experiment identifier
            metrics: Dictionary of metric name -> value
        
        Returns:
            Path to updated metadata file
        """
        # Find most recent matching experiment file
        files = sorted(self.state_dir.glob(f"experiment_{experiment_id}_*.yaml"))
        if not files:
            raise ValueError(f"No experiment found with ID: {experiment_id}")
        
        filepath = files[-1]
        with open(filepath, 'r') as f:
            metadata = yaml.safe_load(f)
        
        metadata["metrics"].update(metrics)
        metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        with open(filepath, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
        
        return filepath
    
    def add_artifact(self, experiment_id: str, artifact_path: str, artifact_type: str) -> Path:
        """
        Register an artifact with the experiment.
        
        Args:
            experiment_id: Experiment identifier
            artifact_path: Relative path to artifact
            artifact_type: Type (model, plot, data, etc.)
        
        Returns:
            Path to updated metadata file
        """
        files = sorted(self.state_dir.glob(f"experiment_{experiment_id}_*.yaml"))
        if not files:
            raise ValueError(f"No experiment found with ID: {experiment_id}")
        
        filepath = files[-1]
        with open(filepath, 'r') as f:
            metadata = yaml.safe_load(f)
        
        metadata["artifacts"].append({
            "path": artifact_path,
            "type": artifact_type,
            "registered_at": datetime.utcnow().isoformat() + "Z"
        })
        
        with open(filepath, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
        
        return filepath
    
    def list_experiments(self) -> List[Dict[str, str]]:
        """List all experiment metadata files."""
        files = sorted(self.state_dir.glob("experiment_*.yaml"))
        return [
            {
                "filename": f.name,
                "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            }
            for f in files
        ]
    
    def load_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Load most recent experiment by ID."""
        files = sorted(self.state_dir.glob(f"experiment_{experiment_id}_*.yaml"))
        if not files:
            return None
        
        with open(files[-1], 'r') as f:
            return yaml.safe_load(f)
    
    def generate_checksum(self, filepath: str) -> str:
        """Generate SHA256 checksum for file integrity verification."""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()


# Convenience function for quick metadata generation
def generate_experiment_metadata(
    experiment_name: str,
    dataset_name: str,
    model_type: str = "DPGMM"
) -> Dict[str, Any]:
    """Quick function to generate experiment metadata."""
    tracker = StateTracker()
    return tracker.generate_experiment_metadata(
        experiment_name=experiment_name,
        dataset_name=dataset_name,
        model_type=model_type
    )
