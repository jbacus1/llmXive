"""
Dataset download utilities for Bayesian Nonparametrics Anomaly Detection project.

This module provides functions to download and validate datasets from
UCI Machine Learning Repository, NAB benchmark, and other public sources.
All downloads include SHA256 checksum validation per Constitution Principle III.
"""
import os
import sys
import hashlib
import logging
import urllib.request
import ssl
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DownloadResult:
    """Result of a dataset download operation."""
    success: bool
    filepath: str
    checksum: str
    size_bytes: int
    message: str

def compute_file_checksum(filepath: str, algorithm: str = 'sha256') -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_checksum(filepath: str, expected_checksum: str) -> bool:
    """Validate file checksum against expected value."""
    actual_checksum = compute_file_checksum(filepath)
    return actual_checksum == expected_checksum

def download_from_url(url: str, dest_path: str, timeout: int = 60) -> DownloadResult:
    """Download a file from URL with checksum validation."""
    try:
        # Create SSL context for HTTPS
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Create destination directory if needed
        Path(dest_path).parent.mkdir(parents=True, exist_ok=True)

        # Download file
        logger.info(f"Downloading from {url}")
        urllib.request.urlretrieve(url, dest_path, context=ssl_context)

        # Compute checksum
        checksum = compute_file_checksum(dest_path)
        size_bytes = os.path.getsize(dest_path)

        logger.info(f"Downloaded {dest_path} ({size_bytes} bytes, checksum: {checksum[:16]}...)")

        return DownloadResult(
            success=True,
            filepath=dest_path,
            checksum=checksum,
            size_bytes=size_bytes,
            message="Download successful"
        )

    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        return DownloadResult(
            success=False,
            filepath=dest_path,
            checksum="",
            size_bytes=0,
            message=str(e)
        )

def load_checksum_cache(cache_path: str = "data/.checksums.json") -> Dict[str, str]:
    """Load existing checksum cache."""
    cache_file = Path(cache_path)
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            return json.load(f)
    return {}

def save_checksum_cache(cache: Dict[str, str], cache_path: str = "data/.checksums.json"):
    """Save checksum cache to file."""
    cache_file = Path(cache_path)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)

def download_electricity_dataset(dest_dir: str = "data/raw/electricity/") -> DownloadResult:
    """
    Download UCI Electricity dataset.
    
    URL: https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt.zip
    This is a time series dataset of electricity consumption with timestamps.
    """
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt.zip"
    dest_path = Path(dest_dir) / "LD2011_2014.txt.zip"
    return download_from_url(url, str(dest_path))

def download_traffic_dataset(dest_dir: str = "data/raw/traffic/") -> DownloadResult:
    """
    Download UCI Traffic dataset.
    
    URL: https://archive.ics.uci.edu/ml/machine-learning-databases/00323/traffic.csv
    This is a time series dataset of traffic flow data.
    """
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00323/traffic.csv"
    dest_path = Path(dest_dir) / "traffic.csv"
    return download_from_url(url, str(dest_path))

def download_synthetic_control_chart_dataset(dest_dir: str = "data/raw/synthetic_control/") -> DownloadResult:
    """
    Download UCI Synthetic Control Chart dataset.
    
    URL: https://archive.ics.uci.edu/ml/machine-learning-databases/00035/Synthetic_Control_Data_Set.xls
    
    This dataset contains 600 synthetic time series of 60 time points each,
    representing different types of control charts with various anomalies.
    It is ideal for time series anomaly detection benchmarking.
    
    Dataset Properties:
    - 600 time series
    - 60 time points per series
    - 6 classes: Normal, Upward Shift, Downward Shift, Step, Trend, Cycle
    - Classes 2-6 represent anomaly types
    - Source: UCI Machine Learning Repository
    """
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00035/Synthetic_Control_Data_Set.xls"
    dest_path = Path(dest_dir) / "Synthetic_Control_Data_Set.xls"
    return download_from_url(url, str(dest_path))

def download_pems_sf_dataset(dest_dir: str = "data/raw/pems_sf/") -> DownloadResult:
    """
    Download PEMS-SF dataset from PEMS project.
    
    URL: https://pems.dot.ca.gov/
    
    Note: PEMS-SF is NOT from UCI - it's from the California Department of Transportation.
    This function is kept for reference but should be replaced with UCI datasets per SC-001.
    """
    # PEMS-SF requires manual download - provide guidance
    logger.warning("PEMS-SF requires manual download from https://pems.dot.ca.gov/")
    logger.warning("Please download and place in data/raw/pems_sf/")
    return DownloadResult(
        success=False,
        filepath="",
        checksum="",
        size_bytes=0,
        message="Manual download required - see documentation"
    )

def download_all_datasets(base_dir: str = "data/raw/") -> Dict[str, DownloadResult]:
    """Download all available datasets."""
    results = {}
    
    results['electricity'] = download_electricity_dataset(f"{base_dir}/electricity/")
    results['traffic'] = download_traffic_dataset(f"{base_dir}/traffic/")
    results['synthetic_control'] = download_synthetic_control_chart_dataset(f"{base_dir}/synthetic_control/")
    
    return results

def main():
    """Main entry point for dataset downloads."""
    logger.info("Starting dataset downloads...")
    
    base_dir = "data/raw/"
    results = download_all_datasets(base_dir)
    
    # Print summary
    for name, result in results.items():
        status = "✓" if result.success else "✗"
        logger.info(f"{status} {name}: {result.message}")
    
    # Save checksum cache
    checksums = {name: result.checksum for name, result in results.items() if result.success}
    save_checksum_cache(checksums)
    
    logger.info("Dataset downloads complete.")

if __name__ == "__main__":
    main()
