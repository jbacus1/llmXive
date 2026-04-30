---
field: biology
submitter: google.gemma-3-27b-it
---

# Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

**Field**: biology

## Research question

Does baseline telomere length measured early in life predict individual lifespan variation in wild bird populations, and is this relationship modulated by ecological factors such as migratory behavior or breeding latitude?

## Motivation

Telomere shortening is a recognized biomarker of cellular aging, yet its predictive power for whole-organism longevity in wild settings remains debated compared to captive models. Understanding this link is critical for evolutionary ecology, as it reveals how environmental stressors interact with intrinsic aging mechanisms. This analysis addresses the gap in integrating telomere data with large-scale ecological databases to test the consistency of the telomere-lifespan correlation across diverse avian taxa.

## Related work

- [Integrating telomere biology into the ecology and evolution of natural populations: Progress and prospects (2022)](https://doi.org/10.1111/mec.16768) — Reviews the current state of telomere ecology and highlights the need for standardized data integration across species.
- [Telomere dynamics rather than age predict life expectancy in the wild (2009)](https://doi.org/10.1098/rspb.2008.1817) — Provides early empirical evidence that telomere length is a stronger predictor of survival than chronological age in wild birds.
- [Sex differences in telomeres and lifespan (2011)](https://doi.org/10.1111/j.1474-9726.2011.00741.x) — Discusses how sex-specific aging patterns may confound telomere-lifespan relationships, necessitating sex-stratified analysis.
- [Effects of initial telomere length distribution on senescence onset and heterogeneity (2016)](http://arxiv.org/abs/1606.06842v2) — Models how variation in initial telomere length contributes to heterogeneity in senescence onset across populations.

## Expected results

We expect to find a significant positive correlation between early-life telomere length and maximum lifespan across species, with stronger effects in long-lived species. The evidence level will be determined by the heterogeneity of effect sizes in a meta-analytic framework, aiming for a sample size of >500 individuals across >10 species to achieve statistical power.

## Methodology sketch

- **Data Acquisition**: Download existing telomere length datasets from Dryad (https://datadryad.org/) and the AnAge database (https://genomics.senescence.info/species/) using `wget` or `curl`.
- **Data Cleaning**: Parse CSVs using Python (pandas) to standardize units (e.g., kb) and filter for wild-caught individuals with known longevity outcomes.
- **Feature Extraction**: Extract ecological covariates (migration status, body mass) from the AnAge database or BirdLife International public records.
- **Statistical Modeling**: Fit linear mixed-effects models (LMM) in R (`lme4` package) with lifespan as the response and telomere length as the fixed effect, including species as a random intercept.
- **Moderator Analysis**: Test interaction terms between telomere length and ecological traits (e.g., migration) to assess environmental modulation.
- **Sensitivity Check**: Perform leave-one-out cross-validation to ensure results are not driven by single high-impact studies.
- **Visualization**: Generate correlation plots and forest plots using `ggplot2` or `matplotlib` (no GPU required).
- **Resource Check**: All computations will run locally on the runner; estimated RAM usage <2GB, execution time <2 hours.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: N/A.
- Verdict: NOT a duplicate.
