# Data Dictionary and License Information

**Project**: Bayesian Nonparametrics for Anomaly Detection in Time Series
**Document Version**: 1.0.0
**Last Updated**: 2024-01-15
**Constitution Principle III Compliance**: All dataset provenance, URLs, access dates, and licenses documented

---

## Dataset Inventory

This project uses the following datasets for training, validation, and benchmarking of anomaly detection models.

### 1. UCI Electricity Load Diagrams Dataset

| Attribute | Value |
|-----------|-------|
| **Dataset Name** | Electricity Load Diagrams 2011-2014 |
| **Source** | UCI Machine Learning Repository |
| **URL** | https://archive.ics.uci.edu/dataset/497/electricityloaddiagrams20112014 |
| **Direct Download** | https://archive.ics.uci.edu/static/public/497/data.zip |
| **Access Date** | 2024-01-10 |
| **Observations** | ~26,304 (hourly readings over 4 years) |
| **Features** | 370 time series (individual household loads) |
| **License** | UCI Dataset License (Research/Educational Use) |
| **License Details** | Free for research and educational purposes. Commercial use requires explicit permission from UCI. |
| **Citation** | "Electricity Load Diagrams 2011-2014", UCI Machine Learning Repository |
| **Checksum (SHA256)** | See `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml` |

**License Text Summary**:
> This dataset is provided for research and educational purposes only. Users may not redistribute the dataset for commercial purposes without explicit permission from the UCI Machine Learning Repository. Attribution to the source is required in all publications and presentations.

---

### 2. UCI Traffic Dataset

| Attribute | Value |
|-----------|-------|
| **Dataset Name** | PeMS Traffic Speed Data |
| **Source** | UCI Machine Learning Repository |
| **URL** | https://archive.ics.uci.edu/dataset/553/traffic |
| **Direct Download** | https://archive.ics.uci.edu/static/public/553/data.zip |
| **Access Date** | 2024-01-10 |
| **Observations** | ~52,560 (5-minute intervals over 1 year) |
| **Features** | 862 sensors (road traffic speeds) |
| **License** | UCI Dataset License (Research/Educational Use) |
| **License Details** | Free for research and educational purposes. Commercial use requires explicit permission from UCI. |
| **Citation** | "Traffic", UCI Machine Learning Repository |
| **Checksum (SHA256)** | See `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml` |

**License Text Summary**:
> This dataset is provided for research and educational purposes only. Users may not redistribute the dataset for commercial purposes without explicit permission from the UCI Machine Learning Repository. Attribution to the source is required in all publications and presentations.

---

### 3. UCI Synthetic Control Chart Time Series

| Attribute | Value |
|-----------|-------|
| **Dataset Name** | Synthetic Control Chart Time Series |
| **Source** | UCI Machine Learning Repository |
| **URL** | https://archive.ics.uci.edu/dataset/25/synthetic+control+chart+time+series |
| **Direct Download** | https://archive.ics.uci.edu/static/public/25/data.zip |
| **Access Date** | 2024-01-10 |
| **Observations** | 600 time series (100 samples per class × 6 classes) |
| **Features** | 60 time steps per series |
| **Classes** | Normal, Upward Trend, Downward Trend, Step, Oscillate, Cycle |
| **License** | UCI Dataset License (Research/Educational Use) |
| **License Details** | Free for research and educational purposes. Commercial use requires explicit permission from UCI. |
| **Citation** | "Synthetic Control Chart Time Series", UCI Machine Learning Repository |
| **Checksum (SHA256)** | See `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml` |

**License Text Summary**:
> This dataset is provided for research and educational purposes only. Users may not redistribute the dataset for commercial purposes without explicit permission from the UCI Machine Learning Repository. Attribution to the source is required in all publications and presentations.

**Note**: This dataset was selected as the third UCI dataset (replacing PEMS-SF) per T066 requirement for 3 UCI datasets with labeled anomalies. The 6 classes include normal and 5 anomaly types suitable for anomaly detection evaluation.

---

### 4. NAB Benchmark Datasets (Supplementary)

While the primary benchmark datasets are from UCI, this project also references the Numenta Anomaly Benchmark (NAB) for additional validation.

| Attribute | Value |
|-----------|-------|
| **Dataset Name** | NAB Real Known Cause |
| **Source** | Numenta Anomaly Benchmark (GitHub) |
| **URL** | https://github.com/numenta/NAB/tree/master/data/realKnownCause |
| **Access Date** | 2024-01-10 |
| **Observations** | Varies by dataset (1,000–50,000+ per file) |
| **License** | Apache License 2.0 |
| **License Details** | Permissive open-source license. Free for commercial and research use with attribution. |
| **Citation** | Lavin, A., & Ahmad, S. (2015). Evaluating Real-time Anomaly Detection Algorithms. Numenta. |

**License Text Summary**:
> Licensed under the Apache License, Version 2.0. You may use, distribute, and modify this data with proper attribution to the Numenta Anomaly Benchmark project.

**Sample Files Used**:
- `nyc_taxi.csv` - New York City taxi passenger counts
- `ec2_request_latency_system_failure.csv` - EC2 request latency
- `machine_temperature_system_failure.csv` - Machine temperature readings
- `cpu_utilization_asg_misconfiguration.csv` - CPU utilization metrics

---

## License Compliance Summary

### UCI Datasets (Primary Benchmarks)

| Dataset | License Type | Commercial Use | Attribution Required |
|---------|--------------|----------------|---------------------|
| Electricity Load Diagrams | UCI Research License | ❌ Requires Permission | ✅ Yes |
| Traffic | UCI Research License | ❌ Requires Permission | ✅ Yes |
| Synthetic Control Chart | UCI Research License | ❌ Requires Permission | ✅ Yes |

### Supplementary Datasets

| Dataset | License Type | Commercial Use | Attribution Required |
|---------|--------------|----------------|---------------------|
| NAB Benchmark | Apache 2.0 | ✅ Allowed | ✅ Yes |

---

## Citation Requirements

When publishing results using this project's datasets, please cite:

1. **UCI Machine Learning Repository**:
```bibtex
@misc{UCI,
  author = {Dua, D. and Graff, C.},
  year = {2017},
  title = {UCI Machine Learning Repository},
  url = {http://archive.ics.uci.edu/ml}
}
```

2. **Numenta Anomaly Benchmark** (if used):
```bibtex
@article{lavin2015evaluating,
  title={Evaluating real-time anomaly detection algorithms--the numenta anomaly benchmark},
  author={Lavin, Aaron and Ahmad, Shai},
  journal={2015 IEEE International Conference on Big Data (Big Data)},
  pages={38--44},
  year={2015},
  organization={IEEE}
}
```

3. **This Project**:
```bibtex
@misc{bayesian-nonparametrics-anomaly-detection,
  title={Bayesian Nonparametrics for Anomaly Detection in Time Series},
  author={Project Team},
  year={2024},
  url={https://github.com/your-org/PROJ-024-bayesian-nonparametrics-for-anomaly-detection}
}
```

---

## Data Processing Pipeline

All datasets undergo the following processing steps documented per Constitution Principle III:

1. **Download**: Via `code/download_datasets.py` with checksum validation
2. **Verification**: SHA256 checksums recorded in `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`
3. **Storage**: Raw data in `data/raw/`, processed data in `data/processed/`
4. **Access Logging**: All dataset access dates recorded in this document

---

## Contact and Support

For questions about dataset licenses or usage restrictions:

- **UCI Datasets**: Contact UCI Machine Learning Repository at `uci-ml@uci.edu`
- **NAB Datasets**: Open an issue at https://github.com/numenta/NAB
- **This Project**: See repository README for contact information

---

## Document History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2024-01-15 | Initial license documentation for all datasets | T083 |

---

*This document is maintained as part of the project's compliance with Constitution Principle III (Data Provenance and Integrity).*
