#!/usr/bin/env python3
"""
Generate experiment metadata with state tracking.

This script creates experiment metadata for tracking reproducibility
and serves as the entry point for experiment registration.
"""
import sys
import yaml
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.state_tracker import StateTracker


def main():
    """Generate initial experiment metadata for T077."""
    tracker = StateTracker()
    
    # Generate metadata for the current project state
    metadata = tracker.generate_experiment_metadata(
        experiment_name="T077_state_tracking_baseline",
        dataset_name="synthetic_anomaly_v1",
        model_type="DPGMM",
        custom_params={
            "task_id": "T077",
            "description": "Generate experiment metadata with state tracking",
            "phase": "Phase 6 - Polish & Cross-Cutting Concerns",
            "implementation_date": "2024"
        }
    )
    
    # Save the metadata
    filepath = tracker.save_metadata(metadata)
    
    print(f"Experiment metadata generated: {filepath}")
    print(f"Experiment ID: {metadata['experiment_id']}")
    print(f"Git Commit: {metadata['git']['commit']}")
    print(f"Python Version: {metadata['environment']['python_version']}")
    
    # Verify the file exists and is readable
    assert filepath.exists(), "Metadata file was not created"
    
    with open(filepath, 'r') as f:
        loaded = yaml.safe_load(f)
    
    assert loaded['experiment_id'] == metadata['experiment_id']
    
    print("✓ Metadata generation verified successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
