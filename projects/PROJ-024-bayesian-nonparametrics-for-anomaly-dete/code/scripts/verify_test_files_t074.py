"""
T074 Verification Script: Verify test files exist and are functional.

Checks:
- tests/contract/test_metrics_schema.py exists and is importable
- tests/integration/test_baseline_comparison.py exists and is importable
- pytest discovery works for both files
"""
import sys
import os
from pathlib import Path
import subprocess
import json
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestFileStatus:
    file_path: str
    exists: bool
    importable: bool
    pytest_discoverable: bool
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

@dataclass
class VerificationReport:
    status: str  # "PASS", "FAIL", "PARTIAL"
    files: List[TestFileStatus]
    summary: str
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            from datetime import datetime
            self.timestamp = datetime.now().isoformat()

def check_file_exists(file_path: Path) -> Tuple[bool, Optional[str]]:
    """Check if file exists and is readable."""
    if not file_path.exists():
        return False, f"File does not exist: {file_path}"
    if not file_path.is_file():
        return False, f"Path is not a file: {file_path}"
    if not os.access(file_path, os.R_OK):
        return False, f"File is not readable: {file_path}"
    return True, None

def check_file_importable(file_path: Path, project_root: Path) -> Tuple[bool, Optional[str]]:
    """Check if Python file can be imported."""
    if not file_path.suffix == '.py':
        return False, "Not a Python file"
    
    # Add project root to path for imports
    sys_path_backup = sys.path.copy()
    try:
        sys.path.insert(0, str(project_root))
        
        # Convert path to module path
        rel_path = file_path.relative_to(project_root)
        module_path = str(rel_path).replace('/', '.').replace(os.sep, '.')
        module_path = module_path[:-3]  # Remove .py
        
        logger.info(f"Attempting to import: {module_path}")
        
        # Try to import
        import importlib.util
        spec = importlib.util.spec_from_file_location(module_path, file_path)
        if spec is None or spec.loader is None:
            return False, "Could not create module spec"
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        logger.info(f"Successfully imported: {module_path}")
        return True, None
        
    except Exception as e:
        return False, f"Import error: {str(e)}"
    finally:
        sys.path = sys_path_backup

def check_pytest_discovery(file_path: Path, project_root: Path) -> Tuple[bool, Optional[str]]:
    """Check if pytest can discover tests in the file."""
    try:
        # Run pytest with --collect-only to discover tests
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', 
             str(file_path), 
             '--collect-only',
             '-q'],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check if pytest found tests
        if result.returncode == 0:
            # Check output for test collection
            if 'test_' in result.stdout or 'no tests collected' in result.stdout:
                return True, None
            return False, f"No tests found in output: {result.stdout[:200]}"
        else:
            # pytest error - check stderr
            stderr = result.stderr[:500] if result.stderr else "No error output"
            return False, f"pytest error: {stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "pytest discovery timed out"
    except Exception as e:
        return False, f"pytest discovery error: {str(e)}"

def verify_test_files(project_root: Path) -> VerificationReport:
    """Verify all T074 test files exist and are functional."""
    
    # Define files to verify
    test_files = [
        project_root / 'tests' / 'contract' / 'test_metrics_schema.py',
        project_root / 'tests' / 'integration' / 'test_baseline_comparison.py'
    ]
    
    file_statuses = []
    all_passed = True
    
    for file_path in test_files:
        logger.info(f"Verifying: {file_path}")
        
        status = TestFileStatus(
            file_path=str(file_path.relative_to(project_root))
        )
        
        # Check existence
        exists, err = check_file_exists(file_path)
        status.exists = exists
        if err:
            status.errors.append(err)
            all_passed = False
            logger.warning(f"  - Exists check failed: {err}")
        else:
            logger.info(f"  - Exists: OK")
        
        if not exists:
            file_statuses.append(status)
            continue
        
        # Check importability
        importable, err = check_file_importable(file_path, project_root)
        status.importable = importable
        if err:
            status.errors.append(err)
            all_passed = False
            logger.warning(f"  - Import check failed: {err}")
        else:
            logger.info(f"  - Importable: OK")
        
        # Check pytest discovery
        discoverable, err = check_pytest_discovery(file_path, project_root)
        status.pytest_discoverable = discoverable
        if err:
            status.errors.append(err)
            all_passed = False
            logger.warning(f"  - pytest discovery failed: {err}")
        else:
            logger.info(f"  - pytest discoverable: OK")
        
        file_statuses.append(status)
    
    # Determine overall status
    if all_passed:
        status_str = "PASS"
        summary = "All T074 test files exist, are importable, and pytest-discoverable"
    else:
        failed_count = sum(1 for f in file_statuses if f.errors)
        status_str = "FAIL" if failed_count == len(file_statuses) else "PARTIAL"
        summary = f"{failed_count}/{len(file_statuses)} test files have issues"
    
    return VerificationReport(
        status=status_str,
        files=file_statuses,
        summary=summary
    )

def print_report(report: VerificationReport) -> None:
    """Print verification report to stdout."""
    print("\n" + "="*60)
    print("T074 TEST FILE VERIFICATION REPORT")
    print("="*60)
    print(f"Timestamp: {report.timestamp}")
    print(f"Status: {report.status}")
    print(f"Summary: {report.summary}")
    print("-"*60)
    
    for file_status in report.files:
        print(f"\nFile: {file_status.file_path}")
        print(f"  Exists: {'✓' if file_status.exists else '✗'}")
        print(f"  Importable: {'✓' if file_status.importable else '✗'}")
        print(f"  pytest-discoverable: {'✓' if file_status.pytest_discoverable else '✗'}")
        if file_status.errors:
            print("  Errors:")
            for err in file_status.errors:
                print(f"    - {err}")
    
    print("\n" + "="*60)
    print(f"FINAL RESULT: {report.status}")
    print("="*60 + "\n")

def main():
    """Main entry point for T074 verification."""
    # Determine project root
    project_root = Path(__file__).parent.parent.parent
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Run verification
    report = verify_test_files(project_root)
    
    # Print report
    print_report(report)
    
    # Save report as JSON for CI
    report_path = project_root / 'state' / 't074_verification_report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(asdict(report), f, indent=2)
    
    logger.info(f"Report saved to: {report_path}")
    
    # Exit with appropriate code
    if report.status == "PASS":
        logger.info("T074 verification PASSED")
        sys.exit(0)
    else:
        logger.error("T074 verification FAILED")
        sys.exit(1)

if __name__ == '__main__':
    main()
