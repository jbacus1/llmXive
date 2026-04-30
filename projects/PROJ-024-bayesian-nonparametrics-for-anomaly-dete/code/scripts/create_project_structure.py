#!/usr/bin/env python3
"""
Create the project directory structure for the Bayesian Nonparametrics
Anomaly Detection project.

This script creates all required directories as specified in the
implementation plan and plan.md Phase 1/2 specifications.

Structure created:
projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/
├── code/
│   ├── src/
│   │   ├── baselines/
│   │   ├── data/
│   │   ├── evaluation/
│   │   ├── models/
│   │   ├── services/
│   │   └── utils/
│   ├── scripts/
│   ├── requirements.txt
│   └── config.yaml
├── data/
│   ├── raw/
│   └── processed/
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
├── state/
└── specs/
    └── 001-bayesian-nonparametrics-anomaly-detection/
"""
import os
import sys
from pathlib import Path

def create_directory_structure():
    """Create all required project directories."""
    # Project root
    project_root = Path("projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete")
    
    # Code directories (per plan.md and Constitution Principle V)
    code_dirs = [
        "code/src/baselines",
        "code/src/data",
        "code/src/evaluation",
        "code/src/models",
        "code/src/services",
        "code/src/utils",
        "code/scripts",
    ]
    
    # Data directories (per FR-007)
    data_dirs = [
        "data/raw",
        "data/processed",
    ]
    
    # Test directories (per Phase 2 T011)
    test_dirs = [
        "tests/contract",
        "tests/integration",
        "tests/unit",
    ]
    
    # State directory (per Constitution Principle III)
    state_dirs = [
        "state/projects",
    ]
    
    # Specs directory (per Phase 0)
    specs_dirs = [
        "specs/001-bayesian-nonparametrics-anomaly-detection",
    ]
    
    # All directories to create
    all_dirs = code_dirs + data_dirs + test_dirs + state_dirs + specs_dirs
    
    # Create directories
    created = []
    for dir_path in all_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created.append(str(full_path))
        print(f"✓ Created: {full_path}")
    
    # Create __init__.py files in Python packages
    python_dirs = [
        "code/src/baselines",
        "code/src/data",
        "code/src/evaluation",
        "code/src/models",
        "code/src/services",
        "code/src/utils",
        "code/scripts",
        "tests/contract",
        "tests/integration",
        "tests/unit",
    ]
    
    for dir_path in python_dirs:
        full_path = project_root / dir_path
        init_file = full_path / "__init__.py"
        if not init_file.exists():
          init_file.write_text("# Package initialization\n")
          print(f"✓ Created: {init_file}")
    
    print(f"\n✓ Successfully created {len(created)} directories")
    print(f"Project root: {project_root}")
    return True

def main():
    """Entry point."""
    print("=" * 60)
    print("Creating Project Directory Structure")
    print("=" * 60)
    
    success = create_directory_structure()
    
    if success:
        print("\n" + "=" * 60)
        print("Project structure creation complete!")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("ERROR: Failed to create project structure")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
