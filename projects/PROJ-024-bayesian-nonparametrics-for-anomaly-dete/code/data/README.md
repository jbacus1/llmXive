# Data Download Module

This module handles downloading and validating datasets for the Bayesian Nonparametrics Anomaly Detection project.

## Usage

```bash
# Download all datasets
python code/data/download_datasets.py

# Force re-download
python code/data/download_datasets.py --force

# Validate existing datasets
python code/data/download_datasets.py --validate
```

## Datasets

The following datasets are downloaded to `data/raw/`:

| Dataset | Description | Source |
|---------|-------------|--------|
| smd.csv | Server Machine Dataset | OmniAnomaly |
| nab_smd.csv | NAB SMD dataset | NAB |
| nab_numenta.csv | NAB Numenta dataset | NAB |
| nab_real_ad.csv | NAB Real Adversarial | NAB |
| yahoo_a3.csv | Yahoo A3 dataset | Yahoo Anomaly Detection |

## Checksums

Each downloaded file has a corresponding `.sha256` checksum file for verification.
Run `python code/data/download_datasets.py --validate` to verify integrity.
