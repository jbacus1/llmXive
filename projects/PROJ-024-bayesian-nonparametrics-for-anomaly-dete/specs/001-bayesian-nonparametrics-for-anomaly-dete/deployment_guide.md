# Deployment Guide

## Overview

This guide covers deployment of the Bayesian Nonparametrics Anomaly Detection system in production environments.

## Prerequisites

- Python 3.11+
- 7GB+ RAM available
- 30-minute runtime budget per dataset
- Network access for dataset downloads (optional)

## Installation

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### Step 3: Install Dependencies

```bash
cd code
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
pytest tests/contract/ -v
```

## Configuration

### Environment Variables

```bash
export DATA_DIR="data/raw"
export PROCESSED_DIR="data/processed"
export MODEL_CONFIG="code/config.yaml"
```

### config.yaml

```yaml
# code/config.yaml
dp_gmm:
  concentration_prior: 1.0
  max_components: 100
  elbo_tolerance: 1e-4
  learning_rate: 0.01

streaming:
  window_size: 100
  min_observations: 10

threshold:
  percentile: 95
  anomaly_rate_bounds: [0.01, 0.10]

paths:
  data_raw: data/raw
  data_processed: data/processed
  models: models
  results: data/results
```

## Running the System

### Option 1: Download Datasets

```bash
python code/download_datasets.py
```

This downloads:
- UCI Electricity dataset
- UCI Traffic dataset
- PEMS-SF dataset
- Synthetic validation dataset

### Option 2: Use Synthetic Data

```bash
python code/scripts/profile_memory_1000_obs.py
```

### Option 3: Run Full Pipeline

```bash
python code/scripts/test_advi_inference.py
```

### Option 4: Calibrate Thresholds

```bash
python code/utils/threshold.py
```

## Streaming Deployment

### Real-Time Processing

```python
from models.dp_gmm import DPGMMModel
from utils.streaming import create_streaming_processor
from utils.threshold import compute_adaptive_threshold

# Initialize model
model = DPGMMModel(config={"concentration_prior": 1.0})

# Initialize streaming processor
processor = create_streaming_processor(window_size=100)

# Process observations
for obs in observation_stream:
    processed = processor.process(obs)
    score = model.update_posterior(processed)

    # Check threshold
    if score.threshold_exceeded:
        alert_anomaly(score)
```

### Batch Processing

```python
from data.synthetic_generator import load_synthetic_dataset
from models.dp_gmm import DPGMMModel

# Load dataset
dataset = load_synthetic_dataset("data/processed/synthetic.json")

# Process in batch
model = DPGMMModel(config={"concentration_prior": 1.0})
scores = []
for obs in dataset.observations:
    score = model.update_posterior(obs)
    scores.append(score)

# Save results
import json
with open("data/results/scores.json", "w") as f:
    json.dump([s.__dict__ for s in scores], f)
```

## Monitoring

### Memory Monitoring

```python
from utils.memory_profiler import MemoryProfiler

profiler = MemoryProfiler(max_memory_gb=7.0)
with profiler.track():
    process_observations()

if profiler.exceeded:
    log_warning("Memory limit exceeded")
```

### Runtime Monitoring

```python
from utils.runtime_monitor import monitor_runtime

result = monitor_runtime(
    operation=lambda: run_pipeline(),
    budget_seconds=1800
)

if result.exceeded:
    log_warning("Runtime budget exceeded")
```

## Output Artifacts

### Generated Files

| Path | Description |
|------|-------------|
| `data/results/scores.json` | Anomaly scores per observation |
| `data/results/metrics.json` | Evaluation metrics |
| `paper/figures/roc_curve.png` | ROC curve visualization |
| `paper/figures/pr_curve.png` | PR curve visualization |
| `state/projects/PROJ-024.yaml` | Checksum state file |

###