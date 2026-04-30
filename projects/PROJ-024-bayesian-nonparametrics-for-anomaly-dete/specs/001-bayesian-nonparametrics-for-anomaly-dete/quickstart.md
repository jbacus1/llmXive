# Quickstart: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Prerequisites

- Python 3.11+
- pip 23.0+
- 7GB+ available RAM
- Network connectivity for dataset downloads

## Installation

1. **Clone and setup virtual environment**

```bash
cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Verify installation**

```bash
python -c "import pymc; import numpy; import pandas; print('Dependencies OK')"
```

## Configuration

Edit `config.yaml` with your settings:

```yaml
# Random seeds for reproducibility
random_seed: 42
pymc_seed: 42

# DPGMM hyperparameters
concentration_param: 1.0
max_components: 10

# ADVI settings
advi_n_iter: 10000
advi_tolerance: 1e-3

# Threshold calibration
threshold_percentile: 95

# Datasets to process
datasets:
  - electricity
  - traffic
  - pems_sf
```

## Running the Pipeline

### Step 1: Download Datasets

```bash
python src/data/downloaders.py --datasets electricity traffic pems_sf
```

This fetches datasets from UCI via ucimlrepo and stores them in `data/raw/`.

### Step 2: Run DPGMM Anomaly Detection

```bash
python src/services/anomaly_detector.py --config config.yaml --mode streaming
```

This processes each dataset incrementally and outputs anomaly scores.

### Step 3: Evaluate Against Baselines

```bash
python src/evaluation/metrics.py --config config.yaml --baselines arima moving_average
```

This computes F1-scores, precision, recall, and AUC for all methods.

### Step 4: Generate Visualizations

```bash
python src/evaluation/visualizations.py --config config.yaml
```

This generates ROC and PR curves saved to `figures/`.

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Contract Tests Only

```bash
pytest tests/contract/ -v
```

### Run Unit Tests Only

```bash
pytest tests/unit/ -v
```

## Expected Outputs

After successful execution:

- `data/processed/`: Processed dataset files with checksums
- `figures/roc_*.png`: ROC curves for all datasets and methods
- `figures/pr_*.png`: Precision-recall curves for all datasets and methods
- `results/metrics.json`: Evaluation metrics in JSON format
- `logs/`: Execution logs with convergence diagnostics

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Memory exceeds 7GB | Reduce max_components in config.yaml; verify ADVI convergence |
| Dataset download fails | Check network connectivity; verify ucimlrepo version |
| Convergence not achieved | Increase advi_n_iter; adjust concentration_param |
| Runtime exceeds 30 minutes | Reduce dataset size for testing; enable early stopping |

## Next Steps

1. Review results in `results/metrics.json`
2. Examine convergence diagnostics in `logs/`
3. Compare F1-scores against SC-001 threshold (within 5% of baselines)
4. Document findings for paper section on experimental results
