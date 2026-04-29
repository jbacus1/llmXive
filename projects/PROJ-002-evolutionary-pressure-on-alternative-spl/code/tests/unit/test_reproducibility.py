"""
Unit tests for reproducibility utilities.
"""

import pytest
import os
import json
import tempfile
from pathlib import Path

from code.src.utils.reproducibility import (
    set_reproducible_seeds,
    get_environment_hash,
    save_seed_config,
    load_seed_config
)

class TestReproducibility:
    """Tests for reproducibility utility functions."""

    def test_set_reproducible_seeds_returns_dict(self):
        """Test that set_reproducible_seeds returns a dictionary."""
        result = set_reproducible_seeds(seed=42)
        assert isinstance(result, dict)
        assert 'base_seed' in result
        assert result['base_seed'] == 42

    def test_set_reproducible_seeds_sets_python_seed(self):
        """Test that Python random seed is set correctly."""
        import random
        set_reproducible_seeds(seed=12345)
        assert random.randint(0, 100) == random.randint(0, 100)

    def test_python_hash_seed_environment_variable(self):
        """Test that PYTHONHASHSEED environment variable is set."""
        seed = 99999
        set_reproducible_seeds(seed=seed)
        assert os.environ.get('PYTHONHASHSEED') == str(seed)

    def test_save_and_load_seed_config(self):
        """Test saving and loading seed configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, 'seed_config.json')
            seed = 54321

            save_seed_config(seed=seed, output_path=config_path)
            assert os.path.exists(config_path)

            loaded = load_seed_config(config_path)
            assert loaded['seed'] == seed
            assert 'timestamp' in loaded
            assert 'environment_hash' in loaded

    def test_get_environment_hash(self):
        """Test that environment hash is generated."""
        hash1 = get_environment_hash()
        hash2 = get_environment_hash()
        assert len(hash1) == 64  # SHA256 hex length
        assert isinstance(hash1, str)