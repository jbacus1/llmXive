"""
Standalone script to download UCI Synthetic Control Chart dataset.

This script provides a convenient entry point for downloading
the UCI Synthetic Control Chart Time Series dataset used in
User Story 2 baseline comparisons.

Usage:
    python download_synthetic_control.py [--force]
"""
import sys
import os
from pathlib import Path
import logging

# Add code directory to path
script_dir = Path(__file__).parent
code_dir = script_dir.parent
sys.path.insert(0, str(code_dir))

from src.data.download_datasets import (
    download_synthetic_control_chart_dataset,
    DownloadResult
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Download the UCI Synthetic Control Chart dataset."""
    # Determine data directory
    project_root = code_dir.parent
    data_dir = project_root / 'data' / 'raw'

    logger.info(f"Data directory: {data_dir}")

    # Parse arguments
    force = '--force' in sys.argv or '-f' in sys.argv

    # Download dataset
    result = download_synthetic_control_chart_dataset(data_dir, force)

    # Report result
    if result.success:
        logger.info(f"✓ {result.message}")
        logger.info(f"  Path: {result.path}")
        logger.info(f"  Checksum: {result.checksum}")
        sys.exit(0)
    else:
        logger.error(f"✗ {result.message}")
        sys.exit(1)

if __name__ == '__main__':
    main()
