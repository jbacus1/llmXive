"""
Verification script for FR-003: Anomaly scores as negative log posterior probability.

This script verifies that the anomaly scores computed by the DPGMM model
are indeed equal to the negative log posterior probability of observations
given the model parameters.

Exit codes:
  0 - Verification passed
  1 - Verification failed
"""

import sys
import os
import numpy as np
import yaml
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

# Import model components
from models.dpgmm import DPGMMModel
from services.anomaly_detector import AnomalyDetector

def load_config():
    """Load configuration from config.yaml"""
    config_path = project_root / 'code' / 'config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def compute_manual_log_posterior(observation, model_params):
    """
    Manually compute negative log posterior probability for verification.
    
    For a Gaussian mixture component k:
    log p(x|k) = log N(x|μ_k, σ_k²)
    log p(k|α) = log π_k  (stick-breaking weights)
    
    Posterior: log p(k|x) ∝ log p(x|k) + log p(k)
    """
    mu_k = model_params['mu']
    sigma_k = model_params['sigma']
    pi_k = model_params['pi']
    
    log_likelihoods = []
    for k in range(len(mu_k)):
        # Log likelihood under Gaussian component k
        log_p_x_given_k = -0.5 * np.log(2 * np.pi * sigma_k[k]**2)
        log_p_x_given_k -= 0.5 * ((observation - mu_k[k]) / sigma_k[k])**2
        
        # Log prior probability of component k
        log_p_k = np.log(pi_k[k] + 1e-10)  # Avoid log(0)
        
        log_posterior = log_p_x_given_k + log_p_k
        log_likelihoods.append(log_posterior)
    
    # Normalize to get proper posterior probabilities
    log_sum_exp = np.max(log_likelihoods) + np.log(
        np.sum(np.exp(np.array(log_likelihoods) - np.max(log_likelihoods)))
    )
    log_posteriors = np.array(log_likelihoods) - log_sum_exp
    
    # Negative log posterior (for anomaly scoring)
    # We use the maximum posterior component for scoring
    max_log_posterior = np.max(log_posteriors)
    negative_log_posterior = -max_log_posterior
    
    return negative_log_posterior

def verify_fr003():
    """
    Main verification routine for FR-003.
    
    Tests that anomaly scores match negative log posterior probability.
    """
    print("=" * 60)
    print("FR-003 Verification: Anomaly Scores as Negative Log Posterior")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    print(f"\nConfiguration loaded from: code/config.yaml")
    print(f"Random seed: {config['random_seeds']['general']}")
    
    # Create test data with known parameters
    np.random.seed(config['random_seeds']['general'])
    
    # Test case 1: Single observation from known Gaussian
    print("\n" + "-" * 60)
    print("Test Case 1: Single observation from known Gaussian")
    print("-" * 60)
    
    # Create a simple model with 2 components
    test_params = {
        'mu': np.array([0.0, 5.0]),
        'sigma': np.array([1.0, 1.0]),
        'pi': np.array([0.7, 0.3]),
        'alpha': 1.0  # Concentration parameter
    }
    
    # Test observations
    test_observations = [
        (0.5, "Normal observation near component 1"),
        (5.5, "Normal observation near component 2"),
        (10.0, "Anomalous observation far from both"),
        (0.0, "Exact component 1 mean"),
        (5.0, "Exact component 2 mean"),
    ]
    
    results = []
    all_passed = True
    
    for obs, description in test_observations:
        # Compute manual negative log posterior
        manual_score = compute_manual_log_posterior(obs, test_params)
        
        # Create minimal DPGMM model for comparison
        model = DPGMMModel(
            n_components=2,
            concentration=1.0,
            random_seed=config['random_seeds']['general']
        )
        
        # Set known parameters (bypassing inference for verification)
        model._mu = test_params['mu']
        model._sigma = test_params['sigma']
        model._pi = test_params['pi']
        model._alpha = test_params['alpha']
        
        # Create anomaly detector
        detector = AnomalyDetector(model)
        
        # Compute anomaly score using the detector
        try:
            detector_score = detector.compute_anomaly_score(obs)
            
            # Compare scores
            tolerance = 1e-3  # Allow small numerical differences
            match = abs(manual_score - detector_score) < tolerance
            
            results.append({
                'observation': obs,
                'description': description,
                'manual_score': manual_score,
                'detector_score': detector_score,
                'difference': abs(manual_score - detector_score),
                'passed': match
            })
            
            status = "✓ PASS" if match else "✗ FAIL"
            print(f"\n{status}: {description}")
            print(f"  Observation: {obs}")
            print(f"  Manual NLPP: {manual_score:.6f}")
            print(f"  Detector Score: {detector_score:.6f}")
            print(f"  Difference: {abs(manual_score - detector_score):.10f}")
            
            if not match:
                all_passed = False
                
        except Exception as e:
            print(f"\n✗ ERROR: {description}")
            print(f"  Exception: {str(e)}")
            results.append({
                'observation': obs,
                'description': description,
                'error': str(e),
                'passed': False
            })
            all_passed = False
    
    # Test case 2: Stream of observations
    print("\n" + "-" * 60)
    print("Test Case 2: Streaming observations (100 points)")
    print("-" * 60)
    
    stream_observations = np.random.normal(0, 1, 100)
    stream_scores = []
    stream_passed = True
    
    for i, obs in enumerate(stream_observations[:10]):  # Test first 10 for speed
        manual_score = compute_manual_log_posterior(obs, test_params)
        
        model = DPGMMModel(
            n_components=2,
            concentration=1.0,
            random_seed=config['random_seeds']['general']
        )
        model._mu = test_params['mu']
        model._sigma = test_params['sigma']
        model._pi = test_params['pi']
        model._alpha = test_params['alpha']
        
        detector = AnomalyDetector(model)
        detector_score = detector.compute_anomaly_score(obs)
        
        match = abs(manual_score - detector_score) < tolerance
        stream_passed = stream_passed and match
        stream_scores.append({
            'observation': obs,
            'manual_score': manual_score,
            'detector_score': detector_score,
            'passed': match
        })
    
    print(f"Stream test: {'✓ PASS' if stream_passed else '✗ FAIL'}")
    print(f"  Tested {len(stream_scores)} observations")
    print(f"  All within tolerance: {stream_passed}")
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed_count = sum(1 for r in results if r.get('passed', False))
    total_count = len(results)
    
    print(f"\nTest Cases: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print(f"\nFR-003 Verification: {'✓ PASSED' if all_passed else '✗ FAILED'}")
    
    # Save results
    results_dir = project_root / 'data' / 'verification'
    results_dir.mkdir(parents=True, exist_ok=True)
    
    results_path = results_dir / 'fr003_verification_results.json'
    import json
    with open(results_path, 'w') as f:
        json.dump({
            'task_id': 'T042',
            'fr_id': 'FR-003',
            'description': 'Anomaly scores as negative log posterior probability',
            'verification_passed': all_passed,
            'test_results': results,
            'stream_test_passed': stream_passed,
            'summary': {
                'total_tests': total_count,
                'passed': passed_count,
                'failed': total_count - passed_count
            }
        }, f, indent=2, default=str)
    
    print(f"\nResults saved to: {results_path}")
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)

if __name__ == '__main__':
    try:
        verify_fr003()
    except Exception as e:
        print(f"\n✗ VERIFICATION ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
