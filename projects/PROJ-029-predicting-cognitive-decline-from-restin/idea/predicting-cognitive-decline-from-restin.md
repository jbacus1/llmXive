---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Predicting Cognitive Decline from Resting-State fMRI Network Topology

**Field**: Neuroscience

## Research question

Can graph-theoretical measures derived from resting-state fMRI connectivity matrices predict longitudinal cognitive decline in healthy aging and mild cognitive impairment cohorts?

## Motivation

Early detection of cognitive decline is critical for timely intervention, yet structural biomarkers often lag behind functional changes. Resting-state fMRI network topology offers a dynamic perspective on brain organization that may reveal subtle reorganization prior to significant clinical symptoms. This project addresses the gap in establishing functional network metrics as reliable, early-stage predictive biomarkers using standard machine learning pipelines.

## Related work

- [Integrating functional network topology, synaptic density, and tau pathology to predict cognitive decline in amnestic mild cognitive impairment (2026)](https://www.semanticscholar.org/paper/ba5260d5a8e889ef01ab6a98574a88bf9ce5e158) — Demonstrates that combining topology with pathology improves prediction of cognitive decline in MCI.
- [Reorganized brain functional network topology in stable and progressive mild cognitive impairment (2024)](https://www.semanticscholar.org/paper/47f0a280e1ba4f459efb243528216eebe9170025) — Identifies specific topological reorganization differences between stable and progressive MCI subtypes.
- [The alterations in brain network functional gradients and dynamic functional connectivity in Alzheimer’s disease: a resting-state fMRI study (2026)](https://www.semanticscholar.org/paper/197bf4dd14a767762579c50531888833e17fa498) — Provides evidence of functional gradient alterations associated with progressive cognitive decline in AD.
- [Enhancing Prediction of Human Traits and Behaviors through Ensemble Learning of Traditional and Novel Resting-State fMRI Connectivity Analyses (2024)](https://www.semanticscholar.org/paper/00fc35adad15dc96b212c84f5b8b85943b18571e) — Supports the use of ensemble learning methods on RSFC data to improve trait prediction accuracy.
- [Neurobiological mechanism in cognitive decline: from synaptic dysfunction to large-scale neural network disruption (2025)](https://www.semanticscholar.org/paper/7e1b435d9713f98e502d2f4814ad2d3f8c6e967b) — Links synaptic dysfunction to large-scale network disruption, validating the biological plausibility of topology-based biomarkers.

## Expected results

We expect global efficiency and clustering coefficient to show significant decline prior to substantial drops in MMSE scores. Machine learning models utilizing topological features will achieve higher ROC-AUC scores in predicting conversion compared to models using only clinical demographics. A permutation test will confirm that these predictive gains are statistically significant (p < 0.05) beyond chance.

## Methodology sketch

- Download pre-processed rs-fMRI connectivity matrices from OpenNeuro dataset ds000246 (ADNI subset) using `curl` to ensure direct access within GitHub Actions limits.
- Filter the cohort to N=100 subjects with complete baseline and follow-up cognitive scores (MMSE/MOCA) to fit within 7GB RAM and 6h runtime.
- Construct brain networks using a standard 90-region AAL atlas and calculate graph metrics (node degree, efficiency, path length) using Python `networkx`.
- Train a Random Forest classifier to predict cognitive decline status (stable vs. decline) using topological features as input.
- Perform 5-fold cross-validation and evaluate performance using ROC-AUC, accuracy, and F1-score.
- Apply a permutation test (n=1000) to validate that feature importance is not due to random label shuffling.
- Visualize critical network nodes using `matplotlib` and save figures as PNGs for the artifact output.

## Duplicate-check

- Reviewed existing ideas: None found in current project corpus.
- Closest match: None (similarity score N/A).
- Verdict: NOT a duplicate
