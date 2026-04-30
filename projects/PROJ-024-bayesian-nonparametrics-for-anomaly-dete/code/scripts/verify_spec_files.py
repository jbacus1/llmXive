#!/usr/bin/env python3
"""
Verify presence of required spec documents per plan.md Phase 0/1 requirements.

Checks for:
- research.md (literature review and DPGMM theoretical foundations)
- data-model.md (entity definitions and schema specifications)
- quickstart.md (usage examples and installation instructions)

These files must exist in specs/001-bayesian-nonparametrics-anomaly-detection/
before Phase 1 Setup can begin.
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any
import json

@dataclass
class FileVerification:
    path: str
    exists: bool
    size_bytes: int
    has_content: bool
    status: str

def get_project_root() -> Path:
    """Get the project root directory."""
    # Try multiple common locations
    candidates = [
        Path.cwd(),
        Path.cwd().parent,
        Path(__file__).parent.parent.parent,
    ]
    
    for candidate in candidates:
        if (candidate / "tasks.md").exists():
            return candidate
    
    # Default to current working directory
    return Path.cwd()

def get_spec_dir(project_root: Path) -> Path:
    """Get the specs directory path."""
    return project_root / "specs" / "001-bayesian-nonparametrics-anomaly-detection"

def verify_file(file_path: Path) -> FileVerification:
    """Verify a single file's presence and content."""
    exists = file_path.exists()
    size_bytes = file_path.stat().st_size if exists else 0
    has_content = size_bytes > 0 if exists else False
    
    if not exists:
        status = "MISSING"
    elif not has_content:
        status = "EMPTY"
    else:
        status = "OK"
    
    return FileVerification(
        path=str(file_path),
        exists=exists,
        size_bytes=size_bytes,
        has_content=has_content,
        status=status
    )

def verify_spec_files() -> Dict[str, Any]:
    """Verify all required spec files exist with content."""
    project_root = get_project_root()
    spec_dir = get_spec_dir(project_root)
    
    required_files = [
        "research.md",
        "data-model.md",
        "quickstart.md",
    ]
    
    results = []
    all_ok = True
    
    print(f"Verifying spec files in: {spec_dir}")
    print(f"Project root: {project_root}")
    print("-" * 60)
    
    for filename in required_files:
        file_path = spec_dir / filename
        verification = verify_file(file_path)
        results.append(verification)
        
        status_icon = "✓" if verification.status == "OK" else "✗"
        print(f"{status_icon} {filename}: {verification.status} ({verification.size_bytes} bytes)")
        
        if verification.status != "OK":
            all_ok = False
    
    print("-" * 60)
    
    # Summary
    ok_count = sum(1 for r in results if r.status == "OK")
    total_count = len(results)
    
    print(f"Summary: {ok_count}/{total_count} files verified")
    
    if all_ok:
        print("✓ All required spec files are present and have content.")
    else:
        print("✗ Some required spec files are missing or empty.")
    
    return {
        "project_root": str(project_root),
        "spec_dir": str(spec_dir),
        "all_ok": all_ok,
        "ok_count": ok_count,
        "total_count": total_count,
        "files": [
            {
                "path": r.path,
                "exists": r.exists,
                "size_bytes": r.size_bytes,
                "has_content": r.has_content,
                "status": r.status,
            }
            for r in results
        ],
    }

def main():
    """Main entry point."""
    try:
        result = verify_spec_files()
        
        # Exit with appropriate code
        sys.exit(0 if result["all_ok"] else 1)
        
    except Exception as e:
        print(f"ERROR: Verification failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    main()
