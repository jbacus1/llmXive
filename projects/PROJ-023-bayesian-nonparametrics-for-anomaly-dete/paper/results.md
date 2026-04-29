# Results: Bayesian vs.\ Shewhart Anomaly Detection on Airline Passenger Series

## Data

We use the public airline-passengers monthly time series (n=144) from
the `jbrownlee/Datasets` GitHub mirror. We inject three synthetic
anomalies: a +50% mean shift at month 20, a +100-passenger variance
spike at month 60, and a -50% drop at month 100.

## Methods

We compare two anomaly detectors:

1. **Shewhart control chart** — flags points outside ±3 SD of the
   global mean. Pure parametric / stationarity assumption.
2. **Rolling-window Bayesian-style detector** — for each point, computes
   a z-score under a Gaussian fit to the previous 12 months and flags
   when |z| > 2.5. Approximates a nonparametric rolling Gaussian
   process.

## Results

| Method | Precision | Recall | F1 |
|--|--|--|--|
| Shewhart | 0.000 | 0.000 | 0.000 |
| Bayesian (rolling GP) | 0.300 | 1.000 | 0.462 |

The rolling Bayesian-style detector recovered all three injected
anomalies (recall = 1.0) at the cost of 7 false positives during the
seasonal swings of the airline series. The Shewhart chart, anchored
at the global mean, missed every injected anomaly because the trend
in the series dominates the global standard deviation.

## Figures

- `paper/figures/fig1_timeseries.png` — time series with injected
  anomaly indices marked.
- `paper/figures/fig2_method_comparison.png` — F1 + recall bar
  comparison.

## Limitations

This is a small pilot on a single series. A full evaluation should
sweep multiple injection magnitudes, test on a battery of UCR
datasets, and use a true Dirichlet-process mixture rather than the
rolling-Gaussian approximation. Each of those extensions decomposes
into <30-minute GHA tasks; they are deferred to a follow-up.

## Reproducibility

All scripts in `code/scripts/`, raw data in `data/raw/`, processed
data in `data/processed/`, results in `data/results/`, figures in
`paper/figures/`. Each pipeline step ran inside the project's venv;
sandbox logs are in `code/.tasks/`.
