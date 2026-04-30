# Bayesian Nonparametrics for Anomaly Detection in Time Series

A research project implementing **Dirichlet Process Gaussian Mixture Models (DPGMM)** with streaming updates for unsupervised anomaly detection in time series data.

## Features

- **DPGMM Core Model**: Bayesian nonparametric clustering with automatic component discovery
- **Streaming Inference**: Process observations one-at-a-time with incremental posterior updates
- **ADVI Variational Inference**: Efficient approximate Bayesian inference for real-time deployment
- **Baseline Comparisons**: ARIMA and Moving Average with Z-score baselines
- **Unsupervised Threshold Calibration**: Adaptive anomaly scoring without labeled data
- **Statistical Validation**: Paired t-tests with Bonferroni correction across datasets

## Project Structure

```
projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/
├── code/
│   ├── config.yaml                 # Hyperparameters and dataset paths
│   ├── download_datasets.py        # Dataset fetchers with checksum validation
│   ├── models/
│   │   ├── dp_gmm.py               # DPGMM implementation
│   │   ├── anomaly_score.py        # Anomaly scoring dataclass
│   │   └── time_series.py          # Time series entity
│   ├── baselines/
│   │   ├── arima.py                # ARIMA baseline
│   │   └── moving_average.py       # Moving average + Z-score baseline
│   ├── evaluation/
│   │   ├── metrics.py              # F1, precision, recall, AUC
│   │   ├── plots.py                # ROC and PR curve generators
│   │   └── statistical_tests.py    # Paired t-tests
│   ├── utils/
│   │   ├── streaming.py            # Streaming observation utilities
│   │   ├── threshold.py            # Adaptive threshold calibration
│   │   ├── memory_profiler.py      # Memory usage monitoring
│   │   └── runtime_monitor.py      # Runtime budget tracking
│   ├── data/
│   │   └── synthetic_generator.py  # Synthetic anomaly dataset generation
│   └── scripts/                    # Test and verification scripts
├── data/
│   ├── raw/                        # Downloaded datasets
│   └── processed/                  # Processed data artifacts
├── tests/
│   ├── contract/                   # Schema contract tests
│   ├── integration/                # Integration tests
│   └── unit/                       # Unit tests
├── specs/                          # Design documentation
├── state/                          # Artifact hashes and checksums
└── README.md                       # This file
```

## Installation

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
# Navigate to project directory
cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

### Verify Installation

```bash
# Run contract tests
pytest tests/contract/ -v

# Run integration tests
pytest tests/integration/ -v
```

## Configuration

Edit `code/config.yaml` to set:

```yaml
# DPGMM hyperparameters
dp_gmm:
  concentration_prior_alpha: 1.0
  max_components: 100
  convergence_threshold: 1e-6

# Baseline configurations
arima:
  order: (1, 1, 1)
  seasonal_order: (0, 1, 1, 12)

moving_average:
  window_size: 20
  z_threshold: 3.0

# Dataset paths
datasets:
  raw_dir: data/raw
  processed_dir: data/processed
```

## Quick Start

### 1. Download Datasets

```bash
cd code
python download_datasets.py --all
```

Available datasets:
- **Electricity**: UCI Electricity Load Diagrams
- **Traffic**: UCI Traffic Flow
- **PEMS-SF**: California Department of Transportation
- **Synthetic**: Generated with known ground truth anomalies

### 2. Generate Synthetic Data (Alternative)

```bash
cd code
python data/synthetic_generator.py --generate
```

### 3. Run DPGMM Model

```bash
# Process streaming observations
cd code
python scripts/test_advi_inference.py

# Test concentration parameter tuning
python scripts/test_concentration_tuning.py

# Test missing value handling
python scripts/test_missing_value_handling.py
```

### 4. Run Baseline Models

```bash
# ARIMA baseline
python baselines/arima.py --dataset electricity

# Moving average baseline
python baselines/moving_average.py --dataset electricity
```

### 5. Evaluate and Compare

```bash
# Compute evaluation metrics
python evaluation/metrics.py

# Generate ROC and PR curves
python evaluation/plots.py

# Statistical comparison across datasets
python evaluation/statistical_tests.py
```

## API Usage

### DPGMM Model

```python
from models.dp_gmm import DPGMMModel
from models.anomaly_score import AnomalyScore
from utils.streaming import create_streaming_processor

# Initialize model
model = DPGMMModel(
  concentration_prior_alpha=1.0,
  max_components=100
)

# Create streaming processor
processor = create_streaming_processor(model)

# Process observations one-at-a-time
for observation in observations:
    result = processor.process(observation)
    score: AnomalyScore = result.anomaly_score

    # Check if anomaly
    if score.is_anomaly:
        print(f"Anomaly detected at {score.timestamp}: {score.score}")
```

### ARIMA Baseline

```python
from baselines.arima import ARIMABaseline, ARIMAConfig

config = ARIMAConfig(
  order=(1, 1, 1),
  seasonal_order=(0, 1, 1, 12)
)

baseline = ARIMABaseline(config)
baseline.fit(train_data)

predictions = baseline.predict(test_data)
anomalies = [p for p in predictions if p.is_anomaly]
```

### Moving Average Baseline

```python
from baselines.moving_average import MovingAverageBaseline, MovingAverageConfig

config = MovingAverageConfig(
  window_size=20,
  z_threshold=3.0
)

baseline = MovingAverageBaseline(config)
baseline.fit(train_data)

predictions = baseline.predict(test_data)
```

### Threshold Calibration (Unsupervised)

```python
from utils.threshold import compute_adaptive_threshold, calibrate_thresholds_across_datasets

# Single dataset calibration
threshold_result = compute_adaptive_threshold(
  anomaly_scores,
  percentile=95  # 95th percentile by default
)

# Multi-dataset calibration
threshold_result = calibrate_thresholds_across_datasets(
  {
    "electricity": scores_electricity,
    "traffic": scores_traffic,
    "pems_sf": scores_pems
  }
)
```

### Evaluation Metrics

```python
from evaluation.metrics import compute_all_metrics, EvaluationMetrics

metrics: EvaluationMetrics = compute_all_metrics(
  y_true=ground_truth_labels,
  y_pred=predicted_anomalies
)

print(f"F1 Score: {metrics.f1_score:.4f}")
print(f"Precision: {metrics.precision:.4f}")
print(f"Recall: {metrics.recall:.4f}")
print(f"AUC: {metrics.auc:.4f}")
```

### Generate Evaluation Plots

```python
from evaluation.plots import generate_roc_curve, generate_pr_curve, save_roc_curve, save_pr_curve

# ROC Curve
generate_roc_curve(
  y_true=ground_truth,
  y_scores=anomaly_scores,
  model_name="DPGMM"
)
save_roc_curve("paper/figures/roc_dpgmm.png")

# PR Curve
generate_pr_curve(
  y_true=ground_truth,
  y_scores=anomaly_scores,
  model_name="DPGMM"
)
save_pr_curve("paper/figures/pr_dpgmm.png")
```

## Dataset Sources

| Dataset | Source | Download Function |
|---------|--------|-------------------|
| Electricity | UCI ML Repository | `download_electricity_dataset()` |
| Traffic | UCI ML Repository | `download_traffic_dataset()` |
| PEMS-SF | PEMS Project | `download_pems_sf_dataset()` |
| Synthetic | Local Generation | `generate_synthetic_timeseries()` |

All downloads include SHA256 checksum validation for data integrity.

## Testing

### Contract Tests

```bash
pytest tests/contract/ -v
```

Validates output schema compliance for:
- DPGMM model output
- Evaluation metrics
- Threshold calibration results

### Integration Tests

```bash
pytest tests/integration/ -v
```

Tests end-to-end pipelines:
- Streaming observation updates
- Baseline comparison pipeline
- Threshold calibration

### Unit Tests

```bash
pytest tests/unit/ -v
```

Tests individual components:
- Memory profiling (<7GB RAM limit)
- Edge case handling
- Statistical test correctness

## Performance Constraints

| Constraint | Limit |
|------------|-------|
| Memory usage | <7GB RAM |
| Runtime per dataset | <30 minutes |
| Hyperparameters | <30% tunable vs baselines |

## Constitution Principles

This project adheres to the following principles:

1. **No modification outside project directory**
2. **Tasker is sole writer of tasks.md**
3. **Checksum recording for all state artifacts**
4. **Real, reachable dataset URLs**
5. **API consistency across modules**
6. **ELBO convergence logging**
7. **Full artifact verification**

## Troubleshooting

### Common Issues

**Import errors**: Ensure you're running from the `code/` directory or have it in PYTHONPATH.

**Memory errors**: Reduce `max_components` in config.yaml or process data in smaller batches.

**Numerical instability**: Enable `smooth_anomaly_scores()` for low-variance time series.

**Missing values**: Use `test_missing_value_handling.py` to verify imputation strategies.

**Timeout warnings**: Check `code/utils/runtime_monitor.py` logs for operations exceeding 30 minutes.

## Research Documentation

See `specs/001-bayesian-nonparametrics-anomaly-detection/` for:
- `research.md`: Literature review and theoretical foundations
- `data-model.md`: Entity definitions and schema specifications
- `quickstart.md`: Installation and usage examples

## License

Research project for academic use. See project repository for license details.

## Citation

If you use this work in your research, please cite the associated technical report or publication.
