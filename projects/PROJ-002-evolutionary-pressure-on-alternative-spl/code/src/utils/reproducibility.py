"""
Environment configuration for reproducibility with random seeds.

This module provides utilities to set and manage random seeds across
multiple libraries to ensure reproducible results in the pipeline.
"""

import os
import random
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any

def set_reproducible_seeds(seed: Optional[int] = None) -> Dict[str, int]:
    """
    Set random seeds for reproducibility across all relevant libraries.

    Args:
        seed: Random seed value. If None, generates from current timestamp.

    Returns:
        Dictionary of seed values used for each library.
    """
    if seed is None:
        seed = int(datetime.now().timestamp() * 1000) % (2**32)

    # Set Python random seed
    random.seed(seed)

    # Set numpy seed (if available)
    try:
        import numpy as np
        np.random.seed(seed)
        numpy_seed = seed
    except ImportError:
        numpy_seed = None

    # Set torch seeds (if available)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        torch_seed = seed
    except ImportError:
        torch_seed = None

    # Set environment variables for reproducibility
    os.environ['PYTHONHASHSEED'] = str(seed)

    return {
        'base_seed': seed,
        'numpy_seed': numpy_seed,
        'torch_seed': torch_seed
    }

def get_environment_hash() -> str:
    """
    Generate a hash of the current environment configuration.

    Returns:
        SHA256 hash of environment settings.
    """
    env_vars = {
        'PYTHONHASHSEED': os.environ.get('PYTHONHASHSEED', ''),
        'CUDA_VISIBLE_DEVICES': os.environ.get('CUDA_VISIBLE_DEVICES', ''),
    }
    env_str = str(sorted(env_vars.items()))
    return hashlib.sha256(env_str.encode()).hexdigest()

def save_seed_config(seed: int, output_path: str) -> None:
    """
    Save seed configuration to a file for audit trail.

    Args:
        seed: The random seed value used.
        output_path: Path to save the configuration file.
    """
    import json

    config = {
        'seed': seed,
        'timestamp': datetime.now().isoformat(),
        'environment_hash': get_environment_hash()
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)

def load_seed_config(config_path: str) -> Dict[str, Any]:
    """
    Load seed configuration from a file.

    Args:
        config_path: Path to the configuration file.

    Returns:
        Dictionary containing seed configuration.
    """
    import json

    with open(config_path, 'r') as f:
        return json.load(f)
