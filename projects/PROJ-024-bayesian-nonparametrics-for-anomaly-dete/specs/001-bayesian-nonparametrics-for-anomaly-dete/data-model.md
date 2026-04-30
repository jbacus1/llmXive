# Data Model: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Overview

This document describes the data structures used throughout the anomaly detection pipeline. All data flows from raw datasets through processed formats to evaluation metrics, with schemas defined in contracts/ for validation.

## Core Entities

### TimeSeries

Represents a univariate time series with observations, timestamps, and optional anomaly labels.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| values | List[float] | Observed time series values | Yes |
| timestamps | List[datetime] | Timestamps for each observation | No |
| labels | List[int] | Anomaly labels (0=normal, 1=anomaly) | No |
| dataset_name | str | Source dataset identifier | Yes |
| checksum | str | SHA256 checksum of raw data | Yes |

### DPGMMModel

Represents the Dirichlet process Gaussian mixture model state.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| mixture_weights | List[float] | Posterior mixture weights π_k | Yes |
| component_means | List[float] | Gaussian component means μ_k | Yes |
| component_variances | List[float] | Gaussian component variances σ²_k | Yes |
| concentration_param | float | Dirichlet process α | Yes |
| n_components | int | Active mixture components | Yes |
| elbo_history | List[float] | ELBO values during optimization | Yes |
| convergence_achieved | bool | Whether ADVI converged | Yes |
| random_seed | int | Random seed for reproducibility | Yes |

### AnomalyScore

Represents the negative log posterior probability computed for each observation.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| observation_index | int | Index in original time series | Yes |
| observation_value | float | Original observation value | Yes |
| timestamp | datetime | Observation timestamp | No |
| anomaly_score | float | Negative log posterior probability | Yes |
| is_anomaly | bool | Flagged as anomaly (score > threshold) | Yes |
| threshold_used | float | Threshold applied for flagging | Yes |
| posterior_uncertainty | float | Uncertainty estimate from posterior | No |

### EvaluationMetrics

Contains performance metrics for model comparison.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| dataset_name | str | Dataset identifier | Yes |
| method | str | Model method (DPGMM, ARIMA, MA) | Yes |
| precision | float | Precision score | Yes |
| recall | float | Recall score | Yes |
| f1_score | float | F1-score | Yes |
| auc_roc | float | Area under ROC curve | Yes |
| auc_pr | float | Area under PR curve | Yes |
| threshold | float | Anomaly threshold used | Yes |
| n_anomalies_detected | int | Number of flagged anomalies | Yes |
| n_true_anomalies | int | Number of ground truth anomalies | Yes |

## Data Flow

```
raw_datasets (UCI/NAB) 
    → downloaders.download_dataset()
    → data/raw/{dataset}/raw.csv
    → checksum verified
    → data/processed/{dataset}_processed.csv
    → anomaly_detector.process_stream()
    → contracts/anomaly_score.schema.yaml validated
    → evaluation.metrics.compute()
    → contracts/evaluation_metrics.schema.yaml validated
    → visualizations.plot_curves()
    → figures/roc_{dataset}_{method}.png
    → figures/pr_{dataset}_{method}.png
```

## Schema Validation

All data structures MUST conform to YAML schemas in contracts/:
- contracts/dataset.schema.yaml: Raw and processed dataset formats
- contracts/anomaly_score.schema.yaml: Anomaly score outputs
- contracts/evaluation_metrics.schema.yaml: Evaluation metric outputs

Contract tests in tests/contract/ validate all outputs against these schemas before metrics are recorded.
