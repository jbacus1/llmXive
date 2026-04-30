"""
Download UCI Synthetic Control Chart Time Series dataset.

This dataset contains 600 time series of length 60, each belonging to one
of 6 classes. It's suitable for anomaly detection benchmarking as it
includes labeled patterns that can be used as ground truth.

Dataset URL: https://archive.ics.uci.edu/ml/machine-learning-databases/00271/
License: UCI Machine Learning Repository Standard License
"""
import sys
import os
import hashlib
import logging
import urllib.request
import ssl
import zipfile
import pandas as pd
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Disable SSL verification for UCI archive (some networks block it)
ssl._create_default_https_context = ssl._create_unverified_context

# Dataset configuration
DATASET_NAME = "synthetic_control"
DATASET_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00271/SYNTHETIC_CONTROL_DATA.zip"
EXPECTED_CHECKSUM = None  # Will be computed after download
OUTPUT_DIR = Path("projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/raw")
PROCESSED_DIR = Path("projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/processed")

def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def download_dataset(url: str, dest_path: Path) -> bool:
    """Download dataset from URL to destination path."""
    logger.info(f"Downloading {DATASET_NAME} from {url}")
    try:
        urllib.request.urlretrieve(url, dest_path)
        size = dest_path.stat().st_size
        logger.info(f"Downloaded {dest_path.name} ({size:,} bytes)")
        return True
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False

def extract_and_process(zip_path: Path, output_dir: Path) -> bool:
    """Extract ZIP and process into CSV format."""
    try:
        logger.info(f"Extracting {zip_path.name} to {output_dir}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)

        # Find and process the data file
        data_files = list(output_dir.glob("*.DAT"))
        if not data_files:
            data_files = list(output_dir.glob("*"))

        if not data_files:
            logger.error("No data files found in extracted archive")
            return False

        # Process the main data file
        for data_file in data_files:
            if data_file.suffix == '.DAT' or data_file.name.endswith('DATA'):
                logger.info(f"Processing {data_file.name}")

                # Read the data - UCI format has space/tab separated values
                try:
                    df = pd.read_csv(
                        data_file,
                        sep=r'\s+',
                        header=None,
                        names=['class'] + [f't_{i}' for i in range(60)]
                    )

                    # Save as CSV
                    csv_path = output_dir / f"{DATASET_NAME}_raw.csv"
                    df.to_csv(csv_path, index=False)
                    logger.info(f"Saved processed data to {csv_path}")

                    # Create a labeled anomaly version (class 0 = normal, others = anomalous)
                    # For anomaly detection, we treat class 0 as normal baseline
                    anomaly_df = df.copy()
                    anomaly_df['is_anomaly'] = (anomaly_df['class'] != 0).astype(int)
                    anomaly_csv = output_dir / f"{DATASET_NAME}_labeled.csv"
                    anomaly_df.to_csv(anomaly_csv, index=False)
                    logger.info(f"Saved labeled anomaly data to {anomaly_csv}")

                    # Compute checksums
                    raw_checksum = compute_file_checksum(csv_path)
                    labeled_checksum = compute_file_checksum(anomaly_csv)
                    logger.info(f"Raw dataset checksum: {raw_checksum}")
                    logger.info(f"Labeled dataset checksum: {labeled_checksum}")

                    return True

                except Exception as e:
                    logger.error(f"Error processing {data_file.name}: {e}")
                    return False

        logger.error("No suitable data file found")
        return False

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return False

def main():
    """Main entry point for dataset download."""
    logger.info("=" * 60)
    logger.info(f"UCI Synthetic Control Chart Dataset Download")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    # Ensure output directories exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    zip_path = OUTPUT_DIR / f"{DATASET_NAME}_data.zip"

    # Step 1: Download
    if not download_dataset(DATASET_URL, zip_path):
        logger.error("Dataset download failed")
        sys.exit(1)

    # Step 2: Extract and process
    if not extract_and_process(zip_path, OUTPUT_DIR):
        logger.error("Dataset processing failed")
        sys.exit(1)

    # Step 3: Verify output files
    raw_csv = OUTPUT_DIR / f"{DATASET_NAME}_raw.csv"
    labeled_csv = OUTPUT_DIR / f"{DATASET_NAME}_labeled.csv"

    if not raw_csv.exists() or not labeled_csv.exists():
        logger.error("Output files not created")
        sys.exit(1)

    # Log statistics
    df = pd.read_csv(labeled_csv)
    logger.info(f"Total samples: {len(df)}")
    logger.info(f"Anomaly rate: {(df['is_anomaly'].sum() / len(df) * 100):.1f}%")
    logger.info(f"Time series length: {len(df.columns) - 2}")  # minus class and is_anomaly
    logger.info(f"Unique classes: {df['class'].nunique()}")

    logger.info("=" * 60)
    logger.info("Download complete!")
    logger.info("=" * 60)

    # Return success
    return 0

if __name__ == "__main__":
    sys.exit(main())
