---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Crystal Structures from Molecular Fingerprints

**Field**: Chemistry

## Research question

Can machine learning models trained on molecular fingerprints accurately predict crystallographic parameters (lattice parameters and space group) from molecular structure alone, bypassing explicit quantum mechanical calculations?

## Motivation

Crystal structure prediction is a bottleneck in materials discovery due to the high computational cost of density functional theory (DFT) or molecular dynamics simulations. If molecular fingerprints—cheap to compute—can serve as effective proxies for crystal packing information, this would enable rapid screening of candidate molecules for specific material properties. This project addresses the gap in understanding the information content of standard chemical descriptors regarding solid-state arrangements.

## Related work

- [Open Babel: An open chemical toolbox (2011)](https://doi.org/10.1186/1758-2946-3-33) — Provides the open-source software infrastructure required to convert molecular structures into the fingerprints necessary for model training.
- [Crystal Structure and Chemistry of Topological Insulators (2013)](http://arxiv.org/abs/1302.1059v1) — Illustrates the critical dependence of electronic and physical properties on precise crystal structure definitions, motivating the need for accurate prediction.
- [Aromatics and Cyclic Molecules in Molecular Clouds: A New Dimension of Interstellar Organic Chemistry (2021)](http://arxiv.org/abs/2103.09608v1) — Demonstrates the utility of molecular representations in identifying complex chemical systems, though applied in an astrochemical context rather than solid-state prediction.

## Expected results

We expect to find that specific fingerprint types (e.g., ECFP) correlate with space group symmetry classes better than others, achieving moderate classification accuracy (e.g., >60% on top-3 predictions). The regression of lattice parameters will show higher error margins, confirming that global molecular topology captures symmetry better than precise geometric dimensions without explicit 3D coordinates.

## Methodology sketch

- **Data Acquisition**: Download the organic subset of the Crystallography Open Database (COD) via `wget` from https://www.crystallography.net/cod/ (filter for CIF files < 500MB total to fit 14GB SSD).
- **Feature Engineering**: Use Open Babel (referencing the provided literature) to parse CIF files into SMILES and generate 2048-bit ECFP4 fingerprints.
- **Data Splitting**: Randomly split the dataset into 80% training and 20% testing, ensuring no molecular scaffold leakage between sets.
- **Model Training**: Train scikit-learn Random Forest and Gradient Boosting classifiers for space group prediction on the GitHub Actions runner (CPU-only, 7GB RAM limit).
- **Hyperparameter Tuning**: Perform a grid search over 5 tree depths and 3 estimator counts, limiting runtime to 2 hours per fold.
- **Regression Task**: Train Ridge Regression models to predict unit cell volume and lattice parameters from fingerprints.
- **Statistical Validation**: Evaluate classification using Accuracy and F1-score; evaluate regression using R-squared and Mean Absolute Error (MAE).
- **Feasibility Check**: If training exceeds 6 hours, reduce dataset size to 10,000 random samples to ensure completion within the GHA job limit.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: N/A (No prior ideas submitted in this session).
- Verdict: NOT a duplicate
