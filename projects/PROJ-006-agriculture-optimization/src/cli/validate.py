"""
Fail-fast validation module for Climate-Smart Agricultural Practices project.

This module provides validation checks that MUST pass before any data collection,
processing, or analysis operations can proceed. Validation failures should halt
execution immediately with clear error messages.

Validates:
- API keys (OpenWeatherMap, USGS)
- Disk space availability
- Required file existence
- Environment configuration

Usage:
    from src.cli.validate import validate_all, validate_api_keys, validate_disk_space
    
    if not validate_all():
        exit(1)

Principle V Compliance: All API calls must have fail-fast validation.
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

# Import project constants (set up in T006)
try:
    from src.config.constants import (
        REQUIRED_ENV_VARS,
        API_KEY_ENV_VARS,
        MIN_DISK_SPACE_GB,
        REQUIRED_FILES,
        DATA_DIR,
        LOGS_DIR,
    )
except ImportError:
    # Fallback defaults if constants not yet available
    REQUIRED_ENV_VARS = ["PROJECT_ID"]
    API_KEY_ENV_VARS = ["OPENWEATHER_API_KEY", "USGS_API_KEY"]
    MIN_DISK_SPACE_GB = 5.0
    REQUIRED_FILES = ["tasks.md", "plan.md", "spec.md"]
    DATA_DIR = "data"
    LOGS_DIR = "logs"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cli.validate")

class ValidationStatus(Enum):
    """Status of a validation check."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"

@dataclass
class ValidationResult:
    """Result of a single validation check."""
    name: str
    status: ValidationStatus
    message: str
    details: Optional[str] = None
    is_critical: bool = True
    
    def __bool__(self) -> bool:
        return self.status == ValidationStatus.PASSED

@dataclass
class ValidationReport:
    """Aggregate validation report."""
    checks: List[ValidationResult]
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    
    @property
    def is_valid(self) -> bool:
        """True if no critical checks failed."""
        return all(check.is_critical or check.status == ValidationStatus.PASSED 
                  for check in self.checks)

def validate_api_keys() -> ValidationResult:
    """
    Validate that required API keys are present in environment.
    
    Checks for OpenWeatherMap and USGS API keys as per project requirements.
    
    Returns:
        ValidationResult indicating pass/fail status.
    """
    missing_keys = []
    
    for key in API_KEY_ENV_VARS:
        if not os.environ.get(key):
            missing_keys.append(key)
    
    if missing_keys:
        return ValidationResult(
            name="API Keys",
            status=ValidationStatus.FAILED,
            message=f"Missing required API keys: {', '.join(missing_keys)}",
            details="Set environment variables before running data collection.",
            is_critical=True
        )
    
    logger.info("API keys validation passed")
    return ValidationResult(
        name="API Keys",
        status=ValidationStatus.PASSED,
        message="All required API keys are configured",
        is_critical=True
    )

def validate_disk_space(min_gb: float = MIN_DISK_SPACE_GB) -> ValidationResult:
    """
    Validate that sufficient disk space is available.
    
    Args:
        min_gb: Minimum required disk space in gigabytes.
    
    Returns:
        ValidationResult indicating pass/fail status.
    """
    try:
        # Get disk usage for the project root
        project_root = Path(__file__).resolve().parent.parent.parent
        stat = shutil.disk_usage(project_root)
        
        available_gb = stat.free / (1024 ** 3)
        
        if available_gb < min_gb:
            return ValidationResult(
                name="Disk Space",
                status=ValidationStatus.FAILED,
                message=f"Insufficient disk space: {available_gb:.2f}GB available, {min_gb}GB required",
                details=f"Free: {available_gb:.2f}GB, Used: {stat.used / (1024 ** 3):.2f}GB",
                is_critical=True
            )
        
        logger.info(f"Disk space validation passed ({available_gb:.2f}GB available)")
        return ValidationResult(
            name="Disk Space",
            status=ValidationStatus.PASSED,
            message=f"Sufficient disk space available ({available_gb:.2f}GB)",
            is_critical=True
        )
    except Exception as e:
        return ValidationResult(
            name="Disk Space",
            status=ValidationStatus.FAILED,
            message=f"Failed to check disk space: {str(e)}",
            is_critical=True
        )

def validate_file_existence(files: List[str] = None) -> ValidationResult:
    """
    Validate that required files exist in the project.
    
    Args:
        files: List of relative file paths to check. Defaults to REQUIRED_FILES.
    
    Returns:
        ValidationResult indicating pass/fail status.
    """
    files = files or REQUIRED_FILES
    missing_files = []
    
    project_root = Path(__file__).resolve().parent.parent.parent
    
    for file_path in files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        return ValidationResult(
            name="File Existence",
            status=ValidationStatus.FAILED,
            message=f"Missing required files: {', '.join(missing_files)}",
            details="Run project setup or restore files from source control.",
            is_critical=True
        )
    
    logger.info("File existence validation passed")
    return ValidationResult(
        name="File Existence",
        status=ValidationStatus.PASSED,
        message=f"All {len(files)} required files present",
        is_critical=True
    )

def validate_data_directory() -> ValidationResult:
    """
    Validate that data directories exist and are writable.
    
    Returns:
        ValidationResult indicating pass/fail status.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    
    required_dirs = [
        project_root / DATA_DIR / "raw",
        project_root / DATA_DIR / "processed",
        project_root / DATA_DIR / "cache",
        LOGS_DIR,
    ]
    
    missing_dirs = []
    unwritable_dirs = []
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            missing_dirs.append(str(dir_path.relative_to(project_root)))
        elif not os.access(dir_path, os.W_OK):
            unwritable_dirs.append(str(dir_path.relative_to(project_root)))
    
    if missing_dirs:
        # Try to create missing directories
        created = []
        for dir_name in missing_dirs:
            try:
                (project_root / dir_name).mkdir(parents=True, exist_ok=True)
                created.append(dir_name)
            except Exception:
                pass
        
        still_missing = [d for d in missing_dirs if d not in created]
        if still_missing:
            return ValidationResult(
                name="Data Directories",
                status=ValidationStatus.FAILED,
                message=f"Could not create data directories: {', '.join(still_missing)}",
                is_critical=True
            )
    
    if unwritable_dirs:
        return ValidationResult(
            name="Data Directories",
            status=ValidationStatus.FAILED,
            message=f"Data directories not writable: {', '.join(unwritable_dirs)}",
            is_critical=True
        )
    
    logger.info("Data directory validation passed")
    return ValidationResult(
        name="Data Directories",
        status=ValidationStatus.PASSED,
        message="All data directories exist and are writable",
        is_critical=True
    )

def validate_python_version(min_version: Tuple[int, int, int] = (3, 11, 0)) -> ValidationResult:
    """
    Validate Python version meets minimum requirements.
    
    Args:
        min_version: Minimum required version tuple (major, minor, micro).
    
    Returns:
        ValidationResult indicating pass/fail status.
    """
    current = sys.version_info[:3]
    
    if current < min_version:
        return ValidationResult(
            name="Python Version",
            status=ValidationStatus.FAILED,
            message=f"Python {current[0]}.{current[1]}.{current[2]} found, "
                   f"{min_version[0]}.{min_version[1]}.{min_version[2]} required",
            is_critical=True
        )
    
    logger.info(f"Python version validation passed ({current[0]}.{current[1]}.{current[2]})")
    return ValidationResult(
        name="Python Version",
        status=ValidationStatus.PASSED,
        message=f"Python {current[0]}.{current[1]}.{current[2]} meets requirements",
        is_critical=True
    )

def validate_all(checks: Optional[List[Callable]] = None) -> bool:
    """
    Run all validation checks and report results.
    
    Args:
        checks: Optional list of specific validation functions to run.
               Defaults to all standard checks.
    
    Returns:
        True if all critical checks passed, False otherwise.
    """
    if checks is None:
        checks = [
            validate_python_version,
            validate_api_keys,
            validate_disk_space,
            validate_file_existence,
            validate_data_directory,
        ]
    
    report = ValidationReport(checks=[])
    
    logger.info("=" * 60)
    logger.info("Starting fail-fast validation")
    logger.info("=" * 60)
    
    for check_func in checks:
        try:
            result = check_func()
            report.checks.append(result)
            
            status_symbol = "✓" if result.status == ValidationStatus.PASSED else "✗"
            logger.info(f"{status_symbol} {result.name}: {result.message}")
            
            if result.status == ValidationStatus.PASSED:
                report.passed += 1
            elif result.status == ValidationStatus.FAILED:
                report.failed += 1
            else:
                report.warnings += 1
                
        except Exception as e:
            error_result = ValidationResult(
                name=check_func.__name__,
                status=ValidationStatus.FAILED,
                message=f"Validation check raised exception: {str(e)}",
                is_critical=True
            )
            report.checks.append(error_result)
            report.failed += 1
            logger.error(f"Validation check {check_func.__name__} failed with exception: {e}")
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"Validation Summary: {report.passed} passed, {report.failed} failed")
    logger.info("=" * 60)
    
    if not report.is_valid:
        logger.error("FAIL-FAST: One or more critical validations failed. Exiting.")
        return False
    
    logger.info("All validations passed. Ready to proceed.")
    return True

def main():
    """CLI entry point for validation."""
    if not validate_all():
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()