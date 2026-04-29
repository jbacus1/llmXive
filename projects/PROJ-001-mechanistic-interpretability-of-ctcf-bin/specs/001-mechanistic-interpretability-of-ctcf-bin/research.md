# Research: Mechanistic Interpretability of CTCF Binding-Site Selection

## Background

CTCF (CCCTC-binding factor) is a zinc-finger protein that plays a critical role in 3D genome organization, including chromatin loop formation, topologically associating domain (TAD) boundaries, and insulator function. Understanding the sequence and chromatin determinants of CTCF binding-site selection is fundamental to deciphering gene regulatory mechanisms.

## Scientific Context

### CTCF Binding Determinants

CTCF binding is influenced by:
- **Primary sequence motifs**: The canonical CTCF binding motif contains a conserved core sequence recognized by the zinc-finger domain
- **Chromatin accessibility**: Open chromatin regions (measured by ATAC-seq) facilitate CTCF binding
- **Histone modifications**: Specific histone marks (e.g., H3K27ac, H3K4me3) correlate with active CTCF binding sites
- **Cell-type specificity**: CTCF binding patterns vary across cell types despite shared core motifs

### Machine Learning in Genomics

Transformer-based models have shown success in predicting regulatory elements from DNA sequence:
- Sequence-context models capture long-range dependencies
- Attention mechanisms provide interpretability through feature importance
- Multi-modal integration (sequence + chromatin) improves predictive accuracy

### Mechanistic Interpretability

Sparse autoencoders (SAEs) decompose neural network activations into interpretable feature directions:
- Identify latent features corresponding to biological determinants
- Enable causal validation through synthetic perturbation
- Bridge the gap between black-box predictions and mechanistic understanding

## Methodology Overview

### Phase 1: Data Ingestion (User Story 1)

1. Fetch ENCODE ChIP-seq, ATAC-seq, and histone modification data for 10+ cell types
2. Align all data to GRCh38/hg38 genome build
3. Normalize signal intensities and handle missing data
4. Generate fixed-size context windows (2048bp) with padding/truncation

### Phase 2: Model Training (User Story 2)

1. Construct transformer architecture with sequence and chromatin input channels
2. Train on binding/non-binding classification task
3. Validate on held-out cell types (not used during training)
4. Achieve target AUC >0.85 on test sets

### Phase 3: Interpretability Analysis (User Story 3)

1. Apply sparse autoencoders to hidden layer activations
2. Extract 3-5 interpretable latent features
3. Validate correspondence to known CTCF motifs and chromatin contexts
4. Perform synthetic perturbation experiments
5. Calculate statistical significance (p < 0.05) for feature contributions

## Key Challenges

### Challenge 1: Data Heterogeneity

Different cell types have varying data availability. The system must gracefully handle missing ATAC-seq or histone modification data while maintaining cross-cell-type comparability.

**Mitigation**: Log warnings for missing cell types (User Story 1, Scenario 2); implement imputation strategies for missing modalities.

### Challenge 2: Model Convergence

Transformer training may fail to converge or overfit to training cell types.

**Mitigation**: Monitor loss convergence (User Story 2, Scenario 1); implement early stopping; validate on held-out cell types.

### Challenge 3: Feature Interpretability

Sparse autoencoder features may not correspond to known biological motifs (overfitting to noise).

**Mitigation**: Validate against established CTCF motifs (Assumption 3); require perturbation evidence for causal claims (Constitution Principle VI).

## Validation Strategy

### Internal Validation

- Loss convergence threshold during training
- AUC >0.85 on held-out cell types (SC-001)
- Feature sparsity metrics from SAE

### External Validation

- Correlation with independent ENCODE ChIP-seq datasets
- Comparison to CRISPRi perturbation studies (if available)
- Motif correspondence analysis against JASPAR/TRANSFAC databases

### Statistical Validation

- Permutation tests for feature significance (FR-005)
- p < 0.05 threshold for perturbation effects (User Story 3, Scenario 3)
- >90% correlation between predicted and actual probability shifts (SC-003)

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| ENCODE data access restrictions | Low | High | Use public API; cache data locally; track accessions |
| GPU resource constraints | Medium | High | Optimize batch sizes; use gradient checkpointing |
| Model overfitting to training cell types | Medium | High | Cross-cell-type validation; regularization |
| SAE features lack biological meaning | Medium | High | Motif correspondence analysis; perturbation validation |
| Synthetic perturbations do not reflect biology | Low | Medium | Compare to CRISPRi datasets if available |

## Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Test AUC (held-out cell types) | >0.85 | Validation set evaluation |
| Interpretable latent features | 3-5 | SAE decomposition + motif analysis |
| Perturbation correlation | >90% | Synthetic perturbation experiments |
| Statistical significance | p < 0.05 | Permutation tests |
| Inference speed | <10s/kb | Timing measurements |
