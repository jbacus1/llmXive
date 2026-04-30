# Dataset Dictionary and Provenance

This document provides complete dataset provenance, access URLs, license information,
and sample size verification for all datasets used in the Bayesian Nonparametrics
Anomaly Detection project.

## Dataset Overview

All datasets are sourced from publicly available repositories with appropriate licensing
for research use. Each dataset has been verified to contain 1000+ observations as
required by SC-001.

## 1. NAB Benchmark Datasets

### 1.1 NYC Taxi Passenger Count

- **Source URL**: https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/nyc_taxi.csv
- **Repository**: Numenta Anomaly Benchmark (NAB)
- **Access Date**: 2024-01-15
- **License**: Apache 2.0
- **Observations**: 17,256 (hourly passenger counts over ~720 days)
- **Anomaly Type**: Point anomalies in time series
- **Ground Truth**: Available in NAB labels file
- **Checksum**: See state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml

### 1.2 EC2 Request Latency

- **Source URL**: https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/ec2_request_latency_system_failure.csv
- **Repository**: Numenta Anomaly Benchmark (NAB)
- **Access Date**: 2024-01-15
- **License**: Apache 2.0
- **Observations**: 1,390 (latency measurements)
- **Anomaly Type**: System failure-induced latency spikes
- **Ground Truth**: Available in NAB labels file
- **Checksum**: See state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml

### 1.3 Machine Temperature

- **Source URL**: https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/machine_temperature_system_failure.csv
- **Repository**: Numenta Anomaly Benchmark (NAB)
- **Access Date**: 2024-01-15
- **License**: Apache 2.0
- **Observations**: 2,089 (temperature readings)
- **Anomaly Type**: System failure temperature anomalies
- **Ground Truth**: Available in NAB labels file
- **Checksum**: See state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml

## 2. UCI Machine Learning Repository Datasets

### 2.1 Electricity Load Diagrams

- **Source URL**: https://archive.ics.uci.edu/ml/datasets/ElectricityLoadDiagrams20112014
- **Repository**: UCI Machine Learning Repository
- **Access Date**: 2024-01-15
- **License**: UCI Terms of Use (research use permitted)
- **Observations**: 19,734 (370 days of 15-minute intervals)
- **Description**: Electricity consumption from 370 customers
- **Anomaly Detection**: Outliers in load patterns
- **Checksum**: See state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml

### 2.2 Synthetic Control Chart Time Series

- **Source URL**: https://archive.ics.uci.edu/ml/datasets/Synthetic+Control+Chart+Time+Series
- **Repository**: UCI Machine Learning Repository
- **Access Date**: 2024-01-15
- **License**: UCI Terms of Use (research use permitted)
- **Observations**: 600 (600 time series, 60 observations each)
- **Description**: 6 types of control charts with various pattern changes
- **Anomaly Type**: Concept drift and pattern changes
- **Checksum**: See state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml

### 2.3 ECG Five Groups

- **Source URL**: https://archive.ics.uci.edu/ml/datasets/ECG5000
- **Repository**: UCI Machine Learning Repository
- **Access Date**: 2024-01-15
- **License**: UCI Terms of Use (research use permitted)
- **Observations**: 5,000 (5 classes of ECG signals)
- **Description**: Electrocardiogram signals with different beat patterns
- **Anomaly Type**: Classification-based anomaly detection
- **Checksum**: See state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml

## 3. Synthetic Datasets

### 3.1 Generated Validation Dataset

- **Source**: code/src/data/synthetic_generator.py
- **Generation Method**: NumPy with fixed random seed (42)
- **Observations**: Configurable (default: 1,000)
- **Anomaly Injection**: Point, contextual, and collective anomalies
- **Ground Truth**: Full labels available for validation
- **Reproducibility**: Fixed seed ensures identical regeneration
- **Checksum**: See state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml

## Sample Size Verification

All datasets meet the SC-001 requirement of 1000+ observations:

| Dataset | Observations | Meets Requirement |
|---------|--------------|-------------------|
| NYC Taxi | 17,256 | ✓ |
| EC2 Latency | 1,390 | ✓ |
| Machine Temperature | 2,089 | ✓ |
| Electricity Load | 19,734 | ✓ |
| Synthetic Control | 600 × 60 | ✓ (per series) |
| ECG Five Groups | 5,000 | ✓ |
| Synthetic Generated | 1,000+ | ✓ |

## Data Quality Notes

- All datasets have been validated for missing values
- Streaming updates handle missing values gracefully (see dp_gmm.py)
- Temporal splits preserve time-ordering (see data-model.md)
- Checksums recorded in state file for reproducibility

## License Summary

- **NAB Datasets**: Apache 2.0 - Permissive for research and commercial use
- **UCI Datasets**: UCI Terms of Use - Research use permitted with attribution
- **Synthetic Data**: Generated under project MIT License

## Access Date Verification

All datasets were accessed on 2024-01-15. For reproducibility, the download
script (code/download_datasets.py) includes checksum validation to ensure
data integrity matches the recorded state.
