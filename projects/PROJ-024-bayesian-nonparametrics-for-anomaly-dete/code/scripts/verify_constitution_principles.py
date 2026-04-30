"""
Verify Constitution Principles I-VII are satisfied and documented.

This script checks that all seven Constitution Principles are properly
implemented in the project and generates a verification report.

Constitution Principles:
I   - Reproducibility: pinned dependencies, .gitignore for cache/logs
II  - Task Isolation: implementer does not modify tasks.md
III - Data Integrity: SHA256 checksums recorded for all data artifacts
IV  - Path Conventions: files follow canonical project layout
V   - Project Structure: code/src/ hierarchy as specified in plan.md
VI  - ELBO Logging: convergence logging for variational inference
VII - API Consistency: imports match documented API surface
"""

import os
import sys
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

class VerificationResult:
    def __init__(self, principle: str, satisfied: bool, details: str, evidence: str = ""):
        self.principle = principle
        self.satisfied = satisfied
        self.details = details
        self.evidence = evidence
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "principle": self.principle,
            "satisfied": self.satisfied,
            "details": self.details,
            "evidence": self.evidence
        }

def verify_principle_i_reproducibility() -> VerificationResult:
    """Verify reproducibility requirements."""
    issues = []
    evidence = []
    
    # Check requirements.txt exists and is pinned
    req_file = PROJECT_ROOT / "code" / "requirements.txt"
    if not req_file.exists():
        issues.append("requirements.txt not found")
    else:
        content = req_file.read_text()
        # Check for pinned versions (==)
        pinned_lines = [l for l in content.split('\n') if '==' in l and not l.startswith('#')]
        if len(pinned_lines) == 0:
            issues.append("No pinned dependencies in requirements.txt")
        else:
            evidence.append(f"Found {len(pinned_lines)} pinned dependencies")
    
    # Check .gitignore for cache/logs
    gitignore = PROJECT_ROOT / ".gitignore"
    if not gitignore.exists():
        issues.append(".gitignore not found")
    else:
        content = gitignore.read_text()
        patterns = ['__pycache__', '*.pyc', '*.log']
        for pattern in patterns:
            if pattern not in content:
                issues.append(f".gitignore missing pattern: {pattern}")
        evidence.append(f".gitignore contains cache/log exclusions")
    
    # Check state directory for reproducibility
    state_dir = PROJECT_ROOT / "state"
    if not state_dir.exists():
        issues.append("state/ directory not found (needed for reproducibility)")
    else:
        evidence.append("state/ directory exists for artifact tracking")
    
    satisfied = len(issues) == 0
    return VerificationResult(
        principle="I - Reproducibility",
        satisfied=satisfied,
        details="; ".join(issues) if issues else "All reproducibility requirements met",
        evidence="; ".join(evidence)
    )

def verify_principle_ii_task_isolation() -> VerificationResult:
    """Verify implementer does not modify tasks.md."""
    issues = []
    evidence = []
    
    tasks_file = PROJECT_ROOT / "tasks.md"
    if tasks_file.exists():
        # Check if tasks.md has been modified by checking for implementation artifacts
        # that should NOT be in tasks.md
        content = tasks_file.read_text()
        
        # Tasks.md should only contain task descriptions, not implementation code
        if "def " in content or "import " in content:
            issues.append("tasks.md contains implementation code (should only have task descriptions)")
        else:
            evidence.append("tasks.md contains only task descriptions")
        
        # Count completed tasks
        completed = len(re.findall(r'\[X\]', content))
        evidence.append(f"Found {completed} completed tasks marked with [X]")
    else:
        issues.append("tasks.md not found")
    
    satisfied = len(issues) == 0
    return VerificationResult(
        principle="II - Task Isolation",
        satisfied=satisfied,
        details="; ".join(issues) if issues else "Task isolation maintained",
        evidence="; ".join(evidence)
    )

def verify_principle_iii_data_integrity() -> VerificationResult:
    """Verify data integrity with SHA256 checksums."""
    issues = []
    evidence = []
    
    # Check state file exists
    state_file = PROJECT_ROOT / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"
    if not state_file.exists():
        issues.append("State file not found for checksum tracking")
    else:
        content = state_file.read_text()
        if "sha256" not in content.lower():
            issues.append("State file does not contain SHA256 checksums")
        else:
            evidence.append("State file contains SHA256 checksums")
    
    # Check data directory exists
    data_dir = PROJECT_ROOT / "data"
    if not data_dir.exists():
        issues.append("data/ directory not found")
    else:
        evidence.append("data/ directory exists")
        
        # Check for downloaded data with checksums
        raw_dir = data_dir / "raw"
        if raw_dir.exists():
            files = list(raw_dir.glob("*"))
            if len(files) > 0:
                evidence.append(f"Found {len(files)} files in data/raw/")
    
    # Check download script has checksum validation
    download_script = PROJECT_ROOT / "code" / "download_datasets.py"
    if download_script.exists():
        content = download_script.read_text()
        if "sha256" in content.lower() or "checksum" in content.lower():
            evidence.append("download_datasets.py includes checksum validation")
        else:
            issues.append("download_datasets.py missing checksum validation")
    
    satisfied = len(issues) == 0
    return VerificationResult(
        principle="III - Data Integrity",
        satisfied=satisfied,
        details="; ".join(issues) if issues else "Data integrity requirements met",
        evidence="; ".join(evidence)
    )

def verify_principle_iv_path_conventions() -> VerificationResult:
    """Verify path conventions follow plan.md specification."""
    issues = []
    evidence = []
    
    expected_dirs = [
        "code",
        "data",
        "state",
        "tests",
        "specs"
    ]
    
    for dir_name in expected_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            issues.append(f"Missing expected directory: {dir_name}/")
        else:
            evidence.append(f"Found {dir_name}/ directory")
    
    # Check code structure
    code_dirs = ["src", "scripts", "baselines", "models", "evaluation", "utils"]
    for dir_name in code_dirs:
        dir_path = PROJECT_ROOT / "code" / dir_name
        if not dir_path.exists():
            issues.append(f"Missing code/{dir_name}/ directory")
        else:
            evidence.append(f"Found code/{dir_name}/ directory")
    
    # Check test structure
    test_dirs = ["contract", "integration", "unit"]
    for dir_name in test_dirs:
        dir_path = PROJECT_ROOT / "tests" / dir_name
        if not dir_path.exists():
            issues.append(f"Missing tests/{dir_name}/ directory")
        else:
            evidence.append(f"Found tests/{dir_name}/ directory")
    
    satisfied = len(issues) == 0
    return VerificationResult(
        principle="IV - Path Conventions",
        satisfied=satisfied,
        details="; ".join(issues) if issues else "Path conventions followed",
        evidence="; ".join(evidence)
    )

def verify_principle_v_project_structure() -> VerificationResult:
    """Verify project structure matches plan.md specification."""
    issues = []
    evidence = []
    
    # Check src hierarchy under code/
    src_dirs = ["baselines", "models", "evaluation", "utils", "data"]
    for dir_name in src_dirs:
        dir_path = PROJECT_ROOT / "code" / dir_name
        if not dir_path.exists():
            issues.append(f"Missing code/{dir_name}/ (should be under code/src/ per plan.md)")
        else:
            evidence.append(f"Found code/{dir_name}/")
    
    # Check for service wrappers
    services_dir = PROJECT_ROOT / "code" / "services"
    if not services_dir.exists():
        issues.append("code/services/ missing (anomaly_detector.py, threshold_calibrator.py)")
    else:
        evidence.append("code/services/ directory exists")
    
    # Check for main entry points
    main_files = ["anomaly_detector.py", "threshold_calibrator.py"]
    for file_name in main_files:
        file_path = services_dir / file_name
        if not file_path.exists():
            issues.append(f"Missing service wrapper: {file_name}")
        else:
            evidence.append(f"Found service wrapper: {file_name}")
    
    satisfied = len(issues) == 0
    return VerificationResult(
        principle="V - Project Structure",
        satisfied=satisfied,
        details="; ".join(issues) if issues else "Project structure matches plan.md",
        evidence="; ".join(evidence)
    )

def verify_principle_vi_elbo_logging() -> VerificationResult:
    """Verify ELBO convergence logging for variational inference."""
    issues = []
    evidence = []
    
    # Check dp_gmm.py for ELBO logging
    dp_gmm_file = PROJECT_ROOT / "code" / "models" / "dp_gmm.py"
    if not dp_gmm_file.exists():
        issues.append("code/models/dp_gmm.py not found")
    else:
        content = dp_gmm_file.read_text()
        
        # Check for ELBO-related logging
        elbo_patterns = ["elbo", "ELBO", "convergence", "variational", "log_likelihood"]
        found_patterns = [p for p in elbo_patterns if p in content.lower()]
        
        if len(found_patterns) == 0:
            issues.append("dp_gmm.py missing ELBO convergence logging")
        else:
            evidence.append(f"Found ELBO-related terms: {', '.join(found_patterns)}")
        
        # Check for logging import and usage
        if "import logging" in content or "from logging" in content:
            evidence.append("logging module imported")
        else:
            issues.append("logging module not imported in dp_gmm.py")
        
        if "logging." in content or "logger." in content:
            evidence.append("Logging statements found in dp_gmm.py")
        else:
            issues.append("No logging statements in dp_gmm.py")
    
    # Check for ELBO history tracking
    history_patterns = ["ELBOHistory", "elbo_history", "convergence_log"]
    if not any(p in content.lower() for p in history_patterns):
        issues.append("No ELBO history tracking in dp_gmm.py")
    
    satisfied = len(issues) == 0
    return VerificationResult(
        principle="VI - ELBO Logging",
        satisfied=satisfied,
        details="; ".join(issues) if issues else "ELBO convergence logging implemented",
        evidence="; ".join(evidence)
    )

def verify_principle_vii_api_consistency() -> VerificationResult:
    """Verify API consistency - imports match documented surface."""
    issues = []
    evidence = []
    
    # Check that main model file exports expected public names
    dp_gmm_file = PROJECT_ROOT / "code" / "models" / "dp_gmm.py"
    if dp_gmm_file.exists():
        content = dp_gmm_file.read_text()
        
        expected_exports = [
            "DPGMMConfig", "DPGMMModel", "ELBOHistory", "ClusterAnomalyResult", "main"
        ]
        
        found_exports = []
        for exp in expected_exports:
            if exp in content:
                found_exports.append(exp)
        
        if len(found_exports) == len(expected_exports):
            evidence.append(f"All expected exports found: {', '.join(found_exports)}")
        else:
            missing = set(expected_exports) - set(found_exports)
            issues.append(f"Missing exports in dp_gmm.py: {', '.join(missing)}")
    
    # Check anomaly_score.py
    anomaly_score_file = PROJECT_ROOT / "code" / "models" / "anomaly_score.py"
    if anomaly_score_file.exists():
        content = anomaly_score_file.read_text()
        if "AnomalyScore" in content:
            evidence.append("AnomalyScore dataclass found in anomaly_score.py")
        else:
            issues.append("AnomalyScore dataclass missing from anomaly_score.py")
    
    # Check baselines
    baseline_files = ["arima.py", "moving_average.py"]
    for bf in baseline_files:
        bf_path = PROJECT_ROOT / "code" / "baselines" / bf
        if bf_path.exists():
            content = bf_path.read_text()
            if "Config" in content and "Prediction" in content:
                evidence.append(f"Found Config/Prediction in baselines/{bf}")
            else:
                issues.append(f"Missing Config/Prediction in baselines/{bf}")
    
    # Check metrics
    metrics_file = PROJECT_ROOT / "code" / "evaluation" / "metrics.py"
    if metrics_file.exists():
        content = metrics_file.read_text()
        if "EvaluationMetrics" in content:
            evidence.append("EvaluationMetrics class found in metrics.py")
        else:
            issues.append("EvaluationMetrics class missing from metrics.py")
    
    satisfied = len(issues) == 0
    return VerificationResult(
        principle="VII - API Consistency",
        satisfied=satisfied,
        details="; ".join(issues) if issues else "API consistency verified",
        evidence="; ".join(evidence)
    )

def generate_verification_report(results: List[VerificationResult]) -> Dict[str, Any]:
    """Generate structured verification report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "project": "PROJ-024-bayesian-nonparametrics-for-anomaly-detection",
        "principles_verified": len(results),
        "all_satisfied": all(r.satisfied for r in results),
        "results": [r.to_dict() for r in results]
    }
    
    summary = {
        "total": len(results),
        "satisfied": sum(1 for r in results if r.satisfied),
        "failed": sum(1 for r in results if not r.satisfied)
    }
    report["summary"] = summary
    
    return report

def save_report(report: Dict[str, Any], output_path: Path):
    """Save verification report as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

def main():
    """Main verification entry point."""
    print("=" * 60)
    print("Constitution Principles Verification")
    print("=" * 60)
    print(f"Project: {PROJECT_ROOT}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Run all verifications
    results = [
        verify_principle_i_reproducibility(),
        verify_principle_ii_task_isolation(),
        verify_principle_iii_data_integrity(),
        verify_principle_iv_path_conventions(),
        verify_principle_v_project_structure(),
        verify_principle_vi_elbo_logging(),
        verify_principle_vii_api_consistency()
    ]
    
    # Print results
    all_satisfied = True
    for result in results:
        status = "✓ SATISFIED" if result.satisfied else "✗ FAILED"
        print(f"\n{result.principle}: {status}")
        print(f"  Details: {result.details}")
        if result.evidence:
            print(f"  Evidence: {result.evidence}")
        if not result.satisfied:
            all_satisfied = False
    
    print("\n" + "=" * 60)
    if all_satisfied:
        print("RESULT: All Constitution Principles satisfied")
    else:
        print("RESULT: Some principles require attention")
    print("=" * 60)
    
    # Save report
    report = generate_verification_report(results)
    report_path = PROJECT_ROOT / "state" / "verification" / "constitution_principles.json"
    save_report(report, report_path)
    print(f"\nReport saved to: {report_path}")
    
    # Also create markdown summary
    md_path = PROJECT_ROOT / "specs" / "001-bayesian-nonparametrics-anomaly-detection" / "constitution-principles-verification.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    
    md_content = f"""# Constitution Principles Verification Report

**Generated**: {datetime.now().isoformat()}
**Project**: PROJ-024-bayesian-nonparametrics-for-anomaly-detection

## Summary

| Status | Count |
|--------|-------|
| Satisfied | {report['summary']['satisfied']} |
| Failed | {report['summary']['failed']} |
| Total | {report['summary']['total']} |

## Principle Details

"""
    
    for result in results:
        status = "✓ SATISFIED" if result.satisfied else "✗ FAILED"
        md_content += f"""
### {result.principle}

**Status**: {status}

**Details**: {result.details}

**Evidence**: {result.evidence}

"""
    
    with open(md_path, 'w') as f:
        f.write(md_content)
    print(f"Markdown report saved to: {md_path}")
    
    # Exit with appropriate code
    sys.exit(0 if all_satisfied else 1)

if __name__ == "__main__":
    main()
    execute: true
    timeout_s: 300