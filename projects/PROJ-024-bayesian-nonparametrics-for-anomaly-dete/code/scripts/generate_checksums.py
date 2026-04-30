"""
Generate and record SHA256 checksums for all raw and processed data files.

This script scans data/raw/ and data/processed/ directories, computes
SHA256 checksums for all files, and updates the state YAML file with
the checksums per Constitution Principle III.

Usage: python generate_checksums.py
"""
import os
import sys
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.checksum_manager import ChecksumManager, ArtifactEntry

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

STATE_FILE = project_root / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"
DATA_RAW_DIR = project_root / "data" / "raw"
DATA_PROCESSED_DIR = project_root / "data" / "processed"

def compute_file_checksum_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_directory_for_files(directory: Path) -> List[Path]:
    """Recursively scan directory for all files."""
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []

    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            # Skip hidden files and common non-data files
            if filename.startswith('.') or filename.endswith('.md'):
                continue
            file_path = Path(root) / filename
            files.append(file_path)

    return files

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """Load existing state file or create new structure."""
    if state_path.exists():
        with open(state_path, 'r') as f:
            return yaml.safe_load(f) or {}
    else:
        # Create directory if it doesn't exist
        state_path.parent.mkdir(parents=True, exist_ok=True)
        return {
            "project_id": "PROJ-024-bayesian-nonparametrics-for-anomaly-dete",
            "last_updated": None,
            "checksums": {
                "raw": {},
                "processed": {}
            },
            "metadata": {
                "total_files": 0,
                "total_size_bytes": 0
            }
        }

def save_state_file(state_path: Path, state: Dict[str, Any]) -> None:
    """Save state file with checksums."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    logger.info(f"State file saved: {state_path}")

def generate_checksums_for_directory(
    directory: Path,
    state: Dict[str, Any],
    category: str
) -> Tuple[int, int]:
    """
    Generate checksums for all files in directory.

    Returns: (files_processed, errors)
    """
    files = scan_directory_for_files(directory)
    files_processed = 0
    errors = 0

    for file_path in files:
        relative_path = str(file_path.relative_to(project_root))

        try:
            # Compute checksum
            checksum = compute_file_checksum_sha256(file_path)
            file_size = file_path.stat().st_size

            # Update state
            state["checksums"][category][relative_path] = {
                "sha256": checksum,
                "size_bytes": file_size,
                "last_modified": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat()
            }

            files_processed += 1
            state["metadata"]["total_size_bytes"] += file_size
            logger.info(f"  Checksummed: {relative_path} ({file_size} bytes)")

        except Exception as e:
            logger.error(f"  Error processing {relative_path}: {e}")
            errors += 1

    return files_processed, errors

def main():
    """Main entry point - generates checksums for all data files."""
    logger.info("=" * 60)
    logger.info("T068: Generate SHA256 Checksums for Data Files")
    logger.info("=" * 60)

    # Load or create state file
    state = load_state_file(STATE_FILE)
    logger.info(f"State file: {STATE_FILE}")

    # Track total files processed
    total_raw_files = 0
    total_raw_errors = 0
    total_processed_files = 0
    total_processed_errors = 0

    # Generate checksums for raw data
    if DATA_RAW_DIR.exists():
        logger.info(f"\nScanning raw data directory: {DATA_RAW_DIR}")
        total_raw_files, total_raw_errors = generate_checksums_for_directory(
            DATA_RAW_DIR, state, "raw"
        )
    else:
        logger.warning(f"Raw data directory does not exist: {DATA_RAW_DIR}")

    # Generate checksums for processed data
    if DATA_PROCESSED_DIR.exists():
        logger.info(f"\nScanning processed data directory: {DATA_PROCESSED_DIR}")
        total_processed_files, total_processed_errors = generate_checksums_for_directory(
            DATA_PROCESSED_DIR, state, "processed"
        )
    else:
        logger.warning(f"Processed data directory does not exist: {DATA_PROCESSED_DIR}")

    # Update metadata
    state["metadata"]["total_files"] = (
        total_raw_files + total_processed_files
    )
    state["last_updated"] = datetime.now().isoformat()

    # Save updated state
    save_state_file(STATE_FILE, state)

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("CHECKSUM GENERATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Raw data files processed: {total_raw_files}")
    logger.info(f"Raw data errors: {total_raw_errors}")
    logger.info(f"Processed data files: {total_processed_files}")
    logger.info(f"Processed data errors: {total_processed_errors}")
    logger.info(f"Total files: {state['metadata']['total_files']}")
    logger.info(f"Total size: {state['metadata']['total_size_bytes']} bytes")
    logger.info(f"State file updated: {STATE_FILE}")
    logger.info("=" * 60)

    # Exit with error code if there were any errors
    total_errors = total_raw_errors + total_processed_errors
    if total_errors > 0:
        logger.error(f"Completed with {total_errors} errors")
        sys.exit(1)

    logger.info("Checksum generation completed successfully!")
    sys.exit(0)

if __name__ == "__main__":
    main()
