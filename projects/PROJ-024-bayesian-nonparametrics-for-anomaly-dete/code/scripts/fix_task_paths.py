"""
Fix task path references in tasks.md after restructuring.

This script applies the suggested path corrections from the verification
report to tasks.md. Run this AFTER running verify_task_paths.py.

WARNING: This script WILL modify tasks.md. Ensure you have a backup.
"""
import re
import sys
import json
from pathlib import Path
from datetime import datetime
import shutil

PROJ_ID = "PROJ-024-bayesian-nonparametrics-for-anomaly-dete"

# Path replacements after T060 restructuring
REPLACEMENTS = {
    f"projects/{PROJ_ID}/code/models/": f"projects/{PROJ_ID}/code/src/models/",
    f"projects/{PROJ_ID}/code/baselines/": f"projects/{PROJ_ID}/code/src/baselines/",
    f"projects/{PROJ_ID}/code/evaluation/": f"projects/{PROJ_ID}/code/src/evaluation/",
    f"projects/{PROJ_ID}/code/utils/": f"projects/{PROJ_ID}/code/src/utils/",
    f"projects/{PROJ_ID}/code/data/": f"projects/{PROJ_ID}/code/src/data/",
    f"projects/{PROJ_ID}/code/scripts/": f"projects/{PROJ_ID}/code/scripts/",  # unchanged
    f"projects/{PROJ_ID}/code/src/models/": f"projects/{PROJ_ID}/code/src/models/",  # already correct
    f"projects/{PROJ_ID}/code/src/baselines/": f"projects/{PROJ_ID}/code/src/baselines/",
    f"projects/{PROJ_ID}/code/src/evaluation/": f"projects/{PROJ_ID}/code/src/evaluation/",
    f"projects/{PROJ_ID}/code/src/utils/": f"projects/{PROJ_ID}/code/src/utils/",
    f"projects/{PROJ_ID}/code/src/data/": f"projects/{PROJ_ID}/code/src/data/",
}

def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent.parent.parent.parent
    tasks_md_path = repo_root / "tasks.md"
    report_path = Path(__file__).parent / "reports" / "task_path_verification_report.json"
    
    if not tasks_md_path.exists():
        print(f"ERROR: tasks.md not found at {tasks_md_path}")
        sys.exit(1)
    
    # Create backup
    backup_path = tasks_md_path.parent / f"tasks.md.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(tasks_md_path, backup_path)
    print(f"Created backup at: {backup_path}")
    
    # Load content
    content = tasks_md_path.read_text(encoding="utf-8")
    original_content = content
    
    # Apply replacements
    replacements_made = 0
    for old_pattern, new_pattern in REPLACEMENTS.items():
        if old_pattern != new_pattern:
            new_content = content.replace(old_pattern, new_pattern)
            if new_content != content:
                replacements_made += content.count(old_pattern)
                content = new_content
    
    # Save updated content
    if content != original_content:
        tasks_md_path.write_text(content, encoding="utf-8")
        print(f"✅ Applied {replacements_made} path replacements to tasks.md")
        print(f"   Backup available at: {backup_path}")
        sys.exit(0)
    else:
        print("✅ No replacements needed - all paths already correct!")
        sys.exit(0)

if __name__ == "__main__":
    main()
