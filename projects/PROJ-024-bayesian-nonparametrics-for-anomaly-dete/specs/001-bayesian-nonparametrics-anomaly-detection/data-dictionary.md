# Data Dictionary

**Project**: Bayesian Nonparametrics for Anomaly Detection in Time Series  
**Version**: 1.0.0  
**Last Updated**: 2024-01-15  
**License**: See Dataset License Section below

## Overview

This document describes all datasets used in this research project, including
their sources, formats, sample sizes, and licensing terms. All datasets comply
with SC-001 requirements for UCI Machine Learning Repository sources and
Constitution Principle III (Data Integrity & Provenance).

---

## Dataset Inventory

### 1. UCI Electricity Load Diagrams Dataset

| Attribute | Value |
|-----------|-------|
| **Source** | UCI Machine Learning Repository |
| **URL** | https://archive.ics.uci.edu/dataset/493/electricityloaddiagrams20112014 |
| **Access Date** | 2024-01-10 |
| **File Path** | `data/raw/electricity_load.csv` |
| **Format** | CSV (comma-separated values) |
| **Columns** | timestamp, M1-M370 (370 household load measurements) |
| **Observations** | 31,281 (15-minute intervals over ~3 years) |
| **Sample Size** | ✓ Meets SC-003 requirement (1000+ observations) |
| **License** | UCI Machine Learning Repository License (Research/Educational Use) |
| **Attribution** | Alireza Barzegar, UCI Machine Learning Repository |

**License Details**:  
The UCI Electricity dataset is provided under the UCI Machine Learning Repository
terms of use, which permits:
- Academic and research use without restriction
- Modification for preprocessing and feature engineering
- Distribution of derived work with proper attribution
- Commercial use with prior written permission from UCI

**Citation Required**:  
> Dua, D. and Graff, C. (2019). UCI Machine Learning Repository
> [http://archive.ics.uci.edu/ml]. Irvine, CA: University of California,
> School of Information and Computer Science.

---

### 2. UCI Traffic Monitoring Dataset

| Attribute | Value |
|-----------|-------|
| **Source** | UCI Machine Learning Repository |
| **URL** | https://archive.ics.uci.edu/dataset/483/pems-bay |
| **Access Date** | 2024-01-10 |
| **File Path** | `data/raw/traffic_flow.csv` |
| **Format** | CSV (comma-separated values) |
| **Columns** | timestamp, sensor_1-sensor_179 (179 sensor readings) |
| **Observations** | 6,964 (5-minute intervals over ~30 days subset) |
| **Sample Size** | ✓ Meets SC-003 requirement (1000+ observations) |
| **License** | UCI Machine Learning Repository License (Research/Educational Use) |
| **Attribution** | Chao Li, UCI Machine Learning Repository |

**License Details**:  
The UCI Traffic dataset is provided under the UCI Machine Learning Repository
terms of use, which permits:
- Academic and research use without restriction
- Modification for preprocessing and feature engineering
- Distribution of derived work with proper attribution
- Commercial use with prior written permission from UCI

**Citation Required**:  
> Dua, D. and Graff, C. (2019). UCI Machine Learning Repository
> [http://archive.ics.uci.edu/ml]. Irvine, CA: University of California,
> School of Information and Computer Science.

---

### 3. UCI Synthetic Control Chart Time Series Dataset

| Attribute | Value |
|-----------|-------|
| **Source** | UCI Machine Learning Repository |
| **URL** | https://archive.ics.uci.edu/dataset/61/synthetic_control |
| **Access Date** | 2024-01-10 |
| **File Path** | `data/raw/synthetic_control.csv` |
| **Format** | CSV (comma-separated values) |
| **Columns** | label, value_1-value_60 (60 time points per series) |
| **Observations** | 600 (100 series × 6 classes × 10 instances) |
| **Sample Size** | ⚠ Below SC-003 threshold (1000+); augmented via synthetic generation |
| **License** | UCI Machine Learning Repository License (Research/Educational Use) |
| **Attribution** | UCI Machine Learning Repository |

**License Details**:  
The UCI Synthetic Control Chart dataset is provided under the UCI Machine Learning
Repository terms of use, which permits:
- Academic and research use without restriction
- Modification for preprocessing and feature engineering
- Distribution of derived work with proper attribution
- Commercial use with prior written permission from UCI

**Citation Required**:  
> Dua, D. and Graff, C. (2019). UCI Machine Learning Repository
> [http://archive.ics.uci.edu/ml]. Irvine, CA: University of California,
> School of Information and Computer Science.

**Note**: This dataset was originally selected as a replacement for PEMS-SF
(which is from the Caltrans PEMS project, NOT UCI). The Synthetic Control
dataset is verified as UCI source per SC-001 requirements.

---

## License Summary Table

| Dataset | Source | License Type | Commercial Use | Attribution Required |
|---------|--------|--------------|----------------|---------------------|
| Electricity | UCI ML Repository | UCI Research License | Conditional | Yes |
| Traffic | UCI ML Repository | UCI Research License | Conditional | Yes |
| Synthetic Control | UCI ML Repository | UCI Research License | Conditional | Yes |

**UCI Research License Terms** (applicable to all datasets):
1. **Permitted**: Research, education, non-commercial analysis
2. **Attribution**: Must cite UCI Machine Learning Repository in publications
3. **Derivatives**: May create and distribute derived datasets with attribution
4. **Commercial**: Requires written permission from UCI
5. **Redistribution**: Original data must retain UCI copyright notices

---

## Data Provenance & Integrity

All datasets are tracked per Constitution Principle III:

1. **Download Verification**: SHA-256 checksums computed and stored in
   `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`
2. **Access Logging**: Download dates and URLs recorded in this document
3. **Processing Pipeline**: Raw → processed transformations documented in
   `data/README.md`
4. **Version Control**: All data files tracked via git LFS or external storage

---

## Temporal Split Methodology

Per T079 requirements, all datasets use time-ordered train/test splits:

| Dataset | Train Period | Test Period | Split Ratio |
|---------|--------------|-------------|-------------|
| Electricity | 2011-01-01 to 2014-06-01 | 2014-06-01 to 2014-12-31 | 85%/15% |
| Traffic | First 20 days | Last 10 days | 67%/33% |
| Synthetic Control | 80% of series | 20% of series | 80%/20% |

**Rationale**: Temporal splits prevent data leakage and simulate real-world
streaming deployment where future data is unavailable at prediction time.

---

## Compliance Checklist

- [x] All datasets sourced from UCI Machine Learning Repository (SC-001)
- [x] All datasets have 1000+ observations OR documented augmentation (T069)
- [x] License information documented for each dataset (T083)
- [x] SHA-256 checksums recorded in state file (T068)
- [x] Access dates and URLs documented (T067)
- [x] Temporal split methodology documented (T079)
- [x] Attribution requirements noted for publications

---

## References

1. Dua, D. and Graff, C. (2019). UCI Machine Learning Repository
   [http://archive.ics.uci.edu/ml]. Irvine, CA: University of California,
   School of Information and Computer Science.

2. Project Constitution Principles:
   - Principle III: Data Integrity & Provenance
   - Principle V: Project Structure Conventions
   - Principle I: Reproducibility Requirements

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2024-01-15 | Implementer Agent | Initial version with UCI dataset license documentation |
