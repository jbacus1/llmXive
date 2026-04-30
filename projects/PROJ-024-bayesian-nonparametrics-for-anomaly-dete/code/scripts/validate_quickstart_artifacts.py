#!/usr/bin/env python3
"""
Validate Quickstart Artifacts Script (T057/T065)

Purpose: Verify all artifacts referenced in quickstart.md exist and
         have correct checksums recorded in state/projects/PROJ-024-*.yaml

Exit Codes:
  0 - All artifacts validated successfully
  1 - Validation failed (missing artifacts, checksum mismatch, etc.)

Usage: python code/scripts/validate_quickstart_artifacts.py
       (no arguments required - does full validation on invocation)
"""

import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import logging
import yaml
from dataclasses import dataclass, field, asdict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root is 3 levels up from this script
SCRIPT_DIR = Path(__file__).parent.resolve()
CODE_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = CODE_DIR.parent

# Path constants
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"
QUICKSTART_DOC_PATH = PROJECT_ROOT / "specs" / "001-bayesian-nonparametrics-anomaly-detection" / "quickstart.md"
DATA_DIR = PROJECT_ROOT / "data"
RESEARCH_DOC_PATH = PROJECT_ROOT / "specs" / "001-bayesian-nonparametrics-anomaly-detection" / "research.md"
DATA_MODEL_DOC_PATH = PROJECT_ROOT / "specs" / "001-bayesian-nonparametrics-anomaly-detection" / "data-model.md"

@dataclass
class ValidationReport:
    """Validation report for quickstart artifacts"""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    project_id: str = "PROJ-024-bayesian-nonparametrics-for-anomaly-dete"
    total_artifacts: int = 0
    validated_artifacts: int = 0
    failed_artifacts: int = 0
    missing_artifacts: List[str] = field(default_factory=list)
    checksum_mismatches: List[Dict[str, Any]] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, success, failure
    details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

def compute_file_checksum(file_path: Path) -> Optional[str]:
    """Compute SHA256 checksum of a file"""
    if not file_path.exists():
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

def load_state_file(state_path: Path) -> Optional[Dict[str, Any]]:
    """Load state YAML file with artifact checksums"""
    if not state_path.exists():
        logger.warning(f"State file not found: {state_path}")
        return None
    
    try:
        with open(state_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading state file {state_path}: {e}")
        return None

def load_quickstart_doc(quickstart_path: Path) -> Optional[str]:
    """Load quickstart.md document content"""
    if not quickstart_path.exists():
        logger.warning(f"Quickstart document not found: {quickstart_path}")
        return None
    
    try:
        with open(quickstart_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading quickstart document {quickstart_path}: {e}")
        return None

def parse_artifact_references(content: str) -> List[Dict[str, str]]:
    """Parse artifact references from quickstart.md content"""
    artifacts = []
    
    # Common artifact patterns to look for
    patterns = [
        # Code files
        r'code/(?:scripts|models|utils|baselines|evaluation|data)/[\w_\.]+\.py',
        # Config files
        r'code/config\.yaml',
        # Data files
        r'data/(?:raw|processed)/[\w_\.]+(?:\.csv|\.json|\.txt)',
        # State files
        r'state/projects/[\w\-]+\.yaml',
        # Spec files
        r'specs/[\w\-]+/[\w_\-]+\.md',
    ]
    
    import re
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            artifacts.append({
                'path': match,
                'type': 'file'
            })
    
    # Also look for explicit artifact mentions
    explicit_patterns = [
        r'[\'"]([\w/\-\.]+)[\'"]',
        r'\*\*([^\*]+)\*\*',
    ]
    
    for pattern in explicit_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if any(ext in match for ext in ['.py', '.yaml', '.csv', '.json', '.md', '.txt']):
                if not any(a['path'] == match for a in artifacts):
                    artifacts.append({
                        'path': match,
                        'type': 'file'
                    })
    
    return artifacts

def validate_artifact(
    artifact_path: Path,
    expected_checksum: Optional[str],
    report: ValidationReport
) -> bool:
    """Validate a single artifact exists and checksum matches"""
    artifact_name = str(artifact_path.relative_to(PROJECT_ROOT)) if artifact_path.is_relative_to(PROJECT_ROOT) else artifact_path.name
    
    if not artifact_path.exists():
        report.missing_artifacts.append(artifact_name)
        report.failed_artifacts += 1
        report.details.append({
            'artifact': artifact_name,
            'status': 'missing',
            'message': f"File does not exist: {artifact_path}"
        })
        logger.error(f"Missing artifact: {artifact_name}")
        return False
    
    actual_checksum = compute_file_checksum(artifact_path)
    
    if expected_checksum is not None and actual_checksum != expected_checksum:
        report.checksum_mismatches.append({
            'artifact': artifact_name,
            'expected': expected_checksum,
            'actual': actual_checksum
        })
        report.failed_artifacts += 1
        report.details.append({
            'artifact': artifact_name,
            'status': 'checksum_mismatch',
            'expected': expected_checksum[:16] + '...' if expected_checksum else None,
            'actual': actual_checksum[:16] + '...' if actual_checksum else None
        })
        logger.error(f"Checksum mismatch for {artifact_name}")
        return False
    
    report.validated_artifacts += 1
    report.details.append({
        'artifact': artifact_name,
        'status': 'valid',
        'checksum': actual_checksum[:16] + '...' if actual_checksum else None
    })
    logger.info(f"Validated artifact: {artifact_name}")
    return True

def get_required_artifacts() -> List[Tuple[Path, Optional[str]]]:
    """
    Return list of required artifacts with their expected checksums.
    
    This is the core validation logic - it checks that all artifacts
    mentioned in quickstart.md and required by the project actually exist.
    """
    artifacts = []
    
    # Load state file for expected checksums
    state_data = load_state_file(STATE_FILE_PATH)
    state_checksums = {}
    
    if state_data:
        artifact_entries = state_data.get('artifacts', {})
        for artifact_path, entry in artifact_entries.items():
            if isinstance(entry, dict):
                state_checksums[artifact_path] = entry.get('checksum')
            elif isinstance(entry, str):
                state_checksums[artifact_path] = entry
    
    # Required artifacts for quickstart validation
    required_paths = [
        # Spec documents (Phase 0)
        QUICKSTART_DOC_PATH,
        RESEARCH_DOC_PATH,
        DATA_MODEL_DOC_PATH,
        
        # State file
        STATE_FILE_PATH,
        
        # Core code structure
        PROJECT_ROOT / "code" / "config.yaml",
        PROJECT_ROOT / "code" / "__init__.py",
        
        # Models
        PROJECT_ROOT / "code" / "models" / "dp_gmm.py",
        PROJECT_ROOT / "code" / "models" / "anomaly_score.py",
        PROJECT_ROOT / "code" / "models" / "time_series.py",
        
        # Baselines
        PROJECT_ROOT / "code" / "baselines" / "arima.py",
        PROJECT_ROOT / "code" / "baselines" / "moving_average.py",
        
        # Evaluation
        PROJECT_ROOT / "code" / "evaluation" / "metrics.py",
        PROJECT_ROOT / "code" / "evaluation" / "plots.py",
        
        # Utils
        PROJECT_ROOT / "code" / "utils" / "__init__.py",
        PROJECT_ROOT / "code" / "utils" / "streaming.py",
        PROJECT_ROOT / "code" / "utils" / "checksum_manager.py",
        PROJECT_ROOT / "code" / "utils" / "memory_profiler.py",
        PROJECT_ROOT / "code" / "utils" / "runtime_monitor.py",
        PROJECT_ROOT / "code" / "utils" / "threshold.py",
        PROJECT_ROOT / "code" / "utils" / "hyperparameter_counter.py",
        
        # Scripts
        PROJECT_ROOT / "code" / "scripts" / "download_datasets.py",
        PROJECT_ROOT / "code" / "scripts" / "validate_quickstart_artifacts.py",
        
        # Data directory structure
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
    ]
    
    for path in required_paths:
        # Check if path is a directory (exists check is sufficient)
        if path.is_dir():
            artifacts.append((path, None))
        else:
            # Get expected checksum from state if available
            rel_path = str(path.relative_to(PROJECT_ROOT))
            expected_checksum = state_checksums.get(rel_path)
            artifacts.append((path, expected_checksum))
    
    return artifacts

def validate_quickstart_artifacts() -> ValidationReport:
    """
    Main validation function - validates all quickstart artifacts.
    
    Returns:
        ValidationReport with validation results
    """
    report = ValidationReport()
    report.total_artifacts = 0
    
    # Load quickstart document
    quickstart_content = load_quickstart_doc(QUICKSTART_DOC_PATH)
    
    if quickstart_content is None:
        report.validation_errors.append("Quickstart document not found")
        report.status = "failure"
        return report
    
    # Parse artifact references from quickstart
    parsed_artifacts = parse_artifact_references(quickstart_content)
    
    # Get required artifacts from validation logic
    required_artifacts = get_required_artifacts()
    
    # Combine all artifacts to validate
    all_artifacts = required_artifacts + [(Path(a['path']), None) for a in parsed_artifacts]
    
    # Deduplicate
    seen_paths = set()
    unique_artifacts = []
    for path, checksum in all_artifacts:
        path_key = str(path)
        if path_key not in seen_paths:
            seen_paths.add(path_key)
            unique_artifacts.append((path, checksum))
    
    report.total_artifacts = len(unique_artifacts)
    
    # Validate each artifact
    for artifact_path, expected_checksum in unique_artifacts:
        validate_artifact(artifact_path, expected_checksum, report)
    
    # Set final status
    if report.failed_artifacts == 0 and report.missing_artifacts == 0:
        report.status = "success"
    else:
        report.status = "failure"
    
    # Log summary
    logger.info(f"Validation complete: {report.validated_artifacts}/{report.total_artifacts} artifacts validated")
    if report.missing_artifacts:
        logger.warning(f"Missing artifacts: {len(report.missing_artifacts)}")
    if report.checksum_mismatches:
        logger.warning(f"Checksum mismatches: {len(report.checksum_mismatches)}")
    
    return report

def save_validation_report(report: ValidationReport, output_path: Path) -> None:
    """Save validation report to JSON file"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report.to_json())
    logger.info(f"Validation report saved to {output_path}")

def main() -> int:
    """
    Main entry point - runs full artifact validation.
    
    Returns:
        0 if all artifacts validated successfully
        1 if validation failed
    """
    logger.info("Starting quickstart artifact validation (T057/T065)")
    
    try:
        # Run validation
        report = validate_quickstart_artifacts()
        
        # Save report to code/.tasks/
        report_output_path = CODE_DIR / ".tasks" / "T057_T065_validation_report.json"
        save_validation_report(report, report_output_path)
        
        # Print summary
        print("\n" + "=" * 60)
        print("QUICKSTART ARTIFACT VALIDATION REPORT")
        print("=" * 60)
        print(f"Project ID: {report.project_id}")
        print(f"Timestamp: {report.timestamp}")
        print(f"Total artifacts: {report.total_artifacts}")
        print(f"Validated: {report.validated_artifacts}")
        print(f"Failed: {report.failed_artifacts}")
        print(f"Missing: {len(report.missing_artifacts)}")
        print(f"Status: {report.status.upper()}")
        
        if report.missing_artifacts:
            print("\nMissing artifacts:")
            for artifact in report.missing_artifacts[:10]:  # Show first 10
                print(f"  - {artifact}")
            if len(report.missing_artifacts) > 10:
                print(f"  ... and {len(report.missing_artifacts) - 10} more")
        
        if report.checksum_mismatches:
            print("\nChecksum mismatches:")
            for mismatch in report.checksum_mismatches[:5]:  # Show first 5
                print(f"  - {mismatch['artifact']}")
        
        print("=" * 60)
        
        # Exit with appropriate code
        if report.status == "success":
            print("\n✓ All artifacts validated successfully!")
            return 0
        else:
            print("\n✗ Validation failed - see report for details")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        import traceback
        traceback.print_exc()
        
        error_report = ValidationReport(
            status="failure",
            validation_errors=[f"Unexpected error: {str(e)}"]
        )
        error_report.total_artifacts = 0
        
        # Save error report
        error_report_path = CODE_DIR / ".tasks" / "T057_T065_error_report.json"
        save_validation_report(error_report, error_report_path)
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
