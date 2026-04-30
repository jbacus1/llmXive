# API Reference

## Models API

### code/models/dp_gmm.py

**Public Names**: `adaptive_concentration_update`, `get_concentration_status`

```python
from models.dp_gmm import (
    DPGMMModel,
    adaptive_concentration_update,
    get_concentration_status
)

# DPGMMModel usage
model = DPGMMModel(config={"concentration_prior": 1.0})
score = model.update_posterior(observation)
status = model.get_concentration_status()
```

### code/models/anomaly_score.py

**Public Names**: `AnomalyScore`

```python
from models.anomaly_score import AnomalyScore

# AnomalyScore fields
# - timestamp: datetime
# - score: float (negative log posterior)
# - uncertainty: float (variance estimate)
# - component_probabilities: Dict[int, float]
# - threshold_exceeded: bool
```

### code/models/time_series.py

**Public Names**: `TimeSeries`, `TimeSeriesIterator`

```python
from models.time_series import TimeSeries, TimeSeriesIterator
from utils.streaming import StreamingObservation

# Create time series
ts = TimeSeries(
    name="example",
    values=[1.0, 2.0, 3.0],
    timestamps=[datetime.now(), ...]
)

# Iterate streaming
for obs in TimeSeriesIterator(ts):
    score = model.update_posterior(obs)
```

## Baselines API

### code/baselines/arima.py

**Public Names**: `ARIMAConfig`, `ARIMAPrediction`, `ARIMABaseline`

```python
from baselines.arima import ARIMABaseline, ARIMAConfig

config = ARIMAConfig(order=(1, 1, 1))
baseline = ARIMABaseline(config)
prediction = baseline.predict(observation)
```

### code/baselines/moving_average.py

**Public Names**: `MovingAverageConfig`, `MovingAveragePrediction`, `MovingAverageState`, `MovingAverageBaseline`, `create_baseline`, `main`

```python
from baselines.moving_average import (
    MovingAverageBaseline,
    MovingAverageConfig,
    create_baseline
)

config = MovingAverageConfig(window_size=50)
baseline = create_baseline(config)
prediction = baseline.predict(observation)
```

## Evaluation API

### code/evaluation/metrics.py

**Public Names**: `EvaluationMetrics`, `compute_f1_score`, `compute_precision`, `compute_recall`, `compute_auc`, `generate_confusion_matrix`, `save_confusion_matrix_plot`, `compute_all_metrics`

```python
from evaluation.metrics import compute_all_metrics, EvaluationMetrics

metrics = compute_all_metrics(
    y_true=ground_truth,
    y_pred=predictions,
    y_scores=scores
)
# metrics.f1_score, metrics.precision, metrics.recall, metrics.auc_roc
```

### code/evaluation/plots.py

**Public Names**: `ROCPlotConfig`, `PRPlotConfig`, `EvaluationPlotConfig`, `generate_roc_curve`, `save_roc_curve`, `generate_pr_curve`, `save_pr_curve`, `generate_evaluation_plots`, `main`

```python
from evaluation.plots import save_roc_curve, save_pr_curve

save_roc_curve(
    y_true=ground_truth,
    y_scores=scores,
    output_path="paper/figures/roc_curve.png"
)
```

### code/evaluation/statistical_tests.py

**Public Names**: `StatisticalTestResult`, `ComparisonSummary`, `paired_ttest_with_bonferroni`, `apply_bonferroni_correction`, `compare_all_models`, `format_comparison_summary`, `save_comparison_results`, `main`

```python
from evaluation.statistical_tests import paired_ttest_with_bonferroni

result = paired_ttest_with_bonferroni(
    scores_model1=scores_dp_gmm,
    scores_model2=scores_arima,
    alpha=0.05
)
```

## Utilities API

### code/utils/streaming.py

**Public Names**: `StreamingObservation`, `StreamingObservationProcessor`, `SlidingWindowBuffer`, `create_streaming_processor`

```python
from utils.streaming import (
    StreamingObservation,
    create_streaming_processor
)

obs = StreamingObservation(
    timestamp=datetime.now(),
    value=123.45,
    window_stats={"mean": 100.0, "std": 10.0}
)

processor = create_streaming_processor(window_size=100)
```

### code/utils/threshold.py

**Public Names**: `ThresholdConfig`, `AnomalyRateValidationResult`, `ThresholdResult`, `AdaptiveThresholdState`, `AdaptiveThresholdCalculator`, `compute_adaptive_threshold`, `calibrate_thresholds_across_datasets`, `main`

```python
from utils.threshold import compute_adaptive_threshold

result = compute_adaptive_threshold(
    scores=scores,
    percentile=95,
    anomaly_rate_bounds=(0.01, 0.10)
)
```

### code/utils/memory_profiler.py

**Public Names**: `MemorySnapshot`, `MemoryProfileResult`, `MemoryProfiler`, `profile_memory_usage`, `main`

```python
from utils.memory_profiler import profile_memory_usage

result = profile_memory_usage(
    operation=lambda: process_observations(),
    max_memory_gb=7.0
)
```

### code/utils/runtime_monitor.py

**Public Names**: `RuntimeSnapshot`, `RuntimeResult`, `RuntimeMonitor`, `RuntimeBudget`, `MultiOperationMonitor`, `monitor_runtime`, `main`

```python
from utils.runtime_monitor import monitor_runtime

result = monitor_runtime(
    operation=lambda: run_model(),
    budget_seconds=1800  # 30 minutes
)
```

### code/utils/checksum_manager.py

**Public Names**: `ArtifactEntry`, `ChecksumResult`, `ChecksumManager`, `main`

```python
from utils.checksum_manager import ChecksumManager

manager = ChecksumManager(
    state_path="state/projects/PROJ-024.yaml"
)
result = manager.compute_and_record("data/raw/dataset.csv")
```

## Data API

### code/data/synthetic_generator.py

**Public Names**: `AnomalyConfig`, `SignalConfig`, `SyntheticDataset`, `generate_base_signal`, `inject_point_anomalies`, `inject_contextual_anomalies`, `inject_collective_anomalies`, `generate_synthetic_timeseries`, `save_synthetic_dataset`, `load_synthetic_dataset`, `generate_validation_dataset`, `main`

```python
from data.synthetic_generator import generate_synthetic_timeseries

dataset = generate_synthetic_timeseries(
    signal_config=SignalConfig(length=1000, frequency=1.0),
    anomaly_config=AnomalyConfig(anomaly_rate=0.05)
)
```

### code/download_datasets.py

**Public Names**: `DownloadResult`, `compute_file_checksum`, `validate_checksum`, `download_from_url`, `load_checksum_cache`, `save_checksum_cache`, `download_electricity_dataset`, `download_traffic_dataset`, `download_pems_sf_dataset`, `download_synthetic_dataset`, `main`

```python
from download_datasets import download_electricity_dataset

result = download_electricity_dataset(
    output_dir="data/raw/",
    validate_checksum=True
)
```

## Scripts API

All scripts in `code/scripts/` are runnable directly with `python <script>` and require no arguments:

- `profile_memory_1000_obs.py`: Memory profiling verification
- `test_advi_inference.py`: ADVI convergence testing
- `test_concentration_tuning.py`: Concentration parameter validation
- `test_missing_value_handling.py`: Missing value edge cases
- `verify_confusion_matrix.py`: Confusion matrix generation verification
- `verify_metrics_functions.py`: Metrics computation verification
- `verify_statistical_tests.py`: Statistical tests verification

## Import Guidelines

When importing from sibling modules:

1. **Always check the API surface** - Only use public names listed above
2. **Relative imports** for intra-package: `from .utils import streaming`
3. **Absolute imports** for cross-package: `from models.dp_gmm import DPGMMModel`
4. **No private names** - Names starting with `_` are internal

Example correct imports:
```python
# ✅ Correct
from models.dp_gmm import DPGMMModel
from utils.streaming import StreamingObservation
from evaluation.metrics import compute_f1_score
```

Example incorrect imports:
```python
# ❌ Incorrect - private name
from models.dp_gmm import _initialize_model

# ❌ Incorrect - invented name
from models.dp_gmm import ARIMABaseline
```
