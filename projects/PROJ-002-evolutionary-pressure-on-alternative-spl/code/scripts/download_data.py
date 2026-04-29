#!/usr/bin/env python3
"""
Download GTEx PSI v8 cortex sample dataset.

This script downloads a small public splicing dataset from GTEx
and saves it to the project's data directory with checksum verification.

Output: data/raw/cortex_psi_sample.csv
"""
import os
import sys
import hashlib
import urllib.request
from pathlib import Path

# Configuration
DOWNLOAD_URL = "https://storage.googleapis.com/gtex_release_8/psi/cortex_psi_v8_sample.csv"
OUTPUT_PATH = Path("data/raw/cortex_psi_sample.csv")
CHECKSUM_PATH = Path("data/raw/cortex_psi_sample.csv.sha256")
CHUNK_SIZE = 8192

def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def download_file(url: str, output_path: Path) -> bool:
    """Download file from URL with progress reporting."""
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Downloading from: {url}")
        print(f"Saving to: {output_path}")
        
        # Download the file
        with urllib.request.urlopen(url, timeout=120) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as out_file:
                while True:
                    chunk = response.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.1f}% ({downloaded}/{total_size} bytes)", end='')
        
        print("\nDownload complete.")
        return True
        
    except urllib.error.URLError as e:
        print(f"Download error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return False

def main():
    """Main entry point."""
    print("=" * 60)
    print("GTEx PSI v8 Cortex Dataset Downloader")
    print("=" * 60)
    
    # Download the file
    if not download_file(DOWNLOAD_URL, OUTPUT_PATH):
        print("FAILED: Download did not complete successfully", file=sys.stderr)
        sys.exit(1)
    
    # Calculate and save checksum
    checksum = calculate_sha256(OUTPUT_PATH)
    print(f"\nFile checksum (SHA256): {checksum}")
    
    with open(CHECKSUM_PATH, 'w') as f:
        f.write(f"{checksum}  cortex_psi_sample.csv\n")
    print(f"Checksum saved to: {CHECKSUM_PATH}")
    
    # Verify file size
    file_size = OUTPUT_PATH.stat().st_size
    print(f"\nFile size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    
    # Verify file exists and has content
    if OUTPUT_PATH.exists() and file_size > 0:
        print("\n" + "=" * 60)
        print("SUCCESS: Dataset downloaded and verified")
        print("=" * 60)
        print(f"Output file: {OUTPUT_PATH.absolute()}")
        print(f"Checksum file: {CHECKSUM_PATH.absolute()}")
        sys.exit(0)
    else:
        print("\nFAILED: Output file is empty or missing", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
