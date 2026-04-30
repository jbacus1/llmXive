"""
Validation script for T078 integration test results
Verifies all required artifacts were generated
"""
import json
import sys
from pathlib import Path

def validate_integration_test():
    """Validate that integration test produced all required artifacts"""
    project_root = Path(__file__).parent.parent.parent
    results_dir = project_root / 'data' / 'results' / 'integration_test'
    
    required_files = [
        'integration_test_summary.json',
    ]
    
    # Check for plot files
    plot_dir = results_dir / 'plots'
    if plot_dir.exists():
        plot_files = list(plot_dir.glob('*.png'))
        print(f"Found {len(plot_files)} plot files")
        required_files.extend([f.name for f in plot_files])
    
    # Check for individual dataset results
    result_files = list(results_dir.glob('*_result.json'))
    print(f"Found {len(result_files)} dataset result files")
    
    # Validate summary
    summary_path = results_dir / 'integration_test_summary.json'
    if not summary_path.exists():
        print("✗ FAIL: Summary file not found")
        return False
    
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    # Check required fields
    required_fields = ['total_datasets', 'completed', 'failed', 'summary_metrics']
    for field in required_fields:
        if field not in summary:
            print(f"✗ FAIL: Missing field '{field}' in summary")
            return False
    
    # Validate metrics
    metrics = summary.get('summary_metrics', {})
    required_metrics = ['dpgmm_avg_precision', 'dpgmm_avg_recall', 'dpgmm_avg_f1']
    for metric in required_metrics:
        if metric not in metrics:
            print(f"✗ FAIL: Missing metric '{metric}'")
            return False
        if metrics[metric] is None or metrics[metric] < 0:
            print(f"✗ FAIL: Invalid value for '{metric}': {metrics[metric]}")
            return False
    
    # Validate minimum success criteria
    if summary['completed'] < 3:
        print(f"✗ FAIL: Only {summary['completed']} datasets completed (need >= 3)")
        return False
    
    print("✓ All validation checks passed")
    print(f"  - Datasets completed: {summary['completed']}/{summary['total_datasets']}")
    print(f"  - Avg F1 Score: {metrics['dpgmm_avg_f1']:.4f}")
    return True


if __name__ == '__main__':
    success = validate_integration_test()
    sys.exit(0 if success else 1)
