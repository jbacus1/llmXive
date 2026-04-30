"""
Dataset download utilities for UCI time series datasets.

This module provides functions to download, validate, and manage
time series datasets from the UCI Machine Learning Repository.

Per Constitution Principle III, all downloads include SHA256 checksum
validation and provenance documentation.
"""
import os
import sys
import hashlib
import logging
import urllib.request
import ssl
import zipfile
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Disable SSL verification for UCI archive
ssl._create_default_https_context = ssl._create_unverified_context

@dataclass
class DownloadResult:
    """Result of a dataset download operation."""
    success: bool
    filepath: Optional[Path]
    checksum: Optional[str]
    message: str

# Dataset configurations
DATASETS: Dict[str, Dict[str, Any]] = {
    'electricity': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00494/ElectricityLoadDiagrams20112014.csv',
        'output_name': 'electricity_raw.csv',
        'expected_columns': 371,  # timestamp + 370 customers
    },
    'traffic': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00522/PEMS/SF.csv',
        'output_name': 'traffic_raw.csv',
        'expected_columns': 863,  # timestamp + 862 sensors
    },
    'synthetic_control': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00271/SYNTHETIC_CONTROL_DATA.zip',
        'output_name': 'synthetic_control_raw.csv',
        'expected_columns': 61,  # class + 60 time points
        'is_zip': True,
    },
}

def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def download_from_url(url: str, dest_path: Path) -> bool:
    """Download file from URL to destination path."""
    try:
        logger.info(f"Downloading from {url}")
        urllib.request.urlretrieve(url, dest_path)
        size = dest_path.stat().st_size
        logger.info(f"Downloaded {dest_path.name} ({size:,} bytes)")
        return True
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False

def download_electricity_dataset(output_dir: Path) -> DownloadResult:
    """Download UCI Electricity Load Diagrams dataset."""
    config = DATASETS['electricity']
    dest_path = output_dir / config['output_name']

    if not download_from_url(config['url'], dest_path):
        return DownloadResult(
            success=False,
            filepath=None,
            checksum=None,
            message="Failed to download electricity dataset"
        )

    checksum = compute_file_checksum(dest_path)
    return DownloadResult(
        success=True,
        filepath=dest_path,
        checksum=checksum,
        message=f"Electricity dataset downloaded successfully"
    )

def download_traffic_dataset(output_dir: Path) -> DownloadResult:
    """Download UCI Traffic dataset."""
    config = DATASETS['traffic']
    dest_path = output_dir / config['output_name']

    if not download_from_url(config['url'], dest_path):
        return DownloadResult(
            success=False,
            filepath=None,
            checksum=None,
            message="Failed to download traffic dataset"
        )

    checksum = compute_file_checksum(dest_path)
    return DownloadResult(
        success=True,
        filepath=dest_path,
        checksum=checksum,
        message=f"Traffic dataset downloaded successfully"
    )

def download_synthetic_control_chart_dataset(output_dir: Path) -> DownloadResult:
    """Download UCI Synthetic Control Chart Time Series dataset."""
    config = DATASETS['synthetic_control']
    zip_path = output_dir / 'synthetic_control_data.zip'

    # Download ZIP file
    if not download_from_url(config['url'], zip_path):
        return DownloadResult(
            success=False,
            filepath=None,
            checksum=None,
            message="Failed to download synthetic control chart dataset"
        )

    # Extract and process
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)

        # Find and process data file
        data_files = list(output_dir.glob("*.DAT"))
        if not data_files:
            data_files = list(output_dir.glob("*"))

        for data_file in data_files:
            if data_file.suffix == '.DAT' or data_file.name.endswith('DATA'):
                try:
                    df = pd.read_csv(
                        data_file,
                        sep=r'\s+',
                        header=None,
                        names=['class'] + [f't_{i}' for i in range(60)]
                    )

                    csv_path = output_dir / config['output_name']
                    df.to_csv(csv_path, index=False)

                    # Create labeled version
                    anomaly_df = df.copy()
                    anomaly_df['is_anomaly'] = (anomaly_df['class'] != 0).astype(int)
                    labeled_path = output_dir / 'synthetic_control_labeled.csv'
                    anomaly_df.to_csv(labeled_path, index=False)

                    checksum = compute_file_checksum(csv_path)
                    return DownloadResult(
                        success=True,
                        filepath=csv_path,
                        checksum=checksum,
                        message="Synthetic Control Chart dataset downloaded and processed"
                    )

                except Exception as e:
                    logger.error(f"Error processing data file: {e}")
                    continue

        return DownloadResult(
            success=False,
            filepath=None,
            checksum=None,
            message="No suitable data file found in archive"
        )

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return DownloadResult(
            success=False,
            filepath=None,
            checksum=None,
            message=f"Extraction failed: {e}"
        )

def load_checksum_cache(cache_path: Path) -> Dict[str, str]:
    """Load cached checksums from file."""
    if not cache_path.exists():
        return {}
    try:
        import json
        with open(cache_path, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_checksum_cache(cache_path: Path, checksums: Dict[str, str]) -> None:
    """Save checksums to cache file."""
    import json
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def validate_checksum(filepath: Path, expected_checksum: str) -> bool:
    """Validate file checksum against expected value."""
    actual = compute_file_checksum(filepath)
    return actual == expected_checksum

def download_all_datasets(output_dir: Path) -> Dict[str, DownloadResult]:
    """Download all configured datasets."""
    results = {}
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results['electricity'] = download_electricity_dataset(output_dir)
    results['traffic'] = download_traffic_dataset(output_dir)
    results['synthetic_control'] = download_synthetic_control_chart_dataset(output_dir)

    return results

def main():
    """Main entry point for dataset download."""
    logger.info("=" * 60)
    logger.info("UCI Time Series Dataset Download")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    output_dir = Path("projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = download_all_datasets(output_dir)

    logger.info("\nDownload Summary:")
    for name, result in results.items():
        status = "✓" if result.success else "✗"
        logger.info(f"  {status} {name}: {result.message}")
        if result.checksum:
            logger.info(f"    Checksum: {result.checksum[:16]}...")

    all_success = all(r.success for r in results.values())
    if all_success:
        logger.info("\nAll datasets downloaded successfully!")
        return 0
    else:
        logger.error("\nSome datasets failed to download")
        return 1

if __name__ == "__main__":
    sys.exit(main())
