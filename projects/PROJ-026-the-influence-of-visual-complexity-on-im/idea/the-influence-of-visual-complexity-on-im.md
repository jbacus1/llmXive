---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Influence of Visual Complexity on Implicit Bias

**Field**: psychology

## Research question

Does increasing the visual complexity of background stimuli presented during an Implicit Association Test (IAT) reduce implicit bias scores by increasing cognitive load and diverting attention from stereotypical associations?

## Motivation

Implicit bias remains a persistent challenge in social psychology and organizational settings. If environmental visual complexity can attenuate implicit associations, this could offer a low-cost intervention strategy for bias mitigation in hiring, education, and policy contexts. This project addresses the gap in understanding how peripheral cognitive load interacts with automatic stereotype activation.

## Related work

TODO — lit-search returned no results.

## Expected results

We expect IAT effect sizes (d-score) to be significantly smaller in high-visual-complexity conditions compared to low-complexity controls. A within-subjects ANOVA should show a main effect of visual complexity (p < 0.05, η² > 0.02). Evidence would require a minimum sample of N = 60 participants to achieve 80% power for a medium effect size.

## Methodology sketch

- **Data source**: Use existing public IAT datasets from Open Science Framework (OSF) repositories or HuggingFace Datasets (e.g., "implicit-bias-attribution" datasets with pre-collected IAT scores and stimulus metadata).
- **Stimulus preparation**: Download image sets classified by visual complexity metrics (fractal dimension, edge density, entropy) from public vision datasets (e.g., COCO, ImageNet subsets) or generate via Python libraries (OpenCV, scikit-image).
- **Complexity quantification**: Compute visual complexity scores per image using: (a) edge detection (Canny), (b) entropy of grayscale histograms, (c) fractal dimension estimation (box-counting method).
- **Task design**: Create a simulated IAT protocol using existing participant response data; assign complexity levels to trial blocks based on pre-computed image metrics.
- **Statistical analysis**: Perform repeated-measures ANOVA on IAT d-scores across complexity conditions using Python (scipy.stats, pingouin).
- **Effect size estimation**: Calculate Cohen's d and partial η² for within-subject comparisons.
- **Power analysis**: Use G*Power-equivalent calculations (statsmodels) to verify N requirements.
- **Visualization**: Generate effect size plots and complexity-IAT score scatterplots using matplotlib/seaborn.
- **Reproducibility**: Document all code in a single Python script executable within 6 hours on standard hardware.

## Duplicate-check

- Reviewed existing ideas: Unable to access existing_idea_paths (not provided in input).
- Closest match: N/A (no corpus access).
- Verdict: NOT a duplicate (pending corpus review)
