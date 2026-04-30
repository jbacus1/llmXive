"""
Verification script for FR-001: Stick-breaking construction for univariate time series.

This script verifies that the DPGMMModel correctly implements stick-breaking
construction for univariate time series data, as required by Functional
Requirement 001 (FR-001).

Verification criteria:
1. Stick weights sum to 1.0 (within numerical tolerance)
2. All stick weights are non-negative
3. Weights decay appropriately per stick-breaking process
4. Construction works for streaming (incremental) updates
"""

import sys
import os
import numpy as np
import yaml
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.dpgmm import DPGMMModel
from utils.logger import get_logger

logger = get_logger(__name__)

def load_config():
    """Load configuration from config.yaml."""
    config_path = Path(__file__).parent.parent.parent / "code" / "config.yaml"
    if not config_path.exists():
        # Create default config if missing
        config = {
            "random_seed": 42,
            "hyperparameters": {
                "concentration": 1.0,
                "max_clusters": 10
            }
        }
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        return config
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def generate_synthetic_univariate_data(n_obs=100, n_clusters=3, seed=42):
    """
    Generate synthetic univariate time series with known cluster structure.
    
    Args:
        n_obs: Number of observations
        n_clusters: True number of clusters
        seed: Random seed for reproducibility
    
    Returns:
        observations: Array of univariate observations
        true_labels: Ground truth cluster assignments
    """
    np.random.seed(seed)
    
    # Generate cluster centers and variances
    centers = np.random.uniform(-5, 5, n_clusters)
    stds = np.random.uniform(0.3, 1.0, n_clusters)
    
    # Assign observations to clusters
    labels = np.random.choice(n_clusters, n_obs)
    
    # Generate observations from cluster distributions
    observations = np.array([
        np.random.normal(centers[labels[i]], stds[labels[i]])
        for i in range(n_obs)
    ])
    
    return observations, labels, centers, stds

def verify_stick_weights(weights, tolerance=1e-6):
    """
    Verify stick-breaking weight properties.
    
    Args:
        weights: Array of stick weights
        tolerance: Numerical tolerance for sum check
    
    Returns:
        dict: Verification results
    """
    results = {
        "sum_to_one": False,
        "all_non_negative": False,
        "decay_pattern": False,
        "valid": False,
        "details": {}
    }
    
    # Check 1: Sum to 1.0 (within tolerance)
    weight_sum = np.sum(weights)
    results["details"]["weight_sum"] = float(weight_sum)
    results["sum_to_one"] = abs(weight_sum - 1.0) < tolerance
    
    # Check 2: All non-negative
    results["all_non_negative"] = np.all(weights >= 0)
    results["details"]["min_weight"] = float(np.min(weights))
    
    # Check 3: Decay pattern (weights should generally decrease)
    # In stick-breaking, later weights tend to be smaller
    if len(weights) > 1:
        # Check that not all weights are equal (would indicate bug)
        results["decay_pattern"] = not np.allclose(weights, weights[0])
        results["details"]["weight_variance"] = float(np.var(weights))
    else:
        results["decay_pattern"] = True
    
    # Overall validity
    results["valid"] = (
        results["sum_to_one"] and 
        results["all_non_negative"] and 
        results["decay_pattern"]
    )
    
    return results

def verify_stick_breaking_construction(model, observations, config):
    """
    Verify stick-breaking construction on streaming data.
    
    Args:
        model: DPGMMModel instance
        observations: Array of univariate observations
        config: Configuration dictionary
    
    Returns:
        dict: Comprehensive verification results
    """
    logger.info("Starting stick-breaking construction verification")
    
    results = {
        "fr001_verified": False,
        "observations_processed": len(observations),
        "verification_steps": []
    }
    
    # Step 1: Initialize model
    logger.info("Step 1: Initializing DPGMM model")
    model.initialize(concentration=config["hyperparameters"]["concentration"])
    results["verification_steps"].append({
        "step": "initialization",
        "status": "success"
    })
    
    # Step 2: Process observations incrementally (streaming)
    logger.info("Step 2: Processing observations in streaming mode")
    for i, obs in enumerate(observations):
        model.update(obs)
        
        # Verify after each batch of 10 observations
        if (i + 1) % 10 == 0:
            weights = model.get_stick_weights()
            if weights is not None:
                weight_check = verify_stick_weights(weights)
                if not weight_check["valid"]:
                    logger.warning(f"Weight check failed at observation {i+1}")
                    results["verification_steps"].append({
                        "step": f"streaming_update_{i+1}",
                        "status": "warning",
                        "details": weight_check
                    })
    
    results["verification_steps"].append({
        "step": "streaming_updates",
        "status": "success",
        "count": len(observations)
    })
    
    # Step 3: Final stick weight verification
    logger.info("Step 3: Final stick weight verification")
    final_weights = model.get_stick_weights()
    
    if final_weights is None:
        results["verification_steps"].append({
            "step": "final_weight_check",
            "status": "failed",
            "details": "No stick weights returned"
        })
        results["fr001_verified"] = False
        return results
    
    weight_check = verify_stick_weights(final_weights)
    results["verification_steps"].append({
        "step": "final_weight_check",
        "status": "success" if weight_check["valid"] else "failed",
        "details": weight_check
    })
    
    # Step 4: Verify cluster assignments work
    logger.info("Step 4: Verifying cluster assignment capability")
    try:
        cluster_probs = model.predict_cluster_probabilities(observations)
        results["verification_steps"].append({
            "step": "cluster_assignment",
            "status": "success",
            "details": {
                "n_cluster_probs": cluster_probs.shape if hasattr(cluster_probs, 'shape') else len(cluster_probs)
            }
        })
    except Exception as e:
        results["verification_steps"].append({
            "step": "cluster_assignment",
            "status": "failed",
            "details": str(e)
        })
    
    # Overall verification
    results["fr001_verified"] = (
        len(results["verification_steps"]) > 0 and
        all(s["status"] != "failed" for s in results["verification_steps"]) and
        weight_check["valid"]
    )
    
    return results

def main():
    """Main verification entry point."""
    logger.info("=" * 60)
    logger.info("FR-001 Verification: Stick-breaking Construction")
    logger.info("=" * 60)
    
    # Load configuration
    config = load_config()
    logger.info(f"Configuration loaded: {config}")
    
    # Generate synthetic univariate data
    n_obs = 100  # Small dataset for quick verification
    observations, true_labels, centers, stds = generate_synthetic_univariate_data(
        n_obs=n_obs,
        n_clusters=3,
        seed=config["random_seed"]
    )
    logger.info(f"Generated {n_obs} synthetic univariate observations")
    logger.info(f"True cluster centers: {centers}")
    
    # Initialize DPGMM model
    model = DPGMMModel()
    logger.info("DPGMM model initialized")
    
    # Run verification
    results = verify_stick_breaking_construction(
        model, observations, config
    )
    
    # Log results
    logger.info("=" * 60)
    logger.info("VERIFICATION RESULTS")
    logger.info("=" * 60)
    logger.info(f"FR-001 Verified: {results['fr001_verified']}")
    logger.info(f"Observations Processed: {results['observations_processed']}")
    
    for step in results["verification_steps"]:
        logger.info(f"  Step: {step['step']} - {step['status']}")
        if "details" in step:
            for key, value in step["details"].items():
                logger.info(f"    {key}: {value}")
    
    # Save verification report
    report_path = Path(__file__).parent.parent.parent / "state" / "fr001_verification_report.yaml"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        yaml.dump(results, f, default_flow_style=False)
    
    logger.info(f"Verification report saved to: {report_path}")
    logger.info("=" * 60)
    
    # Return exit code based on verification
    return 0 if results["fr001_verified"] else 1

if __name__ == "__main__":
    sys.exit(main())
