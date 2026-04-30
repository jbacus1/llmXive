"""
Run all contract tests and document pass/fail status in test report.

This script executes pytest on all contract test files and generates
a comprehensive markdown report documenting pass/fail status.

Usage:
    python run_all_contract_tests.py
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

def get_contract_test_files() -> List[Path]:
    """Find all contract test files in the tests/contract directory."""
    project_root = get_project_root()
    contract_dir = project_root / 'tests' / 'contract'
    
    if not contract_dir.exists():
        logger.warning(f"Contract test directory not found: {contract_dir}")
        return []
    
    test_files = list(contract_dir.glob('test_*.py'))
    return sorted(test_files)

def run_pytest_tests(test_files: List[Path]) -> Dict[str, Any]:
    """Run pytest on the specified test files and capture results."""
    if not test_files:
        return {
            'success': True,
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'tests': [],
            'message': 'No contract test files found'
        }
    
    project_root = get_project_root()
    test_paths = [str(f) for f in test_files]
    
    # Run pytest with JSON output
    cmd = [
        sys.executable, '-m', 'pytest',
        *test_paths,
        '-v',
        '--tb=short',
        '--json-report',
        '--json-report-file=code/.tasks/T077_pytest_report.json',
        '--json-report-omit', 'collect',
        '-p', 'no:warnings'
    ]
    
    logger.info(f"Running pytest on {len(test_files)} contract test files...")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Load JSON report if it exists
        report_path = project_root / 'code' / '.tasks' / 'T077_pytest_report.json'
        pytest_json = None
        if report_path.exists():
            try:
                with open(report_path, 'r') as f:
                    pytest_json = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse pytest JSON report: {e}")
        
        return {
            'success': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'json_report': pytest_json,
            'test_files': test_paths
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'pytest timed out after 300 seconds',
            'test_files': test_paths
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'test_files': test_paths
        }

def parse_pytest_json_report(pytest_json: Optional[Dict]) -> Dict[str, Any]:
    """Parse the pytest JSON report into a structured result."""
    if not pytest_json:
        return {
            'success': False,
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'tests': []
        }
    
    tests = pytest_json.get('tests', [])
    passed = sum(1 for t in tests if t.get('outcome') == 'passed')
    failed = sum(1 for t in tests if t.get('outcome') == 'failed')
    skipped = sum(1 for t in tests if t.get('outcome') == 'skipped')
    errors = sum(1 for t in tests if t.get('outcome') == 'error')
    
    test_details = []
    for test in tests:
        test_details.append({
            'name': test.get('nodeid', 'unknown'),
            'outcome': test.get('outcome', 'unknown'),
            'duration': test.get('duration', 0),
            'calls': test.get('calls', [])
        })
    
    return {
        'success': failed == 0 and errors == 0,
        'total_tests': len(tests),
        'passed': passed,
        'failed': failed,
        'skipped': skipped,
        'errors': errors,
        'tests': test_details
    }

def generate_markdown_report(
    test_files: List[Path],
    pytest_result: Dict[str, Any],
    parsed_result: Dict[str, Any]
) -> str:
    """Generate a comprehensive markdown test report."""
    report_lines = []
    
    # Header
    report_lines.append("# Contract Test Report")
    report_lines.append("")
    report_lines.append(f"**Generated**: {datetime.now().isoformat()}")
    report_lines.append(f"**Task ID**: T077")
    report_lines.append("")
    
    # Summary
    report_lines.append("## Summary")
    report_lines.append("")
    total = parsed_result['total_tests']
    passed = parsed_result['passed']
    failed = parsed_result['failed']
    skipped = parsed_result['skipped']
    errors = parsed_result['errors']
    
    report_lines.append(f"| Metric | Count |")
    report_lines.append(f"|--------|-------|")
    report_lines.append(f"| Total Tests | {total} |")
    report_lines.append(f"| Passed | {passed} |")
    report_lines.append(f"| Failed | {failed} |")
    report_lines.append(f"| Skipped | {skipped} |")
    report_lines.append(f"| Errors | {errors} |")
    report_lines.append("")
    
    overall_status = "✅ PASS" if parsed_result['success'] else "❌ FAIL"
    report_lines.append(f"**Overall Status**: {overall_status}")
    report_lines.append("")
    
    # Test Files
    report_lines.append("## Test Files")
    report_lines.append("")
    for test_file in test_files:
        report_lines.append(f"- `{test_file}`")
    report_lines.append("")
    
    # Detailed Results
    report_lines.append("## Detailed Test Results")
    report_lines.append("")
    
    if not parsed_result['tests']:
        report_lines.append("No individual test results available.")
        report_lines.append("")
    else:
        report_lines.append("| Test Name | Outcome | Duration (s) |")
        report_lines.append("|-----------|---------|--------------|")
        for test in parsed_result['tests']:
            name = test['name'].split('::')[-1] if '::' in test['name'] else test['name']
            outcome = test['outcome']
            duration = test['duration']
            status_icon = "✅" if outcome == 'passed' else "❌" if outcome in ['failed', 'error'] else "⏭️"
            report_lines.append(f"| {status_icon} {name} | {outcome} | {duration:.4f} |")
        report_lines.append("")
    
    # Failure Details
    if failed > 0 or errors > 0:
        report_lines.append("## Failure Details")
        report_lines.append("")
        
        for test in parsed_result['tests']:
            if test['outcome'] in ['failed', 'error']:
                report_lines.append(f"### {test['name']}")
                report_lines.append("")
                
                # Get failure info from calls if available
                calls = test.get('calls', [])
                if calls:
                    for call in calls:
                        if call.get('outcome') in ['failed', 'error']:
                            longrepr = call.get('longrepr', '')
                            if longrepr:
                                report_lines.append("```")
                                report_lines.append(str(longrepr)[:2000])
                                report_lines.append("```")
                                report_lines.append("")
        
        # Also include pytest stderr if available
        if pytest_result.get('stderr'):
            report_lines.append("## Pytest Stderr")
            report_lines.append("")
            report_lines.append("```")
            report_lines.append(pytest_result['stderr'][:2000])
            report_lines.append("```")
            report_lines.append("")
    
    # Raw Output
    report_lines.append("## Raw Pytest Output")
    report_lines.append("")
    if pytest_result.get('stdout'):
        report_lines.append("```")
        report_lines.append(pytest_result['stdout'][:3000])
        report_lines.append("```")
        report_lines.append("")
    
    # Conclusion
    report_lines.append("## Conclusion")
    report_lines.append("")
    if parsed_result['success']:
        report_lines.append("All contract tests passed successfully. The implementation satisfies the schema requirements defined in the project specifications.")
    else:
        report_lines.append(f"**{failed} tests failed and {errors} tests had errors.** Please review the failure details above and fix the corresponding implementation issues.")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append(f"*Report generated by T077 contract test runner*")
    
    return '\n'.join(report_lines)

def save_report(report_content: str, output_path: Path) -> None:
    """Save the markdown report to the specified path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    logger.info(f"Report saved to: {output_path}")

def main() -> int:
    """Main entry point for the contract test runner."""
    logger.info("Starting contract test execution (Task T077)...")
    
    # Ensure .tasks directory exists
    project_root = get_project_root()
    tasks_dir = project_root / 'code' / '.tasks'
    tasks_dir.mkdir(parents=True, exist_ok=True)
    
    # Find contract test files
    test_files = get_contract_test_files()
    logger.info(f"Found {len(test_files)} contract test files")
    
    if not test_files:
        logger.warning("No contract test files found. Creating empty report.")
        
        # Create a report noting no tests were found
        report = generate_markdown_report(
            test_files=[],
            pytest_result={'success': True, 'message': 'No tests found'},
            parsed_result={'success': True, 'total_tests': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': 0, 'tests': []}
        )
        
        output_path = tasks_dir / 'T077_contract_tests_report.md'
        save_report(report, output_path)
        return 0
    
    # Run pytest
    pytest_result = run_pytest_tests(test_files)
    
    # Parse JSON report if available
    parsed_result = parse_pytest_json_report(pytest_result.get('json_report'))
    
    # Generate markdown report
    report_content = generate_markdown_report(
        test_files=test_files,
        pytest_result=pytest_result,
        parsed_result=parsed_result
    )
    
    # Save report
    output_path = tasks_dir / 'T077_contract_tests_report.md'
    save_report(report_content, output_path)
    
    # Also save JSON report separately
    if pytest_result.get('json_report'):
        json_path = tasks_dir / 'T077_pytest_results.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(pytest_result['json_report'], f, indent=2)
        logger.info(f"JSON results saved to: {json_path}")
    
    # Print summary to stdout
    print("\n" + "=" * 60)
    print("CONTRACT TEST SUMMARY (T077)")
    print("=" * 60)
    print(f"Total Tests: {parsed_result['total_tests']}")
    print(f"Passed: {parsed_result['passed']}")
    print(f"Failed: {parsed_result['failed']}")
    print(f"Skipped: {parsed_result['skipped']}")
    print(f"Errors: {parsed_result['errors']}")
    print(f"Overall: {'✅ PASS' if parsed_result['success'] else '❌ FAIL'}")
    print(f"Report: {output_path}")
    print("=" * 60)
    
    return 0 if parsed_result['success'] else 1

if __name__ == '__main__':
    sys.exit(main())
