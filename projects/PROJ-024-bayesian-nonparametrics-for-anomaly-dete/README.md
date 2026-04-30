# Bayesian Nonparametrics for Anomaly Detection in Time Series

A research-grade implementation of Dirichlet Process Gaussian Mixture Models (DPGMM) for streaming anomaly detection, with baseline comparisons against ARIMA and Moving Average methods.

## Overview

This project implements Bayesian nonparametric anomaly detection for time series data using:
- **DPGMM**: Core model with stick-breaking construction and ADVI variational inference
- **ARIMA Baseline**: Classical time series forecasting approach
- **Moving Average Baseline**: Statistical z-score based detection

## Quick Start

```bash
# Clone and setup
cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete
cd code
pip install -r requirements.txt

# Download datasets
python scripts/download_all_datasets.py

# Run DPGMM anomaly detection
python scripts/run_dp_gmm.py

# Compare with baselines
python scripts/run_baseline_comparison.py
```

## Installation

### Prerequisites
- Python 3.11+
- pip package manager
- (Optional) CUDA for LSTM baseline

### Dependencies

```bash
cd code
pip install -r requirements.txt
```

Key dependencies:
- `numpy>=1.24.0` - Numerical operations
- `scipy>=1.10.0` - Statistical functions
- `pandas>=2.0.0` - Data handling
- `matplotlib>=3.7.0` - Visualization
- `seaborn>=0.12.0` - Statistical plots
- `scikit-learn>=1.2.0` - Evaluation metrics

## Usage Instructions

### 1. DPGMM Model (Primary)

The DPGMM model provides streaming anomaly detection with probabilistic uncertainty estimates.

```python
from models.dp_gmm import DPGMMModel, DPGMMConfig
from models.anomaly_score import AnomalyScore

# Initialize model with configuration
config = DPGMMConfig(
    concentration_prior=1.0,
    mean_prior_variance=10.0,
    precision_prior=1.0,
    max_components=50,
    elbo_tolerance=1e-4
)
model = DPGMMModel(config)

# Stream observations one at a time
for t, observation in enumerate(time_series):
    score: AnomalyScore = model.update(observation)
    if score.is_anomaly:
        print(f"Anomaly detected at t={t}, score={score.value}")
```

**Key Features:**
- Incremental posterior updates (no batch retraining)
- Automatic component count via stick-breaking
- Probabilistic uncertainty estimates
- Memory-efficient (<7GB for 100K observations)

**Configuration Options:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `concentration_prior` | 1.0 | Dirichlet process concentration parameter |
| `mean_prior_variance` | 10.0 | Prior variance for cluster means |
| `precision_prior` | 1.0 | Prior precision for cluster variances |
| `max_components` | 50 | Maximum mixture components allowed |
| `elbo_tolerance` | 1e-4 | Convergence threshold for ADVI |

### 2. ARIMA Baseline

Classical time series forecasting baseline for comparison.

```python
from baselines.arima import ARIMABaseline, ARIMAConfig

# Initialize ARIMA baseline
config = ARIMAConfig(
    order=(1, 1, 1),  # (p, d, q)
    seasonal_order=(0, 0, 0, 0),
    max_iterations=100
)
baseline = ARIMABaseline(config)

# Fit on training data
baseline.fit(training_series)

# Get anomaly scores for test data
predictions = baseline.predict(test_series)
scores = predictions.residuals  # Higher residuals = more anomalous
```

**Key Features:**
- Configurable ARIMA orders (p, d, q)
- Seasonal component support
- Residual-based anomaly scoring
- Fast inference on univariate series

### 3. Moving Average Baseline

Statistical z-score based detection using rolling windows.

```python
from baselines.moving_average import MovingAverageBaseline, MovingAverageConfig

# Initialize moving average baseline
config = MovingAverageConfig(
    window_size=50,
    z_threshold=3.0,  # Anomaly if |z-score| > 3
    min_observations=10  # Warmup period
)
baseline = MovingAverageBaseline(config)

# Process streaming data
for observation in time_series:
    is_anomaly = baseline.update(observation)
    z_score = baseline.z_score  # Current z-score value
```

**Key Features:**
- Configurable rolling window size
- Adjustable z-score threshold
- Warmup period for stable statistics
- Minimal computational overhead

## Dataset Management

### Supported Datasets

| Dataset | Source | Description |
|---------|--------|-------------|
| Electricity Load Diagrams | UCI ML Repository | Hourly electricity consumption |
| Traffic Sensor Data | UCI ML Repository | Highway traffic flow measurements |
| Synthetic Control Charts | UCI ML Repository | Time series with labeled anomalies |

### Downloading Datasets

```bash
# Download all datasets with checksum validation
cd code
python scripts/download_all_datasets.py

# Download specific dataset
python scripts/download_electricity.py
```

### Dataset Structure

```
data/
├── raw/              # Original downloaded files
│   ├── electricity.csv
│   ├── traffic.csv
│   └── synthetic_control.csv
└── processed/        # Cleaned/normalized versions
    └── <dataset>_cleaned.csv
```

## Configuration

Edit `config.yaml` for project-wide settings:

```yaml
# Hyperparameters
dpgmm:
  concentration_prior: 1.0
  max_components: 50
  elbo_tolerance: 1e-4

# Random seeds for reproducibility
random_seed: 42

# Dataset paths
data:
  raw_dir: data/raw
  processed_dir: data/processed

# Evaluation settings
evaluation:
  anomaly_rate_target: 0.05
  threshold_percentile: 95
```

## Output Artifacts

### Anomaly Scores

```
data/results/
├── <dataset>_dp_gmm_scores.csv
├── <dataset>_arima_scores.csv
└── <dataset>_ma_scores.csv
```

**Score CSV Format:**
| Column | Description |
|--------|-------------|
| `timestamp` | Observation index |
| `value` | Original time series value |
| `score` | Anomaly score (negative log posterior) |
| `is_anomaly` | Binary flag (1 = anomaly) |
| `uncertainty` | Confidence interval width |

### Evaluation Metrics

```
data/results/
├── <dataset>_metrics.json
├── <dataset>_roc_curve.png
└── <dataset>_pr_curve.png
```

### Model State

```
state/
└── projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml
```

Contains SHA256 checksums for all artifacts (Constitution Principle III).

## Testing

### Contract Tests (Schema Validation)

```bash
python scripts/run_contract_tests.py
```

Tests verify:
- Model output schema compliance
- Metric calculation correctness
- Threshold calibration output format

### Integration Tests

```bash
python -m pytest tests/integration/ -v
```

Tests verify:
- End-to-end streaming updates
- Baseline comparison pipeline
- Threshold calibration on unlabeled data

### Unit Tests

```bash
python -m pytest tests/unit/ -v
```

Tests verify:
- Memory profiling (<7GB limit)
- Edge case handling
- Numerical stability

## Performance Benchmarks

### Runtime Constraints (SC-003)

| Dataset Size | Max Runtime |
|--------------|-------------|
| 10K observations | 5 minutes |
| 100K observations | 30 minutes |
| 1M observations | 5 hours |

### Memory Constraints (FR-005)

| Operation | Max Memory |
|-----------|------------|
| Streaming update | <7GB RAM |
| Model checkpoint | <100MB |

## Evaluation Metrics

### Primary Metrics (FR-006)

- **F1-Score**: Harmonic mean of precision and recall
- **Precision**: True positives / (True positives + False positives)
- **Recall**: True positives / (True positives + False negatives)
- **AUC-ROC**: Area under receiver operating characteristic curve

### Statistical Significance (US2)

```python
from evaluation.statistical_tests import paired_ttest_with_bonferroni

# Compare DPGMM vs ARIMA across datasets
result = paired_ttest_with_bonferroni(
    dp_gmm_scores,
    arima_scores,
    datasets=['electricity', 'traffic', 'synthetic']
)
print(f"p-value: {result.p_value}")
print(f"significant: {result.is_significant}")
```

## Edge Cases

### Missing Values

The DPGMM model handles missing values via:
- Skip strategy (ignore missing observations)
- Imputation (mean/median fill)
- Configuration in `config.yaml`

### Low-Variance Series

Numerical stability is maintained via:
- Precision floor (1e-6 minimum variance)
- Log-space computations
- Regularization terms

### Clustered Anomalies

The model detects clustered anomalies through:
- Mixture component weight updates
- Concentration parameter tuning
- Temporal context awareness

## Reproducibility

### Constitution Principle Compliance

- **Principle I**: All code under `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/`
- **Principle III**: SHA256 checksums recorded in state files
- **Principle V**: Code organized under `code/src/`
- **Principle VI**: ELBO convergence logging enabled
- **Principle VII**: Type hints on all public APIs

### Random Seeds

All experiments use fixed seeds for reproducibility:

```yaml
random_seed: 42
numpy_seed: 42
```

## Citation

If you use this code in your research, please cite:

```bibtex
@software{bnp_anomaly_detection,
  title = {Bayesian Nonparametrics for Anomaly Detection in Time Series},
  author = {Research Team},
  year = {2024},
  url = {https://github.com/example/bnp-anomaly-detection}
}
```

## License

See LICENSE file for open-source license terms.

## Contributing

1. Create feature branch from `main`
2. Implement changes with tests
3. Run `pytest` to verify all tests pass
4. Submit pull request with detailed description

## Support

For issues or questions:
- Open an issue on GitHub
- Check `specs/001-bayesian-nonparametrics-anomaly-detection/` for design docs
- Review `research.md` for theoretical background
