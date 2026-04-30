"""
Verify presence of required specification documents per plan.md Phase 0/1 requirements.

This script checks that the following files exist in the specs directory:
- research.md (literature review and DPGMM theoretical foundations)
- data-model.md (entity definitions and schema specifications)
- quickstart.md (usage examples and installation instructions)

Usage:
    python verify_spec_docs.py
"""
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple
import logging
from dataclasses import dataclass, field
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DocVerificationResult:
    """Result of verifying a single specification document."""
    filename: str
    path: Path
    exists: bool
    size_bytes: int = 0
    line_count: int = 0
    verified: bool = False
    error_message: str = ""

@dataclass
class VerificationReport:
    """Full verification report for specification documents."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    project_root: Path = field(default_factory=lambda: Path.cwd())
    specs_dir: Path = field(default_factory=lambda: Path("specs/001-bayesian-nonparametrics-anomaly-detection"))
    results: List[DocVerificationResult] = field(default_factory=list)
    all_verified: bool = False
    total_files: int = 0
    verified_count: int = 0

def get_project_root() -> Path:
    """Determine the project root directory."""
    # Look for the project root by finding the code directory
    current = Path.cwd()
    
    # Check if we're already in the project root
    if (current / "code").exists() and (current / "specs").exists():
        return current
    
    # Search parent directories
    for parent in current.parents:
        if (parent / "code").exists() and (parent / "specs").exists():
            return parent
    
    # Default to current directory
    logger.warning("Could not determine project root, using current directory")
    return current

def verify_document(filepath: Path, required: bool = True) -> DocVerificationResult:
    """Verify a single specification document exists and is valid."""
    result = DocVerificationResult(
        filename=filepath.name,
        path=filepath,
        exists=filepath.exists()
    )
    
    if not result.exists:
        result.error_message = f"File does not exist: {filepath}"
        result.verified = False
        return result
    
    try:
        # Check file size
        result.size_bytes = filepath.stat().st_size
        
        # Check line count
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            result.line_count = len(lines)
        
        # Verify it's not empty
        if result.size_bytes == 0:
            result.error_message = "File exists but is empty"
            result.verified = False
            return result
        
        # Verify it has content
        if result.line_count < 3:
            result.error_message = f"File has too few lines ({result.line_count})"
            result.verified = False
            return result
        
        result.verified = True
        result.error_message = ""
        
    except Exception as e:
        result.error_message = f"Error reading file: {str(e)}"
        result.verified = False
    
    return result

def verify_spec_docs(specs_dir: Path) -> VerificationReport:
    """
    Verify presence of all required specification documents.
    
    Required documents per plan.md Phase 0/1:
    - research.md: Literature review and DPGMM theoretical foundations
    - data-model.md: Entity definitions and schema specifications
    - quickstart.md: Usage examples and installation instructions
    """
    report = VerificationReport(specs_dir=specs_dir)
    report.total_files = 3
    
    required_docs = [
        "research.md",
        "data-model.md",
        "quickstart.md"
    ]
    
    logger.info(f"Verifying specification documents in: {specs_dir}")
    logger.info(f"Expected {report.total_files} documents")
    
    for doc_name in required_docs:
        doc_path = specs_dir / doc_name
        result = verify_document(doc_path)
        report.results.append(result)
        
        if result.verified:
            report.verified_count += 1
            logger.info(f"✓ {doc_name}: OK ({result.size_bytes} bytes, {result.line_count} lines)")
        else:
            logger.error(f"✗ {doc_name}: FAILED - {result.error_message}")
    
    report.all_verified = report.verified_count == report.total_files
    
    return report

def print_report(report: VerificationReport) -> None:
    """Print a formatted verification report to console."""
    print("\n" + "=" * 70)
    print("SPECIFICATION DOCUMENT VERIFICATION REPORT")
    print("=" * 70)
    print(f"Timestamp: {report.timestamp}")
    print(f"Project Root: {report.project_root}")
    print(f"Specs Directory: {report.specs_dir}")
    print("-" * 70)
    
    for result in report.results:
        status = "✓ VERIFIED" if result.verified else "✗ FAILED"
        print(f"\n{result.filename}")
        print(f"  Path: {result.path}")
        print(f"  Status: {status}")
        if result.exists:
            print(f"  Size: {result.size_bytes} bytes")
            print(f"  Lines: {result.line_count}")
        if result.error_message:
            print(f"  Error: {result.error_message}")
    
    print("\n" + "-" * 70)
    print(f"Summary: {report.verified_count}/{report.total_files} documents verified")
    print(f"Overall Status: {'✓ ALL VERIFIED' if report.all_verified else '✗ VERIFICATION FAILED'}")
    print("=" * 70 + "\n")

def save_report(report: VerificationReport, output_path: Path) -> None:
    """Save the verification report as JSON."""
    report_dict = {
        "timestamp": report.timestamp,
        "project_root": str(report.project_root),
        "specs_dir": str(report.specs_dir),
        "total_files": report.total_files,
        "verified_count": report.verified_count,
        "all_verified": report.all_verified,
        "results": [
            {
                "filename": r.filename,
                "path": str(r.path),
                "exists": r.exists,
                "size_bytes": r.size_bytes,
                "line_count": r.line_count,
                "verified": r.verified,
                "error_message": r.error_message
            }
            for r in report.results
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_dict, f, indent=2)
    
    logger.info(f"Report saved to: {output_path}")

def main() -> int:
    """Main entry point for the verification script."""
    logger.info("Starting specification document verification...")
    
    # Determine project root and specs directory
    project_root = get_project_root()
    specs_dir = project_root / "specs" / "001-bayesian-nonparametrics-anomaly-detection"
    
    # Ensure specs directory exists
    if not specs_dir.exists():
        logger.error(f"Specs directory does not exist: {specs_dir}")
        logger.info("Please ensure Phase 0 design documents have been created first (T000-T002)")
        return 1
    
    # Run verification
    report = verify_spec_docs(specs_dir)
    
    # Print report
    print_report(report)
    
    # Save report to state directory
    state_dir = project_root / "state"
    state_dir.mkdir(exist_ok=True)
    report_path = state_dir / "spec_docs_verification.json"
    save_report(report, report_path)
    
    # Return appropriate exit code
    if report.all_verified:
        logger.info("All specification documents verified successfully")
        return 0
    else:
        logger.error("Some specification documents are missing or invalid")
        logger.info("Please complete Phase 0 tasks (T000-T002) to create the required documents")
        return 1

if __name__ == "__main__":
    sys.exit(main())
