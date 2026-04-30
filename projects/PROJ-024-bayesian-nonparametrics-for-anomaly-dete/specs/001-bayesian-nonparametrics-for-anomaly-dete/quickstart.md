# Quickstart Guide: Bayesian Nonparametrics for Anomaly Detection in Time Series

This guide provides installation instructions and usage examples for the DPGMM-based anomaly detection system.

## Prerequisites

- Python 3.11+
- pip 23.0+
- 8GB+ RAM recommended (7GB limit enforced)
- 30-minute runtime budget per dataset

## Installation

### 1. Clone and Navigate to Project

```bash
cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
cd code
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python -c "import dp_gmm; print('DPGMM module loaded successfully')"
python -c "from utils.streaming import StreamingProcessor; print('Streaming utilities ready')"
```

## Quick Start Workflow

### Step 1: Download Datasets

```bash
python code/download_datasets.py --all
```

This will download and validate (SHA256 checksum) the following datasets:
- UCI Electricity (if available)
- UCI Traffic (if available)
- PEMS-SF (from https://pems.dot.ca.gov)
- NAB benchmark datasets (synthetic fallback if needed)

Generated files will be placed in:
```
data/raw/
  ├── electricity.csv
  ├── traffic.csv
  ├── pems_sf.csv
  └── nab/
      └── *.csv
```

### Step 2: Configure Hyperparameters

Edit `code/config.yaml` to set your preferences:

```yaml
# DPGMM Hyperparameters
dp_gmm:
  concentration_prior: 1.0
  max_components: 50
  convergence_threshold: 1e-6
  max_iterations: 1000

# Anomaly Detection
anomaly:
  threshold_percentile: 95
  min_anomaly_rate: 0.01
  max_anomaly_rate: 0.10

# Data Paths
data:
  raw_dir: data/raw
  processed_dir: data/processed

# Random Seeds (for reproducibility)
random_seed: 42
```

### Step 3: Run DPGMM Model on Synthetic Data (Recommended First)

```bash
python code/scripts/run_synthetic_demo.py
```

This generates synthetic time series with known anomalies and runs the DPGMM detector:
```
data/processed/synthetic_demo/
  ├── scores.csv
  ├── anomalies.csv
  └── elbo_convergence.json
```

### Step 4: Process Real Dataset

```bash
python code/scripts/run_dp_gmm.py \
  --config code/config.yaml \
  --dataset data/raw/electricity.csv \
  --output data/processed/electricity_results/
```

### Step 5: Generate Evaluation Metrics

```bash
python code/scripts/evaluate_baseline_comparison.py \
  --dataset data/raw/electricity.csv \
  --models dp_gmm arima moving_average \
  --output data/processed/evaluation_metrics/
```

This produces:
- F1-scores, precision, recall, AUC
- ROC curve PNG (`data/processed/evaluation_metrics/roc_curve.png`)
- PR curve PNG (`data/processed/evaluation_metrics/pr_curve.png`)
- Confusion matrix

## Key Scripts Overview

| Script | Purpose |
|--------|---------|
| `code/download_datasets.py` | Download and validate datasets |
| `code/scripts/run_dp_gmm.py` | Run DPGMM anomaly detection |
| `code/scripts/run_synthetic_demo.py` | Demo with synthetic data |
| `code/scripts/evaluate_baseline_comparison.py` | Compare models |
| `code/scripts/compute_threshold.py` | Calibrate anomaly thresholds |
| `code/utils/memory_profiler.py` | Monitor memory usage |

## User Story 1: Core DPGMM (MVP)

To test the core streaming DPGMM implementation:

```bash
python code/scripts/run_dp_gmm.py \
  --config code/config.yaml \
  --mode streaming \
  --dataset data/raw/electricity.csv \
  --output data/processed/dp_gmm_streaming/
```

Expected output:
```
data/processed/dp_gmm_streaming/
  ├── anomaly_scores.csv      # Negative log posterior per observation
  ├── anomalies_detected.csv  # Flagged anomalies with timestamps
  ├── posterior_weights.json  # Mixture component weights
  └── elbo_history.json       # ELBO convergence logging
```

## User Story 2: Baseline Comparison

```bash
python code/scripts/evaluate_baseline_comparison.py \
  --dataset data/raw/traffic.csv \
  --models dp_gmm arima moving_average \
  --statistical_test paired_ttest \
  --output data/processed/baseline_comparison/
```

## User Story 3: Threshold Calibration (Unlabeled Data)

```bash
python code/scripts/compute_threshold.py \
  --scores data/processed/dp_gmm_streaming/anomaly_scores.csv \
  --method percentile \
  --percentile 95 \
  --output data/processed/thresholds/
```

## Testing

### Run All Tests

```bash
pytest tests/ -v --tb=short
```

### Run Contract Tests Only

```bash
pytest tests/contract/ -v
```

### Run Integration Tests Only

```bash
pytest tests/integration/ -v
```

### Run Memory Profile Test

```bash
pytest tests/unit/test_memory_profile.py -v
```

## Configuration Reference

### Required Files

| File | Purpose |
|------|---------|
| `code/config.yaml` | Main configuration |
| `code/requirements.txt` | Python dependencies |
| `data/raw/` | Downloaded datasets |
| `data/processed/` | Generated results |

### Environment Variables (Optional)

```bash
export DPGMM_RANDOM_SEED=42
export DPGMM_MAX_COMPONENTS=50
export DPGMM_MEMORY_LIMIT_GB=7
```

## Troubleshooting

### Dataset Download Fails

If NAB datasets are unavailable, use synthetic generation:
```bash
python code/data/synthetic_generator.py --output data/raw/synthetic.csv
```

### Memory Limit Exceeded

Reduce `max_components` in `config.yaml` or process data in chunks.

### Convergence Issues

Increase `max_iterations` or adjust `concentration_prior` in `config.yaml`.

### Numerical Instability (Low Variance)

The model includes edge case handling for low-variance time series. If warnings appear, check `data/processed/<run>/numerical_warnings.log`.

## Next Steps

1. **Phase 2 (Foundational)**: Complete `download_datasets.py`, `streaming.py`, `TimeSeries` dataclass
2. **Phase 3 (User Story 1)**: Implement `DPGMMModel` with ADVI inference
3. **Phase 4 (User Story 2)**: Add ARIMA and moving average baselines
4. **Phase 5 (User Story 3)**: Implement threshold calibration

## Support

- Design Documents: `specs/001-bayesian-nonparametrics-anomaly-detection/`
- API Surface: See `specs/001-bayesian-nonparametrics-anomaly-detection/contracts/`
- Task Tracking: `tasks.md`
