"""
Verification script for FR-004: Flag observations when scores exceed adaptive threshold.

This script validates that the anomaly detection system correctly flags observations
when their anomaly scores exceed the adaptive threshold computed by the threshold
calibrator service.

Expected behavior:
- Observations with scores > threshold should be flagged as anomalies
- Observations with scores <= threshold should NOT be flagged
- Threshold should be computed adaptively (e.g., 95th percentile)
"""

import os
import sys
import yaml
import json
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
code_root = project_root / 'code'
sys.path.insert(0, str(code_root))

from models.dpgmm import DPGMMModel
from services.anomaly_detector import AnomalyDetector
from services.threshold_calibrator import ThresholdCalibrator
from models.timeseries import TimeSeries
from config import load_config


def verify_fr004():
    """
    Verify FR-004: flag observations when scores exceed adaptive threshold.
    
    Returns:
        dict: Verification results with pass/fail status and evidence
    """
    results = {
        'fr_id': 'FR-004',
        'description': 'Flag observations when scores exceed adaptive threshold',
        'verdict': 'PASS',
        'evidence': [],
        'threshold': None,
        'flagged_count': 0,
        'total_count': 0,
        'flagged_above_threshold': 0,
        'not_flagged_below_threshold': 0
    }
    
    # Load configuration
    config = load_config()
    threshold_params = config.get('threshold', {})
    results['threshold_config'] = threshold_params
    
    # Initialize threshold calibrator
    calibrator = ThresholdCalibrator(config)
    
    # Generate synthetic test data with known anomalies
    # We'll create a time series where we know which points are anomalies
    np.random.seed(config.get('random_seeds', {}).get('verification', 42))
    
    # Create normal observations (low scores expected)
    n_normal = 800
    normal_data = np.random.normal(loc=0.0, scale=1.0, size=n_normal)
    
    # Create anomalous observations (high scores expected)
    n_anomaly = 100
    anomaly_data = np.random.normal(loc=5.0, scale=2.0, size=n_anomaly)
    
    # Combine and create ground truth labels
    all_data = np.concatenate([normal_data, anomaly_data])
    ground_truth = np.array([0] * n_normal + [1] * n_anomaly)  # 1 = anomaly
    
    # Shuffle the data
    indices = np.random.permutation(len(all_data))
    all_data = all_data[indices]
    ground_truth = ground_truth[indices]
    
    # Create TimeSeries object
    ts = TimeSeries(
        values=all_data,
        timestamps=np.arange(len(all_data)),
        name='verification_test'
    )
    
    results['total_count'] = len(all_data)
    
    # Initialize DPGMM model
    dpgmm = DPGMMModel(config)
    
    # Process observations in streaming fashion
    anomaly_detector = AnomalyDetector(dpgmm, config)
    
    scores = []
    for i, obs in enumerate(all_data):
        score = anomaly_detector.compute_anomaly_score(obs)
        scores.append(score)
    
    scores = np.array(scores)
    
    # Calibrate threshold on validation split (first 70%)
    validation_size = int(len(scores) * 0.7)
    validation_scores = scores[:validation_size]
    
    threshold = calibrator.calibrate(validation_scores)
    results['threshold'] = float(threshold)
    
    results['evidence'].append(f'Calibrated threshold: {threshold:.4f}')
    
    # Apply threshold to flag anomalies
    flagging_results = anomaly_detector.flag_anomalies(scores, threshold)
    flagged_indices = np.where(flagging_results)[0]
    results['flagged_count'] = len(flagged_indices)
    
    # Verify flagging logic: all flagged should have scores > threshold
    flagged_scores = scores[flagged_indices]
    unflagged_scores = scores[~flagging_results]
    
    # Check that all flagged observations have scores above threshold
    all_flagged_above = np.all(flagged_scores > threshold) if len(flagged_scores) > 0 else True
    
    # Check that all unflagged observations have scores at or below threshold
    all_unflagged_below = np.all(unflagged_scores <= threshold) if len(unflagged_scores) > 0 else True
    
    # Count violations
    flagged_above_count = np.sum(flagged_scores > threshold) if len(flagged_scores) > 0 else 0
    not_flagged_below_count = np.sum(unflagged_scores <= threshold) if len(unflagged_scores) > 0 else 0
    
    results['flagged_above_threshold'] = int(flagged_above_count)
    results['not_flagged_below_threshold'] = int(not_flagged_below_count)
    
    results['evidence'].append(
        f'Flagged observations: {results["flagged_count"]} out of {results["total_count"]}'
    )
    results['evidence'].append(
        f'All flagged scores > threshold: {all_flagged_above}'
    )
    results['evidence'].append(
        f'All unflagged scores <= threshold: {all_unflagged_below}'
    )
    
    # Verify against ground truth (optional, shows effectiveness)
    true_positives = np.sum((flagging_results == True) & (ground_truth == 1))
    false_positives = np.sum((flagging_results == True) & (ground_truth == 0))
    true_negatives = np.sum((flagging_results == False) & (ground_truth == 0))
    false_negatives = np.sum((flagging_results == False) & (ground_truth == 1))
    
    results['evidence'].append(
        f'TP: {true_positives}, FP: {false_positives}, '
        f'TN: {true_negatives}, FN: {false_negatives}'
    )
    
    # Determine pass/fail
    if all_flagged_above and all_unflagged_below:
        results['verdict'] = 'PASS'
        results['evidence'].append(
            'FR-004 VERIFIED: All observations correctly flagged based on threshold comparison'
        )
    else:
        results['verdict'] = 'FAIL'
        results['evidence'].append(
            'FR-004 FAILED: Some observations were incorrectly flagged/unflagged'
        )
    
    return results


def main():
    """Main entry point for verification."""
    print('=' * 60)
    print('FR-004 Verification: Threshold-Based Anomaly Flagging')
    print('=' * 60)
    print()
    
    results = verify_fr004()
    
    print(f"Verification ID: {results['fr_id']}")
    print(f"Description: {results['description']}")
    print(f"Verdict: {results['verdict']}")
    print()
    print('Evidence:')
    for i, evidence in enumerate(results['evidence'], 1):
        print(f'  {i}. {evidence}')
    print()
    print(f'Threshold: {results["threshold"]:.4f}')
    print(f'Flagged: {results["flagged_count"]}/{results["total_count"]}')
    print(f'Flagged above threshold: {results["flagged_above_threshold"]}')
    print(f'Not flagged below threshold: {results["not_flagged_below_threshold"]}')
    print()
    
    # Save results to JSON for audit trail
    output_path = Path(__file__).parent / 'verification_results' / 'fr004_results.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f'Results saved to: {output_path}')
    print()
    
    # Exit with appropriate code
    sys.exit(0 if results['verdict'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
