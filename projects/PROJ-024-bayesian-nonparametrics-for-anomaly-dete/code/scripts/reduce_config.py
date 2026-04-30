#!/usr/bin/env python3
"""
Reduce config.yaml size from 11KB to under 2KB by moving derived statistics
to state files, keeping only hyperparameters, seeds, and paths.

Per Constitution Principle I and T073 requirement.
"""
import os
import sys
import yaml
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, List

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "code" / "config.yaml"
STATE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"

# Categories for config items
CONFIG_CATEGORIES = {
    "hyperparameters": ["alpha", "beta", "gamma", "concentration", "max_components", 
                      "min_components", "variance_prior", "mean_prior", "learning_rate",
                      "convergence_threshold", "max_iterations", "batch_size"],
    "seeds": ["random_seed", "numpy_seed", "torch_seed", "experiment_seed"],
    "paths": ["data_raw_dir", "data_processed_dir", "model_output_dir", "log_dir",
             "state_dir", "artifact_dir", "checkpoint_dir"],
    "dataset": ["dataset_name", "dataset_url", "dataset_checksum", "target_column",
               "timestamp_column", "anomaly_column", "train_split", "test_split"],
    "evaluation": ["f1_threshold", "precision_threshold", "recall_threshold",
                  "auc_threshold", "statistical_significance_level"],
    "monitoring": ["memory_limit_gb", "runtime_limit_minutes", "elbo_log_interval"],
    "derived_statistics": ["total_observations", "anomaly_count", "normal_count",
                         "anomaly_rate", "component_count", "final_elbo",
                         "training_duration_seconds", "model_checksum",
                         "dataset_hash", "observation_stats", "component_stats",
                         "baseline_f1_scores", "baseline_precision", "baseline_recall",
                         "baseline_auc", "comparison_results", "hyperparameter_sweep_results"]
}

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def load_state_file(path: Path) -> Dict[str, Any]:
    """Load existing state file or return empty dict."""
    if path.exists():
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {
        "project_id": "PROJ-024-bayesian-nonparametrics-for-anomaly-dete",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "derived_statistics": {}
    }

def save_state_file(path: Path, state: Dict[str, Any]) -> None:
    """Save state file with checksum."""
    # Update timestamp
    state["updated_at"] = datetime.utcnow().isoformat()
    
    # Write to temp first, then rename for atomicity
    temp_path = path.with_suffix('.tmp')
    with open(temp_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    # Compute and add checksum
    checksum = compute_file_checksum(temp_path)
    state["state_checksum"] = checksum
    
    with open(temp_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    temp_path.rename(path)

def is_derived_statistic(key: str, value: Any) -> bool:
    """Check if a config key represents derived statistics."""
    key_lower = key.lower()
    
    # Check against known derived statistics patterns
    derived_patterns = [
        'total_observations', 'observation_count', 'anomaly_count', 'normal_count',
        'anomaly_rate', 'component_count', 'final_elbo', 'training_duration',
        'model_checksum', 'dataset_hash', 'observation_stats', 'component_stats',
        'baseline_f1', 'baseline_precision', 'baseline_recall', 'baseline_auc',
        'comparison_results', 'sweep_results', 'hyperparameter_results',
        'convergence_history', 'elbo_history', 'training_metrics', 'validation_metrics'
    ]
    
    for pattern in derived_patterns:
        if pattern in key_lower:
            return True
    
    # Check if value is a computed statistic (not a simple config value)
    if isinstance(value, (list, dict)):
        # Complex structures are often derived
        return True
    
    if isinstance(value, float):
        # Floats might be computed statistics
        return True
    
    return False

def is_config_parameter(key: str, value: Any) -> bool:
    """Check if a config key is a valid configuration parameter."""
    key_lower = key.lower()
    
    # Check against known config categories
    for category, keys in CONFIG_CATEGORIES.items():
        if category != "derived_statistics":
            for config_key in keys:
                if config_key in key_lower or key_lower in config_key:
                    return True
    
    # Simple scalar values are typically config parameters
    if isinstance(value, (int, float, str, bool)) and not is_derived_statistic(key, value):
        return True
    
    return False

def categorize_config(config: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Separate config into parameters and derived statistics."""
    parameters = {}
    derived = {}
    
    for key, value in config.items():
        if is_derived_statistic(key, value):
            derived[key] = value
        elif is_config_parameter(key, value):
            parameters[key] = value
        else:
            # Default: treat as parameter if not clearly derived
            parameters[key] = value
    
    return parameters, derived

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def reduce_config() -> Dict[str, Any]:
    """Main function to reduce config.yaml size."""
    print(f"Loading config from {CONFIG_PATH}")
    
    if not CONFIG_PATH.exists():
        print(f"ERROR: Config file not found at {CONFIG_PATH}")
        sys.exit(1)
    
    with open(CONFIG_PATH, 'r') as f:
        original_config = yaml.safe_load(f)
    
    original_size = CONFIG_PATH.stat().st_size
    print(f"Original config size: {original_size} bytes")
    
    # Separate parameters from derived statistics
    parameters, derived = categorize_config(original_config)
    
    print(f"Identified {len(parameters)} config parameters")
    print(f"Identified {len(derived)} derived statistics to move to state")
    
    # Load or create state file
    state = load_state_file(STATE_PATH)
    
    # Merge derived statistics into state
    if "derived_statistics" not in state:
        state["derived_statistics"] = {}
    
    state["derived_statistics"].update(derived)
    state["derived_statistics"]["last_updated"] = datetime.utcnow().isoformat()
    state["derived_statistics"]["original_config_path"] = str(CONFIG_PATH)
    
    # Save reduced state file
    save_state_file(STATE_PATH, state)
    print(f"Saved derived statistics to {STATE_PATH}")
    
    # Create minimal config with only essential parameters
    minimal_config = {
        "project_id": "PROJ-024-bayesian-nonparametrics-for-anomaly-dete",
        "version": "1.0.0",
        "hyperparameters": parameters.get("hyperparameters", {}),
        "seeds": parameters.get("seeds", {}),
        "paths": parameters.get("paths", {}),
        "dataset": parameters.get("dataset", {}),
        "evaluation": parameters.get("evaluation", {}),
        "monitoring": parameters.get("monitoring", {}),
        "state_reference": {
            "path": str(STATE_PATH.relative_to(PROJECT_ROOT)),
            "note": "Derived statistics moved here per T073"
        }
    }
    
    # Save reduced config
    temp_config_path = CONFIG_PATH.with_suffix('.yaml.tmp')
    with open(temp_config_path, 'w') as f:
        yaml.dump(minimal_config, f, default_flow_style=False, sort_keys=False)
    
    reduced_size = temp_config_path.stat().st_size
    print(f"Reduced config size: {reduced_size} bytes")
    
    # Verify size reduction
    if reduced_size > 2048:
        print(f"WARNING: Reduced config still exceeds 2KB ({reduced_size} bytes)")
        print("Additional manual review may be needed")
    
    # Atomic rename
    temp_config_path.rename(CONFIG_PATH)
    
    # Compute and log final checksum
    final_checksum = compute_file_checksum(CONFIG_PATH)
    print(f"Final config checksum: {final_checksum}")
    
    return {
        "original_size": original_size,
        "reduced_size": reduced_size,
        "reduction_percent": ((original_size - reduced_size) / original_size) * 100,
        "parameters_kept": len(parameters),
        "derived_moved": len(derived),
        "config_checksum": final_checksum
    }

def main():
    """Entry point."""
    print("=" * 60)
    print("Config Reduction Script (T073)")
    print("=" * 60)
    
    result = reduce_config()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Original size: {result['original_size']} bytes")
    print(f"Reduced size: {result['reduced_size']} bytes")
    print(f"Reduction: {result['reduction_percent']:.1f}%")
    print(f"Parameters kept: {result['parameters_kept']}")
    print(f"Derived moved to state: {result['derived_moved']}")
    print(f"Config checksum: {result['config_checksum']}")
    
    if result['reduced_size'] <= 2048:
        print("\n✓ SUCCESS: Config is under 2KB")
    else:
        print("\n⚠ WARNING: Config still exceeds 2KB")
    
    return 0 if result['reduced_size'] <= 2048 else 1

if __name__ == "__main__":
    sys.exit(main())
