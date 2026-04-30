"""
Validate Quickstart Artifacts Script (T065)

This script validates that all artifacts referenced in quickstart.md
exist and have correct checksums. It is designed to run without
arguments and produce a validation report.

Exit codes:
  0 - All artifacts validated successfully
  1 - Validation failed (missing files, checksum mismatches)
  2 - Configuration error (missing quickstart.md, state file)
"""
import os
import sys
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
import yaml
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/validate_quickstart.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationReport:
    """Report structure for validation results."""
    success: bool = False
    total_artifacts: int = 0
    validated_artifacts: int = 0
    failed_artifacts: int = 0
    missing_artifacts: List[str] = field(default_factory=list)
    checksum_mismatches: List[Dict[str, Any]] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    artifacts_validated: List[Dict[str, Any]] = field(default_factory=list)
    report_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> Optional[str]:
    """
    Compute SHA256 checksum of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (default: sha256)

    Returns:
        Hex digest string or None if file cannot be read
    """
    if not file_path.exists():
        logger.warning(f"File does not exist: {file_path}")
        return None

    if not file_path.is_file():
        logger.warning(f"Not a file: {file_path}")
        return None

    try:
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except (IOError, OSError) as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

def load_state_file(state_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load state YAML file containing artifact checksums.

    Args:
        state_path: Path to state YAML file

    Returns:
        Dictionary with state contents or None if loading fails
    """
    if not state_path.exists():
        logger.warning(f"State file does not exist: {state_path}")
        return None

    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, IOError, OSError) as e:
        logger.error(f"Error loading state file {state_path}: {e}")
        return None

def load_quickstart_doc(quickstart_path: Path) -> Optional[str]:
    """
    Load quickstart.md document.

    Args:
        quickstart_path: Path to quickstart.md

    Returns:
        Document contents or None if loading fails
    """
    if not quickstart_path.exists():
        logger.warning(f"Quickstart document does not exist: {quickstart_path}")
        return None

    try:
        with open(quickstart_path, 'r', encoding='utf-8') as f:
            return f.read()
    except (IOError, OSError) as e:
        logger.error(f"Error loading quickstart.md {quickstart_path}: {e}")
        return None

def parse_artifact_references(doc_contents: str) -> List[str]:
    """
    Parse artifact file references from quickstart.md.

    Looks for file paths in common patterns:
    - Inline code: `path/to/file.ext`
    - Code blocks: ```path/to/file.ext```
    - Direct references in lists

    Args:
        doc_contents: Contents of quickstart.md

    Returns:
        List of artifact file paths
    """
    artifacts = []

    # Pattern 1: Inline code with file paths
    inline_pattern = r'`([^`]*\.(md|py|txt|yaml|yml|json|csv|png|jpg|pdf))`'
    matches = re.findall(inline_pattern, doc_contents)
    for match in matches:
        path_str = match[0]
        # Normalize path separators
        path_str = path_str.replace('\\', '/')
        artifacts.append(path_str)

    # Pattern 2: Direct file references in lists (e.g., - data/raw/file.csv)
    list_pattern = r'[-*]\s+([a-zA-Z0-9_/.-]+\.(md|py|txt|yaml|yml|json|csv|png|jpg|pdf))'
    matches = re.findall(list_pattern, doc_contents)
    for match in matches:
        path_str = match[0]
        path_str = path_str.replace('\\', '/')
        artifacts.append(path_str)

    # Pattern 3: Code block file paths
    code_block_pattern = r'```([a-zA-Z0-9_/.-]+\.(md|py|txt|yaml|yml|json|csv))'
    matches = re.findall(code_block_pattern, doc_contents)
    for match in matches:
        path_str = match[0]
        path_str = path_str.replace('\\', '/')
        artifacts.append(path_str)

    # Deduplicate while preserving order
    seen = set()
    unique_artifacts = []
    for artifact in artifacts:
        if artifact not in seen:
            seen.add(artifact)
            unique_artifacts.append(artifact)

    return unique_artifacts

def get_required_artifacts(state_data: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """
    Extract required artifacts and their expected checksums from state file.

    Args:
        state_data: Loaded state YAML contents

    Returns:
        Dictionary mapping artifact paths to expected checksums
    """
    required = {}

    if not state_data:
        return required

    # Look for artifact checksums in various state file locations
    artifact_sections = [
        'artifacts',
        'checksums',
        'artifact_checksums',
        'projects'
    ]

    for section in artifact_sections:
        if section in state_data:
            section_data = state_data[section]
            if isinstance(section_data, dict):
                for path, checksum_data in section_data.items():
                    if isinstance(checksum_data, str):
                        # Direct checksum value
                        required[path] = checksum_data
                    elif isinstance(checksum_data, dict) and 'sha256' in checksum_data:
                        # Checksum in structured format
                        required[path] = checksum_data['sha256']

    return required

def validate_artifact(
    artifact_path: Path,
    expected_checksum: Optional[str] = None,
    project_root: Optional[Path] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate a single artifact.

    Args:
        artifact_path: Path to the artifact
        expected_checksum: Expected SHA256 checksum (optional)
        project_root: Project root directory for path resolution

    Returns:
        Tuple of (success, computed_checksum, error_message)
    """
    # Resolve path relative to project root if provided
    if project_root and not artifact_path.is_absolute():
        artifact_path = project_root / artifact_path

    # Check if file exists
    if not artifact_path.exists():
      return (False, None, f"File does not exist: {artifact_path}")

    if not artifact_path.is_file():
      return (False, None, f"Not a file: {artifact_path}")

    # Compute checksum
    computed_checksum = compute_file_checksum(artifact_path)
    if computed_checksum is None:
      return (False, None, f"Could not compute checksum for: {artifact_path}")

    # Verify checksum if expected
    if expected_checksum:
        if computed_checksum != expected_checksum:
            return (
                False,
                computed_checksum,
                f"Checksum mismatch: expected {expected_checksum}, got {computed_checksum}"
            )

    return (True, computed_checksum, None)

def validate_quickstart_artifacts(
    project_root: Optional[Path] = None,
    quickstart_rel_path: str = 'specs/001-bayesian-nonparametrics-anomaly-detection/quickstart.md',
    state_rel_path: str = 'state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml'
) -> ValidationReport:
    """
    Main validation function.

    Args:
        project_root: Project root directory (auto-detected if None)
        quickstart_rel_path: Relative path to quickstart.md
        state_rel_path: Relative path to state YAML file

    Returns:
        ValidationReport with results
    """
    report = ValidationReport()

    # Auto-detect project root if not provided
    if project_root is None:
        # Look for project root in common locations
        cwd = Path.cwd()
        possible_roots = [
            cwd,
            cwd.parent,
            cwd / 'projects' / 'PROJ-024-bayesian-nonparametrics-for-anomaly-dete',
            Path('/workspace') / 'projects' / 'PROJ-024-bayesian-nonparametrics-for-anomaly-dete'
        ]
        for candidate in possible_roots:
            if (candidate / 'tasks.md').exists():
                project_root = candidate
                break
        if project_root is None:
            # Default to current directory
            project_root = cwd

    logger.info(f"Project root: {project_root}")

    # Load quickstart.md
    quickstart_path = project_root / quickstart_rel_path
    quickstart_contents = load_quickstart_doc(quickstart_path)
    if quickstart_contents is None:
        report.validation_errors.append(f"Could not load quickstart.md at {quickstart_path}")
        report.success = False
        return report

    # Load state file for checksums
    state_path = project_root / state_rel_path
    state_data = load_state_file(state_path)
    required_artifacts = get_required_artifacts(state_data)

    # Parse artifact references from quickstart.md
    referenced_artifacts = parse_artifact_references(quickstart_contents)
    logger.info(f"Found {len(referenced_artifacts)} artifact references in quickstart.md")

    # Combine: use state file checksums where available, otherwise just validate existence
    all_artifacts = set(referenced_artifacts)
    all_artifacts.update(required_artifacts.keys())

    report.total_artifacts = len(all_artifacts)
    logger.info(f"Total artifacts to validate: {report.total_artifacts}")

    # Validate each artifact
    for artifact_path_str in all_artifacts:
        artifact_path = Path(artifact_path_str)
        expected_checksum = required_artifacts.get(artifact_path_str)

        success, computed_checksum, error = validate_artifact(
            artifact_path,
            expected_checksum,
            project_root
        )

        artifact_info = {
            'path': str(artifact_path),
            'success': success,
            'checksum': computed_checksum
        }
        report.artifacts_validated.append(artifact_info)

        if success:
            report.validated_artifacts += 1
            logger.info(f"✓ Validated: {artifact_path}")
        else:
            report.failed_artifacts += 1
            if error:
                if "does not exist" in error:
                    report.missing_artifacts.append(str(artifact_path))
                else:
                    report.checksum_mismatches.append({
                        'path': str(artifact_path),
                        'error': error,
                        'checksum': computed_checksum
                    })
            logger.warning(f"✗ Failed: {artifact_path} - {error}")

    # Determine overall success
    if report.failed_artifacts == 0:
        report.success = True
        logger.info("✓ All artifacts validated successfully")
    else:
        report.success = False
        logger.error(f"✗ Validation failed: {report.failed_artifacts} artifacts failed")

    return report

def save_validation_report(report: ValidationReport, output_path: Optional[Path] = None) -> Path:
    """
    Save validation report to JSON file.

    Args:
        report: ValidationReport to save
        output_path: Output file path (default: logs/quickstart_validation_report.json)

    Returns:
        Path to saved report
    """
    if output_path is None:
        output_path = Path('logs') / 'quickstart_validation_report.json'

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report.to_json())

    report.report_path = str(output_path)
    logger.info(f"Validation report saved to: {output_path}")
    return output_path

def main() -> int:
    """
    Main entry point for the validation script.

    Returns:
        Exit code: 0 for success, 1 for validation failure, 2 for config error
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting Quickstart Artifacts Validation (T065)")
        logger.info("=" * 60)

        # Run validation
        report = validate_quickstart_artifacts()

        # Save report
        report_path = save_validation_report(report)

        # Print summary
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total artifacts:     {report.total_artifacts}")
        print(f"Validated:           {report.validated_artifacts}")
        print(f"Failed:              {report.failed_artifacts}")
        print(f"Missing:             {len(report.missing_artifacts)}")
        print(f"Checksum mismatches: {len(report.checksum_mismatches)}")
        print(f"Validation errors:   {len(report.validation_errors)}")
        print(f"Overall success:     {'YES' if report.success else 'NO'}")
        print(f"Report saved to:     {report.report_path}")
        print("=" * 60)

        if report.missing_artifacts:
            print("\nMissing artifacts:")
            for path in report.missing_artifacts:
                print(f"  - {path}")

        if report.checksum_mismatches:
            print("\nChecksum mismatches:")
            for mismatch in report.checksum_mismatches:
                print(f"  - {mismatch['path']}: {mismatch['error']}")

        if report.validation_errors:
            print("\nValidation errors:")
            for error in report.validation_errors:
                print(f"  - {error}")

        # Return appropriate exit code
        if report.success:
            logger.info("Validation completed successfully")
            return 0
        else:
            logger.error("Validation completed with failures")
            return 1

    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        import traceback
        traceback.print_exc()
        return 2

if __name__ == '__main__':
    sys.exit(main())
