# Quickstart: Bayesian Nonparametrics for Anomaly Detection

## Prerequisites

- Python 3.11+
- pip package manager
- Git (for version control)
- Minimum 7GB available RAM
- ~30 minutes per dataset runtime budget

## Setup

### 1. Clone and Install

```bash
# Navigate to project
cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection/

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r code/requirements.txt
```

### 2. Verify Installation

```bash
# Run tests (should pass)
pytest code/tests/ -v

# Run linting
black --check code/
flake8 code/
```

## Configuration

Edit `code/config.yaml` for your environment:

```yaml
random_seed: 42
hyperparameters:
  concentration: 1.0
  mean_prior: 0.0
  variance_prior: 1.0
  max_components: 100
datasets:
  raw: data/raw/
  processed: data/processed/
threshold:
  percentile: 95
  min_rate: 0.01
  max_rate: 0.10
```

## Usage

### Option 1: Process Synthetic Data (Quick Test)

```bash
# Generate synthetic anomaly dataset
python code/data/synthetic_anomaly_generator.py

# Run DPGMM detector
python code/scripts/run_dpgmm_detection.py

# Expected output: Anomaly scores and detection summary
```

### Option 2: Process UCI Datasets

```bash
# Download datasets (requires internet)
python code/data/download_datasets.py

# Run full evaluation pipeline
python code/scripts/run_full_evaluation.py

# Expected output:
# - Precision/Recall/F1 scores
# - ROC and PR curve PNGs in paper/figures/
# - Comparison with ARIMA and Moving Average baselines
```

### Option 3: Streaming Inference Example

```python
from code.models.dpgmm import DPGMMModel
from code.services.anomaly_detector import AnomalyDetector

# Initialize model
model = DPGMMModel(concentration=1.0, random_seed=42)

# Process streaming observations
detector = AnomalyDetector(model, threshold_percentile=95)

for value in time_series_values:
    score = detector.update_and_score(value)
    if score.is_anomaly:
        print(f"Anomaly detected: {value} (score={score.score})")
```

## Validation Checkpoints

### Checkpoint 1: After Phase 3 (MVP)

```bash
# Verify streaming DPGMM works
python code/scripts/verify_fr001_stick_breaking.py
python code/scripts/verify_fr002_incremental_update.py
python code/scripts/verify_fr003_anomaly_scores.py

# All should complete without errors
```

### Checkpoint 2: After Phase 5 (Full Feature Set)

```bash
# Verify threshold calibration
python code/scripts/verify_fr004_threshold_flagging.py

# Verify baseline comparison
python code/scripts/verify_sc005_pr_curves.py

# All should generate expected outputs
```

### Final Validation

```bash
# Run complete test suite
pytest code/tests/ -v --tb=short

# Verify memory constraints
python code/utils/memory_profiler.py

# Verify runtime constraints
python code/utils/runtime_profiler.py
```

## Expected Outputs

| Output | Location | Description |
|--------|----------|-------------|
| Anomaly scores | data/results/anomaly_scores.csv | Per-observation scores |
| Evaluation metrics | data/results/metrics.json | Precision, recall, F1, AUC |
| ROC curves | paper/figures/roc_curves.png | ROC visualization |
| PR curves | paper/figures/pr_curves.png | Precision-Recall visualization |
| Confusion matrices | paper/figures/confusion_matrices.png | Classification breakdown |
| Logs | code/.tasks/*.log | Execution logs |

## Troubleshooting

### Memory Issues

If you encounter memory errors:
1. Reduce `max_components` in config.yaml
2. Process data in smaller batches
3. Verify you have 7GB+ available RAM

### Runtime Issues

If processing exceeds 30 minutes:
1. Check network speed for dataset downloads
2. Reduce `max_components` for faster inference
3. Use GPU acceleration if available

### Installation Errors

If dependencies fail to install:
```bash
# Upgrade pip first
pip install --upgrade pip
pip install -r code/requirements.txt --no-cache-dir
```

## Next Steps

1. Review `research.md` for theoretical background
2. Review `data-model.md` for entity specifications
3. Run tests to verify installation
4. Process your own time series data

## Support

- Check `code/.tasks/*.log` for execution errors
- Review `specs/001-bayesian-nonparametrics-anomaly-detection/contracts/` for schema validation
- Consult `research.md` for algorithmic details

---
*Version: 1.0.0 | Last updated: Implementation complete - Phase 6 polish*
