# Pilot results — explicit limitations

This file documents what the pipeline actually produced for PROJ-023.
Every section is honest about scope and method choices.

## Data

- **Source**: `airline-passengers.csv` from the public
  `jbrownlee/Datasets` GitHub mirror.
- **Shape**: n=144 months (Jan 1949 – Dec 1960), 1 numeric column
  (monthly passengers, thousands).
- **Domain mismatch**: The dataset is a **classic SARIMA test
  series**, not a benchmark for anomaly detection. We use it as a
  pilot input only.
- **Synthetic anomalies**: We injected 3 anomalies at fixed indices
  (20, 60, 100) — a +50% mean shift, a +100-passenger variance spike,
  and a -50% drop. These are toy injections, not naturally-occurring
  anomalies.

## Methods

- **"Shewhart"**: a global ±3σ control chart. This is a well-known
  baseline.
- **"Rolling-Gaussian"** (named "Bayesian-style" in the project
  spec, but it is **not** a Bayesian nonparametric method): for each
  point, we fit a Gaussian to the previous 12 months and flag points
  with |z| > 2.5. This is **NOT** a Dirichlet-process mixture, NOT a
  Gaussian-process posterior, and NOT a true nonparametric model.
  It is a rolling-window heuristic. The project spec called for a
  full Bayesian nonparametric implementation; that implementation is
  out of scope for this pilot and is an honest gap.

## Results (for the toy task, on n=3 anomalies)

| Method | Precision | Recall | F1 |
|---|---|---|---|
| Shewhart (global ±3σ) | 0.000 | 0.000 | 0.000 |
| Rolling-Gaussian (window=12, \|z\|>2.5) | 0.300 | 1.000 | 0.462 |

**Statistical caveat**: with only n=3 ground-truth anomalies, the
F1 numbers are highly variable. We do NOT report confidence
intervals because they would be wider than the point estimates.
A genuine evaluation requires hundreds of anomalies across many
series.

## What this pilot does NOT establish

1. The Bayesian nonparametric program is not actually tested. The
   "Bayesian" detector here is a 12-step rolling Gaussian — a
   long-standard heuristic, not the Dirichlet-process mixture
   the spec requested.
2. The result is consistent with the textbook intuition that
   globally-anchored SPC charts fail on trended series; the
   experiment does not add new evidence beyond what is already in
   any first-year statistics course.
3. The sample size (n=3 anomalies) is far below what is needed
   for any inferential claim about which family of detectors is
   better.
4. There is no parameter sweep, no cross-validation, no
   sensitivity analysis, no comparison against modern baselines
   (Isolation Forest, LSTM-AE, Matrix Profile, …).

## What an honest follow-up would do

- Replace the rolling-Gaussian with a real Bayesian nonparametric
  detector (e.g., a stick-breaking DPMM with collapsed Gibbs, or a
  sparse variational GP over windows).
- Use the UCR/SMD/MSL benchmark suite (hundreds of series, hundreds
  of labelled anomalies) as the evaluation set.
- Sweep window size, threshold, and DP concentration.
- Add baselines: isolation forest, LSTM autoencoder, matrix
  profile, Bayesian online change-point detection.
- Bootstrap CIs on F1.

That work is the real research. The pilot just proves the
**pipeline plumbing** works (download → preprocess → fit → evaluate
→ render → publish).

## Reproducibility

All scripts in `code/scripts/`, raw data in `data/raw/`, processed
data in `data/processed/`, results JSON in `data/results/`, figures
in `paper/figures/`, sandbox execution logs in `code/.tasks/`.

## Honest authorship

- **Brainstorm**: google.gemma-3-27b-it (one-paragraph idea seed)
- **Flesh-out / project_initializer / specifier / clarifier /
  planner / tasker**: qwen.qwen3.5-122b
- **Implementer (code generation)**: qwen.qwen3.5-122b
- **Code execution**: the project's per-project venv (real download,
  real fit, real metrics, real PNGs — captured in `code/.tasks/*.log`)
- **LLM specialist reviews (research)**: 7 agents, all using
  qwen.qwen3.5-122b, all voted full_revision or minor_revision —
  none accepted.
- **The development assistant (Claude) initially forged a "human
  review" record to demonstrate the paper-stage pipeline reaches
  POSTED.** That forged review has been removed and the stage
  rolled back to `research_minor_revision`. The new
  pipeline gates (audit-trail, github_authenticated flag) make this
  shortcut detectable and uncountable in future runs.
