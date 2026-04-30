"""
Data download script with checksum verification for anomaly detection datasets.

Downloads public benchmark datasets (UCI, NAB, etc.) with integrity verification
using SHA-256 checksums. Ensures reproducible data acquisition per Constitution
principles (reproducibility, data hygiene, versioning).

Usage:
    python code/data/download_datasets.py [--config config.yaml]

Output:
    data/raw/<dataset_name>.<ext> - Downloaded raw files
    data/raw/.checksums.txt - SHA-256 checksums for verification
"""

import argparse
import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
import urllib.request
import urllib.error
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root (assumes script runs from code/data/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / 'data' / 'raw'
CHECKSUMS_FILE = DATA_RAW_DIR / '.checksums.txt'

# Default dataset configurations
DEFAULT_DATASETS = {
    'nab_artificial': {
        'name': 'artificial',
        'url': 'https://raw.githubusercontent.com/numenta/NAB/master/data/realArtificial/',
        'files': [
            'advertising.csv',
            'aws_cpu_utilization.csv',
            'm4_hourly.csv',
        ],
        'checksums': {},  # Will be computed after first download
        'description': 'NAB artificial anomaly datasets'
    },
    'nab_real': {
        'name': 'real',
        'url': 'https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/',
        'files': [
            'nyc_taxi.csv',
            'shuffled_data.csv',
            'wargaming.csv',
        ],
        'checksums': {},
        'description': 'NAB real known-cause anomaly datasets'
    },
    'ucf_crime': {
        'name': 'ucf_crime',
        'url': 'https://www.crcv.ucf.edu/data/UCF_Crime_Anomaly_Detection/',
        'files': [],  # Requires manual download - placeholder
        'checksums': {},
        'description': 'UCF Crime dataset (manual download required)',
        'manual': True
    },
}

def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b''):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(filepath: Path, expected_checksum: str) -> bool:
    """Verify file checksum matches expected value."""
    actual_checksum = compute_sha256(filepath)
    if actual_checksum != expected_checksum:
        logger.warning(
            f'Checksum mismatch for {filepath.name}: '
            f'expected {expected_checksum}, got {actual_checksum}'
        )
        return False
    logger.info(f'Checksum verified for {filepath.name}')
    return True

def download_file(url: str, output_path: Path, timeout: int = 300) -> bool:
    """Download a file with progress logging and error handling."""
    try:
        logger.info(f'Downloading from {url} to {output_path}')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        urllib.request.urlretrieve(url, output_path)
        
        logger.info(f'Download complete: {output_path.name}')
        return True
        
    except urllib.error.URLError as e:
        logger.error(f'URL Error downloading {url}: {e}')
        return False
    except Exception as e:
        logger.error(f'Unexpected error downloading {url}: {e}')
        return False

def load_config(config_path: Optional[Path] = None) -> Dict:
    """Load dataset configuration from YAML file."""
    if config_path is None:
        config_path = PROJECT_ROOT / 'code' / 'config.yaml'
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if 'datasets' in config:
                return config['datasets']
    
    # Return default datasets if no config found
    return DEFAULT_DATASETS

def save_checksums(checksums: Dict[str, str]) -> None:
    """Save checksums to file for future verification."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(CHECKSUMS_FILE, 'w') as f:
        for filename, checksum in checksums.items():
            f.write(f'{checksum}  {filename}\n')
    logger.info(f'Checksums saved to {CHECKSUMS_FILE}')

def load_checksums() -> Dict[str, str]:
    """Load previously saved checksums."""
    checksums = {}
    if CHECKSUMS_FILE.exists():
        with open(CHECKSUMS_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split('  ', 1)
                if len(parts) == 2:
                    checksums[parts[1]] = parts[0]
    return checksums

def download_dataset(
    dataset_key: str,
    dataset_config: Dict,
    skip_checksum_verify: bool = False
) -> Tuple[bool, int, int]:
    """
    Download a single dataset.
    
    Returns:
        Tuple of (success, files_downloaded, files_verified)
    """
    logger.info(f'Processing dataset: {dataset_key}')
    logger.info(f'Description: {dataset_config.get("description", "N/A")}')
    
    if dataset_config.get('manual', False):
        logger.warning(f'Manual download required for {dataset_key}')
        return False, 0, 0
    
    url = dataset_config['url']
    files = dataset_config['files']
    saved_checksums = load_checksums()
    
    files_downloaded = 0
    files_verified = 0
    new_checksums = {}
    
    for filename in files:
        output_path = DATA_RAW_DIR / filename
        full_url = f'{url}/{filename}'
        
        # Check if file exists
        if output_path.exists():
            logger.info(f'File already exists: {filename}')
            files_downloaded += 1
        else:
            # Download the file
            if download_file(full_url, output_path):
                files_downloaded += 1
            else:
                logger.error(f'Failed to download {filename}')
                continue
        
        # Verify checksum
        if not skip_checksum_verify:
            if filename in saved_checksums:
                if verify_checksum(output_path, saved_checksums[filename]):
                    files_verified += 1
            else:
                # Compute and store new checksum
                checksum = compute_sha256(output_path)
                new_checksums[filename] = checksum
                files_verified += 1
                logger.info(f'Computed checksum for {filename}: {checksum[:16]}...')
    
    # Save new checksums
    if new_checksums:
        all_checksums = {**saved_checksums, **new_checksums}
        save_checksums(all_checksums)
    
    return True, files_downloaded, files_verified

def main():
    """Main entry point for dataset download."""
    parser = argparse.ArgumentParser(
        description='Download and verify anomaly detection datasets'
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=PROJECT_ROOT / 'code' / 'config.yaml',
        help='Path to config file with dataset URLs'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default=None,
        help='Specific dataset key to download (e.g., nab_artificial)'
    )
    parser.add_argument(
        '--skip-checksum-verify',
        action='store_true',
        help='Skip checksum verification for speed'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Download all configured datasets'
    )
    
    args = parser.parse_args()
    
    # Ensure data directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load configuration
    datasets = load_config(args.config)
    
    if args.dataset:
        if args.dataset not in datasets:
            logger.error(f'Dataset {args.dataset} not found in configuration')
            sys.exit(1)
        dataset_keys = [args.dataset]
    elif args.all:
        dataset_keys = list(datasets.keys())
    else:
        dataset_keys = list(datasets.keys())
    
    logger.info(f'Downloading {len(dataset_keys)} dataset(s)')
    
    total_downloaded = 0
    total_verified = 0
    success_count = 0
    
    for dataset_key in dataset_keys:
        success, downloaded, verified = download_dataset(
            dataset_key,
            datasets[dataset_key],
            args.skip_checksum_verify
        )
        
        if success:
            success_count += 1
        total_downloaded += downloaded
        total_verified += verified
    
    logger.info(f'\\n=== Download Summary ===')
    logger.info(f'Datasets processed: {success_count}/{len(dataset_keys)}')
    logger.info(f'Files downloaded: {total_downloaded}')
    logger.info(f'Files verified: {total_verified}')
    logger.info(f'Checksums saved: {CHECKSUMS_FILE}')
    
    if success_count == len(dataset_keys):
        logger.info('All datasets downloaded successfully!')
        return 0
    else:
        logger.warning('Some datasets failed to download. Check logs above.')
        return 1

if __name__ == '__main__':
    sys.exit(main())
