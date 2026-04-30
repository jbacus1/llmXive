"""
Checksum Manager Utility
Constitution Principle III: All artifacts must have checksums recorded for verification

This module provides utilities for computing SHA256 checksums of project artifacts
and recording them in the state YAML file for verification purposes.
"""

import hashlib
import os
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class ArtifactEntry:
    """Represents a single artifact in the state registry."""
    path: str
    type: str  # config, script, module, directory, state, data
    sha256: Optional[str] = None
    size_bytes: Optional[int] = None
    recorded_at: Optional[str] = None


@dataclass
class ChecksumResult:
    """Result of a checksum computation."""
    success: bool
    artifact_path: str
    sha256: Optional[str] = None
    size_bytes: Optional[int] = None
    error: Optional[str] = None


class ChecksumManager:
    """
    Manages artifact checksums for Constitution Principle III compliance.
    
    This class provides methods to:
    - Compute SHA256 checksums for files and directories
    - Update the state YAML file with artifact hashes
    - Validate existing checksums against current artifacts
    - Generate validation reports
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize the checksum manager.
        
        Args:
            project_root: Root path of the project
        """
        self.project_root = project_root
        self.state_file = project_root / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"
    
    def compute_sha256(self, file_path: Path) -> str:
        """
        Compute SHA256 hash of a file.
        
        Args:
            file_path: Path to the file
        
        Returns:
            SHA256 hex digest string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def compute_directory_hash(self, dir_path: Path) -> str:
        """
        Compute a combined SHA256 hash for all files in a directory.
        
        Args:
            dir_path: Path to the directory
        
        Returns:
            Combined SHA256 hex digest string
        """
        combined_hash = hashlib.sha256()
        
        for root, dirs, files in sorted(os.walk(dir_path)):
            for filename in sorted(files):
                filepath = Path(root) / filename
                if filepath.is_file():
                    file_hash = self.compute_sha256(filepath)
                    combined_hash.update(file_hash.encode())
        
        return combined_hash.hexdigest()
    
    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes."""
        return file_path.stat().st_size
    
    def get_directory_size(self, dir_path: Path) -> int:
        """Get total size of all files in a directory in bytes."""
        total_size = 0
        for root, dirs, files in os.walk(dir_path):
            for filename in files:
                filepath = Path(root) / filename
                if filepath.is_file():
                    total_size += filepath.stat().st_size
        return total_size
    
    def record_artifact(self, artifact_path: Path, artifact_type: str) -> ChecksumResult:
        """
        Compute and record checksum for a single artifact.
        
        Args:
            artifact_path: Path to the artifact
            artifact_type: Type of artifact (config, script, module, etc.)
        
        Returns:
            ChecksumResult with success status and computed values
        """
        if not artifact_path.exists():
            return ChecksumResult(
                success=False,
                artifact_path=str(artifact_path),
                error=f"Artifact does not exist: {artifact_path}"
            )
        
        try:
            if artifact_path.is_file():
                sha256 = self.compute_sha256(artifact_path)
                size_bytes = self.get_file_size(artifact_path)
            elif artifact_path.is_dir():
                sha256 = self.compute_directory_hash(artifact_path)
                size_bytes = self.get_directory_size(artifact_path)
            else:
                return ChecksumResult(
                    success=False,
                    artifact_path=str(artifact_path),
                    error=f"Unknown artifact type: {artifact_path}"
                )
            
            return ChecksumResult(
                success=True,
                artifact_path=str(artifact_path),
                sha256=sha256,
                size_bytes=size_bytes
            )
        except Exception as e:
            return ChecksumResult(
                success=False,
                artifact_path=str(artifact_path),
                error=str(e)
            )
    
    def load_state(self) -> Dict:
        """Load the current state YAML file."""
        if not self.state_file.exists():
            return {
                "project_id": "PROJ-024-bayesian-nonparametrics-for-anomaly-dete",
                "version": "1.0.0",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "artifacts": [],
                "validation": {
                    "last_check": None,
                    "all_checksums_valid": None,
                    "missing_checksums": [],
                    "invalid_checksums": []
                }
            }
        
        with open(self.state_file, "r") as f:
            return yaml.safe_load(f)
    
    def save_state(self, state: Dict) -> bool:
        """
        Save the state YAML file.
        
        Args:
            state: State dictionary to save
        
        Returns:
            True if save was successful
        """
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w") as f:
                yaml.dump(state, f, default_flow_style=False, sort_keys=False)
            return True
        except Exception as e:
            print(f"Error saving state file: {e}")
            return False
    
    def update_artifact_in_state(self, state: Dict, artifact_path: str, 
                                  sha256: str, size_bytes: int) -> Dict:
        """
        Update a single artifact entry in the state.
        
        Args:
            state: Current state dictionary
            artifact_path: Path of the artifact
            sha256: Computed SHA256 hash
            size_bytes: File size in bytes
        
        Returns:
            Updated state dictionary
        """
        updated_at = datetime.utcnow().isoformat() + "Z"
        
        for artifact in state["artifacts"]:
            if artifact["path"] == artifact_path:
                artifact["sha256"] = sha256
                artifact["size_bytes"] = size_bytes
                artifact["recorded_at"] = updated_at
                break
        
        state["updated_at"] = updated_at
        return state
    
    def record_all_artifacts(self) -> Tuple[int, int]:
        """
        Record checksums for all artifacts defined in the state file.
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        state = self.load_state()
        successful = 0
        failed = 0
        
        for artifact in state["artifacts"]:
            artifact_path = self.project_root / artifact["path"]
            result = self.record_artifact(artifact_path, artifact["type"])
            
            if result.success:
                state = self.update_artifact_in_state(
                    state,
                    artifact["path"],
                    result.sha256,
                    result.size_bytes
                )
                successful += 1
            else:
                failed += 1
                print(f"Failed to record {artifact['path']}: {result.error}")
        
        self.save_state(state)
        return successful, failed
    
    def validate_all_checksums(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate all checksums in the state file against current artifacts.
        
        Returns:
            Tuple of (all_valid, missing_paths, invalid_paths)
        """
        state = self.load_state()
        missing = []
        invalid = []
        
        for artifact in state["artifacts"]:
            artifact_path = self.project_root / artifact["path"]
            stored_hash = artifact.get("sha256")
            
            if stored_hash is None:
                missing.append(artifact["path"])
                continue
            
            if not artifact_path.exists():
                missing.append(artifact["path"])
                continue
            
            try:
                if artifact_path.is_file():
                    current_hash = self.compute_sha256(artifact_path)
                elif artifact_path.is_dir():
                    current_hash = self.compute_directory_hash(artifact_path)
                else:
                    missing.append(artifact["path"])
                    continue
                
                if current_hash != stored_hash:
                    invalid.append(artifact["path"])
            except Exception as e:
                missing.append(artifact["path"])
        
        all_valid = len(missing) == 0 and len(invalid) == 0
        
        state["validation"]["last_check"] = datetime.utcnow().isoformat() + "Z"
        state["validation"]["all_checksums_valid"] = all_valid
        state["validation"]["missing_checksums"] = missing
        state["validation"]["invalid_checksums"] = invalid
        
        self.save_state(state)
        
        return all_valid, missing, invalid
    
    def generate_report(self) -> str:
        """Generate a human-readable validation report."""
        state = self.load_state()
        report_lines = [
            f"Project State Report: {state['project_id']}",
            f"Version: {state['version']}",
            f"Created: {state['created_at']}",
            f"Last Updated: {state['updated_at']}",
            "",
            "Validation Status:",
            f"  Last Check: {state['validation']['last_check']}",
            f"  All Valid: {state['validation']['all_checksums_valid']}",
            "",
            f"Artifacts: {len(state['artifacts'])}",
        ]
        
        valid_count = sum(1 for a in state["artifacts"] if a["sha256"] is not None)
        report_lines.append(f"  With Checksums: {valid_count}")
        report_lines.append(f"  Without Checksums: {len(state['artifacts']) - valid_count}")
        
        if state["validation"]["missing_checksums"]:
            report_lines.append("")
            report_lines.append("Missing Checksums:")
            for path in state["validation"]["missing_checksums"]:
                report_lines.append(f"  - {path}")
        
        if state["validation"]["invalid_checksums"]:
            report_lines.append("")
            report_lines.append("Invalid Checksums:")
            for path in state["validation"]["invalid_checksums"]:
                report_lines.append(f"  - {path}")
        
        return "\n".join(report_lines)

def main():
    """Main entry point for CLI usage."""
    import sys
    
    # Default to project root
    project_root = Path("projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete")
    
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
    
    manager = ChecksumManager(project_root)
    
    if len(sys.argv) > 2:
        command = sys.argv[2]
        
        if command == "record":
            print("Recording all artifact checksums...")
            success, failed = manager.record_all_artifacts()
            print(f"Recorded: {success} successful, {failed} failed")
        elif command == "validate":
            print("Validating all artifact checksums...")
            all_valid, missing, invalid = manager.validate_all_checksums()
            print(f"All valid: {all_valid}")
            print(f"Missing: {len(missing)}")
            print(f"Invalid: {len(invalid)}")
        elif command == "report":
            print(manager.generate_report())
        else:
            print(f"Unknown command: {command}")
            print("Usage: python checksum_manager.py [project_root] [record|validate|report]")
            sys.exit(1)
    else:
        # Default action: record all artifacts
        print("Recording all artifact checksums...")
        success, failed = manager.record_all_artifacts()
        print(f"Recorded: {success} successful, {failed} failed")
        print("")
        print(manager.generate_report())

if __name__ == "__main__":
    main()
