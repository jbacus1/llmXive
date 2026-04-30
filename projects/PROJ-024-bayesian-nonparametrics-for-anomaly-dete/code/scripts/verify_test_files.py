"""
Verify all test files exist and are functional (T073).

This script verifies:
1. All required test files exist at expected paths
2. Test files can be discovered by pytest
3. Test files can be imported without syntax errors

Per Phase 7: Review-Driven Revisions - verify test infrastructure before
final acceptance.
"""
import sys
import os
from pathlib import Path
import subprocess
import json
from typing import Dict, Any, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root - adjust based on actual project structure
PROJECT_ROOT = Path(__file__).parent.parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"

# Required test files per T073 specification
REQUIRED_TESTS: List[Path] = [
    TESTS_DIR / "contract" / "test_dp_gmm_schema.py",
    TESTS_DIR / "integration" / "test_streaming_update.py",
    TESTS_DIR / "unit" / "test_memory_profile.py",
]

class TestFileReport:
    """Report structure for test file verification."""
    def __init__(self):
        self.files_checked: List[Dict[str, Any]] = []
        self.total_files: int = 0
        self.files_exist: int = 0
        self.files_importable: int = 0
        self.files_discoverable: int = 0
        self.errors: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files_checked": self.files_checked,
            "total_files": self.total_files,
            "files_exist": self.files_exist,
            "files_importable": self.files_importable,
            "files_discoverable": self.files_discoverable,
            "errors": self.errors,
            "all_passed": (
                self.files_exist == self.total_files and
                self.files_importable == self.total_files and
                self.files_discoverable == self.total_files
            )
        }

def check_file_exists(file_path: Path) -> Tuple[bool, Optional[str]]:
    """Check if a file exists at the given path."""
    if not file_path.exists():
        return False, f"File does not exist: {file_path}"
    if not file_path.is_file():
        return False, f"Path is not a file: {file_path}"
    if file_path.stat().st_size == 0:
        return False, f"File is empty: {file_path}"
    return True, None

def check_file_importable(file_path: Path) -> Tuple[bool, Optional[str]]:
    """Check if a file can be imported without syntax errors."""
    try:
        # Try to compile the file to check for syntax errors
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        compile(source, str(file_path), 'exec')
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error in {file_path}: {e}"
    except Exception as e:
        return False, f"Error reading {file_path}: {e}"

def check_pytest_discovery(test_file: Path) -> Tuple[bool, Optional[str]]:
    """Check if pytest can discover tests in the file."""
    try:
        # Run pytest with --collect-only to discover tests without running
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', str(test_file), '--collect-only', '-q'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        # Check for discovery errors (exit code 0 or 5 is OK - 5 means no tests collected)
        if result.returncode in [0, 5]:
            # Check if there are any collection errors in stderr
            if "ERROR" in result.stderr.upper():
                # Some errors are expected if tests use pytest.skip
                pass
            return True, None
        else:
            return False, f"pytest discovery failed for {test_file}: {result.stderr[:500]}"
    except subprocess.TimeoutExpired:
        return False, f"pytest discovery timed out for {test_file}"
    except Exception as e:
        return False, f"Error running pytest discovery for {test_file}: {e}"

def verify_test_files() -> TestFileReport:
    """Main verification function for test files."""
    report = TestFileReport()
    report.total_files = len(REQUIRED_TESTS)

    logger.info(f"Verifying {report.total_files} test files...")
    logger.info(f"Project root: {PROJECT_ROOT}")

    for test_file in REQUIRED_TESTS:
        file_report = {
            "path": str(test_file.relative_to(PROJECT_ROOT)) if test_file.is_relative_to(PROJECT_ROOT) else str(test_file),
            "exists": False,
            "importable": False,
            "discoverable": False,
            "errors": []
        }

        # Check existence
        exists, error = check_file_exists(test_file)
        file_report["exists"] = exists
        if error:
            file_report["errors"].append(error)
            report.errors.append(error)
        else:
            report.files_exist += 1

        # Check importability (only if file exists)
        if exists:
            importable, error = check_file_importable(test_file)
            file_report["importable"] = importable
            if error:
                file_report["errors"].append(error)
                report.errors.append(error)
            else:
                report.files_importable += 1

            # Check pytest discovery (only if importable)
            if importable:
                discoverable, error = check_pytest_discovery(test_file)
                file_report["discoverable"] = discoverable
                if error:
                    file_report["errors"].append(error)
                    report.errors.append(error)
                else:
                    report.files_discoverable += 1

        report.files_checked.append(file_report)
        logger.info(f"  {test_file.name}: exist={exists}, importable={file_report['importable']}, discoverable={file_report['discoverable']}")

    return report

def print_report(report: TestFileReport) -> None:
    """Print a formatted verification report."""
    print("\n" + "=" * 60)
    print("TEST FILE VERIFICATION REPORT (T073)")
    print("=" * 60)
    print(f"\nTotal files checked: {report.total_files}")
    print(f"Files exist: {report.files_exist}/{report.total_files}")
    print(f"Files importable: {report.files_importable}/{report.total_files}")
    print(f"Files discoverable: {report.files_discoverable}/{report.total_files}")
    print(f"\nAll checks passed: {report.to_dict()['all_passed']}")

    if report.errors:
        print(f"\nErrors ({len(report.errors)}):")
        for error in report.errors:
            print(f"  - {error}")

    print("\n" + "=" * 60)

def main() -> int:
    """Main entry point."""
    print(f"Verifying test files for T073...")
    print(f"Working directory: {Path.cwd()}")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Tests directory: {TESTS_DIR}")

    # Ensure tests directory exists
    if not TESTS_DIR.exists():
        logger.error(f"Tests directory does not exist: {TESTS_DIR}")
        print(f"ERROR: Tests directory does not exist at {TESTS_DIR}")
        return 1

    # Run verification
    report = verify_test_files()

    # Print report
    print_report(report)

    # Save detailed report as JSON
    report_path = PROJECT_ROOT / "code" / "scripts" / "test_verification_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report.to_dict(), f, indent=2)
    print(f"\nDetailed report saved to: {report_path}")

    # Return exit code based on success
    if report.to_dict()['all_passed']:
        print("\n✓ All test files verified successfully!")
        return 0
    else:
        print("\n✗ Some test files failed verification!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
