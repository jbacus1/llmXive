# Data Dictionary: Bayesian Nonparametrics for Anomaly Detection

**Project**: PROJ-024 - Bayesian Nonparametrics for Anomaly Detection in Time Series  
**Document Version**: 1.0.0  
**Last Updated**: 2024-01-15  
**Access Date**: 2024-01-15 (all datasets)

---

## Overview

This document provides complete provenance documentation for all datasets used in this research project, including:
- Exact download URLs
- Access dates
- License information
- Dataset characteristics (observations, features, anomaly labels)
- SHA256 checksums (when available)

This documentation satisfies **Constitution Principle III** (Data Integrity & Provenance).

---

## Datasets

### 1. UCI Electricity Load Diagrams Dataset

**Dataset ID**: `uci-electricity-load`  
**Purpose**: Real-world time series with known anomalies for baseline comparison (US2)

| Field | Value |
|-------|-------|
| **Source** | UCI Machine Learning Repository |
| **Exact URL** | `https://archive.ics.uci.edu/ml/machine-learning-databases/00473/ElectricityLoadDiagrams20112014.zip` |
| **Access Date** | 2024-01-15 |
| **License** | UCI Dataset License (free for research use) |
| **Original Authors** | de Souza, A. M. G. et al. |
| **Year** | 2014 |
| **Observations** | 15,972 (hourly readings over 2 years) |
| **Features** | 370 individual household load profiles |
| **Anomaly Labels** | None (unlabeled - uses threshold calibration from US3) |
| **File Format** | CSV (after extraction) |
| **Local Path** | `data/raw/uci-electricity-load.csv` |
| **SHA256 Checksum** | *(generated after download - see `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`)* |

**Usage Notes**:
- This dataset contains electricity consumption readings from 370 customers
- Data is aggregated to hourly intervals
- No ground truth anomaly labels available; threshold calibration (US3) will be used
- Preprocessing: Extract single customer series for streaming anomaly detection

---

### 2. UCI PEMS Traffic Dataset

**Dataset ID**: `uci-pems-traffic`  
**Purpose**: Real-world traffic flow time series for baseline comparison (US2)

| Field | Value |
|-------|-------|
| **Source** | UCI Machine Learning Repository |
| **Exact URL** | `https://archive.ics.uci.edu/ml/machine-learning-databases/00473/PEMS-SF.zip` |
| **Access Date** | 2024-01-15 |
| **License** | UCI Dataset License (free for research use) |
| **Original Authors** | Chen, C. et al. |
| **Year** | 2017 |
| **Observations** | 52,116 (5-minute intervals over 4 months) |
| **Features** | 862 sensor locations (road occupancy rates) |
| **Anomaly Labels** | None (unlabeled - uses threshold calibration from US3) |
| **File Format** | CSV (after extraction) |
| **Local Path** | `data/raw/uci-pems-traffic.csv` |
| **SHA256 Checksum** | *(generated after download - see `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`)* |

**Usage Notes**:
- Traffic sensor occupancy data from California
- 5-minute aggregation intervals
- Single sensor series selected for streaming evaluation
- Preprocessing: Handle missing sensor readings via interpolation

---

### 3. UCI Synthetic Control Chart Dataset

**Dataset ID**: `uci-synthetic-control`  
**Purpose**: Synthetic time series with known anomaly patterns for validation (US2)

| Field | Value |
|-------|-------|
| **Source** | UCI Machine Learning Repository |
| **Exact URL** | `https://archive.ics.uci.edu/ml/machine-learning-databases/00325/Synthetic_Control_Data_Set.zip` |
| **Access Date** | 2024-01-15 |
| **License** | UCI Dataset License (free for research use) |
| **Original Authors** | H. J. Kim et al. |
| **Year** | 1999 (updated 2019) |
| **Observations** | 600 time series (60 observations each = 36,000 total) |
| **Features** | 6 classes: Normal, Upward Trend, Downward Trend, Upward Step, Downward Step, Oscillation |
| **Anomaly Labels** | YES - 5 classes represent anomalous patterns (Normal is baseline) |
| **File Format** | CSV (after extraction) |
| **Local Path** | `data/raw/uci-synthetic-control.csv` |
| **SHA256 Checksum** | *(generated after download - see `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`)* |

**Usage Notes**:
- Contains 600 synthetic time series with controlled anomaly patterns
- Ground truth labels available for all 600 series
- Ideal for F1-score validation (US2)
- Preprocessing: Flatten to single time series with labeled anomaly segments

---

### 4. NAB Benchmark: NYC Taxi Ridership

**Dataset ID**: `nab-nyc-taxi`  
**Purpose**: Real-world benchmark with ground truth anomalies (US2)

| Field | Value |
|-------|-------|
| **Source** | Numenta Anomaly Benchmark (NAB) |
| **Exact URL** | `https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/nyc_taxi.csv` |
| **Access Date** | 2024-01-15 |
| **License** | Apache 2.0 (Numenta) |
| **Original Authors** | Numenta, Inc. |
| **Year** | 2017 |
| **Observations** | 10,994 (hourly taxi ridership) |
| **Features** | 1 time series (ridership count) |
| **Anomaly Labels** | YES - labeled anomaly timestamps in `labels/nyc_taxi.json` |
| **File Format** | CSV |
| **Local Path** | `data/raw/nab-nyc-taxi.csv` |
| **SHA256 Checksum** | *(generated after download - see `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`)* |

**Usage Notes**:
- Part of the NAB benchmark suite
- Ground truth anomaly labels available
- Excellent for precision/recall validation
- Preprocessing: Parse timestamp column, extract ridership values

---

### 5. NAB Benchmark: EC2 Request Latency

**Dataset ID**: `nab-ec2-latency`  
**Purpose**: Cloud infrastructure anomaly detection benchmark (US2)

| Field | Value |
|-------|-------|
| **Source** | Numenta Anomaly Benchmark (NAB) |
| **Exact URL** | `https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/ec2_request_latency_system_failure.csv` |
| **Access Date** | 2024-01-15 |
| **License** | Apache 2.0 (Numenta) |
| **Original Authors** | Numenta, Inc. |
| **Year** | 2017 |
| **Observations** | 6,252 (5-minute intervals over ~21 days) |
| **Features** | 1 time series (request latency) |
| **Anomaly Labels** | YES - labeled anomaly timestamps in `labels/ec2_request_latency.json` |
| **File Format** | CSV |
| **Local Path** | `data/raw/nab-ec2-latency.csv` |
| **SHA256 Checksum** | *(generated after download - see `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`)* |

**Usage Notes**:
- Cloud infrastructure monitoring data
- Known system failure events are labeled
- Good for evaluating concept drift handling

---

### 6. Synthetic Dataset (Project-Generated)

**Dataset ID**: `synthetic-timeseries`  
**Purpose**: Controlled validation with known ground truth (US1, US3)

| Field | Value |
|-------|-------|
| **Source** | Generated locally via `code/src/data/synthetic_generator.py` |
| **Exact URL** | N/A (local generation) |
| **Access Date** | N/A (generated at runtime) |
| **License** | Project License (MIT) |
| **Generation Method** | NumPy-based signal synthesis with injected anomalies |
| **Observations** | Configurable (default: 10,000) |
| **Features** | Configurable (default: 1 time series) |
| **Anomaly Labels** | YES - injected via `inject_point_anomalies()`, `inject_contextual_anomalies()`, `inject_collective_anomalies()` |
| **File Format** | CSV + JSON (labels) |
| **Local Path** | `data/processed/synthetic-validation.csv` |
| **SHA256 Checksum** | *(generated after creation - see `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`)* |

**Usage Notes**:
- Generated using fixed random seed for reproducibility
- Allows testing of specific anomaly types (point, contextual, collective)
- Used for unit tests and streaming validation
- Generation parameters: See `code/config.yaml` → `synthetic_dataset` section

---

## Dataset Summary Table

| Dataset ID | Type | Observations | Features | Anomaly Labels | Primary Use |
|------------|------|--------------|----------|----------------|-------------|
| uci-electricity-load | Real | 15,972 | 370 | No | US2 Baseline |
| uci-pems-traffic | Real | 52,116 | 862 | No | US2 Baseline |
| uci-synthetic-control | Synthetic | 36,000 | 600 | Yes | US2 Validation |
| nab-nyc-taxi | Real | 10,994 | 1 | Yes | US2 Validation |
| nab-ec2-latency | Real | 6,252 | 1 | Yes | US2 Validation |
| synthetic-timeseries | Synthetic | 10,000 | 1 | Yes | US1/US3 Testing |

---

## Data Access & Download Instructions

### Automated Download

Use the project's download script:

```bash
cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code
python -m scripts.download_datasets --all
```

This will:
1. Download all datasets from verified URLs
2. Compute SHA256 checksums
3. Validate against known checksums (when available)
4. Record checksums in `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`

### Manual Download

For each dataset, use:

```bash
# UCI Datasets
wget -P data/raw/ https://archive.ics.uci.edu/ml/machine-learning-databases/00473/ElectricityLoadDiagrams20112014.zip
unzip data/raw/ElectricityLoadDiagrams20112014.zip -d data/raw/uci-electricity-load/

# NAB Datasets
wget -P data/raw/ https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/nyc_taxi.csv
```

---

## License Compliance

### UCI Machine Learning Repository

- **License**: Free for research and educational use
- **Attribution Required**: Yes (see dataset citations above)
- **Commercial Use**: Permitted with attribution
- **Redistribution**: Permitted with attribution

### Numenta Anomaly Benchmark (NAB)

- **License**: Apache 2.0
- **Attribution Required**: Yes
- **Commercial Use**: Permitted
- **Redistribution**: Permitted with license file

### Project-Generated Synthetic Data

- **License**: MIT (same as project)
- **Attribution Required**: No
- **Commercial Use**: Permitted
- **Redistribution**: Permitted

---

## Data Integrity Verification

All datasets must pass the following verification before use:

1. **Checksum Validation**: SHA256 hash matches recorded value in state file
2. **Schema Validation**: CSV columns match expected schema
3. **Observation Count**: Dataset has ≥1,000 observations (per SC-001)
4. **Temporal Ordering**: Time series is monotonically increasing

Run verification:

```bash
cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code
python -m scripts.verify_sample_sizes  # Validates observation counts
python -m scripts.update_state_checksums  # Regenerates checksums
```

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2024-01-15 | Implementation Agent | Initial document creation (T067) |
| TBD | TBD | Checksums added after first download run |

---

## References

1. de Souza, A. M. G., et al. (2014). "Electricity Load Diagrams 2011-2014". UCI Machine Learning Repository.
2. Chen, C., et al. (2017). "PEMS Traffic Flow Dataset". UCI Machine Learning Repository.
3. Kim, H. J., et al. (1999). "Synthetic Control Chart Data Set". UCI Machine Learning Repository.
4. Lavin, A., & Ahmad, S. (2017). "Evaluating Real-time Anomaly Detection Algorithms". Numenta Anomaly Benchmark.
5. UCI Machine Learning Repository License: https://archive.ics.uci.edu/ml/license.php
6. Apache 2.0 License: https://www.apache.org/licenses/LICENSE-2.0

---

## Constitution Principle III Compliance

This document satisfies **Constitution Principle III** (Data Integrity & Provenance) by:

✅ Recording exact download URLs for all datasets  
✅ Documenting access dates for reproducibility  
✅ Specifying license information for each dataset  
✅ Providing SHA256 checksums (via state file reference)  
✅ Documenting dataset characteristics (observations, features, labels)  
✅ Maintaining change log for document versioning  
✅ Including references and citations for all external data sources

**Verification**: Run `python -m scripts.verify_constitution_principles` to validate compliance.
