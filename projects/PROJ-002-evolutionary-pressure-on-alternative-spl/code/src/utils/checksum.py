"""
Checksum utilities for data integrity verification in the pipeline.

Provides functions for computing and verifying file/directory checksums
using MD5 and SHA-256 algorithms. Essential for tracking data provenance
and ensuring reproducibility in the evolutionary splicing analysis pipeline.

Usage:
    from utils.checksum import compute_file_checksum, verify_checksum
  
    checksum = compute_file_checksum("data/sample.bam")
    is_valid = verify_checksum("data/sample.bam", expected_checksum)
"""

import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, Any

CHUNK_SIZE = 8192  # Read files in 8KB chunks for memory efficiency


def compute_file_checksum(
    file_path: str,
    algorithm: str = "sha256"
) -> str:
    """
    Compute checksum for a single file.
    
    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use ('md5' or 'sha256')
    
    Returns:
        Hexadecimal checksum string
    
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If an unsupported algorithm is specified
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if algorithm not in ["md5", "sha256"]:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Use 'md5' or 'sha256'.")
    
    hash_obj = hashlib.md5() if algorithm == "md5" else hashlib.sha256()
    
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def compute_directory_checksum(
    dir_path: str,
    algorithm: str = "sha256",
    recursive: bool = True,
    exclude_patterns: Optional[list] = None
) -> Dict[str, str]:
    """
    Compute checksums for all files in a directory.
    
    Args:
        dir_path: Path to the directory
        algorithm: Hash algorithm to use ('md5' or 'sha256')
        recursive: Whether to include subdirectories
        exclude_patterns: List of filename patterns to exclude
    
    Returns:
        Dictionary mapping relative file paths to checksums
    
    Raises:
        NotADirectoryError: If the path is not a directory
    """
    path = Path(dir_path)
    
    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")
    
    if exclude_patterns is None:
        exclude_patterns = []
    
    checksums: Dict[str, str] = {}
    
    if recursive:
        files = list(path.rglob("*"))
    else:
        files = list(path.glob("*"))
    
    for file_path in files:
        if not file_path.is_file():
            continue
        
        # Check exclusion patterns
        rel_path = file_path.relative_to(path)
        should_exclude = any(
            pattern in str(rel_path) for pattern in exclude_patterns
        )
        
        if should_exclude:
            continue
        
        try:
            checksum = compute_file_checksum(str(file_path), algorithm)
            checksums[str(rel_path)] = checksum
        except FileNotFoundError:
            # Skip files that may have been deleted during scan
            continue
    
    return checksums


def verify_checksum(
    file_path: str,
    expected_checksum: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify a file's checksum against an expected value.
    
    Args:
        file_path: Path to the file to verify
        expected_checksum: Expected checksum value
        algorithm: Hash algorithm to use ('md5' or 'sha256')
    
    Returns:
        True if checksum matches, False otherwise
    
    Raises:
        FileNotFoundError: If the file does not exist
    """
    actual_checksum = compute_file_checksum(file_path, algorithm)
    return actual_checksum.lower() == expected_checksum.lower()


def compute_checksum_for_metadata(
    data: Dict[str, Any],
    algorithm: str = "sha256"
) -> str:
    """
    Compute checksum for a dictionary (e.g., metadata).
    
    Args:
        data: Dictionary to checksum
        algorithm: Hash algorithm to use ('md5' or 'sha256')
    
    Returns:
        Hexadecimal checksum string
    """
    import json

    # Serialize with sorted keys for deterministic output
    serialized = json.dumps(data, sort_keys=True, default=str)
    hash_obj = hashlib.md5() if algorithm == "md5" else hashlib.sha256()
    hash_obj.update(serialized.encode("utf-8"))
    
    return hash_obj.hexdigest()


def compare_checksums(
    checksum1: str,
    checksum2: str
) -> bool:
    """
    Compare two checksums for equality.
    
    Args:
        checksum1: First checksum string
        checksum2: Second checksum string
    
    Returns:
        True if checksums match, False otherwise
    """
    return checksum1.lower().strip() == checksum2.lower().strip()

__all__ = [
    "compute_file_checksum",
    "compute_directory_checksum",
    "verify_checksum",
    "compute_checksum_for_metadata",
    "compare_checksums",
    "CHUNK_SIZE",
]