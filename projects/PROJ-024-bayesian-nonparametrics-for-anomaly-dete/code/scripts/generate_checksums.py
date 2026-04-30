"""
Generate and verify checksums for project artifacts.

This script provides functionality to:
1. Compute SHA256 checksums for files in specified directories
2. Save checksums to a state YAML file
3. Verify existing checksums against current files
4. Generate checksum cache for downloaded datasets

Usage:
    python code/scripts/generate_checksums.py --generate --output state/checksums.yaml
    python code/scripts/generate_checksums.py --verify --input state/checksums.yaml
"""
import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

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


def scan_directory_for_files(directory: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """Scan directory for files with specified extensions."""
    files = []
    if not directory.exists():
        logger.warning(f"Directory not found: {directory}")
        return files
    
    for file_path in directory.rglob('*'):
        if file_path.is_file():
            if extensions is None or any(file_path.suffix == ext for ext in extensions):
                files.append(file_path)
    
    return files


def load_state_file(state_path: Path) -> Dict[str, Any]:
    """Load state YAML file."""
    if not state_path.exists():
        logger.warning(f"State file not found: {state_path}")
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


def generate_checksums_for_directory(
    directory: Path,
    output_path: Path,
    extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """Generate checksums for all files in a directory."""
    checksums = {}
    files = scan_directory_for_files(directory, extensions)
    
    logger.info(f"Found {len(files)} files in {directory}")
    
    for file_path in files:
        rel_path = file_path.relative_to(directory)
        checksum = compute_file_checksum_sha256(file_path)
        
        if checksum:
          checksums[str(rel_path)] = checksum
          logger.debug(f"Checksum: {rel_path} -> {checksum[:16]}...")
    
    # Save to output file
    state_data = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'directory': str(directory),
        'checksums': checksums
    }
    
    if save_state_file(output_path, state_data):
        logger.info(f"Checksums saved to {output_path}")
    else:
        logger.error(f"Failed to save checksums to {output_path}")
    
    return checksums


def verify_checksums(checksums: Dict[str, str], base_path: Path) -> Tuple[int, int]:
    """Verify checksums against current files."""
    passed = 0
    failed = 0
    
    for rel_path, expected_hash in checksums.items():
        file_path = base_path / rel_path
        actual_hash = compute_file_checksum_sha256(file_path)
        
        if actual_hash == expected_hash:
            passed += 1
            logger.debug(f"Verified: {rel_path}")
        else:
            failed += 1
            logger.error(f"Failed: {rel_path} (expected {expected_hash}, got {actual_hash})")
    
    return passed, failed


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate and verify checksums for project artifacts'
    )
    parser.add_argument(
        '--generate',
        action='store_true',
        help='Generate checksums for directory'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify checksums'
    )
    parser.add_argument(
        '--input',
        type=str,
        help='Input state file for verification'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output state file for generation'
    )
    parser.add_argument(
        '--directory',
        type=str,
        help='Directory to scan for checksums'
    )
    parser.add_argument(
        '--extensions',
        type=str,
        nargs='+',
        help='File extensions to include (e.g., .py .yaml)'
    )
    
    args = parser.parse_args()
    
    if args.generate:
        if not args.directory or not args.output:
            parser.error("--generate requires --directory and --output")
        
        directory = Path(args.directory)
        output = Path(args.output)
        extensions = args.extensions if args.extensions else None
        
        generate_checksums_for_directory(directory, output, extensions)
    
    elif args.verify:
        if not args.input:
            parser.error("--verify requires --input")
        
        state_data = load_state_file(Path(args.input))
        checksums = state_data.get('checksums', {})
        base_path = Path(state_data.get('directory', '.'))
        
        passed, failed = verify_checksums(checksums, base_path)
        logger.info(f"Verification complete: {passed} passed, {failed} failed")
        
        sys.exit(0 if failed == 0 else 1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
