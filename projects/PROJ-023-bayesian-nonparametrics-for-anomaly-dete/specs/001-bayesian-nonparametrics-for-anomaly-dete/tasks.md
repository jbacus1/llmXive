# Tasks: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Format**: `[ID] [P?] Description` — `[P]` means parallelizable; ID format `T###`.

## Phase 1: Setup

- [X] T001 Create code/requirements.txt with numpy, pandas, scipy, scikit-learn, matplotlib, pymc dependencies (pinned versions, CPU only)
- [X] T002 Create code/scripts/ directory structure for download, analysis, baselines, figures

## Phase 2: Data acquisition

- [X] T003 Write code/scripts/download_data.py that downloads a small UCR Time Series Archive dataset (e.g., NormalDistribution from https://raw.githubusercontent.com/cbergmeir/numerical_time_series_data/master/data/NormalDistribution.txt) to data/raw/series.csv. MUST execute and produce the file.
- [X] T004 Write code/scripts/inject_anomalies.py that loads data/raw/series.csv, injects mean shifts and variance spikes at known indices, saves data/processed/series_with_anomalies.csv plus data/processed/ground_truth.csv. MUST execute and produce both files.

## Phase 3: Baseline + Bayesian methods

- [X] T005 Write code/scripts/baseline_shewhart.py implementing a Shewhart control chart on data/processed/series_with_anomalies.csv. Save predictions to data/results/shewhart_predictions.csv. MUST execute.
- [X] T006 Write code/scripts/bayesian_gp.py implementing a simple Gaussian process anomaly detector via scipy/numpy on the same input. Save predictions to data/results/bayesian_predictions.csv. MUST execute.

## Phase 4: Evaluation

- [X] T007 Write code/scripts/evaluate.py that computes precision, recall, F1, and AUC-ROC for both methods against data/processed/ground_truth.csv. Save data/results/evaluation.json. MUST execute.

## Phase 5: Figures

- [X] T008 Write code/scripts/render_fig1.py producing paper/figures/fig1_timeseries.png — line plot of the time series with anomaly indices marked. MUST execute.
- [X] T009 Write code/scripts/render_fig2.py producing paper/figures/fig2_method_comparison.png — bar chart comparing F1/AUC of the two methods. MUST execute.

## Phase 6: Results note

- [X] T010 Write paper/results.md summarizing what the figures and statistics show. NO citations beyond what's in research.md.
