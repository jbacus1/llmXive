#!/usr/bin/env python3
"""
Verify threshold test files exist and are functional.

This script verifies:
1. tests/contract/test_threshold_schema.py exists and is syntactically valid
2. tests/integration/test_threshold_calibration.py exists and is syntactically valid
3. Both test files can be imported without errors
4. Both test files have at least one test function
5. Both test files pass pytest execution

Usage:
    python code/scripts/verify_threshold_tests.py
"""

import os
import sys
import ast
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
import json

@dataclass
class TestFileStatus:
    """Status of a single test file."""
    path: str
    exists: bool = False
    syntax_valid: bool = False
    importable: bool = False
    has_tests: bool = False
    test_count: int = 0
    error_message: str = ""

@dataclass
class VerificationReport:
    """Complete verification report for threshold tests."""
    project_root: str = ""
    test_files: List[TestFileStatus] = field(default_factory=list)
    all_passed: bool = False
    summary: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

def check_test_file(file_path: Path, project_root: Path) -> TestFileStatus:
    """Check if a test file exists and is valid."""
    status = TestFileStatus(path=str(file_path))
    
    # Check if file exists
    if not file_path.exists():
        status.error_message = f"File does not exist: {file_path}"
        return status
    status.exists = True
    
    # Check syntax
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        status.syntax_valid = True
    except SyntaxError as e:
        status.error_message = f"Syntax error: {e}"
        return status
    
    # Check if importable
    try:
        # Add project root to path
        sys.path.insert(0, str(project_root))
        sys.path.insert(0, str(project_root / 'code'))
        
        # Try to import the test module
        module_name = f"tests.contract.test_threshold_schema" if 'contract' in str(file_path) else "tests.integration.test_threshold_calibration"
        __import__(module_name)
        status.importable = True
    except ImportError as e:
        status.error_message = f"Import error: {e}"
        return status
    
    # Check for test functions
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
        
        test_functions = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')
        ]
        status.test_count = len(test_functions)
        status.has_tests = status.test_count > 0
    except Exception as e:
        status.error_message = f"Error counting tests: {e}"
        return status
    
    return status

def run_pytest_tests(file_path: Path) -> Dict[str, Any]:
    """Run pytest on a specific test file."""
    result = {
        'success': False,
        'exit_code': None,
        'stdout': '',
        'stderr': ''
    }
    
    try:
        proc = subprocess.run(
            ['python', '-m', 'pytest', str(file_path), '-v', '--tb=short'],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(file_path.parent.parent.parent)
        )
        result['exit_code'] = proc.returncode
        result['stdout'] = proc.stdout
        result['stderr'] = proc.stderr
        result['success'] = proc.returncode == 0
    except subprocess.TimeoutExpired:
        result['error_message'] = "Test execution timed out"
    except Exception as e:
        result['error_message'] = str(e)
    
    return result

def verify_threshold_tests(project_root: Path) -> VerificationReport:
    """Verify threshold test files exist and are functional."""
    report = VerificationReport(project_root=str(project_root))
    
    # Define test files to verify
    test_files = [
        project_root / 'tests' / 'contract' / 'test_threshold_schema.py',
        project_root / 'tests' / 'integration' / 'test_threshold_calibration.py'
    ]
    
    # Check each file
    for test_file in test_files:
        status = check_test_file(test_file, project_root)
        report.test_files.append(status)
    
    # Check if all files passed basic checks
    all_basic_passed = all(
        status.exists and status.syntax_valid and status.importable and status.has_tests
        for status in report.test_files
    )
    
    # Run pytest on each file if basic checks passed
    pytest_results = {}
    if all_basic_passed:
        for test_file in test_files:
            file_key = str(test_file.relative_to(project_root))
            pytest_results[file_key] = run_pytest_tests(test_file)
    
    report.details['pytest_results'] = pytest_results
    
    # Determine overall status
    report.all_passed = all_basic_passed and all(
        result.get('success', False) for result in pytest_results.values()
    )
    
    # Generate summary
    if report.all_passed:
        report.summary = "All threshold test files exist, are syntactically valid, importable, have tests, and pass pytest."
    else:
        failed_checks = []
        for status in report.test_files:
            if not status.exists:
                failed_checks.append(f"{status.path}: File does not exist")
            elif not status.syntax_valid:
                failed_checks.append(f"{status.path}: Syntax error")
            elif not status.importable:
                failed_checks.append(f"{status.path}: Cannot import")
            elif not status.has_tests:
                failed_checks.append(f"{status.path}: No test functions found")
        
        if pytest_results:
            for file_key, result in pytest_results.items():
                if not result.get('success', False):
                    failed_checks.append(f"{file_key}: pytest failed (exit code {result.get('exit_code')})")
        
        report.summary = f"Verification failed. Issues found: {'; '.join(failed_checks)}"
    
    return report

def main():
    """Main entry point."""
    # Determine project root
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    
    print("=" * 80)
    print("Threshold Test File Verification")
    print("=" * 80)
    print(f"Project root: {project_root}")
    print()
    
    # Run verification
    report = verify_threshold_tests(project_root)
    
    # Print results
    print("Test File Status:")
    print("-" * 80)
    for status in report.test_files:
        print(f"\nFile: {status.path}")
        print(f"  Exists: {status.exists}")
        print(f"  Syntax Valid: {status.syntax_valid}")
        print(f"  Importable: {status.importable}")
        print(f"  Has Tests: {status.has_tests}")
        print(f"  Test Count: {status.test_count}")
        if status.error_message:
            print(f"  Error: {status.error_message}")
    
    print("\n" + "=" * 80)
    print(f"Overall Status: {'PASS' if report.all_passed else 'FAIL'}")
    print(f"Summary: {report.summary}")
    print("=" * 80)
    
    # Save report
    output_path = project_root / 'code' / '.tasks' / 'T076_verification_report.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'project_root': report.project_root,
            'all_passed': report.all_passed,
            'summary': report.summary,
            'test_files': [
                {
                    'path': status.path,
                    'exists': status.exists,
                    'syntax_valid': status.syntax_valid,
                    'importable': status.importable,
                    'has_tests': status.has_tests,
                    'test_count': status.test_count,
                    'error_message': status.error_message
                }
                for status in report.test_files
            ],
            'pytest_results': report.details.get('pytest_results', {})
        }, f, indent=2)
    
    print(f"\nReport saved to: {output_path}")
    
    # Exit with appropriate code
    sys.exit(0 if report.all_passed else 1)

if __name__ == '__main__':
    main()
