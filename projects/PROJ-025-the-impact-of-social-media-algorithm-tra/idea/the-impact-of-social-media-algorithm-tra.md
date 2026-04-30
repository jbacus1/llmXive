---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Social Media Algorithm Transparency on User Well-being

**Field**: psychology

## Research question

Does providing users with transparent explanations of algorithmic content curation significantly improve perceived control and reduce anxiety compared to opaque systems?

## Motivation

Opaque algorithms contribute to user uncertainty and potential distress by obscuring why specific content is shown. Transparency mechanisms might empower users, but empirical evidence linking technical explainability to psychological outcomes remains limited. This study addresses the gap between technical interpretability and user well-being metrics.

## Related work

- [Examining the Impact of Label Detail and Content Stakes on User Perceptions of AI-Generated Images on Social Media (2025)](http://arxiv.org/abs/2510.19024v1) — Investigates how label detail levels influence user perception, relevant to understanding transparency mechanisms.
- [Machine Learning Interpretability: A Survey on Methods and Metrics (2019)](https://doi.org/10.3390/electronics8080832) — Provides metrics for interpretability that can be adapted to define algorithmic transparency levels.
- [Characterizing Information Diets of Social Media Users (2017)](http://arxiv.org/abs/1704.01442v1) — Describes how algorithmic curation shapes information consumption, a key mediator for well-being.
- [Information Consumption and Boundary Spanning in Decentralized Online Social Networks: the case of Mastodon Users (2022)](http://arxiv.org/abs/2203.15752v3) — Offers context on user agency and control in alternative social network structures.

## Expected results

We expect higher levels of algorithmic transparency to correlate with increased perceived control and decreased anxiety scores. This will be confirmed if regression coefficients for transparency predictors are statistically significant (p < 0.05) after controlling for usage intensity. Evidence strength will be evaluated using effect sizes (Cohen's d) from the public survey data.

## Methodology sketch

- **Data Acquisition**: Download anonymized social media usage and well-being survey data from the Pew Research Center Internet & Technology public data archive (https://www.pewresearch.org/internet/data/).
- **Preprocessing**: Clean data using Python (pandas) to handle missing values and normalize well-being scales; ensure memory usage stays under 7GB.
- **Variable Definition**: Define "Transparency Exposure" based on survey items regarding awareness of content curation; define "Well-being" using standard anxiety and life satisfaction scales.
- **Statistical Analysis**: Perform multiple linear regression using `statsmodels` to test the relationship between transparency and well-being.
- **Mediation Testing**: Run a mediation analysis to see if "Perceived Control" mediates the relationship between transparency and well-being.
- **Robustness Check**: Perform sensitivity analysis by excluding high-intensity users (>4 hours/day) to check for confounding effects.
- **Visualization**: Generate static plots (matplotlib) showing regression coefficients and confidence intervals.
- **Execution**: Run the entire pipeline as a single Python script on the GitHub Actions runner (no GPU required).

## Duplicate-check

- Reviewed existing ideas: None provided in this execution context.
- Closest match: N/A.
- Verdict: NOT a duplicate
