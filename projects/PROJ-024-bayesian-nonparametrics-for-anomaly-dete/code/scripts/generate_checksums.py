"""
Utility functions for computing and managing SHA256 checksums.

Per Constitution Principle III - Data Integrity
"""
import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def compute_file_checksum_sha256(file_path: Path) -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum
        
    Returns:
        Hexadecimal SHA256 hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def scan_directory_for_files(directory: Path, extensions: List[str] = None) -> List[Path]:
    """
    Recursively scan directory for files with given extensions.
    
    Args:
        directory: Directory to scan
        extensions: List of file extensions to include (e.g., ['.csv', '.json'])
        
    Returns:
        List of matching file paths
    """
    if extensions is None:
        extensions = ['.csv', '.json', '.parquet', '.txt', '.tsv', '.npy', '.pkl', '.h5', '.hdf5']
    
    files = []
    for ext in extensions:
        files.extend(directory.rglob(f"*{ext}"))
    return files


def load_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Load state YAML file.
    
    Args:
        state_path: Path to state file
        
    Returns:
        State dictionary
    """
    if state_path.exists():
        with open(state_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}


def save_state_file(state_path: Path, state_data: Dict[str, Any]):
    """
    Save state YAML file.
    
    Args:
        state_path: Path to state file
        state_data: State dictionary to save
    """
    # Ensure parent directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def generate_checksums_for_directory(
    directory: Path,
    output_file: Path,
  extensions: List[str] = None
) -> Dict[str, Any]:
    """
    Generate checksums for all files in a directory.
    
    Args:
        directory: Directory to scan
        output_file: Path to output checksum file
        extensions: List of file extensions to include
        
    Returns:
        Dictionary mapping file paths to checksums
    """
    files = scan_directory_for_files(directory, extensions)
    checksums = {}
    
    for file_path in files:
        rel_path = str(file_path.relative_to(directory))
        checksum = compute_file_checksum_sha256(file_path)
        checksums[rel_path] = {
            "sha256": checksum,
            "size_bytes": file_path.stat().st_size
        }
    
    save_state_file(output_file, {"checksums": checksums})
    return checksums


def verify_checksums(checksums: Dict[str, Any], base_dir: Path) -> Dict[str, bool]:
    """
    Verify checksums for files.
    
    Args:
        checksums: Dictionary mapping file paths to checksum info
        base_dir: Base directory for file paths
        
    Returns:
        Dictionary mapping file paths to verification status
    """
    results = {}
    for rel_path, info in checksums.items():
        file_path = base_dir / rel_path
        if file_path.exists():
            current_checksum = compute_file_checksum_sha256(file_path)
            results[rel_path] = current_checksum == info.get("sha256")
        else:
            results[rel_path] = False
            logger.warning(f"File not found for verification: {rel_path}")
    return results


def main():
    """Main entry point for standalone checksum generation."""
    logger.info("=== Checksum Generation Utility ===")
    logger.info("Use generate_data_checksums.py for project-specific checksum generation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
