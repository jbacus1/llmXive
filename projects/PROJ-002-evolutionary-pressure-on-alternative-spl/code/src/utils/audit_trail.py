"""
Reproducibility Audit Trail Module

Provides utilities for creating and managing reproducibility audit trails
to ensure research outputs can be reproduced and validated.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import hashlib
import subprocess

# Project root directory (adjust based on actual project structure)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
AUDIT_DIR = PROJECT_ROOT / "state" / "projects"


def ensure_audit_directory() -> Path:
    """Create audit directory if it doesn't exist."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    return AUDIT_DIR


def get_git_info() -> Dict[str, Any]:
    """Extract current git repository information."""
    git_info = {
        "commit_hash": "unknown",
        "branch": "unknown",
        "dirty": False
    }

    try:
        # Get commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        if result.returncode == 0:
            git_info["commit_hash"] = result.stdout.strip()

        # Get branch name
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        if result.returncode == 0:
            git_info["branch"] = result.stdout.strip()

        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        git_info["dirty"] = len(result.stdout.strip()) > 0

    except (FileNotFoundError, subprocess.SubprocessError):
        pass  # Git not available or error

    return git_info


def get_environment_info() -> Dict[str, Any]:
    """Extract environment information for reproducibility."""
    import sys
    import platform

    return {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.platform(),
        "dependencies_snapshot": str(AUDIT_DIR / "dependencies_snapshot.txt")
    }


def save_dependencies_snapshot() -> str:
    """Save current dependencies to a snapshot file."""
    snapshot_path = AUDIT_DIR / "dependencies_snapshot.txt"

    try:
        result = subprocess.run(
            ["pip", "freeze"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        if result.returncode == 0:
            with open(snapshot_path, "w") as f:
                f.write(result.stdout)
            return str(snapshot_path)
    except (FileNotFoundError, subprocess.SubprocessError):
        pass

    return str(snapshot_path)


def calculate_checksum(file_path: Path) -> Optional[str]:
    """Calculate SHA256 checksum for a file."""
    if not file_path.exists():
        return None

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (IOError, OSError):
        return None


def create_audit_entry(
    task_id: str,
    user_story: str,
    status: str = "pending",
    random_seeds: Optional[Dict[str, int]] = None,
    data_checksums: Optional[Dict[str, str]] = None,
    notes: Optional[str] = None,
    config_snapshot_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new reproducibility audit entry.

    Args:
        task_id: Identifier for the task being audited
        user_story: Associated user story (US1, US2, US3)
        status: Execution status (pending, success, failure, partial)
        random_seeds: Dictionary of random seed values
        data_checksums: Dictionary of data file checksums
        notes: Optional notes about the execution
        config_snapshot_path: Path to configuration snapshot file

    Returns:
        Complete audit entry dictionary
    """
    audit_entry = {
        "audit_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "project_id": "PROJ-002-evolutionary-pressure-on-alternative-spl",
        "git_info": get_git_info(),
        "environment": get_environment_info(),
        "pipeline_execution": {
            "task_id": task_id,
            "user_story": user_story,
            "start_time": datetime.utcnow().isoformat() + "Z",
            "end_time": None,
            "status": status
        },
        "random_seeds": random_seeds or {
            "global_seed": None,
            "numpy_seed": None,
            "tensorflow_seed": None,
            "pytorch_seed": None
        },
        "data_checksums": data_checksums or {
            "input_data": None,
            "output_data": None
        },
        "config_snapshot": config_snapshot_path,
        "notes": notes
    }

    return audit_entry


def save_audit_entry(audit_entry: Dict[str, Any], task_id: str) -> Path:
    """
    Save an audit entry to the audit directory.

    Args:
        audit_entry: Complete audit entry dictionary
        task_id: Task identifier for filename

    Returns:
        Path to the saved audit file
    """
    ensure_audit_directory()

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"audit_{task_id}_{timestamp}.json"
    filepath = AUDIT_DIR / filename

    with open(filepath, "w") as f:
        json.dump(audit_entry, f, indent=2)

    return filepath


def finalize_audit_entry(
    audit_path: Path,
    end_time: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update and finalize an existing audit entry.

    Args:
        audit_path: Path to the audit file
        end_time: End timestamp (ISO 8601)
        status: Final execution status

    Returns:
        Updated audit entry dictionary
    """
    with open(audit_path, "r") as f:
        audit_entry = json.load(f)

    if end_time:
        audit_entry["pipeline_execution"]["end_time"] = end_time
    if status:
        audit_entry["pipeline_execution"]["status"] = status

    with open(audit_path, "w") as f:
        json.dump(audit_entry, f, indent=2)

    return audit_entry


def list_audit_entries() -> list:
    """List all audit entries in the audit directory."""
    ensure_audit_directory()

    audit_files = sorted(AUDIT_DIR.glob("audit_*.json"))
    return [str(f) for f in audit_files]
