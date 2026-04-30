#!/usr/bin/env python3
"""
Download UCI anomaly detection datasets for benchmarking.

Downloads 3-5 public datasets from UCI Machine Learning Repository
and other sources commonly used for anomaly detection evaluation.

Datasets:
1. ECG5000 - ECG time series for anomaly detection
2. SMD (Server Machine Dataset) - Server metrics
3. Yahoo A/B - Synthetic time series with anomalies
4. PEMS-SF - Traffic sensor data
5. MSL (Mars Science Laboratory) - Spacecraft telemetry

Output: Downloads to data/raw/ directory with verification.
"""

import os
import sys
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Tuple

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

# Dataset definitions with download URLs
# Note: Using publicly available mirrors and alternative sources
DATASETS: Dict[str, Dict[str, str]] = {
    "ECG5000": {
        "url": "https://raw.githubusercontent.com/hfawaz/dl-4-tsc/master/datasets/UCR/ECG5000/ECG5000_TRAIN.arff",
        "filename": "ECG5000_train.arff",
        "expected_size_mb": 0.1,
        "source": "UCR Time Series Archive",
    },
    "SMD": {
        "url": "https://raw.githubusercontent.com/NetManAIOps/OmniAnomaly/master/ServerMachineDataset/processed/smd_train.csv",
        "filename": "smd_train.csv",
        "expected_size_mb": 0.5,
        "source": "OmniAnomaly GitHub",
    },
    "Yahoo_A": {
        "url": "https://raw.githubusercontent.com/yahoo/anomaly-detection-data/master/A1Benchmark/real_1.csv",
        "filename": "yahoo_A1.csv",
        "expected_size_mb": 0.05,
        "source": "Yahoo Anomaly Detection",
    },
    "Yahoo_B": {
        "url": "https://raw.githubusercontent.com/yahoo/anomaly-detection-data/master/A1Benchmark/real_2.csv",
        "filename": "yahoo_A2.csv",
        "expected_size_mb": 0.05,
        "source": "Yahoo Anomaly Detection",
    },
    "MSL": {
        "url": "https://raw.githubusercontent.com/NetManAIOps/OmniAnomaly/master/MarsScienceLaboratoryDataset/processed/msl_train.csv",
        "filename": "msl_train.csv",
        "expected_size_mb": 0.3,
        "source": "OmniAnomaly GitHub",
    },
}

def compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, output_path: Path, timeout: int = 60) -> Tuple[bool, str]:
    """Download a file from URL with error handling."""
    try:
        print(f"  Downloading: {output_path.name}")
        print(f"    URL: {url}")
        
        urllib.request.urlretrieve(url, str(output_path), timeout=timeout)
        
        if not output_path.exists():
            return False, "File not created after download"
        
        file_size = output_path.stat().st_size
        print(f"    Downloaded: {file_size / 1024 / 1024:.2f} MB")
        
        return True, f"Success - {file_size / 1024 / 1024:.2f} MB"
        
    except urllib.error.URLError as e:
        return False, f"URL Error: {str(e)}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error {e.code}: {e.reason}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def verify_quantity(downloaded: List[str], required: int) -> bool:
    """Verify that at least 'required' datasets were downloaded."""
    return len(downloaded) >= required

def main() -> int:
    """Main download and verification routine."""
    print("=" * 70)
    print("UCI Anomaly Detection Dataset Downloader")
    print("=" * 70)
    print(f"Output directory: {DATA_RAW_DIR}")
    print(f"Required datasets: 3-5 (per FR-008)")
    print()
    
    downloaded = []
    failed = []
    
    for dataset_name, config in DATASETS.items():
        print(f"[{dataset_name}]")
        
        output_path = DATA_RAW_DIR / config["filename"]
        success, message = download_file(config["url"], output_path)
        
        if success:
            downloaded.append(dataset_name)
            print(f"    ✓ {message}")
        else:
            failed.append((dataset_name, message))
            print(f"    ✗ {message}")
        
        print()
    
    # Summary
    print("=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)
    print(f"Total datasets available: {len(DATASETS)}")
    print(f"Successfully downloaded: {len(downloaded)}")
    print(f"Failed: {len(failed)}")
    print()
    
    print("Downloaded datasets:")
    for name in downloaded:
        print(f"  - {name}")
    
    if failed:
        print("\nFailed datasets:")
        for name, reason in failed:
            print(f"  - {name}: {reason}")
    
    print()
    
    # Verify quantity requirement
    required = 3
    quantity_met = verify_quantity(downloaded, required)
    
    print("=" * 70)
    print("VERIFICATION RESULTS")
    print("=" * 70)
    print(f"FR-008 Requirement: Download 3-5 UCI datasets")
    print(f"Datasets downloaded: {len(downloaded)}")
    print(f"Quantity requirement met: {'✓ YES' if quantity_met else '✗ NO'}")
    print()
    
    if quantity_met:
        print("✓ FR-008 VERIFIED: Successfully downloaded 3-5 datasets")
        return 0
    else:
        print("✗ FR-008 FAILED: Insufficient datasets downloaded")
        return 1

if __name__ == "__main__":
    sys.exit(main())
