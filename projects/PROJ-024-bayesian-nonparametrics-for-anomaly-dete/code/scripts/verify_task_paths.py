"""
Verify and report task path references in tasks.md after restructuring.

This script scans tasks.md for file path references and validates they
use the correct `projects/.../code/src/` structure per Constitution
Principle V and T060 restructuring requirements.

CRITICAL: This script ONLY REPORTS issues — it does NOT modify tasks.md.
The Tasker agent must apply any necessary corrections to tasks.md.
"""
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set
import json
from datetime import datetime

# Expected project structure after T060 restructuring
PROJ_ID = "PROJ-024-bayesian-nonparametrics-for-anomaly-dete"
BASE_PATH = f"projects/{PROJ_ID}/code/src"

# Known correct paths after restructuring (from API surface)
KNOWN_CORRECT_PATHS = {
    "code/src/models/dp_gmm.py",
    "code/src/models/anomaly_score.py",
    "code/src/models/time_series.py",
    "code/src/baselines/arima.py",
    "code/src/baselines/moving_average.py",
    "code/src/evaluation/metrics.py",
    "code/src/evaluation/plots.py",
    "code/src/evaluation/statistical_tests.py",
    "code/src/utils/streaming.py",
    "code/src/utils/memory_profiler.py",
    "code/src/utils/threshold.py",
    "code/src/utils/runtime_monitor.py",
    "code/src/utils/hyperparameter_counter.py",
    "code/src/data/synthetic_generator.py",
    "code/src/data/download_datasets.py",
    "code/src/services/anomaly_detector.py",
    "code/src/services/threshold_calibrator.py",
    "code/baselines/lstm_ae.py",  # T090 - may not exist yet
    "code/download_datasets.py",  # Root level script
    "code/config.yaml",
    "data/raw/",
    "data/processed/",
    "tests/contract/",
    "tests/integration/",
    "tests/unit/",
    "specs/001-bayesian-nonparametrics-anomaly-detection/",
    "state/projects/",
    ".github/workflows/",
}

# Old incorrect paths that should be replaced
INCORRECT_PATTERNS = [
    r"projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/",
    r"projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/baselines/",
    r"projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/evaluation/",
    r"projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/utils/",
    r"projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/data/",
]

def load_tasks_md(path: Path) -> str:
    """Load tasks.md content."""
    if not path.exists():
        print(f"ERROR: tasks.md not found at {path}")
        sys.exit(1)
    return path.read_text(encoding="utf-8")

def extract_file_references(text: str) -> List[Tuple[int, str, str]]:
    """
    Extract all file path references from tasks.md.
    Returns list of (line_number, task_id, file_path).
    """
    references = []
    
    # Pattern 1: `path/to/file.py` style references
    pattern1 = r"`(projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/[^\`]+)`"
    
    # Pattern 2: Direct path mentions like projects/.../code/models/
    pattern2 = r"projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/[^\s\`\(\)]+\.(py|yaml|md|txt)"
    
    lines = text.split("\n")
    for line_num, line in enumerate(lines, 1):
        # Find all matches in this line
        for match in re.finditer(pattern1, line):
            path_str = match.group(1)
            task_match = re.search(r"\[T(\d+)\]", line)
            task_id = f"T{task_match.group(1)}" if task_match else "UNKNOWN"
            references.append((line_num, task_id, path_str))
        
        for match in re.finditer(pattern2, line):
            path_str = match.group(0)
            task_match = re.search(r"\[T(\d+)\]", line)
            task_id = f"T{task_match.group(1)}" if task_match else "UNKNOWN"
            references.append((line_num, task_id, path_str))
    
    return references

def categorize_paths(references: List[Tuple[int, str, str]]) -> Dict[str, List[Tuple[int, str, str]]]:
    """Categorize paths as correct, incorrect, or unknown."""
    categorized = {
        "correct": [],
        "incorrect": [],
        "unknown": [],
    }
    
    for line_num, task_id, path_str in references:
        # Check if path contains old incorrect patterns
        is_incorrect = False
        for pattern in INCORRECT_PATTERNS:
            if re.search(pattern, path_str):
                is_incorrect = True
                break
        
        if is_incorrect:
            categorized["incorrect"].append((line_num, task_id, path_str))
        elif path_str in KNOWN_CORRECT_PATHS or path_str.startswith(BASE_PATH):
            categorized["correct"].append((line_num, task_id, path_str))
        else:
            categorized["unknown"].append((line_num, task_id, path_str))
    
    return categorized

def generate_suggestions(incorrect_paths: List[Tuple[int, str, str]]) -> List[Dict]:
    """Generate replacement suggestions for incorrect paths."""
    suggestions = []
    
    # Mapping of old patterns to new patterns
    replacements = {
        "/code/models/": "/code/src/models/",
        "/code/baselines/": "/code/src/baselines/",
        "/code/evaluation/": "/code/src/evaluation/",
        "/code/utils/": "/code/src/utils/",
        "/code/data/": "/code/src/data/",
    }
    
    for line_num, task_id, old_path in incorrect_paths:
        new_path = old_path
        for old_pattern, new_pattern in replacements.items():
            if old_pattern in old_path:
                new_path = old_path.replace(old_pattern, new_pattern)
                break
        
        suggestions.append({
            "line": line_num,
            "task_id": task_id,
            "old_path": old_path,
            "suggested_path": new_path,
        })
    
    return suggestions

def generate_report(categorized: Dict[str, List[Tuple[int, str, str]]], 
                   suggestions: List[Dict],
                   output_path: Path) -> Dict:
    """Generate a detailed verification report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_references": len(categorized["correct"]) + len(categorized["incorrect"]) + len(categorized["unknown"]),
            "correct_count": len(categorized["correct"]),
            "incorrect_count": len(categorized["incorrect"]),
            "unknown_count": len(categorized["unknown"]),
        },
        "incorrect_references": [
            {"line": r[0], "task_id": r[1], "path": r[2]}
            for r in categorized["incorrect"]
        ],
        "unknown_references": [
            {"line": r[0], "task_id": r[1], "path": r[2]}
            for r in categorized["unknown"]
        ],
        "suggestions": suggestions,
        "action_required": len(categorized["incorrect"]) > 0,
    }
    
    # Save report
    report_path = output_path / "task_path_verification_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    return report

def print_summary(report: Dict):
    """Print human-readable summary to stdout."""
    print("\n" + "="*70)
    print("TASK PATH VERIFICATION REPORT")
    print("="*70)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total references found: {report['summary']['total_references']}")
    print(f"  - Correct paths: {report['summary']['correct_count']}")
    print(f"  - Incorrect paths: {report['summary']['incorrect_count']}")
    print(f"  - Unknown paths: {report['summary']['unknown_count']}")
    print("-"*70)
    
    if report["incorrect_references"]:
        print("\n❌ INCORRECT PATHS (must be updated in tasks.md):")
        for ref in report["incorrect_references"]:
            print(f"   Line {ref['line']} [{ref['task_id']}]: {ref['path']}")
    
    if report["unknown_references"]:
        print("\n⚠️  UNKNOWN PATHS (verify manually):")
        for ref in report["unknown_references"]:
            print(f"   Line {ref['line']} [{ref['task_id']}]: {ref['path']}")
    
    if report["suggestions"]:
        print("\n📝 SUGGESTED REPLACEMENTS:")
        for sug in report["suggestions"]:
            print(f"   Line {sug['line']} [{sug['task_id']}]:")
            print(f"      OLD: {sug['old_path']}")
            print(f"      NEW: {sug['suggested_path']}")
    
    print("-"*70)
    if report["action_required"]:
        print("⚠️  ACTION REQUIRED: tasks.md must be updated by Tasker agent.")
        print("   Run: python code/scripts/fix_task_paths.py (if available)")
        print("   Or manually apply the suggested replacements above.")
    else:
        print("✅ All task paths are correctly structured!")
    print("="*70 + "\n")

def main():
    """Main entry point."""
    # Determine paths
    repo_root = Path(__file__).parent.parent.parent.parent.parent
    tasks_md_path = repo_root / "tasks.md"
    output_dir = Path(__file__).parent / "reports"
    output_dir.mkdir(exist_ok=True)
    
    print(f"Scanning tasks.md at: {tasks_md_path}")
    
    # Load and analyze
    content = load_tasks_md(tasks_md_path)
    references = extract_file_references(content)
    categorized = categorize_paths(references)
    suggestions = generate_suggestions(categorized["incorrect"])
    report = generate_report(categorized, suggestions, output_dir)
    
    # Print summary
    print_summary(report)
    
    # Exit with error if issues found
    if report["action_required"]:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
