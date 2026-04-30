# Quick Start Guide

## Installation

```bash
# Clone and setup
git clone <repository-url>
cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Example

### 1. Download Datasets

```bash
python code/download_datasets.py --all
```

This downloads all NAB and UCI datasets with checksum validation.

### 2. Run DPGMM on Synthetic Data

```bash
python code/scripts/test_advi_inference.py
```

This generates synthetic data, trains the DPGMM, and outputs anomaly scores.

### 3. Compare with Baselines

```bash
python code/evaluation/statistical_tests.py --datasets nyc_taxi electricity
```

Compares DPGMM against ARIMA and Moving Average baselines.

## Project Structure

```
projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/
├── code/
│   ├── src/
│   │   ├── models/
│   │   │   ├── dp_gmm.py          # Main DPGMM implementation
│   │   │   └── time_series.py     # Time series dataclass
│   │   ├── baselines/
│   │   │   ├── arima.py           # ARIMA baseline
│   │   │   └── moving_average.py  # Moving average baseline
│   │   ├── evaluation/
│   │   │   ├── metrics.py         # Evaluation metrics
│   │   │   └── plots.py           # ROC/PR curve plots
│   │   └── utils/
│   │       ├── streaming.py       # Streaming observation utils
│   │       └── threshold.py       # Threshold calibration
│   ├── scripts/
│   │   ├── download_datasets.py   # Dataset download script
│   │   └── test_advi_inference.py # Quick test script
│   └── config.yaml                # Hyperparameters
├── data/
│   ├── raw/                       # Downloaded datasets
│   └── processed/                 # Processed data
├── specs/
│   └── 001-bayesian-nonparametrics-anomaly-detection/
│       ├── research.md            # Literature review
│       ├── data-model.md          # Data specifications
│       └── quickstart.md          # This file
├── tests/
│   ├── contract/                  # Schema contract tests
│   ├── integration/               # Integration tests
│   └── unit/                      # Unit tests
└── state/
    └── projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml
```

## Configuration

Edit `code/config.yaml` to customize:

```yaml
hyperparameters:
  concentration: 1.0        # Dirichlet process concentration
  truncation_level: 100     # Maximum mixture components
  learning_rate: 0.01       # ADVI step size
  random_seed: 42           # Reproducibility

thresholds:
  anomaly_percentile: 95    # Adaptive anomaly threshold
```

## Running Tests

```bash
# Contract tests
python code/scripts/run_contract_tests.py

# All tests
pytest tests/ -v
```

## Expected Output

After running `test_advi_inference.py`:

```
[INFO] Generated synthetic time series with 1000 observations
[INFO] Trained DPGMM with 7 active components
[INFO] ELBO converged after 234 iterations
[INFO] Anomaly scores computed for all observations
[INFO] Detected 48 anomalies (4.8% rate)
[INFO] Results saved to data/results/anomaly_scores.csv
```

## Troubleshooting

### Issue: Checksum validation fails

**Solution**: Re-run `download_datasets.py` to redownload corrupted files.

### Issue: Memory limit exceeded

**Solution**: Reduce `truncation_level` in config.yaml or use synthetic data.

### Issue: No anomalies detected

**Solution**: Lower `anomaly_percentile` threshold or verify data quality.

## Next Steps

1. Review `research.md` for theoretical background
2. Examine `data-model.md` for schema details
3. Run baseline comparisons in `statistical_tests.py`
4. Deploy streaming detector using `anomaly_detector.py` service
