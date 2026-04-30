"""
Data directory structure setup script for PROJ-024.

Creates the required data directory structure:
- data/raw/      : Raw downloaded datasets
- data/processed/: Processed/feature-engineered datasets

Per plan.md Phase 1 Setup requirements.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine project root (parent of code/ directory)
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent
    project_root = code_dir.parent
    
    # Define data directories
    data_root = project_root / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    
    # Create directories with parents
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep files to ensure directories are tracked in git
    (data_root / ".gitkeep").touch()
    (raw_dir / ".gitkeep").touch()
    (processed_dir / ".gitkeep").touch()
    
    print(f"✓ Created data directory structure:")
    print(f"  - {data_root}")
    print(f"  - {raw_dir}")
    print(f"  - {processed_dir}")
    print(f"✓ Setup complete for T011")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
