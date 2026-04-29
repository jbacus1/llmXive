"""
Base Configuration Management Module

Provides type-safe configuration handling for the evolutionary pressure
on alternative splicing analysis pipeline. Supports environment variables,
configuration files (YAML/JSON), and runtime overrides.

Usage:
    from utils.config import Config, get_config
    
    config = get_config()
    db_path = config.get("database.path")
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field
from functools import lru_cache

# Try to import yaml, fall back gracefully if not available
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None

from .logger import get_logger

logger = get_logger(__name__)

# Default configuration values
DEFAULTS = {
    "project": {
        "name": "evolutionary-pressure-alternative-spl",
        "id": "PROJ-002",
        "version": "0.1.0",
        "root_dir": str(Path(__file__).parent.parent.parent),
    },
    "database": {
        "path": "state/projects/PROJ-002-evolutionary-pressure-on-alternative-spl/metadata.db",
        "driver": "sqlite",
    },
    "data": {
        "raw_dir": "data/raw",
        "processed_dir": "data/processed",
        "temp_dir": "data/temp",
        "output_dir": "data/output",
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "logs/pipeline.log",
    },
    "random_seed": {
        "default": 42,
        "numpy": 42,
        "python": 42,
    },
    "pipeline": {
        "parallel_workers": 4,
        "batch_size": 100,
        "timeout_seconds": 3600,
    },
    "thresholds": {
        "mapping_rate_min": 0.70,
        "psi_delta_min": 0.1,
        "read_coverage_min": 20,
        "fdr_threshold": 0.05,
    },
    "species": {
        "supported": ["human", "chimpanzee", "macaque", "marmoset"],
        "references": {
            "human": "GRCh38",
            "chimpanzee": "Pan_tro_3.0",
            "macaque": "Mmul_10",
            "marmoset": "CalJac3",
        },
    },
    "sra": {
        "download_dir": "data/raw/sra",
        "max_retries": 3,
        "timeout_seconds": 300,
    },
    "alignment": {
        "star_index_dir": "data/reference/STAR_index",
        "output_dir": "data/processed/aligned",
        "mapping_rate_threshold": 0.70,
    },
    "quantification": {
        "rmats_output_dir": "data/processed/rmats",
        "psi_output_dir": "data/processed/psi",
    },
    "analysis": {
        "selection_output_dir": "data/processed/selection",
        "enrichment_output_dir": "data/processed/enrichment",
    },
}

@dataclass
class Config:
    """
    Type-safe configuration container with dot-notation access and validation.
    
    Attributes:
        _data: Internal dictionary storing all configuration values
        _defaults: Default values for the configuration
        _overrides: Runtime overrides from environment or config file
    """
    _data: Dict[str, Any] = field(default_factory=dict)
    _defaults: Dict[str, Any] = field(default_factory=lambda: DEFAULTS)
    _overrides: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize configuration by merging defaults and overrides."""
        self._data = self._deep_merge(self._defaults, self._overrides)
        logger.debug("Configuration initialized with %d keys", len(self._flatten_dict(self._data)))
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Recursively merge two dictionaries, with override taking precedence."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """Flatten a nested dictionary with dot-notation keys."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Dot-separated path (e.g., 'database.path', 'thresholds.mapping_rate_min')
            default: Value to return if key not found
        
        Returns:
            Configuration value or default
        
        Example:
            config.get('database.path')  # Returns database path
            config.get('missing.key', 'fallback')  # Returns 'fallback'
        """
        keys = key.split('.')
        value = self._data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Dot-separated path
            value: Value to set
        
        Example:
            config.set('database.path', '/new/path.db')
        """
        keys = key.split('.')
        current = self._data
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
    
    def get_env(self, env_var: str, default: Any = None) -> Any:
        """
        Get value from environment variable with type coercion.
        
        Args:
            env_var: Environment variable name
            default: Default value if not set
        
        Returns:
            Typed environment variable value
        """
        value = os.getenv(env_var, default)
        if value is None:
            return default
        
        # Type coercion
        if isinstance(value, str):
            if value.lower() in ('true', '1', 'yes'):
                return True
            elif value.lower() in ('false', '0', 'no'):
                return False
            elif value.isdigit():
                return int(value)
            try:
                return float(value)
            except ValueError:
                pass
        return value
    
    def load_from_file(self, path: Union[str, Path]) -> None:
        """
        Load configuration from a YAML or JSON file.
        
        Args:
            path: Path to configuration file
        
        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file format is unsupported
        """
        path = Path(path)
        if not path.exists():
            logger.warning("Configuration file not found: %s", path)
            return
        
        logger.info("Loading configuration from: %s", path)
        
        try:
            with open(path, 'r') as f:
                if path.suffix in ('.yaml', '.yml'):
                    if YAML_AVAILABLE:
                        config_data = yaml.safe_load(f) or {}
                    else:
                        raise ImportError("PyYAML not installed for YAML config loading")
                elif path.suffix == '.json':
                    config_data = json.load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {path.suffix}")
            
            self._overrides = self._deep_merge(self._overrides, config_data)
            self._data = self._deep_merge(self._defaults, self._overrides)
            logger.info("Configuration loaded successfully from %s", path)
            
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            logger.error("Failed to parse configuration file: %s", e)
            raise
    
    def validate(self) -> bool:
        """
        Validate configuration values against constraints.
        
        Returns:
            True if all validations pass
        
        Raises:
            ValueError: If any validation fails
        """
        errors = []
        
        # Validate thresholds
        if self.get('thresholds.mapping_rate_min', 0.7) < 0 or self.get('thresholds.mapping_rate_min', 0.7) > 1:
            errors.append("mapping_rate_min must be between 0 and 1")
        
        if self.get('thresholds.fdr_threshold', 0.05) < 0 or self.get('thresholds.fdr_threshold', 0.05) > 1:
            errors.append("fdr_threshold must be between 0 and 1")
        
        # Validate directories exist or can be created
        for key in ['data.raw_dir', 'data.processed_dir', 'data.output_dir']:
            dir_path = self.get(key)
            if dir_path:
                full_path = Path(self.get('project.root_dir')) / dir_path
                try:
                    full_path.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    errors.append(f"Cannot create directory: {full_path}")
        
        if errors:
            error_msg = "; ".join(errors)
            logger.error("Configuration validation failed: %s", error_msg)
            raise ValueError(error_msg)
        
        logger.debug("Configuration validation passed")
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as a flat dictionary."""
        return self._flatten_dict(self._data)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        flat = self._flatten_dict(self._data)
        return f"Config({len(flat)} keys)"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        lines = ["Configuration:"]
        for key in sorted(self._flatten_dict(self._data).keys()):
            lines.append(f"  {key}: {self.get(key)}")
        return "\n".join(lines)

# Singleton pattern for global config access
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Get or create the global configuration singleton.
    
    Returns:
        Global Config instance
    
    Usage:
        config = get_config()
        config.get('database.path')
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
        # Check for environment config file
        env_config = os.getenv("PROJECT_CONFIG", "config.yaml")
        if os.path.exists(env_config):
            _config_instance.load_from_file(env_config)
        # Apply environment variable overrides
        _apply_env_overrides(_config_instance)
        logger.info("Global configuration initialized")
    return _config_instance

def _apply_env_overrides(config: Config) -> None:
    """Apply environment variable overrides to configuration."""
    env_prefix = "PIPELINE_"
    for key, value in config._flatten_dict(config._data).items():
        env_key = f"{env_prefix}{key.upper().replace('.', '_')}"
        env_value = config.get_env(env_key)
        if env_value is not None and env_value != value:
            config.set(key, env_value)
            logger.debug("Applied env override: %s = %s", env_key, env_value)

@lru_cache(maxsize=1)
def get_cached_config() -> Config:
    """Get cached configuration (useful for testing)."""
    return get_config()

def reset_config() -> None:
    """Reset global configuration (useful for testing)."""
    global _config_instance
    _config_instance = None
    get_cached_config.cache_clear()
    logger.debug("Configuration reset")

# Convenience functions for common access patterns
def get_database_path() -> str:
    """Get the database file path."""
    return get_config().get('database.path')

def get_random_seed() -> int:
    """Get the default random seed for reproducibility."""
    return get_config().get('random_seed.default', 42)

def get_mapping_rate_threshold() -> float:
    """Get the minimum acceptable mapping rate."""
    return get_config().get('thresholds.mapping_rate_min', 0.70)

def get_psi_delta_threshold() -> float:
    """Get the minimum ΔPSI threshold."""
    return get_config().get('thresholds.psi_delta_min', 0.1)

def get_read_coverage_threshold() -> int:
    """Get the minimum read coverage threshold."""
    return get_config().get('thresholds.read_coverage_min', 20)

def get_fdr_threshold() -> float:
    """Get the FDR threshold for statistical significance."""
    return get_config().get('thresholds.fdr_threshold', 0.05)