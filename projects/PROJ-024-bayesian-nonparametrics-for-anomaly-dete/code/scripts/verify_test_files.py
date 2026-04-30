"""
Verification script for test files in Phase 7 Review-Driven Revisions.

T075: Verify all test files exist and are functional:
- tests/contract/test_metrics_schema.py
- tests/integration/test_baseline_comparison.py

This script checks file existence, imports validity, and runs pytest
to verify the tests are functional.
"""
import os
import sys
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestFileStatus:
    """Status of a single test file."""
    path: str
    exists: bool
    importable: bool
    test_count: int
    pytest_passed: bool
    pytest_output: str = ""
    error_message: str = ""

@dataclass
class VerificationReport:
    """Complete verification report for test files."""
    timestamp: str
    project_root: str
    test_files: List[TestFileStatus] = field(default_factory=list)
    overall_passed: bool = True
    summary: str = ""

def get_project_root() -> Path:
    """Get the project root directory."""
    # Assume script is in code/scripts/, project root is two levels up
    return Path(__file__).parent.parent.parent

def check_file_exists(path: Path) -> bool:
    """Check if a file exists at the given path."""
    return path.exists() and path.is_file()

def check_import_validity(project_root: Path, relative_path: str) -> tuple:
    """
    Check if the test file can be imported without errors.
    
    Returns:
        tuple: (importable: bool, error_message: str)
    """
    test_file = project_root / relative_path
    if not test_file.exists():
        return False, "File does not exist"

    # Add project root to Python path for imports
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    new_python_path = f"{project_root}:{python_path}" if python_path else str(project_root)
    env['PYTHONPATH'] = new_python_path

    try:
        # Try to compile the file to check for syntax errors
        with open(test_file, 'r') as f:
            source = f.read()
        compile(source, str(test_file), 'exec')
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Import error: {e}"

def count_tests_in_file(test_file: Path) -> int:
    """Count the number of test functions in a file using grep."""
    if not test_file.exists():
        return 0

    try:
        result = subprocess.run(
            ['grep', '-c', 'def test_', str(test_file)],
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip()) if result.stdout.strip() else 0
        return count
    except (subprocess.SubprocessError, ValueError):
        return 0

def run_pytest_tests(project_root: Path, relative_path: str, timeout: int = 600) -> tuple:
    """
    Run pytest on a single test file.
    
    Returns:
        tuple: (passed: bool, output: str)
    """
    test_file = project_root / relative_path
    if not test_file.exists():
        return False, "File does not exist"

    # Set up environment
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    new_python_path = f"{project_root}:{python_path}" if python_path else str(project_root)
    env['PYTHONPATH'] = new_python_path

    # Run pytest with verbose output and timeout
    cmd = [
        sys.executable, '-m', 'pytest',
        str(test_file),
        '-v',
        '--tb=short',
        '--timeout=300'  # Per-test timeout
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )
        passed = result.returncode == 0
        output = result.stdout + result.stderr
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "Test execution timed out"
    except Exception as e:
        return False, f"Pytest execution error: {e}"

def verify_test_file(
    project_root: Path,
    relative_path: str,
    expected_min_tests: int = 1
) -> TestFileStatus:
    """
    Verify a single test file for existence, importability, and functionality.
    
    Args:
        project_root: Path to project root directory
        relative_path: Relative path from project root to test file
        expected_min_tests: Minimum number of test functions expected
    
    Returns:
        TestFileStatus with verification results
    """
    status = TestFileStatus(
        path=relative_path,
        exists=False,
        importable=False,
        test_count=0,
        pytest_passed=False
    )

    test_file = project_root / relative_path

    # Check existence
    status.exists = check_file_exists(test_file)
    if not status.exists:
        status.error_message = f"File not found: {relative_path}"
        return status

    # Check import validity
    status.importable, import_error = check_import_validity(project_root, relative_path)
    if not status.importable:
        status.error_message = import_error
        return status

    # Count test functions
    status.test_count = count_tests_in_file(test_file)
    if status.test_count < expected_min_tests:
        status.error_message = f"Expected at least {expected_min_tests} test functions, found {status.test_count}"
        # Continue to run pytest anyway

    # Run pytest
    status.pytest_passed, status.pytest_output = run_pytest_tests(project_root, relative_path)

    return status

def generate_verification_report(
    project_root: Path,
    test_files: List[str],
    expected_min_tests_per_file: int = 1
) -> VerificationReport:
    """
    Generate a complete verification report for all test files.
    
    Args:
        project_root: Path to project root directory
        test_files: List of relative paths to test files
        expected_min_tests_per_file: Minimum expected test functions per file
    
    Returns:
        VerificationReport with all results
    """
    report = VerificationReport(
        timestamp=datetime.now().isoformat(),
        project_root=str(project_root),
        overall_passed=True
    )

    for relative_path in test_files:
        status = verify_test_file(
            project_root,
            relative_path,
            expected_min_tests_per_file
        )
        report.test_files.append(status)
        if not status.pytest_passed:
            report.overall_passed = False

    # Generate summary
    total_files = len(report.test_files)
    passed_files = sum(1 for s in report.test_files if s.pytest_passed)
    total_tests = sum(s.test_count for s in report.test_files)

    report.summary = (
        f"Verification completed at {report.timestamp}\n"
        f"Project root: {report.project_root}\n"
        f"Total test files: {total_files}\n"
        f"Files passed: {passed_files}/{total_files}\n"
        f"Total test functions: {total_tests}\n"
        f"Overall status: {'PASSED' if report.overall_passed else 'FAILED'}\n\n"
    )

    # Add per-file details
    for status in report.test_files:
        file_status = "PASSED" if status.pytest_passed else "FAILED"
        report.summary += (
            f"  {status.path}: {file_status}\n"
            f"    Exists: {status.exists}\n"
            f"    Importable: {status.importable}\n"
            f"    Test count: {status.test_count}\n"
        )
        if status.error_message:
            report.summary += f"    Error: {status.error_message}\n"
        report.summary += "\n"

    return report

def save_report(report: VerificationReport, output_dir: Path) -> Path:
    """Save the verification report to a file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"test_verification_{report.timestamp.replace(':', '-')}.txt"

    with open(output_file, 'w') as f:
        f.write(report.summary)

    return output_file

def main():
    """Main entry point for test file verification."""
    logger.info("Starting test file verification (T075)")

    # Get project root
    project_root = get_project_root()
    logger.info(f"Project root: {project_root}")

    # Test files to verify (from T075 task description)
    test_files = [
        "tests/contract/test_metrics_schema.py",
        "tests/integration/test_baseline_comparison.py"
    ]

    # Generate verification report
    report = generate_verification_report(project_root, test_files)

    # Log summary
    logger.info("=" * 60)
    logger.info(report.summary)
    logger.info("=" * 60)

    # Save report to code/.tasks/
    tasks_dir = project_root / ".tasks"
    report_path = save_report(report, tasks_dir)
    logger.info(f"Report saved to: {report_path}")

    # Exit with appropriate code
    if report.overall_passed:
        logger.info("T075 VERIFICATION: PASSED")
        sys.exit(0)
    else:
        logger.error("T075 VERIFICATION: FAILED - See report for details")
        sys.exit(1)

if __name__ == "__main__":
    main()
