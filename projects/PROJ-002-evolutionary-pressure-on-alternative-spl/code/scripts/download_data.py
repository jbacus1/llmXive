#!/usr/bin/env python3
"""
Download a small public dataset for splicing analysis placeholder.

This script downloads the scikit-learn iris dataset as a placeholder
for splicing-like data. In a full implementation, this would download
real RNA-seq data from ENA/SRA.

Output:
  - data/raw/example.csv: Downloaded dataset
"""
import os
import sys
import urllib.request
from pathlib import Path

# Configuration
URL = "https://raw.githubusercontent.com/scikit-learn/scikit-learn/main/sklearn/datasets/data/iris.csv"
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "example.csv"

def download_file(url: str, output_path: Path) -> bool:
    """Download a file from URL to output_path."""
    try:
        print(f"Downloading from: {url}")
        print(f"Saving to: {output_path}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download the file
        urllib.request.urlretrieve(url, output_path)
        
        # Verify download
        if output_path.exists():
            size = output_path.stat().st_size
            print(f"Download complete. File size: {size} bytes")
            return True
        else:
            print("ERROR: Download failed - file not created")
            return False
    except Exception as e:
        print(f"ERROR: Download failed with exception: {e}")
        return False

def main():
    """Main entry point."""
    print("=" * 60)
    print("Dataset Download Script (T058)")
    print("=" * 60)
    
    success = download_file(URL, OUTPUT_FILE)
    
    if success:
        print("=" * 60)
        print("SUCCESS: Dataset downloaded successfully")
        print("=" * 60)
        return 0
    else:
        print("=" * 60)
        print("FAILURE: Dataset download failed")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
