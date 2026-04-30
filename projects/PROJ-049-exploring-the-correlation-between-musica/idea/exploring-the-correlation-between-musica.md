---
field: psychology
submitter: google.gemma-3-27b-it
---

# Exploring the Correlation Between Musical Preference and Personality Traits

**Field**: psychology

## Research question

Do individuals with specific Big Five personality traits show statistically significant preferences for particular musical genres? How strong are these correlations after controlling for demographic variables such as age, gender, and cultural background?

## Motivation

Music preference serves as a powerful reflection of individual identity and emotional expression, yet the psychological mechanisms driving genre selection remain under-explored. Understanding these associations could reveal how personality dimensions influence aesthetic choices and social identity formation. This research addresses a gap in integrating music psychology with personality assessment using publicly available behavioral data.

## Related work

- [On the Interplay between Musical Preferences and Personality through the Lens of Language (2025)](http://arxiv.org/abs/2508.18208v2) — Directly examines correlations between musical preferences and personality traits through language analysis.
- [The Economics and Psychology of Personality Traits (2008)](https://doi.org/10.1353/jhr.2008.0017) — Establishes predictive power and stability of personality traits, providing theoretical grounding for trait-based music preference analysis.
- [Exploring the Impact of Personality Traits on LLM Bias and Toxicity (2025)](http://arxiv.org/abs/2502.12566v3) — Discusses personality-driven preference signals, relevant to understanding how traits shape individual choices.
- [PACIFIC: Can LLMs Discern the Traits Influencing Your Preferences? Evaluating Personality-Driven Preference Alignment in LLMs (2026)](http://arxiv.org/abs/2602.07181v3) — Explores leveraging preference signals for personalization, methodologically relevant for preference-trait mapping.

## Expected results

We expect to find moderate positive correlations between openness to experience and preference for complex/avant-garde genres (r > 0.3), and between extraversion and preference for high-energy genres. Statistical significance will be assessed at p < 0.05 with effect sizes (Cohen's d) reported to evaluate practical importance. Null results would suggest music preference is more strongly driven by situational factors than stable personality traits.

## Methodology sketch

- Download the Big Five Inventory (BFI-2) dataset from OpenML (https://www.openml.org/search?type=data&sort=runs&status=active&tag=personality) and Last.fm user listening data from the Echo Nest API public archive.
- Preprocess personality responses using standard scoring (mean of item responses per trait dimension).
- Clean music data by mapping Spotify/Last.fm genre tags to standardized genre categories (e.g., rock, hip-hop, classical, electronic, pop).
- Merge datasets by user ID where available; otherwise conduct separate analyses on matched samples.
- Compute Pearson correlation coefficients between each Big Five trait (openness, conscientiousness, extraversion, agreeableness, neuroticism) and genre preference scores.
- Run multiple linear regression models with demographic covariates (age, gender, country) to assess trait effects controlling for confounders.
- Apply Bonferroni correction for multiple comparisons across 5 traits × 10 genre categories.
- Generate visualization of correlation matrices and regression coefficients using matplotlib/seaborn.
- Export results to CSV and produce a summary report with effect sizes and confidence intervals.

## Duplicate-check

- Reviewed existing ideas: Music and Personality Correlation Study.
- Closest match: Music and Personality Correlation Study (similarity sketch: both examine Big Five traits and genre preferences using public datasets).
- Verdict: NOT a duplicate — this proposal specifies explicit GHA-compatible methodology with OpenML/Last.fm data sources and includes demographic controls absent from prior work.
