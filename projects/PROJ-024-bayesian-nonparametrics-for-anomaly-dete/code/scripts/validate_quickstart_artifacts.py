"""
Validate quickstart.md artifacts and verify SHA256 checksums.

This script:
1. Reads quickstart.md from specs/001-bayesian-nonparametrics-anomaly-detection/
2. Parses artifact references (file paths, data files, etc.)
3. Computes SHA256 checksums for all referenced artifacts
4. Compares against stored checksums in state/projects/PROJ-024-*.yaml
5. Generates a validation report with pass/fail status
"""
import os
import sys
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict, field
import yaml

@dataclass
class ValidationReport:
    """Validation report for quickstart artifacts."""
    quickstart_path: str
    total_artifacts: int
    passed: int
    failed: int
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = ""
    overall_status: str = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

def compute_file_checksum(filepath: Path, algorithm: str = "sha256") -> str:
    """Compute SHA256 checksum of a file."""
    if not filepath.exists():
        return "FILE_NOT_FOUND"
    
    hash_obj = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """Load state file containing artifact checksums."""
    if not state_path.exists():
        return {}
    
    with open(state_path, "r") as f:
        return yaml.safe_load(f)

def load_quickstart_doc(quickstart_path: Path) -> str:
    """Load quickstart.md content."""
    if not quickstart_path.exists():
        raise FileNotFoundError(f"quickstart.md not found at {quickstart_path}")
    
    with open(quickstart_path, "r", encoding="utf-8") as f:
        return f.read()

def parse_artifact_references(content: str) -> List[str]:
    """Parse artifact file paths from quickstart.md content."""
    artifacts = []
    
    # Match file paths in markdown links [text](path)
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    for match in re.finditer(link_pattern, content):
        path = match.group(2)
        if path.startswith(("http://", "https://")):
            continue  # Skip URLs
        if path.endswith((".md", ".yaml", ".txt", ".py", ".csv", ".json", ".png")):
            artifacts.append(path)
    
    # Match inline code paths `path/to/file`
    code_pattern = r'`([^`]+)`'
    for match in re.finditer(code_pattern, content):
        path = match.group(1)
        if path.startswith(("http://", "https://")):
            continue
        if any(path.endswith(ext) for ext in [".md", ".yaml", ".txt", ".py", ".csv", ".json", ".png", ".log"]):
            if path not in artifacts:
                artifacts.append(path)
    
    # Match common artifact patterns
    path_patterns = [
        r'code/[\w/-]+\.(py|yaml|txt|csv)',
        r'data/[\w/-]+\.(csv|json|txt)',
        r'specs/[\w/-]+\.md',
        r'state/[\w/-]+\.yaml',
        r'tests/[\w/-]+\.py',
        r'paper/[\w/-]+\.(png|pdf)',
    ]
    
    for pattern in path_patterns:
        for match in re.finditer(pattern, content):
            path = match.group(0)
            if path not in artifacts:
                artifacts.append(path)
    
    return list(set(artifacts))

def get_required_artifacts(quickstart_content: str) -> List[str]:
    """Get list of required artifacts from quickstart.md."""
    return parse_artifact_references(quickstart_content)

def validate_artifact(
    artifact_path: Path,
    expected_checksum: Optional[str] = None,
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """Validate a single artifact."""
    result = {
        "path": str(artifact_path),
        "exists": artifact_path.exists(),
        "checksum": None,
        "expected_checksum": expected_checksum,
        "status": "unknown",
        "message": ""
    }
    
    if not artifact_path.exists():
        result["status"] = "missing"
        result["message"] = "Artifact file not found"
        return result
    
    result["checksum"] = compute_file_checksum(artifact_path)
    
    if expected_checksum is None:
        result["status"] = "no_checksum_reference"
        result["message"] = "No checksum reference found in state file"
        return result
    
    if result["checksum"] == expected_checksum:
        result["status"] = "valid"
        result["message"] = "Checksum matches"
    else:
        result["status"] = "checksum_mismatch"
        result["message"] = f"Checksum mismatch: got {result['checksum'][:16]}..., expected {expected_checksum[:16]}..."
    
    return result

def validate_quickstart_artifacts(
    project_root: Path,
    quickstart_rel_path: str = "specs/001-bayesian-nonparametrics-anomaly-detection/quickstart.md",
    state_rel_path: str = "state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"
) -> ValidationReport:
    """Main validation function."""
    from datetime import datetime
    
    quickstart_path = project_root / quickstart_rel_path
    state_path = project_root / state_rel_path
    
    # Load quickstart document
    try:
        quickstart_content = load_quickstart_doc(quickstart_path)
    except FileNotFoundError as e:
        report = ValidationReport(
            quickstart_path=str(quickstart_path),
            total_artifacts=0,
            passed=0,
            failed=1,
            timestamp=datetime.now().isoformat(),
            overall_status="failed"
        )
        report.artifacts.append({
            "path": str(quickstart_path),
            "status": "error",
            "message": str(e)
        })
        return report
    
    # Load state file for checksums
    state_data = load_state_file(state_path)
    
    # Parse artifact references
    required_artifacts = get_required_artifacts(quickstart_content)
    
    # Validate each artifact
    report = ValidationReport(
        quickstart_path=str(quickstart_path),
        total_artifacts=len(required_artifacts),
        passed=0,
        failed=0,
        timestamp=datetime.now().isoformat(),
        overall_status="pending"
    )
    
    for artifact_rel_path in required_artifacts:
        artifact_path = project_root / artifact_rel_path
        
        # Get expected checksum from state file
        expected_checksum = None
        if state_data and "artifacts" in state_data:
            for artifact_entry in state_data["artifacts"]:
                if artifact_entry.get("path") == artifact_rel_path:
                    expected_checksum = artifact_entry.get("checksum")
                    break
        
        validation_result = validate_artifact(
            artifact_path,
            expected_checksum=expected_checksum,
            project_root=project_root
        )
        
        report.artifacts.append(validation_result)
        
        if validation_result["status"] == "valid":
            report.passed += 1
        else:
            report.failed += 1
    
    # Set overall status
    if report.failed == 0 and report.total_artifacts > 0:
        report.overall_status = "passed"
    elif report.failed == report.total_artifacts:
        report.overall_status = "failed"
    else:
        report.overall_status = "partial"
    
    return report

def save_validation_report(report: ValidationReport, output_path: Path) -> None:
    """Save validation report to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report.to_json())

def main():
    """Entry point for artifact validation."""
    # Determine project root
    project_root = Path(__file__).parent.parent.parent
    
    print(f"Validating quickstart artifacts in {project_root}")
    print("=" * 60)
    
    # Run validation
    report = validate_quickstart_artifacts(project_root)
    
    # Print summary
    print(f"\nValidation Summary:")
    print(f"  Quickstart: {report.quickstart_path}")
    print(f"  Total artifacts: {report.total_artifacts}")
    print(f"  Passed: {report.passed}")
    print(f"  Failed: {report.failed}")
    print(f"  Status: {report.overall_status}")
    
    # Print detailed results
    print(f"\nArtifact Details:")
    for artifact in report.artifacts:
        status_icon = "✓" if artifact["status"] == "valid" else "✗"
        print(f"  {status_icon} {artifact['path']}: {artifact['status']}")
        if artifact.get("message"):
            print(f"      {artifact['message']}")
    
    # Save report
    output_path = project_root / "state" / "validation_reports" / "quickstart_validation.json"
    save_validation_report(report, output_path)
    print(f"\nReport saved to: {output_path}")
    
    # Exit with appropriate code
    if report.overall_status == "passed":
        print("\n✓ All artifacts validated successfully")
        sys.exit(0)
    else:
        print(f"\n✗ Validation failed: {report.failed} artifact(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
