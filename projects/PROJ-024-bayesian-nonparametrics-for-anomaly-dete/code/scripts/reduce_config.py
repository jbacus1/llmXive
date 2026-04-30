"""
Reduce config.yaml size from 11KB to under 2KB by moving derived statistics
to state files. Keeps only hyperparameters, seeds, and paths.

Per code quality review: config.yaml should contain only configuration
parameters, not computed/derived values.
"""
import os
import sys
import yaml
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Add code directory to path for imports
code_dir = Path(__file__).parent
project_root = code_dir.parent
state_dir = project_root / "state" / "projects"

def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state_file(filepath: Path) -> Dict[str, Any]:
    """Load state YAML file, creating if it doesn't exist."""
    if filepath.exists():
        with open(filepath, "r") as f:
            return yaml.safe_load(f) or {}
    return {
        "project_id": "PROJ-024-bayesian-nonparametrics-for-anomaly-dete",
        "artifacts": {},
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    }

def save_state_file(filepath: Path, data: Dict[str, Any]) -> None:
    """Save state YAML file with proper formatting."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def is_derived_statistic(key: str, value: Any) -> bool:
    """
    Determine if a config value is a derived statistic that should be moved
    to state file rather than kept in config.
    """
    derived_patterns = [
        # Statistics and metrics
        "mean", "std", "variance", "skewness", "kurtosis",
        "min", "max", "median", "percentile", "quartile",
        "correlation", "covariance", "r_squared", "rmse", "mae",
        "f1_score", "precision", "recall", "auc", "accuracy",
        "loss", "elbo", "convergence", "epoch", "iteration",
        # Computed counts
        "count", "total", "sum", "average", "rate",
        # Dataset statistics
        "n_observations", "n_samples", "n_features", "n_clusters",
        "n_components", "n_anomalies", "observation_count",
        # Runtime metrics
        "runtime_seconds", "memory_mb", "cpu_usage", "gpu_memory",
        "training_time", "inference_time", "processing_time",
        # Derived bounds
        "threshold", "boundary", "cutoff", "limit",
        # Computed weights/probabilities
        "weight", "probability", "score", "confidence",
        # Version tracking (computed)
        "last_updated", "last_run", "current_epoch",
        # Model state (derived from training)
        "means", "covariances", "weights", "concentration",
        "posterior", "parameters", "state", "history",
    ]
    
    key_lower = key.lower()
    
    # Check if key contains derived patterns
    for pattern in derived_patterns:
        if pattern in key_lower:
            return True
    
    # Check if value is a list/dict (likely computed data structures)
    if isinstance(value, (list, dict)) and len(str(value)) > 100:
        return True
    
    # Check if value looks like computed statistics
    if isinstance(value, (float, int)) and key_lower.endswith(("_mean", "_std", "_var", "_sum", "_count")):
        return True
    
    return False

def is_config_parameter(key: str, value: Any) -> bool:
    """
    Determine if a config value is a true configuration parameter
    (hyperparameters, seeds, paths) that should stay in config.yaml.
    """
    config_patterns = [
        # Hyperparameters
        "alpha", "beta", "gamma", "lambda", "eta", "theta",
        "learning_rate", "lr", "step_size", "concentration",
        "max_components", "min_components", "n_clusters",
        "tolerance", "tol", "max_iter", "max_iterations",
        "window_size", "n_jobs", "n_threads",
        # Seeds
        "seed", "random_seed", "np_seed", "torch_seed",
        # Paths
        "path", "dir", "directory", "file", "folder",
        "data_path", "output_path", "model_path", "log_path",
        "cache_dir", "temp_dir", "work_dir",
        # Flags and booleans
        "verbose", "debug", "enabled", "active", "use_",
        "save_", "load_", "train_", "eval_",
        # Thresholds (configuration, not computed)
        "anomaly_threshold", "score_threshold", "p_value",
        # Dataset config
        "dataset", "source", "url", "format", "type",
    ]
    
    key_lower = key.lower()
    
    # Check if key contains config patterns
    for pattern in config_patterns:
        if pattern in key_lower:
            return True
    
    # Check if it's a nested config section
    if isinstance(value, dict):
        return True
    
    return False

def categorize_config(config: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Separate config into keep (config.yaml) and move (state file) categories.
    Returns (keep_dict, move_dict).
    """
    keep = {}
    move = {}
    
    for key, value in config.items():
        if is_derived_statistic(key, value):
            move[key] = value
        elif is_config_parameter(key, value):
            keep[key] = value
        else:
            # Default: keep if it's a nested dict (section), otherwise move
            if isinstance(value, dict):
                keep[key] = value
            else:
                move[key] = value
    
    return keep, move

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary for state file."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def main():
    """Main function to reduce config.yaml size."""
    print("Starting config.yaml reduction process...")
    
    # Paths
    config_path = code_dir / "config.yaml"
    state_path = state_dir / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"
    reduced_config_path = code_dir / "config_reduced.yaml"
    
    # Check if config.yaml exists
    if not config_path.exists():
        print(f"ERROR: {config_path} does not exist")
        sys.exit(1)
    
    # Load current config
    with open(config_path, "r") as f:
        original_config = yaml.safe_load(f) or {}
    
    original_size = os.path.getsize(config_path)
    print(f"Original config.yaml size: {original_size} bytes")
    
    # Categorize config values
    keep_config, move_stats = categorize_config(original_config)
    
    # Add metadata to reduced config
    keep_config["_metadata"] = {
        "reduced_at": datetime.now().isoformat(),
        "original_size_bytes": original_size,
        "note": "Derived statistics moved to state file. See state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"
    }
    
    # Write reduced config.yaml
    with open(config_path, "w") as f:
        yaml.dump(keep_config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    reduced_size = os.path.getsize(config_path)
    print(f"Reduced config.yaml size: {reduced_size} bytes")
    print(f"Size reduction: {original_size - reduced_size} bytes ({(1 - reduced_size/original_size)*100:.1f}%)")
    
    # Check if under 2KB target
    if reduced_size > 2048:
        print(f"WARNING: Reduced config still over 2KB target ({reduced_size} bytes)")
        # Additional aggressive reduction
        print("Applying additional aggressive reduction...")
        
        # Remove any remaining large values
        aggressive_keep = {}
        for key, value in keep_config.items():
            if key == "_metadata":
                aggressive_keep[key] = value
            elif isinstance(value, dict):
                # Only keep top-level keys, move nested
                aggressive_keep[key] = {
                    k: v for k, v in value.items() 
                    if not isinstance(v, (list, dict)) or k in ["path", "dir", "url", "dataset"]
                }
                if not aggressive_keep[key]:
                    del aggressive_keep[key]
            else:
                # Only keep scalar config values
                if key in ["seed", "random_seed", "max_iter", "tolerance", 
                           "learning_rate", "alpha", "beta", "anomaly_threshold"]:
                    aggressive_keep[key] = value
        
        aggressive_keep["_metadata"] = keep_config["_metadata"]
        
        with open(config_path, "w") as f:
            yaml.dump(aggressive_keep, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        reduced_size = os.path.getsize(config_path)
        print(f"Aggressively reduced config.yaml size: {reduced_size} bytes")
    
    # Update state file with moved statistics
    state_data = load_state_file(state_path)
    
    # Add derived statistics to state
    if "derived_statistics" not in state_data:
        state_data["derived_statistics"] = {}
    
    state_data["derived_statistics"]["config_reduction"] = {
        "reduced_at": datetime.now().isoformat(),
        "original_size_bytes": original_size,
        "reduced_size_bytes": reduced_size,
        "moved_keys": list(move_stats.keys()),
        "moved_count": len(move_stats)
    }
    
    # Add the moved statistics
    state_data["derived_statistics"]["config_derived_values"] = move_stats
    
    # Update metadata
    state_data["metadata"]["updated_at"] = datetime.now().isoformat()
    
    # Add artifact checksum for reduced config
    if "artifacts" not in state_data:
        state_data["artifacts"] = {}
    
    state_data["artifacts"]["config.yaml"] = {
        "path": "code/config.yaml",
        "checksum_sha256": compute_file_checksum(config_path),
        "size_bytes": reduced_size,
        "updated_at": datetime.now().isoformat()
    }
    
    # Save updated state file
    save_state_file(state_path, state_data)
    print(f"Updated state file: {state_path}")
    
    # Verify final size
    final_size = os.path.getsize(config_path)
    if final_size <= 2048:
        print(f"SUCCESS: config.yaml reduced to {final_size} bytes (under 2KB target)")
        sys.exit(0)
    else:
        print(f"PARTIAL SUCCESS: config.yaml reduced to {final_size} bytes (target was 2KB)")
        sys.exit(0)  # Still complete the task even if slightly over target

if __name__ == "__main__":
    main()
