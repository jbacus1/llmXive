"""
Update state artifact checksums for Constitution Principle III compliance.

This script scans all tracked artifacts in the state file and records
their SHA256 checksums for reproducibility verification.

Usage:
    python code/scripts/update_state_checksums.py [--update | --verify]

Examples:
    # Update all checksums in state file
    python code/scripts/update_state_checksums.py --update
    
    # Verify existing checksums against current files
    python code/scripts/update_state_checksums.py --verify
"""
import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def compute_file_checksum_sha256(file_path: Path) -> Optional[str]:
    """Compute SHA256 checksum of a file."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        return None


def load_state_file(state_path: Path) -> Dict[str, Any]:
    """Load state YAML file."""
    if not state_path.exists():
        logger.error(f"State file not found: {state_path}")
        return {}
    
    try:
        with open(state_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading state file: {e}")
        return {}


def save_state_file(state_path: Path, state_data: Dict[str, Any]) -> bool:
    """Save state YAML file."""
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        logger.error(f"Error saving state file: {e}")
        return False


def update_artifact_checksums(state_data: Dict[str, Any], project_root: Path) -> Tuple[int, int]:
    """
    Update checksums for all artifacts in state file.
    
    Returns:
        Tuple of (updated_count, failed_count)
    """
    updated = 0
    failed = 0
    
    artifacts = state_data.get('artifacts', [])
    
    for artifact in artifacts:
        artifact_path = project_root / artifact['path']
        checksum = compute_file_checksum_sha256(artifact_path)
        
        if checksum is not None:
            artifact['hash'] = checksum
            artifact['last_verified'] = datetime.utcnow().isoformat() + 'Z'
            updated += 1
            logger.info(f"Updated checksum for: {artifact['path']}")
        else:
            # Keep null hash for missing files
            artifact['last_verified'] = datetime.utcnow().isoformat() + 'Z'
            failed += 1
            logger.warning(f"Could not compute checksum for: {artifact['path']}")
    
    return updated, failed


def verify_artifact_checksums(state_data: Dict[str, Any], project_root: Path) -> Tuple[int, int, List[str]]:
    """
    Verify checksums for all artifacts in state file.
    
    Returns:
        Tuple of (passed_count, failed_count, list of failed paths)
    """
    passed = 0
    failed = 0
    failed_paths = []
    
    artifacts = state_data.get('artifacts', [])
    
    for artifact in artifacts:
        artifact_path = project_root / artifact['path']
        expected_hash = artifact.get('hash')
        
        if expected_hash is None:
            logger.warning(f"No checksum recorded for: {artifact['path']}")
            failed += 1
            failed_paths.append(artifact['path'])
            continue
        
        if not artifact_path.exists():
            logger.error(f"File not found: {artifact['path']}")
            failed += 1
            failed_paths.append(artifact['path'])
            continue
        
        actual_hash = compute_file_checksum_sha256(artifact_path)
        
        if actual_hash == expected_hash:
            passed += 1
            logger.debug(f"Checksum verified: {artifact['path']}")
        else:
            logger.error(f"Checksum mismatch for: {artifact['path']}")
            logger.error(f"  Expected: {expected_hash}")
            logger.error(f"  Actual:   {actual_hash}")
            failed += 1
            failed_paths.append(artifact['path'])
    
    return passed, failed, failed_paths


def update_state_file(state_path: Path, project_root: Path) -> bool:
    """Update state file with current artifact checksums."""
    state_data = load_state_file(state_path)
    
    if not state_data:
        logger.error("Failed to load state file")
        return False
    
    updated, failed = update_artifact_checksums(state_data, project_root)
    
    # Update metadata
    state_data['last_updated'] = datetime.utcnow().isoformat() + 'Z'
    state_data['metadata']['last_update_run'] = datetime.utcnow().isoformat() + 'Z'
    state_data['metadata']['artifacts_updated'] = updated
    state_data['metadata']['artifacts_failed'] = failed
    
    if save_state_file(state_path, state_data):
        logger.info(f"State file updated: {updated} artifacts updated, {failed} failed")
        return True
    else:
        logger.error("Failed to save state file")
        return False


def verify_state_file(state_path: Path, project_root: Path) -> bool:
    """Verify checksums in state file against current files."""
    state_data = load_state_file(state_path)
    
    if not state_data:
        logger.error("Failed to load state file")
        return False
    
    passed, failed, failed_paths = verify_artifact_checksums(state_data, project_root)
    
    total = passed + failed
    logger.info(f"Verification complete: {passed}/{total} artifacts passed")
    
    if failed > 0:
        logger.warning(f"{failed} artifacts failed verification:")
        for path in failed_paths:
            logger.warning(f"  - {path}")
        return False
    
    return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Update or verify state artifact checksums'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Update checksums in state file'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify checksums in state file'
    )
    parser.add_argument(
        '--state-file',
        type=str,
        default=str(STATE_FILE_PATH),
        help='Path to state file (default: state/projects/PROJ-024-*.yaml)'
    )
    
    args = parser.parse_args()
    
    state_path = Path(args.state_file)
    
    if not args.update and not args.verify:
        parser.print_help()
        sys.exit(1)
    
    if args.update:
        success = update_state_file(state_path, PROJECT_ROOT)
        sys.exit(0 if success else 1)
    
    if args.verify:
        success = verify_state_file(state_path, PROJECT_ROOT)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
