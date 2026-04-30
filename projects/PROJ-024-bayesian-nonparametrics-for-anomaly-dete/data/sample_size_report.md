# Dataset Sample Size Verification Report

Generated: 2026-04-30T16:36:44.696415

## Summary

- **Total Datasets Analyzed**: 5
- **Datasets with 1000+ Observations**: 5
- **Datasets Below 1000 Observations**: 0

## Dataset Details

| Dataset Name | File Path | Observations | Features | Has Anomalies | Anomaly Count | File Size (MB) | Valid (>1000) |
|--------------|-----------|--------------|----------|---------------|---------------|----------------|---------------|
| electricity | /Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/raw/electricity.csv | 10000 | 2 | No | 0 | 0.48 | ✓ |
| traffic | /Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/raw/traffic.csv | 10000 | 2 | No | 0 | 0.48 | ✓ |
| synthetic_control | /Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/raw/synthetic_control.csv | 22695 | 2 | No | 0 | 0.7 | ✓ |
| pems_sf_synthetic | /Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/raw/pems_sf_synthetic.csv | 10000 | 3 | Yes | 500 | 0.38 | ✓ |
| pems_sf | /Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/raw/pems_sf.csv | 18050 | 2 | No | 0 | 0.51 | ✓ |

## Requirements

- **Minimum Observations**: 1000 per dataset (per SC-001)
- **Datasets Analyzed**: Electricity, Traffic, Synthetic Control Chart

## Datasets Below Requirement

All datasets meet the 1000+ observation requirement.
