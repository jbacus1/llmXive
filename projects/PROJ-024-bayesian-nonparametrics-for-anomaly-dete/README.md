# Bayesian Nonparametrics for Anomaly Detection in Time Series

A research-grade implementation of streaming Dirichlet Process Gaussian Mixture Models (DPGMM) for real-time anomaly detection in time series data, with baseline comparisons against ARIMA and Moving Average methods.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage Guide](#usage-guide)
  - [Downloading Datasets](#downloading-datasets)
  - [Running DPGMM Model](#running-dpgmm-model)
  - [Running ARIMA Baseline](#running-arima-baseline)
  - [Running Moving Average Baseline](#running-moving-average-baseline)
  - [Evaluation & Metrics](#evaluation--metrics)
- [Configuration](#configuration)
- [Testing](#testing)
- [License](#license)

## Overview

This project implements a streaming DPGMM algorithm for anomaly detection in time series data. The key features include:

- **Streaming Inference**: Process observations one at a time with incremental posterior updates
- **AdVI Variational Inference**: Efficient posterior approximation with ELBO convergence monitoring
- **Adaptive Threshold Calibration**: Automatic threshold computation for unlabeled data
- **Memory Efficient**: <7GB RAM limit for processing 1000+ observations
- **Baseline Comparison**: Compare against ARIMA and Moving Average baselines with F1-score validation

## Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt

# Download datasets
python code/download_datasets.py

# Run DPGMM model
python code/models/dp_gmm.py

# Run evaluation
python code/evaluation/metrics.py
```

## Installation

### Prerequisites

- Python 3.11+
- pip package manager
- Virtual environment (recommended)

### Step-by-Step

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

3. **Verify installation**:
   ```bash
   python -c "import numpy; import scipy; print('Installation OK')"
   ```

## Project Structure

```
projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/
├── code/
│   ├── baselines/
│   │   ├── arima.py              # ARIMA baseline implementation
│   │   └── moving_average.py     # Moving average baseline
│   ├── data/
│   │   └── synthetic_generator.py # Synthetic data generation
│   ├── evaluation/
│   │   ├── metrics.py            # Evaluation metrics (F1, precision, recall, AUC)
│   │   ├── plots.py              # ROC/PR curve visualization
│   │   └── statistical_tests.py  # Paired t-tests with Bonferroni correction
│   ├── models/
│   │   ├── dp_gmm.py             # Core DPGMM model with ADVI
│   │   ├── anomaly_score.py      # AnomalyScore dataclass
│   │   └── time_series.py        # TimeSeries dataclass
│   ├── utils/
│   │   ├── streaming.py          # Streaming observation utilities
│   │   ├── memory_profiler.py    # Memory profiling utilities
│   │   ├── runtime_monitor.py    # Runtime monitoring
│   │   ├── threshold.py          # Threshold calibration
│   │   └── hyperparameter_counter.py
│   ├── scripts/                  # Utility scripts for testing/validation
│   │   ├── download_synthetic_control.py
│   │   ├── generate_checksums.py
│   │   ├── profile_memory_1000_obs.py
│   │   ├── reduce_config.py
│   │   ├── run_contract_tests.py
│   │   ├── test_advi_inference.py
│   │   ├── test_concentration_tuning.py
│   │   ├── test_missing_value_handling.py
│   │   ├── validate_quickstart_artifacts.py
│   │   └── verify_*.py           # Various verification scripts
│   └── config.yaml               # Hyperparameters and configuration
├── data/
│   ├── raw/                      # Raw downloaded datasets
│   └── processed/                # Processed datasets
├── paper/
│   └── figures/                  # Generated plots and figures
├── specs/
│   └── 001-bayesian-nonparametrics-anomaly-detection/
│       ├── research.md           # Literature review
│       ├── data-model.md         # Entity definitions
│       ├── quickstart.md         # Usage examples
│       └── data-dictionary.md    # Dataset provenance
├── state/
│   └── projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml
├── tests/
│   ├── contract/                 # Contract tests
│   ├── integration/              # Integration tests
│   └── unit/                     # Unit tests
└── README.md                     # This file
```

## Usage Guide

### Downloading Datasets

The project supports multiple datasets from UCI Machine Learning Repository and other sources:

```bash
# Download all available datasets
python code/download_datasets.py

# Download specific datasets
python code/download_datasets.py --dataset electricity
python code/download_datasets.py --dataset traffic
python code/download_datasets.py --dataset synthetic_control
```

**Supported Datasets**:
- **Electricity**: UCI Electricity dataset with labeled anomalies
- **Traffic**: UCI Traffic dataset
- **Synthetic Control Chart**: UCI Synthetic Control Chart dataset
- **PEMS-SF**: PEMS project traffic data (https://pems.dotca.gov)

After downloading, datasets are stored in `data/raw/` with SHA256 checksums validated and recorded in `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`.

### Running DPGMM Model

The DPGMM model can be run in streaming mode to process time series observations:

```bash
# Basic usage with default configuration
python code/models/dp_gmm.py

# With custom configuration
python code/models/dp_gmm.py --config code/config.yaml
```

**Key Features**:
- **Streaming Updates**: Process observations one at a time
- **ADVI Inference**: Automatic differentiation variational inference
- **ELBO Monitoring**: Convergence logging for inference quality
- **Anomaly Scoring**: Negative log posterior probability computation
- **Adaptive Threshold**: 95th percentile threshold calibration

**Output**:
- Anomaly scores saved to `data/results/dpgmm_scores.csv`
- ELBO history logged to console and `data/results/elbo_history.json`
- Cluster assignments saved to `data/results/cluster_assignments.csv`

### Running ARIMA Baseline

The ARIMA baseline provides a traditional time series forecasting approach:

```bash
# Basic usage
python code/baselines/arima.py

# With custom parameters
python code/baselines/arima.py --p 1 --d 1 --q 1
```

**Configuration** (`code/config.yaml`):
```yaml
arima:
  order: [1, 1, 1]  # (p, d, q)
  seasonal_order: [0, 0, 0, 0]
  enforce_stationarity: true
  enforce_invertibility: true
```

**Output**:
- Predictions saved to `data/results/arima_predictions.csv`
- Anomaly flags based on residual thresholds

### Running Moving Average Baseline

The moving average baseline with z-score detection:

```bash
# Basic usage
python code/baselines/moving_average.py

# With custom window size
python code/baselines/moving_average.py --window_size 20 --z_threshold 3.0
```

**Configuration** (`code/config.yaml`):
```yaml
moving_average:
  window_size: 20
  z_threshold: 3.0
  min_samples: 10
```

**Output**:
- Predictions saved to `data/results/moving_average_predictions.csv`
- Z-scores and anomaly flags

### Evaluation & Metrics

Compare model performance using evaluation metrics:

```bash
# Run full evaluation pipeline
python code/evaluation/metrics.py

# Generate ROC/PR curves
python code/evaluation/plots.py

# Run statistical tests
python code/evaluation/statistical_tests.py
```

**Metrics Computed**:
- F1-Score
- Precision
- Recall
- AUC (Area Under Curve)
- Confusion Matrix

**Statistical Tests**:
- Paired t-test with Bonferroni correction
- Model comparison across datasets

## Configuration

Main configuration file: `code/config.yaml`

```yaml
# DPGMM Configuration
dp_gmm:
  alpha: 1.0              # Concentration parameter
  gamma: 1.0              # Base measure parameter
  mu_0: 0.0               # Prior mean
  lambda_0: 1.0           # Prior precision
  alpha_0: 1.0            # Prior degrees of freedom
  beta_0: 1.0             # Prior scale
  max_components: 100     # Maximum mixture components
  elbo_tolerance: 1e-4    # Convergence tolerance
  max_iterations: 1000    # Maximum iterations

# Random seed for reproducibility
random_seed: 42

# Dataset paths
data:
  raw_dir: data/raw
  processed_dir: data/processed
  results_dir: data/results

# Threshold calibration
threshold:
  percentile: 95          # 95th percentile for anomaly threshold
  min_anomaly_rate: 0.01  # Minimum expected anomaly rate
  max_anomaly_rate: 0.10  # Maximum expected anomaly rate
```

## Testing

Run the complete test suite:

```bash
# Run all tests
pytest tests/ -v

# Run contract tests only
pytest tests/contract/ -v

# Run integration tests
pytest tests/integration/ -v

# Run unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/ -v --cov=code --cov-report=html
```

**Test Categories**:
- **Contract Tests**: Verify API schema compliance
- **Integration Tests**: End-to-end pipeline validation
- **Unit Tests**: Individual component testing
- **Memory Tests**: Verify <7GB RAM constraint
- **Runtime Tests**: Verify <30 minute execution constraint

**Verification Scripts**:
```bash
# Verify project structure
python code/scripts/verify_project_structure.py

# Verify spec documentation
python code/scripts/verify_spec_docs.py

# Run contract tests via script
python code/scripts/run_contract_tests.py

# Profile memory usage
python code/scripts/profile_memory_1000_obs.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Research Contact**: See `specs/001-bayesian-nonparametrics-anomaly-detection/research.md` for literature review and theoretical foundations.

**Data Provenance**: See `specs/001-bayesian-nonparametrics-anomaly-detection/data-dictionary.md` for dataset URLs, licenses, and checksums.
