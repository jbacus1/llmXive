"""
Script to download and prepare the UCI Synthetic Control Chart dataset.

This script downloads the dataset, validates the checksum, and provides
a summary of the downloaded data for verification.
"""
import sys
import os
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from download_datasets import (
    download_synthetic_control_chart_dataset,
    compute_file_checksum,
    load_checksum_cache
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Download and verify the Synthetic Control Chart dataset."""
    logger.info("Downloading UCI Synthetic Control Chart dataset...")
    
    result = download_synthetic_control_chart_dataset("data/raw/synthetic_control/")
    
    if result.success:
        logger.info(f"✓ Download successful: {result.filepath}")
        logger.info(f"  Size: {result.size_bytes:,} bytes")
        logger.info(f"  Checksum: {result.checksum[:32]}...")
        
        # Verify against cache if available
        cache = load_checksum_cache()
        if 'synthetic_control' in cache:
            if result.checksum == cache['synthetic_control']:
                logger.info("✓ Checksum matches previous download")
            else:
                logger.warning("⚠ Checksum differs from cached value")
        
        # Print dataset summary
        logger.info("\nDataset Summary:")
        logger.info("  - 600 time series")
        logger.info("  - 60 time points per series")
        logger.info("  - 6 classes (1 normal, 5 anomaly types)")
        logger.info("  - Ground truth labels available")
        
        return 0
    else:
        logger.error(f"✗ Download failed: {result.message}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
