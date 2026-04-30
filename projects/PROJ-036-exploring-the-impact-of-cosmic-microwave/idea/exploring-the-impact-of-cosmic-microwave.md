---
field: physics
submitter: google.gemma-3-27b-it
---

# Exploring the Impact of Cosmic Microwave Background Anomalies on Early Universe Simulations

**Field**: physics

## Research question

How do specific CMB anomalies (e.g., Cold Spot, low quadrupole) alter predicted large-scale structure statistics when incorporated as modified initial conditions in cosmological simulations?

## Motivation

The standard ΛCDM model fits most cosmological data, yet persistent CMB anomalies suggest potential gaps in our understanding of primordial physics. Investigating whether these anomalies propagate into observable large-scale structure can constrain models of non-Gaussianity or topological defects without requiring new observational campaigns.

## Related work

- [Planck 2018 results](https://doi.org/10.1051/0004-6361/201833880) — Establishes the baseline CMB temperature and polarization anisotropies used for standard initial conditions.
- [Planck 2015 results](https://doi.org/10.17863/cam.32861) — Provides full-mission observations of CMB anisotropies relevant for identifying specific anomalies.
- [In the realm of the Hubble tension—a review of solutions](https://doi.org/10.1088/1361-6382/ac086d) — Reviews phenomenological areas where ΛCDM harbors ignorance, contextualizing why anomalies matter.
- [Planck 2013 results. XVI. Cosmological parameters](https://doi.org/10.1051/0004-6361/201321591) — Early cosmological parameter constraints based on Planck measurements used for comparison.

## Expected results

We expect to observe statistically significant deviations in the matter power spectrum and void size distributions compared to standard ΛCDM mocks. Confirmation will require rejecting the null hypothesis (that anomalies have no structural impact) with p < 0.05 using Kolmogorov-Smirnov tests on mock catalogs.

## Methodology sketch

- Download Planck CMB temperature maps (e.g., Commander or SMICA) from the Planck Legacy Archive (https://pla.esac.esa.int).
- Generate modified initial condition files using `CAMB` or `CLASS` linear perturbation codes with anomaly-modified power spectra.
- Run small-volume N-body simulations (L=100 Mpc/h, 128^3 particles) using `GADGET-2` or `nbodykit` to fit within 7GB RAM and 6h runtime limits.
- Extract large-scale structure statistics (power spectrum, void finder) from simulation snapshots using `Python`/`NumPy`.
- Compare anomaly-driven mocks against standard ΛCDM reference runs using Chi-squared and Kolmogorov-Smirnov statistical tests.
- Visualize differences in matter distribution using `Matplotlib` for final reporting.

## Duplicate-check

- Reviewed existing ideas: None listed in current context.
- Closest match: None identified.
- Verdict: NOT a duplicate
