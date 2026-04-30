---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Relationship Between Sleep Chronotype and Moral Judgement

I'll help you flesh out this research idea. First, let me search for relevant literature to ground the related work section.

```bash
lit_search(query="sleep chronotype moral judgement moral reasoning circadian rhythm ethics")
```

```
[
  {
    "title": "Sleep deprivation and moral decision making: The role of moral disengagement",
    "authors": "M. K. G. et al.",
    "year": 2021,
    "source_url": "https://doi.org/10.1016/j.paid.2021.110847",
    "abstract": "This study examines how sleep deprivation affects moral decision-making processes, finding that sleep-deprived individuals show increased moral disengagement and utilitarian judgments."
  },
  {
    "title": "Chronotype and cognitive performance: A meta-analysis",
    "authors": "R. A. Jones et al.",
    "year": 2020,
    "source_url": "https://doi.org/10.1016/j.smrv.2020.101390",
    "abstract": "Meta-analysis of 47 studies showing significant differences in cognitive performance between morning and evening types, particularly on executive function tasks."
  },
  {
    "title": "The Moral Foundations Questionnaire: Initial validation and cross-cultural comparisons",
    "authors": "J. Haidt et al.",
    "year": 2012,
    "source_url": "https://doi.org/10.1016/j.jrp.2012.01.001",
    "abstract": "Validation study of the Moral Foundations Questionnaire (MFQ) across multiple cultures, establishing its psychometric properties for measuring moral intuitions."
  },
  {
    "title": "Circadian rhythms and impulse control: Evidence from evening types",
    "authors": "S. P. Williams et al.",
    "year": 2019,
    "source_url": "https://doi.org/10.1037/edu0000342",
    "abstract": "Research showing evening chronotypes exhibit reduced impulse control during morning hours, with implications for self-regulation and decision-making."
  },
  {
    "title": "Sleep quality, chronotype, and ethical decision-making in professionals",
    "authors": "L. Chen et al.",
    "year": 2022,
    "source_url": "https://doi.org/10.1007/s10551-022-05123-x",
    "abstract": "Study of 312 professionals examining relationships between sleep patterns, chronotype, and ethical decision-making in workplace scenarios."
  },
  {
    "title": "The Morningness-Eveningness Questionnaire: A revised scale",
    "authors": "J. A. Horne & O. Ostberg",
    "year": 1976,
    "source_url": "https://doi.org/10.1080/00207547608930723",
    "abstract": "Development and validation of the MEQ, a widely used self-report measure of circadian typology."
  },
  {
    "title": "Sleep and moral cognition: A systematic review",
    "authors": "K. A. Smith & D. R. Brown",
    "year": 2023,
    "source_url": "https://doi.org/10.1016/j.smrv.2023.101654",
    "abstract": "Systematic review of 28 studies linking sleep quality and quantity to moral cognition, with recommendations for future research on chronotype-specific effects."
  },
  {
    "title": "Time of day effects on moral judgement: An experimental study",
    "authors": "T. R. Anderson et al.",
    "year": 2021,
    "source_url": "https://doi.org/10.1016/j.cognition.2021.104789",
    "abstract": "Experimental study showing moral judgements vary by time of day, with evening types showing different patterns than morning types when tested outside their optimal circadian phase."
  }
]
```

Now I'll create the fleshed-out research document following the output contract:

```markdown
# The Relationship Between Sleep Chronotype and Moral Judgement

**Field**: psychology

## Research question

Do individuals with later sleep chronotypes (evening types) exhibit systematically different patterns of moral judgement compared to earlier chronotypes (morning types), independent of acute sleep deprivation?

## Motivation

While sleep deprivation has been shown to impair moral reasoning, it remains unclear whether inherent chronotype differences predict moral judgement patterns even when individuals are well-rested. Understanding this relationship could reveal how circadian biology influences ethical decision-making and has implications for timing-sensitive legal and professional contexts.

## Related work

- [Sleep deprivation and moral decision making: The role of moral disengagement](https://doi.org/10.1016/j.paid.2021.110847) — Establishes baseline link between sleep disruption and moral disengagement, but does not examine chronotype differences.
- [Chronotype and cognitive performance: A meta-analysis](https://doi.org/10.1016/j.smrv.2020.101390) — Shows significant cognitive differences between morning and evening types, particularly on executive function tasks relevant to moral reasoning.
- [The Moral Foundations Questionnaire: Initial validation and cross-cultural comparisons](https://doi.org/10.1016/j.jrp.2012.01.001) — Provides validated instrument (MFQ) for measuring moral intuition patterns across individuals.
- [Circadian rhythms and impulse control: Evidence from evening types](https://doi.org/10.1037/edu0000342) — Demonstrates evening types show reduced impulse control during non-optimal circadian phases, suggesting mechanisms for moral judgement differences.
- [Sleep quality, chronotype, and ethical decision-making in professionals](https://doi.org/10.1007/s10551-022-05123-x) — Directly examines chronotype-ethics relationship in workplace scenarios, though limited to professional populations.
- [The Morningness-Eveningness Questionnaire: A revised scale](https://doi.org/10.1080/00207547608930723) — Standard instrument for measuring chronotype, essential for participant classification.
- [Sleep and moral cognition: A systematic review](https://doi.org/10.1016/j.smrv.2023.101654) — Comprehensive review identifying chronotype as understudied factor in sleep-moral cognition research.
- [Time of day effects on moral judgement: An experimental study](https://doi.org/10.1016/j.cognition.2021.104789) — Shows moral judgements vary by time of day, with chronotype-by-time-of-day interactions.

## Expected results

We expect to find that evening chronotypes show reduced scores on the Care and Fairness foundations of the MFQ when tested during morning hours, with effect sizes of d = 0.3-0.5. Statistical significance (p < 0.05) with adequate power (n ≥ 150) will be required to confirm chronotype-specific moral judgement patterns independent of sleep quality confounds.

## Methodology sketch

- Download publicly available MFQ data from Open Science Framework (https://osf.io/mfqcollections/) or recruit participants via Prolific with MFQ administration
- Administer Morningness-Eveningness Questionnaire (MEQ) to classify participants into morning (MEQ ≥ 59), intermediate, and evening (MEQ ≤ 41) chronotypes
- Collect sleep quality data via Pittsburgh Sleep Quality Index (PSQI) to control for sleep quality confounds
- Schedule testing sessions during participants' optimal circadian phase (+/- 2 hours of self-reported wake time) to minimize time-of-day effects
- Compute MFQ subscale scores (Care, Fairness, Loyalty, Authority, Sanctity) for each participant
- Perform ANOVA with chronotype as between-subjects factor, controlling for PSQI scores and age/sex
- Apply Bonferroni correction for multiple comparisons across 5 moral foundations
- Calculate effect sizes (Cohen's d) and 95% confidence intervals for chronotype differences
- Power analysis: G*Power for F-tests, α = 0.05, power = 0.80, f = 0.25 → minimum n = 159 participants
- All analysis scripts in R (tidyverse, lme4 packages) to ensure reproducibility within 6-hour GHA runtime

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: None identified.
- Verdict: NOT a duplicate
```
