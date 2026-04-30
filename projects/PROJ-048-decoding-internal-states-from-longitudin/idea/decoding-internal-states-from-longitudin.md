---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Decoding Internal States from Longitudinal Calcium Imaging Data

**Field**: neuroscience

## Research question

Can non-negative matrix factorization (NMF) applied to longitudinal calcium imaging time series reveal latent neural states that correlate with behavioral metadata, and how do these states evolve over time?

## Motivation

Longitudinal calcium imaging captures plasticity and adaptation, but standard analyses often treat time points as independent snapshots. Decoding latent states from the temporal dynamics of these signals could reveal how neural representations reorganize during learning. This approach addresses the gap between static functional mapping and dynamic state tracking using computationally efficient matrix factorization rather than resource-intensive deep learning.

## Related work

- [SADM: Sequence-Aware Diffusion Model for Longitudinal Medical Image Generation (2022)](http://arxiv.org/abs/2212.08228v2) — Establishes the importance of modeling short-term and long-term anatomical/functional changes in longitudinal medical imaging, relevant to our focus on temporal dynamics.
- [Questions and controversies in the study of time-varying functional connectivity in resting fMRI (2019)](https://doi.org/10.1162/netn_a_00116) — Discusses the challenges and methods for analyzing time-varying connectivity in brain dynamics, providing a conceptual framework for decoding latent states from neuroimaging time series.

## Expected results

We expect NMF components to exhibit distinct temporal activation patterns that align with specific behavioral epochs or stimulus conditions. Correlation analysis will show significant relationships between component weights and behavioral metadata compared to shuffled controls. Evidence will be confirmed if permutation tests yield p-values < 0.05 for state-behavior correlations.

## Methodology sketch

- **Data Acquisition**: Download pre-extracted ROI fluorescence traces from the Allen Brain Atlas Open Data Portal (e.g., Visual Coding dataset subset) via `wget` from `https://portal.brain-map.org/`.
- **Preprocessing**: Load traces into Python (pandas/numpy), normalize fluorescence (dF/F), and detrend to remove slow drifts; ensure memory usage stays < 5GB by selecting a single session subset.
- **Dimensionality Reduction**: Apply `sklearn.decomposition.NMF` to the time-by-ROI matrix to extract k latent components (k=10 to 50).
- **Temporal Dynamics**: Compute the time-varying contribution weights of each NMF component across the recording session.
- **Behavioral Alignment**: Align component weight time series with available behavioral metadata (e.g., running speed, stimulus onset) stored in the dataset metadata.
- **Statistical Testing**: Perform Spearman correlation between component weights and behavior; apply a permutation test (1000 iterations) to establish significance thresholds.
- **Visualization**: Generate heatmaps of component activation over time and bar plots of correlation strengths using `matplotlib`.

## Duplicate-check

- Reviewed existing ideas: None provided.
- Closest match: N/A (similarity sketch: N/A).
- Verdict: NOT a duplicate
