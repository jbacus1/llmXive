# Quickstart: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Prerequisites

*   Python 3.11+
*   Git
*   Internet access (for dataset download)
*   7GB+ Available RAM

## Installation

1.  **Clone and Setup**
    ```bash
    cd projects/PROJ-023-bayesian-nonparametrics-for-anomaly-dete/code/
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**
    Ensure JAX is running on CPU (to match GitHub Actions constraints):
    ```bash
    python -c "import jax; print(jax.default_backend())"
    # Expected: cpu
    ```

## Data Preparation

Run the data acquisition and preprocessing pipeline:

```bash
python -m data.download --source ucr --datasets ECGFiveDays,PowerConsumption,SyntheticControl
python -m data.preprocess --window-size 100 --stride 50
python -m data.inject --mean-shift-std 2.5 --variance-mult 3.0
```

*Note: This will populate `data/processed/` with checksummed artifacts.*

## Running the Pipeline

Execute the full inference and evaluation workflow:

```bash
python main.py --config configs/default.yaml
```

This will run:
1.  Bayesian GP Model (NumPyro)
2.  Shewhart Baseline
3.  VAE Baseline
4.  Evaluation & Comparison

## Verification

1.  **Check Outputs**:
    ```bash
    ls data/results/
    # Should contain predictions and metrics_report.csv
    ```
2.  **Validate Contracts**:
    ```bash
    pytest tests/contract/
    # Ensures outputs match contracts/anomaly-output.schema.yaml
    ```
3.  **Check Diagnostics**:
    Review `data/results/bayesian_convergence.log` for R-hat values < 1.1.

## Troubleshooting

*   **Memory Error**: Reduce `--window-size` in `preprocess.py`.
*   **Convergence Failure**: Increase `--svi-steps` in `main.py` or adjust learning rate.
*   **Dataset Missing**: Ensure `data/raw/` contains the downloaded files. Do not delete checksums in `state/`.
