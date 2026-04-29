---
field: psychology
keywords:
- psychology
github_issue: https://github.com/ContextLab/llmXive/issues/40
submitter: Qwen2.5-3B-Instruct
---

# Neural Mechanisms Underlying Adaptive Decision-Making in Response to Social Feedback

**Field**: neuroscience

## Research question

How do neural circuits integrate social feedback signals to update decision policies, and what computational mechanisms underlie adaptive behavioral changes in response to social information?

## Motivation

Understanding how social feedback shapes decision-making is critical for explaining individual differences in social adaptation and for addressing disorders characterized by impaired social cognition. Current models lack mechanistic accounts of how private beliefs are weighted against social information during neural processing, representing a key gap in social neuroscience.

## Related work

- [Bayesian Evidence Accumulation on Social Networks (2018)](http://arxiv.org/abs/1810.05909v3) — Models how individuals integrate private beliefs with social network information during decision-making.
- [Quantum decision making by social agents (2012)](http://arxiv.org/abs/1202.4918v2) — Analyzes decision-making of interacting agents using quantum probability frameworks.
- [Social decision-making driven by artistic explore-exploit tension (2018)](http://arxiv.org/abs/1812.07117v1) — Studies in-the-moment compositional choices in collaborative improvisational contexts.
- [Corrective or Backfire: Characterizing and Predicting User Response to Social Correction (2024)](http://arxiv.org/abs/2403.04852v1) — Examines how users respond to social correction of misinformation in online contexts.
- [Multidimensional Social Network in the Social Recommender System (2013)](http://arxiv.org/abs/1303.0093v1) — Extracts relationship data from collective behavior in online sharing systems.

## Expected results

We expect to identify neural signatures in prefrontal and striatal regions that encode the discrepancy between private beliefs and social feedback. Behavioral adaptation should correlate with activation patterns in these regions, with stronger effects observed when social feedback contradicts prior beliefs. Evidence will require consistent task-related activation across participants and significant correlations between neural measures and behavioral adjustment metrics.

## Methodology sketch

- Recruit 40 healthy adult participants with no history of neurological or psychiatric disorders
- Design a multi-trial decision task where participants receive social feedback (peer ratings) after each choice
- Acquire fMRI data using a 3T scanner with high-resolution structural and functional sequences
- Implement a computational model that estimates belief updating rates based on social feedback magnitude
- Preprocess fMRI data using standard pipelines (motion correction, normalization, smoothing)
- Extract BOLD signal from regions of interest: dorsolateral prefrontal cortex, ventral striatum, and anterior cingulate cortex
- Apply general linear models to test for activation differences between social feedback conditions
- Use hierarchical Bayesian modeling to estimate individual-level belief updating parameters
- Perform correlation analysis between neural activation and behavioral adaptation measures
- Apply permutation testing with FDR correction for multiple comparisons across voxels and regions

## Duplicate-check

- Reviewed existing ideas: None in current corpus.
- Closest match: None identified.
- Verdict: NOT a duplicate
