"""
T076: Run all contract tests and document pass/fail status in test report.

This script executes all contract tests for the Bayesian Nonparametrics
anomaly detection project and generates a comprehensive test report.
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
CONTRACT_TESTS_DIR = TESTS_DIR / "contract"
REPORTS_DIR = PROJECT_ROOT / "code" / "reports"

# Contract test files (per completed tasks T013, T027, T042)
CONTRACT_TEST_FILES = [
    "tests/contract/test_dp_gmm_schema.py",
    "tests/contract/test_metrics_schema.py",
    "tests/contract/test_threshold_schema.py"
]

@dataclass
class TestResult:
    """Single test result structure."""
    test_name: str
    passed: bool
    duration: float
    message: str
    traceback: Optional[str] = None

@dataclass
class TestReport:
    """Complete contract test report structure."""
    timestamp: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    total_duration: float
    results: List[TestResult]
    summary: str

def run_pytest_tests(test_files: List[str]) -> Dict[str, Any]:
    """Run pytest on specified test files and capture results."""
    results = {
        "success": False,
        "return_code": None,
        "stdout": "",
        "stderr": "",
        "json_output": None
    }

    # Create pytest command with JSON output for parsing
    pytest_args = [
        "pytest",
        "-v",
        "--json-report",
        "--json-report-file=-",  # Output to stdout
        "--tb=short"
    ] + test_files

    logger.info(f"Running pytest on: {test_files}")

    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT / "code") + ":" + env.get("PYTHONPATH", "")

        result = subprocess.run(
            pytest_args,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout for all tests
            env=env
        )

        results["return_code"] = result.returncode
        results["stdout"] = result.stdout
        results["stderr"] = result.stderr
        results["success"] = result.returncode == 0

        # Try to parse JSON output
        try:
            # The JSON report goes to stderr with --json-report-file=-
            json_str = result.stderr.strip()
            if json_str:
                results["json_output"] = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse pytest JSON output: {e}")
            results["json_output"] = None

    except subprocess.TimeoutExpired:
        results["return_code"] = -1
        results["stderr"] = "pytest timed out after 300 seconds"
        logger.error("pytest timed out")
    except Exception as e:
        results["return_code"] = -1
        results["stderr"] = str(e)
        logger.error(f"Error running pytest: {e}")

    return results

def parse_pytest_json_report(json_output: Dict[str, Any]) -> List[TestResult]:
    """Parse pytest JSON report into TestResult objects."""
    results = []

    if not json_output or "tests" not in json_output:
        return results

    for test in json_output["tests"]:
        # Extract test name (last part after ::)
        test_name = test["nodeid"].split("::")[-1] if "::" in test["nodeid"] else test["nodeid"]

        # Determine status
        passed = test["outcome"] == "passed"
        skipped = test["outcome"] == "skipped"
        failed = test["outcome"] == "failed"

        # Get duration (in seconds)
        duration = test.get("duration", 0.0) / 1_000_000_000  # Convert ns to s

        # Get message
        message = ""
        if "call" in test and test["call"]:
            call = test["call"]
            if "longrepr" in call:
                message = str(call["longrepr"])[:500]  # Truncate long tracebacks

        results.append(TestResult(
            test_name=test_name,
            passed=passed and not skipped,
            duration=duration,
            message=message,
            traceback=str(test.get("call", {}).get("longrepr", "")) if failed else None
        ))

    return results

def generate_markdown_report(report: TestReport) -> str:
    """Generate markdown test report."""
    lines = [
        "# Contract Test Report",
        "",
        f"**Generated**: {report.timestamp}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Tests | {report.total_tests} |",
        f"| Passed | {report.passed_tests} |",
        f"| Failed | {report.failed_tests} |",
        f"| Skipped | {report.skipped_tests} |",
        f"| Total Duration | {report.total_duration:.2f}s |",
        "",
        "## Overall Status",
        "",
        f"**Status**: {'✅ ALL TESTS PASSED' if report.failed_tests == 0 else '❌ SOME TESTS FAILED'}",
        "",
        "## Test Details",
        "",
    ]

    # Add test results table
    lines.append("| Test Name | Status | Duration |")
    lines.append("|-----------|--------|----------|")

    for result in report.results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        lines.append(f"| {result.test_name} | {status} | {result.duration:.3f}s |")

    lines.append("")
    lines.append("## Failed Tests Details", "")

    failed_tests = [r for r in report.results if not r.passed]
    if failed_tests:
        for result in failed_tests:
            lines.append(f"### {result.test_name}")
            lines.append("")
            lines.append(f"- **Duration**: {result.duration:.3f}s")
            if result.message:
                lines.append(f"- **Message**: {result.message[:200]}...")
            if result.traceback:
                lines.append("")
                lines.append("```")
                lines.append(result.traceback[:1000])
                lines.append("```")
            lines.append("")
    else:
        lines.append("No failed tests.")
        lines.append("")

    lines.append("## Contract Test Files Verified", "")
    lines.append("")
    for test_file in CONTRACT_TEST_FILES:
        exists = (PROJECT_ROOT / test_file).exists()
        status = "✅" if exists else "❌"
        lines.append(f"- {status} `{test_file}`")

    lines.append("")
    lines.append("---")
    lines.append("*Generated by run_contract_tests.py (T076)*")

    return "\n".join(lines)

def save_report(report: TestReport, markdown_content: str) -> Path:
    """Save test report to file."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"contract_test_report_{timestamp}.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    # Also save latest as symlink/copy for easy access
      latest_path = REPORTS_DIR / "contract_test_report_latest.md"
    if latest_path.exists():
        latest_path.unlink()
    latest_path.write_text(markdown_content)

    logger.info(f"Report saved to: {report_path}")
    return report_path

def main():
    """Main entry point for T076 contract test runner."""
    logger.info("=" * 60)
    logger.info("T076: Running Contract Tests")
    logger.info("=" * 60)

    # Verify test files exist
    missing_files = []
    for test_file in CONTRACT_TEST_FILES:
        if not (PROJECT_ROOT / test_file).exists():
            missing_files.append(test_file)
            logger.warning(f"Missing test file: {test_file}")

    if missing_files:
        logger.error(f"Missing {len(missing_files)} contract test files!")
        # Create partial report even with missing files
        report = TestReport(
            timestamp=datetime.now().isoformat(),
            total_tests=0,
            passed_tests=0,
            failed_tests=len(missing_files),
            skipped_tests=0,
            total_duration=0.0,
            results=[],
            summary=f"Missing test files: {missing_files}"
        )
        markdown = generate_markdown_report(report)
        save_report(report, markdown)
        sys.exit(1)

    # Run pytest
    test_results = run_pytest_tests(CONTRACT_TEST_FILES)

    if test_results["json_output"]:
        parsed_results = parse_pytest_json_report(test_results["json_output"])
    else:
        # Fallback: parse stdout if JSON not available
        parsed_results = []
        logger.warning("Could not parse JSON output, using stdout fallback")
        # Simple parsing of pytest output
        for line in test_results["stdout"].split("\n"):
            if "PASSED" in line or "FAILED" in line or "SKIPPED" in line:
                parts = line.strip().split()
                if parts:
                    test_name = parts[0]
                    passed = "PASSED" in line
                    parsed_results.append(TestResult(
                        test_name=test_name,
                        passed=passed,
                        duration=0.0,
                        message=line
                    ))

    # Calculate summary
    total = len(parsed_results)
    passed = sum(1 for r in parsed_results if r.passed)
    failed = sum(1 for r in parsed_results if not r.passed)
    skipped = sum(1 for r in parsed_results if r.duration == 0.0 and not r.passed)
    total_duration = sum(r.duration for r in parsed_results)

    report = TestReport(
        timestamp=datetime.now().isoformat(),
        total_tests=total,
        passed_tests=passed,
        failed_tests=failed,
        skipped_tests=skipped,
        total_duration=total_duration,
        results=parsed_results,
        summary=f"Passed: {passed}/{total} ({100*passed/max(1,total):.1f}%)"
    )

    # Generate and save report
    markdown = generate_markdown_report(report)
    report_path = save_report(report, markdown)

    # Print summary
    print("\n" + "=" * 60)
    print(f"CONTRACT TEST SUMMARY (T076)")
    print("=" * 60)
    print(f"Total Tests:  {report.total_tests}")
    print(f"Passed:       {report.passed_tests} ✅")
    print(f"Failed:       {report.failed_tests} ❌")
    print(f"Skipped:      {report.skipped_tests}")
    print(f"Duration:     {report.total_duration:.2f}s")
    print(f"Report:       {report_path}")
    print("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if report.failed_tests == 0 else 1)

if __name__ == "__main__":
    main()
