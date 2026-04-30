---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Plant Stress Response from Publicly Available Transcriptomic Data

**Field**: biology

## Research question

Can supervised machine learning models accurately classify specific abiotic stress types (drought, salinity, heat, cold) in plants using only normalized transcriptomic profiles from public repositories?

## Motivation

Rapid diagnosis of crop stress is critical for breeding resilient varieties, yet current methods often require targeted biomarker assays or wet-lab validation. A generalizable computational model could enable rapid stress screening from existing RNA-seq data, reducing the need for new experimental data collection and accelerating agricultural research pipelines.

## Related work

- [iDEP: an integrated web application for differential expression and pathway analysis of RNA-Seq data (2018)](https://doi.org/10.1186/s12859-018-2486-6) — Provides a standardized framework for RNA-seq preprocessing and differential expression, informing the normalization steps required before ML classification.

## Expected results

We expect to achieve >80% classification accuracy on held-out test sets using a Random Forest classifier trained on the top 2,000 most variable genes. Evidence will be confirmed via stratified 5-fold cross-validation performance metrics (F1-score and confusion matrix) demonstrating distinct separation between stress classes.

## Methodology sketch

- Download raw count matrices and metadata for 5–10 public RNA-seq datasets (GEO accessions) covering drought, salinity, heat, and cold stress using `wget` or `curl` from NCBI GEO.
- Preprocess data in Python using `pandas` and `scipy` to normalize counts (TPM/FPKM) and filter out low-expression genes (<10 counts per million).
- Perform feature selection to retain the top 2,000 most variable genes across all samples to ensure memory usage stays within 7GB RAM limits.
- Split data into training (80%) and test (20%) sets, ensuring stratification by stress type to maintain class balance.
- Train a Random Forest classifier (using `scikit-learn`) on the training set with hyperparameters tuned via grid search on the training fold only.
- Evaluate model performance on the test set using stratified 5-fold cross-validation to compute accuracy, precision, recall, and F1-score.
- Generate a confusion matrix and feature importance plot to identify key stress-responsive genes driving the classification.

## Duplicate-check

- Reviewed existing ideas: (None provided in input context).
- Closest match: (No match found in provided context).
- Verdict: NOT a duplicate
