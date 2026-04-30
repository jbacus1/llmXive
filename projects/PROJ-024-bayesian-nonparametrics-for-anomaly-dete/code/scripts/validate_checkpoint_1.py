"""
Quickstart.md Intermediate Validation Checkpoint 1
Validates Phase 3 (User Story 1) completion after DPGMM implementation.

This script verifies:
1. DPGMMModel can be instantiated with valid config
2. Stick-breaking construction produces valid weights
3. Streaming update works on synthetic time series
4. Anomaly scores are computed correctly
5. Memory usage stays under 7GB constraint
"""
import sys
import time
import yaml
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from models.dpgmm import DPGMMModel
from models.timeseries import TimeSeries
from models.anomaly_score import AnomalyScore
from utils.logger import get_logger
from utils.memory_profiler import MemoryProfiler

logger = get_logger(__name__)

def load_config():
    """Load configuration from config.yaml"""
    config_path = project_root / "code" / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def test_stick_breaking_construction():
    """Verify stick-breaking produces valid probability weights"""
    logger.info("Testing stick-breaking construction...")
    config = load_config()
    model = DPGMMModel.from_config(config)
    
    # Generate stick-breaking weights
    alpha = model.concentration_param
    K_max = 100
    weights = model._stick_breaking(alpha, K_max)
    
    # Validate weights
    assert len(weights) == K_max, f"Expected {K_max} weights, got {len(weights)}"
    assert np.all(weights >= 0), "Weights must be non-negative"
    assert np.isclose(weights.sum(), 1.0, atol=1e-6), "Weights must sum to 1"
    
    logger.info(f"✓ Stick-breaking validated: {len(weights)} clusters, sum={weights.sum():.6f}")
    return True

def test_streaming_update():
    """Verify incremental posterior update on synthetic data"""
    logger.info("Testing streaming DPGMM update...")
    config = load_config()
    model = DPGMMModel.from_config(config)
    
    # Generate synthetic time series with known anomalies
    np.random.seed(config['random_seeds']['main'])
    n_observations = 100
    n_anomalies = 5
    
    # Normal observations from mixture of 2 Gaussians
    true_means = [0.0, 5.0]
    true_stds = [1.0, 1.5]
    data = []
    labels = []
    
    for i in range(n_observations):
        if i < n_anomalies:
            # Anomaly: far from both clusters
            data.append(np.random.normal(20.0, 0.5))
            labels.append(1)
        else:
            # Normal: from one of the clusters
            cluster = np.random.choice([0, 1])
            data.append(np.random.normal(true_means[cluster], true_stds[cluster]))
            labels.append(0)
    
    data = np.array(data).reshape(-1, 1)
    ts = TimeSeries(values=data.flatten(), timestamps=np.arange(len(data)))
    
    # Stream observations one at a time
    memory_profiler = MemoryProfiler()
    memory_profiler.start()
    
    for i, obs in enumerate(data):
        model.incremental_update(obs[0])
        if i % 20 == 0:
            logger.debug(f"  Processed {i+1}/{n_observations} observations")
    
    memory_usage = memory_profiler.stop()
    logger.info(f"✓ Streaming update complete: {n_observations} observations, memory={memory_usage:.2f}MB")
    
    # Verify memory constraint
    assert memory_usage < 7000, f"Memory {memory_usage}MB exceeds 7GB constraint"
    return True

def test_anomaly_scoring():
    """Verify anomaly scores are computed correctly"""
    logger.info("Testing anomaly score computation...")
    config = load_config()
    model = DPGMMModel.from_config(config)
    
    # Create simple time series
    np.random.seed(config['random_seeds']['main'])
    n_observations = 50
    data = np.random.normal(0, 1, n_observations)
    
    # Add one clear anomaly
  data[25] = 10.0  # Anomaly point
    
    ts = TimeSeries(values=data, timestamps=np.arange(len(data)))
    
    # Stream all observations
  for obs in data:
      model.incremental_update(obs)
    
    # Compute anomaly scores
    scores = []
    for i, obs in enumerate(data):
        score = model.compute_anomaly_score(obs)
        scores.append(score)
        assert isinstance(score, AnomalyScore), f"Expected AnomalyScore, got {type(score)}"
        assert score.score >= 0, "Anomaly score must be non-negative (negative log probability)"
    
    scores = np.array([s.score for s in scores])
    
    # Verify anomaly point has highest score
    anomaly_idx = np.argmax(scores)
    assert anomaly_idx == 25, f"Expected anomaly at index 25, got {anomaly_idx}"
    
    logger.info(f"✓ Anomaly scoring validated: anomaly at index {anomaly_idx}, score={scores[25]:.4f}")
    return True

def test_convergence():
    """Verify model converges within reasonable iterations"""
    logger.info("Testing ADVI convergence...")
    config = load_config()
    model = DPGMMModel.from_config(config)
    
  np.random.seed(config['random_seeds']['main'])
  n_observations = 100
  data = np.random.normal(0, 1, n_observations)
    
    start_time = time.time()
  for obs in data:
      model.incremental_update(obs)
  elapsed = time.time() - start_time
    
    # Verify ELBO improved
    if hasattr(model, 'elbo_history') and len(model.elbo_history) > 1:
        assert model.elbo_history[-1] >= model.elbo_history[0], "ELBO should not decrease"
        logger.info(f"✓ Convergence validated: ELBO improved from {model.elbo_history[0]:.2f} to {model.elbo_history[-1]:.2f}")
    
    logger.info(f"✓ Processing time: {elapsed:.2f}s for {n_observations} observations")
  assert elapsed < 300, f"Processing took {elapsed}s, exceeds budget"
  return True

def main():
    """Run all validation checks"""
    logger.info("=" * 60)
    logger.info("Quickstart Checkpoint 1: Phase 3 (User Story 1) Validation")
    logger.info("=" * 60)
    
    checks = [
        ("Stick-breaking construction", test_stick_breaking_construction),
        ("Streaming update", test_streaming_update),
        ("Anomaly scoring", test_anomaly_scoring),
        ("Model convergence", test_convergence),
    ]
    
    results = []
  for name, check_fn in checks:
      try:
          result = check_fn()
          results.append((name, "PASS", None))
          logger.info(f"✓ {name}: PASS")
      except Exception as e:
          results.append((name, "FAIL", str(e)))
          logger.error(f"✗ {name}: FAIL - {e}")
    
    # Summary
    logger.info("=" * 60)
    passed = sum(1 for _, status, _ in results if status == "PASS")
    total = len(results)
    logger.info(f"Validation Summary: {passed}/{total} checks passed")
    
    if passed == total:
        logger.info("✓ Checkpoint 1 PASSED - Phase 3 implementation validated")
        print("CHECKPOINT_1_STATUS: PASS")
        return 0
    else:
        logger.error(f"✗ Checkpoint 1 FAILED - {total - passed} checks failed")
        print("CHECKPOINT_1_STATUS: FAIL")
        return 1

if __name__ == "__main__":
  sys.exit(main())
