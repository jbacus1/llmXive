"""
Validate quickstart.md and verify all artifacts hash correctly.

This script:
1. Reads quickstart.md from specs/001-bayesian-nonparametrics-anomaly-detection/
2. Parses artifact references mentioned in the document
3. Verifies each artifact exists on disk
4. Computes SHA256 checksums for each artifact
5. Compares against stored hashes in state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml
6. Outputs a validation report with pass/fail status

Usage:
    python code/scripts/validate_quickstart_artifacts.py

Exit codes:
    0 - All artifacts validated successfully
    1 - One or more artifacts failed validation
"""
import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.checksum_manager import ChecksumManager, ChecksumResult, ArtifactEntry
from utils.streaming import StreamingObservation

@dataclass
class ValidationReport:
    """Report structure for artifact validation results."""
    quickstart_path: str
    total_artifacts: int
    passed: int
    failed: int
    missing: int
    results: List[Dict[str, Any]]
    overall_status: str
    timestamp: str

def compute_file_checksum(filepath: Path) -> Optional[str]:
    """Compute SHA256 checksum of a file."""
    if not filepath.exists():
        return None
    
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error computing checksum for {filepath}: {e}")
        return None

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """Load the project state YAML file containing artifact hashes."""
    if not state_path.exists():
        return {}
    
    try:
        with open(state_path, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading state file {state_path}: {e}")
        return {}

def load_quickstart_doc(quickstart_path: Path) -> str:
    """Load the quickstart.md document."""
    if not quickstart_path.exists():
        raise FileNotFoundError(f"quickstart.md not found at {quickstart_path}")
    
    with open(quickstart_path, "r", encoding="utf-8") as f:
        return f.read()

def parse_artifact_references(quickstart_content: str) -> List[str]:
    """
    Parse artifact references from quickstart.md.
    
    Looks for patterns like:
    - File paths in code blocks
    - Explicit artifact mentions in text
    - Config file references
    """
    artifacts = []
    
    # Common artifact patterns to look for
    patterns = [
        "code/requirements.txt",
        "code/config.yaml",
        "data/raw/",
        "data/processed/",
        "specs/001-bayesian-nonparametrics-anomaly-detection/research.md",
        "specs/001-bayesian-nonparametrics-anomaly-detection/data-model.md",
        "specs/001-bayesian-nonparametrics-anomaly-detection/quickstart.md",
        "code/models/dp_gmm.py",
        "code/models/anomaly_score.py",
        "code/models/time_series.py",
        "code/utils/streaming.py",
        "code/baselines/arima.py",
        "code/baselines/moving_average.py",
        "code/evaluation/metrics.py",
        "code/evaluation/plots.py",
        "code/utils/threshold.py",
        "state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml",
    ]
    
    for pattern in patterns:
        if pattern in quickstart_content:
            artifacts.append(pattern)
    
    # Also look for code block references
    lines = quickstart_content.split('\n')
    for line in lines:
        # Look for file path patterns
        if 'code/' in line or 'data/' in line or 'specs/' in line or 'state/' in line:
            line = line.strip()
            if line.endswith(('.py', '.yaml', '.txt', '.md', '.csv', '.json')):
                if line not in artifacts:
                    artifacts.append(line)
    
    return artifacts

def validate_artifact(
    artifact_path: Path,
    expected_checksum: Optional[str],
    project_root: Path
) -> Dict[str, Any]:
    """
    Validate a single artifact: check existence and compute/compare checksum.
    """
    result = {
        "path": str(artifact_path),
        "exists": False,
        "checksum": None,
        "expected_checksum": expected_checksum,
        "status": "missing",
        "error": None
    }
    
    if not artifact_path.exists():
        result["error"] = "File does not exist"
        return result
    
    result["exists"] = True
    computed_checksum = compute_file_checksum(artifact_path)
    result["checksum"] = computed_checksum
    
    if computed_checksum is None:
        result["status"] = "error"
        result["error"] = "Could not compute checksum"
        return result
    
    if expected_checksum is None:
        result["status"] = "passed_no_expected"
        result["error"] = None
        return result
    
    if computed_checksum == expected_checksum:
        result["status"] = "passed"
        result["error"] = None
    else:
        result["status"] = "failed"
        result["error"] = f"Checksum mismatch: expected {expected_checksum[:16]}..., got {computed_checksum[:16]}..."
    
    return result

def validate_quickstart_artifacts(
    project_root: Path,
    quickstart_rel_path: str = "specs/001-bayesian-nonparametrics-anomaly-detection/quickstart.md",
    state_rel_path: str = "state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"
) -> ValidationReport:
    """
    Main validation function that orchestrates the entire artifact validation process.
    """
    import time
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    quickstart_path = project_root / quickstart_rel_path
    state_path = project_root / state_rel_path
    
    print("=" * 70)
    print("Artifact Validation Report")
    print("=" * 70)
    print(f"Quickstart document: {quickstart_path}")
    print(f"State file: {state_path}")
    print(f"Timestamp: {timestamp}")
    print()
    
    # Load documents
    try:
        quickstart_content = load_quickstart_doc(quickstart_path)
    except FileNotFoundError as e:
        return ValidationReport(
            quickstart_path=str(quickstart_path),
            total_artifacts=0,
            passed=0,
            failed=0,
            missing=0,
            results=[],
            overall_status="failed",
            timestamp=timestamp
        )
    
    # Load state file
    state_data = load_state_file(state_path)
    stored_checksums = state_data.get("artifacts", {}) if state_data else {}
    
    # Parse artifact references
    artifact_paths = parse_artifact_references(quickstart_content)
    
    print(f"Found {len(artifact_paths)} artifact references in quickstart.md")
    print("-" * 70)
    
    # Validate each artifact
    results = []
    passed = 0
    failed = 0
    missing = 0
    
    for artifact_rel_path in artifact_paths:
        artifact_path = project_root / artifact_rel_path
        
        # Get expected checksum from state file if available
        expected_checksum = stored_checksums.get(artifact_rel_path)
        
        result = validate_artifact(artifact_path, expected_checksum, project_root)
        results.append(result)
        
        if result["status"] == "passed" or result["status"] == "passed_no_expected":
            passed += 1
            print(f"✓ PASS: {artifact_rel_path}")
        elif result["status"] == "failed":
            failed += 1
            print(f"✗ FAIL: {artifact_rel_path} - {result['error']}")
        elif result["status"] == "missing":
            missing += 1
            print(f"✗ MISSING: {artifact_rel_path}")
        else:
            failed += 1
            print(f"✗ ERROR: {artifact_rel_path} - {result['error']}")
    
    # Summary
    print("-" * 70)
    total = passed + failed + missing
    overall_status = "passed" if failed == 0 and missing == 0 else "failed"
    
    print(f"SUMMARY:")
    print(f"  Total artifacts: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Missing: {missing}")
    print(f"  Overall: {overall_status.upper()}")
    print("=" * 70)
    
    return ValidationReport(
        quickstart_path=str(quickstart_path),
        total_artifacts=total,
        passed=passed,
        failed=failed,
        missing=missing,
        results=results,
        overall_status=overall_status,
        timestamp=timestamp
    )

def save_validation_report(report: ValidationReport, output_path: Path) -> None:
    """Save the validation report to JSON for audit trail."""
    report_dict = {
        "quickstart_path": report.quickstart_path,
        "total_artifacts": report.total_artifacts,
        "passed": report.passed,
        "failed": report.failed,
        "missing": report.missing,
        "overall_status": report.overall_status,
        "timestamp": report.timestamp,
        "results": report.results
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2)
    
    print(f"\nReport saved to: {output_path}")

def main():
    """Entry point for the validation script."""
    print("Starting artifact validation...\n")
    
    report = validate_quickstart_artifacts(PROJECT_ROOT)
    
    # Save report
    report_path = PROJECT_ROOT / "code" / "validation_reports" / "quickstart_validation.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    save_validation_report(report, report_path)
    
    # Exit with appropriate code
    if report.overall_status == "passed":
        print("\n✓ All artifacts validated successfully!")
        sys.exit(0)
    else:
        print(f"\n✗ Validation failed: {report.failed} failed, {report.missing} missing")
        sys.exit(1)

if __name__ == "__main__":
    main()
