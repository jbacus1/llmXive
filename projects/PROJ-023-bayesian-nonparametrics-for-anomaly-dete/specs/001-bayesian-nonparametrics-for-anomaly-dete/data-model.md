# Data Model: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Entities

### TimeSeriesWindow
A segmented subset of the original time series data used for inference.
*   **Attributes**:
    *   `window_id`: Unique string identifier (hash of content).
    *   `dataset_source`: Name of the original dataset (e.g., "ECGFiveDays").
    *   `start_index`: Integer index in raw data.
    *   `end_index`: Integer index in raw data.
    *   `values`: Float array of normalized time series values.
    *   `timestamp_origin`: ISO-8601 timestamp of the window start (if available).

### AnomalyLabel
Ground truth indicator marking the index and type of injected anomaly.
*   **Attributes**:
    *   `window_id`: Reference to `TimeSeriesWindow`.
    *   `anomaly_indices`: List of integers indicating indices where anomalies were injected.
    *   `anomaly_type`: Enum (`mean_shift`, `variance_spike`).
    *   `injection_params`: Dictionary containing shift magnitude and variance multiplier used.

### PerformanceMetric
Aggregated scores representing model effectiveness.
*   **Attributes**:
    *   `model_name`: String (e.g., "Bayesian_GP", "Shewhart", "VAE").
    *   `dataset_name`: String.
    *   `precision`: Float (0.0 - 1.0).
    *   `recall`: Float (0.0 - 1.0).
    *   `f1_score`: Float (0.0 - 1.0).
    *   `auc_roc`: Float (0.0 - 1.0).
    *   `inference_time_seconds`: Float.
    *   `peak_memory_mb`: Float.

## Data Flow

1.  **Ingestion**: `code/data/download.py` fetches raw CSV/ARFF from UCR/UCI.
    *   **Storage**: `data/raw/<dataset_name>.<ext>`
    *   **Hygiene**: Checksum recorded in `state/projects/PROJ-023-bayesian-nonparametrics-for-anomaly-dete.yaml`.
2.  **Preprocessing**: `code/data/preprocess.py` normalizes and segments.
    *   **Output**: `data/processed/<dataset_name>_windows.parquet`
    *   **Hygiene**: New checksum recorded.
3.  **Injection**: `code/data/inject.py` adds anomalies.
    *   **Output**: `data/processed/<dataset_name>_windows_anomalous.parquet`
    *   **Hygiene**: Metadata includes `anomaly_indices`.
4.  **Inference**: `code/models/` generates scores.
    *   **Output**: `data/results/<model_name>_predictions.json` (Validated against `contracts/anomaly-output.schema.yaml`).
5.  **Evaluation**: `code/eval/` computes metrics.
    *   **Output**: `data/results/metrics_report.csv`.

## Storage Constraints

*   **Format**: Parquet for processed data (compression, type safety). JSON for model outputs (schema validation).
*   **PII**: No Personally Identifiable Information allowed in `data/`.
*   **Versioning**: Every file in `data/` is versioned via content hash in the project state YAML.
