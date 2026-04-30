---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting Material Properties from Compositional Data with Graph Neural Networks

**Field**: materials science

## Research question

Can graph neural networks (GNNs) trained on publicly available compositional data accurately predict band gap and hardness values for crystalline materials without requiring full crystal structure information?

## Motivation

Materials discovery is bottlenecked by expensive DFT simulations and experimental synthesis. If GNNs can learn meaningful structure-property relationships from composition alone, they could enable rapid screening of candidate materials. This work addresses the gap between traditional composition-based heuristics and full-structure deep learning approaches by testing whether compositional graphs retain sufficient signal for property prediction.

## Related work

- [CTGNN: Crystal Transformer Graph Neural Network for Crystal Material Property Prediction (2024)](http://arxiv.org/abs/2405.11502v1) — Demonstrates deep learning approaches for crystal material property prediction, relevant to GNN-based property modeling.
- [Learning to fail: Predicting fracture evolution in brittle material models using recurrent graph convolutional neural networks (2018)](http://arxiv.org/abs/1810.06118v3) — Shows graph convolutional networks can model material failure, supporting GNN applicability to mechanical properties.
- [Novel machine learning framework for thermal conductivity prediction by crystal graph convolution embedded ensemble (2021)](https://doi.org/10.1002/smm2.1074) — Applies crystal graph convolution to predict thermal properties, validating graph-based approaches for material properties.
- [Prediction of the functional properties of ceramic materials from composition using artificial neural networks (2007)](http://arxiv.org/abs/cond-mat/0703210v1) — Early work on composition-based property prediction, establishing precedent for composition-only approaches.
- [Orbital Graph Convolutional Neural Network for Material Property Prediction (2020)](http://arxiv.org/abs/2008.06415v1) — Explores atomic orbital interactions in GNNs, relevant for understanding how compositional graphs encode physical properties.
- [Graph Neural Networks for an Accurate and Interpretable Prediction of the Properties of Polycrystalline Materials (2020)](http://arxiv.org/abs/2010.05851v3) — Demonstrates interpretability of GNN predictions for polycrystalline materials, supporting analysis of learned representations.
- [Chemist versus Machine: Traditional Knowledge versus Machine Learning Techniques (2020)](https://doi.org/10.1016/j.trechm.2020.10.007) — Discusses transition from chemical heuristics to ML-based materials discovery, contextualizing this work's motivation.
- [The Deep Arbitrary Polynomial Chaos Neural Network or how Deep Artificial Neural Networks could benefit from Data-Driven Homogeneous Chaos Theory (2023)](http://arxiv.org/abs/2306.14753v1) — Explores ML uncertainty quantification, relevant for assessing prediction confidence in materials screening.

## Expected results

We expect the GNN to achieve R² > 0.7 for band gap prediction and R² > 0.5 for hardness prediction on held-out test sets, with performance degrading when trained on composition-only versus full-structure inputs. The learned node embeddings should correlate with known periodic table properties (electronegativity, atomic radius), confirming the model captures chemically meaningful features.

## Methodology sketch

- **Data acquisition**: Download Materials Project dataset subset via Materials Project API (https://materialsproject.org/) or Materials Project Open Data (https://doi.org/10.17188/1399059); extract composition, band gap, and hardness for ≤10,000 crystalline materials.
- **Data preprocessing**: Parse chemical formulas to construct compositional graphs where nodes are unique elements with features (atomic number, electronegativity, valence electrons); edges connect all element pairs with features (element distance in periodic table).
- **Train/test split**: Stratified split by crystal system (80% train, 10% validation, 10% test) to ensure distributional consistency across sets.
- **Model architecture**: Implement lightweight GNN (2-3 graph convolution layers, hidden dim ≤128) using PyTorch Geometric; train on CPU with batch size ≤32 to fit 7GB RAM.
- **Training procedure**: Optimize with Adam (lr=1e-3, early stopping patience=10 epochs); limit training to ≤50 epochs with max 30-minute runtime per epoch on GHA.
- **Statistical evaluation**: Compute R², MAE, and RMSE for band gap (eV) and hardness (GPa); use 5-fold cross-validation to estimate variance in performance metrics.
- **Baseline comparison**: Compare against random forest and linear regression baselines trained on the same compositional features to quantify GNN advantage.
- **Embedding analysis**: Perform PCA on learned node embeddings; correlate principal components with periodic properties using Pearson correlation (p-value < 0.05 threshold).
- **Ablation study**: Remove edge features incrementally to test their contribution to prediction accuracy; report ΔR² for each ablation.
- **Reproducibility**: Archive all code, data preprocessing scripts, and trained model weights to Zenodo; include environment.yml for exact dependency pinning.

## Duplicate-check

- Reviewed existing ideas: N/A (initial flesh-out in this field).
- Closest match: None identified in current corpus.
- Verdict: NOT a duplicate
