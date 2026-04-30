# State Directory

This directory contains experiment metadata and state tracking artifacts
for the Bayesian Nonparametrics for Anomaly Detection project.

## Purpose

- Track experiment parameters, metrics, and environment information
- Ensure reproducibility per Constitution Principle 1
- Maintain single source of truth per Constitution Principle 7
- Enable experiment comparison and iteration

## File Naming Convention

- `experiment_<ID>_<timestamp>.yaml`: Full experiment metadata
- `experiment_metadata.yaml`: Current baseline/summary metadata
- `README.md`: This documentation

## Metadata Structure

Each experiment metadata file contains:

```yaml
experiment_id: unique-identifier
dataset: dataset-name
model_type: DPGMM|ARIMA|MA
created_at: ISO-8601 timestamp
git:
  commit: sha
  branch: branch-name
  dirty: boolean
environment:
  python_version: x.y.z
  platform: os
config:
  random_seed: int
  hyperparameters: {...}
metrics:
  precision: float
  recall: float
  f1_score: float
artifacts:
  - path: relative/path
    type: model|plot|data
```

## Usage

Use the `StateTracker` class in `code/services/state_tracker.py`:

```python
from services.state_tracker import StateTracker

tracker = StateTracker()
metadata = tracker.generate_experiment_metadata(
    experiment_name="my_experiment",
    dataset_name="uci_nsbands"
)
tracker.save_metadata(metadata)
```

## Integration

- T077: Initial state tracking implementation
- T078: Full pipeline integration with state tracking
- All verification scripts (T040-T076) register their state here
