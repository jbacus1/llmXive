"""
T075 Verification Script: Verify threshold test files exist and are functional

Verifies:
- tests/contract/test_threshold_schema.py exists and is importable
- tests/integration/test_threshold_calibration.py exists and is importable
- pytest can discover tests in both files

Usage:
    python code/scripts/verify_test_files_t075.py
"""
import sys
import os
from pathlib import Path
import subprocess
import json
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
import importlib.util


@dataclass
class TestFileStatus:
    """Status of a single test file verification."""
    path: str
    exists: bool = False
    importable: bool = False
    pytest_discoverable: bool = False
    error_message: str = ""


@dataclass
class VerificationReport:
    """Complete verification report for T075."""
    test_files: List[TestFileStatus] = field(default_factory=list)
    all_passed: bool = False
    summary: str = ""


def check_file_exists(file_path: Path) -> Tuple[bool, str]:
    """Check if a file exists at the given path."""
    if file_path.exists() and file_path.is_file():
        return True, "File exists"
    return False, f"File not found: {file_path}"


def check_file_importable(file_path: Path, project_root: Path) -> Tuple[bool, str]:
    """Check if a Python file can be imported as a module."""
    try:
        # Add project root to sys.path for imports
        sys.path.insert(0, str(project_root))
        
        # Construct module name from path
        relative_path = file_path.relative_to(project_root)
        module_name = str(relative_path).replace(os.sep, '.').replace('/', '.')[:-3]
        
        # Try to import
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            return False, "Could not create module spec"
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return True, "Module imported successfully"
    except Exception as e:
        return False, f"Import error: {str(e)}"
    finally:
        # Clean up sys.path
        if str(project_root) in sys.path:
            sys.path.remove(str(project_root))


def check_pytest_discovery(file_path: Path, project_root: Path) -> Tuple[bool, str]:
    """Check if pytest can discover tests in the file."""
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                str(file_path), "--collect-only",
                "-q", "--tb=no"
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Check if any tests were collected
            if "no tests collected" in result.stdout.lower():
                return False, "No tests collected by pytest"
            return True, "Tests discovered successfully"
        else:
            return False, f"pytest failed: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "pytest collection timed out"
    except Exception as e:
        return False, f"pytest error: {str(e)}"


def verify_test_files(project_root: Path) -> VerificationReport:
    """Verify all T075 test files exist and are functional."""
    report = VerificationReport()
    
    # Define test files to verify
    test_files = [
        project_root / "tests" / "contract" / "test_threshold_schema.py",
        project_root / "tests" / "integration" / "test_threshold_calibration.py"
    ]
    
    for test_file in test_files:
        status = TestFileStatus(path=str(test_file))
        
        # Check existence
        exists, exists_msg = check_file_exists(test_file)
        status.exists = exists
        if not exists:
            status.error_message = exists_msg
            report.test_files.append(status)
            continue
        
        # Check importability
        importable, import_msg = check_file_importable(test_file, project_root)
        status.importable = importable
        if not importable:
            status.error_message = import_msg
            report.test_files.append(status)
            continue
        
        # Check pytest discovery
        discoverable, discover_msg = check_pytest_discovery(test_file, project_root)
        status.pytest_discoverable = discoverable
        if not discoverable:
            status.error_message = discover_msg
        
        report.test_files.append(status)
    
    # Determine overall status
    all_passed = all(
        f.exists and f.importable and f.pytest_discoverable
        for f in report.test_files
    )
    report.all_passed = all_passed
    
    # Generate summary
    passed_count = sum(
        1 for f in report.test_files
        if f.exists and f.importable and f.pytest_discoverable
    )
    total_count = len(report.test_files)
    
    if all_passed:
        report.summary = f"All {total_count} test files verified successfully ({passed_count}/{total_count})"
    else:
        failed_count = total_count - passed_count
        report.summary = f"Verification failed: {failed_count}/{total_count} files have issues"
    
    return report


def print_report(report: VerificationReport) -> None:
    """Print verification report to stdout."""
    print("=" * 70)
    print("T075 Test File Verification Report")
    print("=" * 70)
    print()
    
    for status in report.test_files:
        print(f"File: {status.path}")
        print(f"  Exists:         {'✓' if status.exists else '✗'}")
        print(f"  Importable:     {'✓' if status.importable else '✗'}")
        print(f"  Pytest:         {'✓' if status.pytest_discoverable else '✗'}")
        if status.error_message:
            print(f"  Error:          {status.error_message}")
        print()
    
    print("-" * 70)
    print(f"Overall Status: {'PASS' if report.all_passed else 'FAIL'}")
    print(f"Summary: {report.summary}")
    print("-" * 70)


def save_report(report: VerificationReport, output_path: Path) -> None:
    """Save verification report to JSON file."""
    data = {
        "all_passed": report.all_passed,
        "summary": report.summary,
        "test_files": [
            {
                "path": f.path,
                "exists": f.exists,
                "importable": f.importable,
                "pytest_discoverable": f.pytest_discoverable,
                "error_message": f.error_message
            }
            for f in report.test_files
        ]
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)


def main() -> int:
    """Main entry point for T075 verification."""
    # Determine project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent  # code/scripts -> code -> project root
    
    print(f"Project root: {project_root}")
    print(f"Script location: {script_path}")
    print()
    
    # Run verification
    report = verify_test_files(project_root)
    
    # Print report
    print_report(report)
    
    # Save report
    report_path = project_root / "state" / "test_verification_t075.json"
    save_report(report, report_path)
    print(f"\nReport saved to: {report_path}")
    
    # Return exit code based on verification result
    return 0 if report.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
