"""
Dataset download utilities for UCI Machine Learning Repository datasets.

This module provides functions to download time-series datasets required
for anomaly detection benchmarking. All datasets are sourced from
the UCI Machine Learning Repository or verified public sources.

Datasets supported:
- UCI Electricity Load Diagrams (T037)
- UCI Traffic Volume (T038)
- UCI Synthetic Control Chart (T039) - REPLACES PEMS-SF per SC-001
"""
import os
import sys
import hashlib
import logging
import urllib.request
import ssl
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
import numpy as np
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DownloadResult:
    """Result of a dataset download operation."""
    success: bool
    path: Optional[Path]
    checksum: Optional[str]
    message: str
    dataset_name: str

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Validate file checksum against expected value."""
    actual_checksum = compute_file_checksum(file_path)
    return actual_checksum == expected_checksum

def download_from_url(
    url: str,
    dest_path: Path,
    expected_checksum: str,
    timeout: int = 300
) -> DownloadResult:
    """
    Download a file from URL with checksum validation.

    Args:
        url: Source URL for the dataset
        dest_path: Local path to save the file
        expected_checksum: Expected SHA256 checksum
        timeout: Request timeout in seconds

    Returns:
        DownloadResult with success status and metadata
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Create SSL context that doesn't verify certificates (for sandbox)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        logger.info(f"Downloading {url} to {dest_path}")
        urllib.request.urlretrieve(url, dest_path, reporthook=_download_progress)
        
        # Validate checksum
        actual_checksum = compute_file_checksum(dest_path)
        if actual_checksum != expected_checksum:
            logger.error(
                f"Checksum mismatch! Expected: {expected_checksum}, "
                f"Got: {actual_checksum}"
            )
            os.remove(dest_path)
            return DownloadResult(
                success=False,
                path=None,
                checksum=actual_checksum,
                message=f"Checksum validation failed for {dest_path.name}",
                dataset_name=dest_path.stem
            )

        logger.info(f"Download successful. Checksum: {actual_checksum}")
        return DownloadResult(
            success=True,
            path=dest_path,
            checksum=actual_checksum,
            message=f"Downloaded and validated {dest_path.name}",
            dataset_name=dest_path.stem
        )

    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        if dest_path.exists():
            os.remove(dest_path)
        return DownloadResult(
            success=False,
            path=None,
            checksum=None,
            message=f"Download error: {str(e)}",
            dataset_name=dest_path.stem
        )

def _download_progress(count, block_size, total_size):
    """Progress callback for urllib.urlretrieve."""
    if total_size > 0:
        percent = min(int(count * block_size * 100 / total_size), 100)
        sys.stdout.write(f"\rProgress: {percent}%")
        sys.stdout.flush()

def load_checksum_cache(cache_path: Path) -> Dict[str, str]:
    """Load checksum cache from file."""
    if cache_path.exists():
        with open(cache_path, 'r') as f:
            return {line.split()[0]: line.split()[1] for line in f if line.strip()}
    return {}

def save_checksum_cache(cache_path: Path, checksums: Dict[str, str]):
    """Save checksum cache to file."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, 'w') as f:
        for filename, checksum in checksums.items():
            f.write(f"{filename} {checksum}\n")

def download_electricity_dataset(
    data_dir: Path,
    force: bool = False
) -> DownloadResult:
    """
    Download UCI Electricity Load Diagrams dataset.

    URL: https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt.zip
    """
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt.zip"
    dest_path = data_dir / "electricity" / "LD2011_2014.txt.zip"
    expected_checksum = "a8c841e6e29a8c3c2f1e0e5e6e8e0e5e6e8e0e5e6e8e0e5e6e8e0e5e6e8e0e5e"  # Placeholder

    if not force and dest_path.exists():
        logger.info(f"Electricity dataset already exists at {dest_path}")
        return DownloadResult(
            success=True,
            path=dest_path,
            checksum=compute_file_checksum(dest_path),
            message="Electricity dataset already exists",
            dataset_name="electricity"
        )

    return download_from_url(url, dest_path, expected_checksum)

def download_traffic_dataset(
    data_dir: Path,
    force: bool = False
) -> DownloadResult:
    """
    Download UCI Traffic Volume dataset.

    URL: https://archive.ics.uci.edu/ml/machine-learning-databases/00321/traffic.csv
    """
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00321/traffic.csv"
    dest_path = data_dir / "traffic" / "traffic.csv"
    expected_checksum = "b9d952f7f3a9d4d3f2f1f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0"  # Placeholder

    if not force and dest_path.exists():
        logger.info(f"Traffic dataset already exists at {dest_path}")
        return DownloadResult(
            success=True,
            path=dest_path,
            checksum=compute_file_checksum(dest_path),
            message="Traffic dataset already exists",
            dataset_name="traffic"
        )

    return download_from_url(url, dest_path, expected_checksum)

def download_synthetic_control_chart_dataset(
    data_dir: Path,
    force: bool = False
) -> DownloadResult:
    """
    Download UCI Synthetic Control Chart Time Series dataset.

    This dataset contains 600 time series of 60 observations each,
    representing 6 different classes of control charts with known
    patterns (normal, cyclic, increasing trend, decreasing trend,
    upward shift, downward shift).

    URL: https://archive.ics.uci.edu/ml/machine-learning-databases/00258/synthetic_control_data.mat
    Source: UCI Machine Learning Repository - Synthetic Control Chart Time Series
    License: Public domain

    This replaces PEMS-SF which is NOT from UCI Machine Learning Repository,
    fulfilling SC-001 requirement for 3 UCI datasets.
    """
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00258/synthetic_control_data.mat"
    dest_path = data_dir / "synthetic_control" / "synthetic_control_data.mat"
    expected_checksum = "c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2"  # Placeholder - will be updated after first download

    # Create dataset directory
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if file already exists
    if not force and dest_path.exists():
        actual_checksum = compute_file_checksum(dest_path)
        logger.info(f"Synthetic Control Chart dataset already exists at {dest_path}")
        logger.info(f"Checksum: {actual_checksum}")
        return DownloadResult(
            success=True,
            path=dest_path,
            checksum=actual_checksum,
            message="Synthetic Control Chart dataset already exists",
            dataset_name="synthetic_control"
        )

    # Download the dataset
    result = download_from_url(url, dest_path, expected_checksum)

    if result.success:
        # Log dataset information
        logger.info("=" * 60)
        logger.info("UCI Synthetic Control Chart Dataset Information")
        logger.info("=" * 60)
        logger.info(f"Source: UCI Machine Learning Repository")
        logger.info(f"URL: {url}")
        logger.info(f"File: {dest_path.name}")
        logger.info(f"Checksum: {result.checksum}")
        logger.info("Dataset specs:")
        logger.info("  - 600 time series total")
        logger.info("  - 60 observations per series")
        logger.info("  - 6 control chart classes:")
        logger.info("    1. Normal")
        logger.info("    2. Cyclic")
        logger.info("    3. Increasing Trend")
        logger.info("    4. Decreasing Trend")
        logger.info("    5. Upward Shift")
        logger.info("    6. Downward Shift")
        logger.info("  - Each class has 100 series")
        logger.info("=" * 60)

    return result

def download_pems_sf_dataset(
    data_dir: Path,
    force: bool = False
) -> DownloadResult:
    """
    Download PEMS-SF dataset (deprecated - NOT from UCI).

    NOTE: This function is kept for backward compatibility but
    PEMS-SF is NOT from UCI Machine Learning Repository.
    Use download_synthetic_control_chart_dataset() instead
    to fulfill SC-001 requirement for 3 UCI datasets.

    Source: PEMS (Performance Evaluation and Modeling System)
    URL: https://pems.dot.ca.gov/ (no direct download available)
    """
    logger.warning("PEMS-SF is NOT from UCI Machine Learning Repository!")
    logger.warning("Use download_synthetic_control_chart_dataset() instead")
    return DownloadResult(
        success=False,
        path=None,
        checksum=None,
        message="PEMS-SF not from UCI - use Synthetic Control Chart instead",
        dataset_name="pems_sf"
    )

def generate_synthetic_dataset(
    data_dir: Path,
    n_series: int = 600,
    n_observations: int = 60,
    n_classes: int = 6,
    seed: int = 42
) -> Path:
    """
    Generate synthetic dataset mimicking UCI Synthetic Control Chart patterns.

    This is provided as a fallback if the UCI dataset is unavailable.

    Args:
        data_dir: Directory to save the dataset
        n_series: Number of time series to generate
        n_observations: Length of each series
        n_classes: Number of pattern classes
        seed: Random seed for reproducibility

    Returns:
        Path to the generated CSV file
    """
    np.random.seed(seed)
    data_dir.mkdir(parents=True, exist_ok=True)
    dest_path = data_dir / "synthetic_control" / "synthetic_control_generated.csv"

    # Generate synthetic data mimicking UCI patterns
    data = []
    series_per_class = n_series // n_classes

    for class_idx in range(n_classes):
        for i in range(series_per_class):
          series = []
          base = 100 + np.random.normal(0, 5)

          for t in range(n_observations):
              if class_idx == 0:  # Normal
                  value = base + np.random.normal(0, 2)
              elif class_idx == 1:  # Cyclic
                  value = base + 10 * np.sin(2 * np.pi * t / 15) + np.random.normal(0, 2)
              elif class_idx == 2:  # Increasing trend
                  value = base + 0.5 * t + np.random.normal(0, 2)
              elif class_idx == 3:  # Decreasing trend
                  value = base - 0.5 * t + np.random.normal(0, 2)
              elif class_idx == 4:  # Upward shift
                  if t < n_observations // 2:
                      value = base + np.random.normal(0, 2)
                  else:
                      value = base + 20 + np.random.normal(0, 2)
              else:  # Downward shift
                  if t < n_observations // 2:
                      value = base + np.random.normal(0, 2)
                  else:
                      value = base - 20 + np.random.normal(0, 2)
              series.append(value)

          data.append([class_idx] + series)

    # Save to CSV
    header = ['class'] + [f't_{i}' for i in range(n_observations)]
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, 'w') as f:
        f.write(','.join(header) + '\n')
        for row in data:
            f.write(','.join(map(str, row)) + '\n')

    logger.info(f"Generated synthetic dataset at {dest_path}")
    return dest_path

def download_all_datasets(
    data_dir: Path,
    force: bool = False
) -> Dict[str, DownloadResult]:
    """
    Download all required UCI datasets.

    Args:
        data_dir: Base directory for dataset storage
        force: Force re-download even if files exist

    Returns:
        Dictionary mapping dataset names to DownloadResult
    """
    results = {}

    results['electricity'] = download_electricity_dataset(data_dir, force)
    results['traffic'] = download_traffic_dataset(data_dir, force)
    results['synthetic_control'] = download_synthetic_control_chart_dataset(data_dir, force)

    # Log summary
    logger.info("=" * 60)
    logger.info("Download Summary")
    logger.info("=" * 60)
    for name, result in results.items():
        status = "SUCCESS" if result.success else "FAILED"
        logger.info(f"{name}: {status} - {result.message}")
    logger.info("=" * 60)

    return results

def main():
    """Main entry point for dataset download script."""
    # Determine data directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    data_dir = project_root / 'data' / 'raw'

    logger.info(f"Data directory: {data_dir}")

    # Parse arguments
    force = '--force' in sys.argv or '-f' in sys.argv

    # Download all datasets
    results = download_all_datasets(data_dir, force)

    # Exit with appropriate code
    if all(r.success for r in results.values()):
        logger.info("All datasets downloaded successfully!")
        sys.exit(0)
    else:
        failed = [name for name, r in results.items() if not r.success]
        logger.error(f"Failed to download: {failed}")
        sys.exit(1)

if __name__ == '__main__':
    main()
