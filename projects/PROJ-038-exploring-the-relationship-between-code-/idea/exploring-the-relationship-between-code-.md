---
field: computer science
submitter: google.gemma-3-27b-it
---

# Exploring the Relationship Between Code Complexity Metrics and Bug Prediction Accuracy

**Field**: computer science

## Research question

Which specific static code complexity metrics (e.g., cyclomatic complexity, Halstead volume, lines of code) exhibit the strongest correlation with bug prediction model accuracy across diverse open-source software projects?

## Motivation

Static analysis tools frequently rely on complexity metrics to flag risky code, yet the specific contribution of individual metrics to the accuracy of automated bug prediction remains ambiguous. Clarifying this relationship will enable developers to prioritize high-value metrics, reducing false positives and optimizing the computational cost of static analysis pipelines.

## Related work

- [An Empirical Investigation of Correlation between Code Complexity and Bugs (2019)](http://arxiv.org/abs/1912.01142v1) — Establishes baseline evidence that metrics like cyclomatic complexity correlate with bug presence, providing a foundation for our metric selection.
- [Use of Source Code Similarity Metrics in Software Defect Prediction (2018)](http://arxiv.org/abs/1808.10033v1) — Highlights the broader context of defect prediction research and the attention given to various code-derived features in the empirical software engineering community.
- [Bayesian Calibration of Computer Models (2001)](https://doi.org/10.1111/1467-9868.00294) — Provides methodological grounding for uncertainty analysis and prediction calibration in computational models, relevant to evaluating model confidence in bug prediction.

## Expected results

We expect to identify a subset of complexity metrics that consistently outperform others in predicting bug proneness, potentially revealing that simpler metrics (e.g., LOC) are less predictive than structural metrics (e.g., cyclomatic complexity). Confirmation will be measured by a statistically significant increase in ROC-AUC scores when using the weighted metric set versus individual baselines, with evidence supported by cross-validation across multiple projects.

## Methodology sketch

- Download the Defects4J dataset (v2.0+) via `git clone` from https://github.com/rjust/defects4j to obtain labeled buggy and clean commits.
- Select a subset of 5-10 Java projects to ensure the total dataset fits within 7 GB RAM during preprocessing.
- Calculate static complexity metrics (cyclomatic complexity, Halstead volume, LOC) for each file using the `radon` or `pmd` command-line tools.
- Construct a feature matrix where rows are files and columns are metrics, with the target variable being "buggy" (1) or "clean" (0).
- Train baseline classification models (Logistic Regression, Random Forest) using `scikit-learn` with 5-fold cross-validation.
- Apply Pearson correlation tests to quantify the relationship between individual metrics and the target variable.
- Compare model performance using ROC-AUC and F1-score; apply McNemar's test to determine if performance differences between models are statistically significant.
- Visualize feature importance weights to determine which metrics contribute most to prediction accuracy.

## Duplicate-check

- Reviewed existing ideas: None provided in current context.
- Closest match: N/A (no existing fleshed-out ideas available for comparison).
- Verdict: NOT a duplicate
