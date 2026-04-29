"""
Configuration constants for Climate-Smart Agricultural Practices project.

Principle I Compliance: All sensitive configuration is loaded from environment
variables. Never commit API keys or credentials to version control.

Usage:
    from src.config.constants import API_KEY, DATA_ROOT, CLIMATE_DATA_CONFIG
"""

import os
from pathlib import Path

# ============================================================================
# PROJECT STRUCTURE
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Data directories
DATA_ROOT = PROJECT_ROOT / "data"
DATA_RAW = DATA_ROOT / "raw"
DATA_PROCESSED = DATA_ROOT / "processed"
DATA_CACHE = DATA_ROOT / "cache"
DATA_INTERIM = DATA_ROOT / "interim"

# Output directories
OUTPUT_ROOT = PROJECT_ROOT / "output"
OUTPUT_REPORTS = OUTPUT_ROOT / "reports"
OUTPUT_VISUALIZATIONS = OUTPUT_ROOT / "visualizations"
OUTPUT_MODELS = OUTPUT_ROOT / "models"

# Contract and schema directories
CONTRACTS_ROOT = PROJECT_ROOT / "contracts"
CONTRACTS_DATASET = CONTRACTS_ROOT / "dataset.schema.yaml"
CONTRACTS_OUTPUT = CONTRACTS_ROOT / "output.schema.yaml"

# Ensure directories exist
for directory in [DATA_ROOT, DATA_RAW, DATA_PROCESSED, DATA_CACHE, DATA_INTERIM,
                  OUTPUT_ROOT, OUTPUT_REPORTS, OUTPUT_VISUALIZATIONS, OUTPUT_MODELS,
                  CONTRACTS_ROOT]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# API CONFIGURATION (Principle I: Environment Variables Only)
# ============================================================================

# OpenWeatherMap API
OPENWEATHERMAP_API_URL = "https://api.openweathermap.org/data/2.5"
OPENWEATHERMAP_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY", "")

# USGS EarthExplorer API
USGS_API_URL = "https://earthexplorer.usgs.gov/api"
USGS_API_KEY = os.environ.get("USGS_API_KEY", "")

# ============================================================================
# CLIMATE DATA CONFIGURATION
# ============================================================================

CLIMATE_DATA_CONFIG = {
    "temperature": {
        "unit": "celsius",
        "min_value": -50,
        "max_value": 60,
    },
    "precipitation": {
        "unit": "mm",
        "min_value": 0,
        "max_value": 1000,
    },
    "humidity": {
        "unit": "percent",
        "min_value": 0,
        "max_value": 100,
    },
    "time_range": {
        "min_years_back": 10,
        "max_years_back": 50,
    }
}

# ============================================================================
# REMOTE SENSING CONFIGURATION
# ============================================================================

REMOTE_SENSING_CONFIG = {
    "satellite_sources": ["landsat", "sentinel-2"],
    "max_resolution_meters": 30,
    "min_cloud_cover_percent": 20,
    "time_range_years": 10,
    "index_types": ["ndvi", "evi", "ndwi", "ndbi"],
}

# ============================================================================
# SURVEY DATA CONFIGURATION
# ============================================================================

SURVEY_DATA_CONFIG = {
    "max_records_per_batch": 5000,
    "timeout_seconds": 300,
    "required_fields": ["location", "crop_type", "yield_data"],
    "optional_fields": ["soil_type", "irrigation_method", "fertilizer_use"],
}

# ============================================================================
# PROCESSING THRESHOLDS
# ============================================================================

PROCESSING_CONFIG = {
    "min_valid_data_percent": 70,
    "max_null_value_percent": 30,
    "outlier_std_threshold": 3.0,
    "min_sample_size": 100,
}

# ============================================================================
# CACHE CONFIGURATION
# ============================================================================

CACHE_CONFIG = {
    "database_path": str(DATA_CACHE / "cache.db"),
    "default_ttl_days": 7,
    "max_size_mb": 1024,
    "enabled": True,
}

# ============================================================================
# ERROR HANDLING & RETRY CONFIGURATION
# ============================================================================

RETRY_CONFIG = {
    "max_retries": 3,
    "retry_delay_seconds": 1,
    "exponential_backoff": True,
    "retryable_status_codes": [408, 429, 500, 502, 503, 504],
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_path": str(PROJECT_ROOT / "logs" / "app.log"),
    "console_enabled": True,
    "file_enabled": True,
    "max_file_size_mb": 10,
    "backup_count": 5,
}

# ============================================================================
# PRINCIPLE I COMPLIANCE HELPERS
# ============================================================================

def get_env_variable(name: str, default: str = None, required: bool = False) -> str:
    """
    Safely retrieve environment variable.
    
    Args:
        name: Environment variable name
        default: Default value if not set
        required: If True, raises error when not set
    
    Returns:
        Environment variable value or default
    
    Raises:
        ValueError: If required and not set
    """
    value = os.environ.get(name, default)
    if required and not value:
        raise ValueError(f"Required environment variable '{name}' is not set")
    return value

def validate_api_keys() -> bool:
    """
    Validate that required API keys are configured (Principle I compliance).
    
    Returns:
        True if all required keys are present, False otherwise
    """
    required_keys = ["OPENWEATHERMAP_API_KEY", "USGS_API_KEY"]
    missing_keys = [key for key in required_keys if not os.environ.get(key)]
    
    if missing_keys:
        print(f"WARNING: Missing API keys: {', '.join(missing_keys)}")
        print("Set these environment variables before running data collection.")
        return False
    return True

# ============================================================================
# VERSION INFO
# ============================================================================

VERSION = "1.0.0"
PROJECT_NAME = "climate-smart-agriculture"
PYTHON_VERSION_REQUIRED = "3.11"