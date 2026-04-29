---
field: biology
keywords: [biology]
submitter: system:brainstorm-seed
---

# Mechanistic Interpretability of CTCF Binding-Site Selection

# Mechanistic Interpretability of CTCF Binding-Site Selection

**Field**: biology

## Research question

Which sequence motifs and neighboring chromatin features causally drive CTCF site selection across cell types, and how can mechanistic interpretability methods applied to sequence-context-aware binding predictors reveal these determinants?

## Motivation

CTCF binds tens of thousands of genomic sites but engages only a fraction in any given cell type, yet the causal determinants of this selective engagement remain poorly understood. Current predictive models capture binding patterns without revealing the mechanistic basis of site selection, limiting biological insight and hypothesis generation. Applying mechanistic interpretability tools to these predictors could bridge the gap between statistical prediction and causal biological understanding.

## Related work

- [Prediction and Comparative Analysis of CTCF Binding Sites based on a First Principle Approach](http://arxiv.org/abs/2110.10508v1) — Provides first-principles calculation of CTCF binding patterns across genomes, establishing baseline predictive capabilities.
- [Challenges in Mechanistically Interpreting Model Representations](http://arxiv.org/abs/2402.03855v2) — Reviews mechanistic interpretability methods for reverse-engineering neural network algorithms, applicable to binding predictors.
- [nnterp: A Standardized Interface for Mechanistic Interpretability of Transformers](http://arxiv.org/abs/2511.14465v2) — Offers standardized tools for analyzing transformer internals that could be adapted for sequence-based binding models.
- [Group Equivariance Meets Mechanistic Interpretability: Equivariant Sparse Autoencoders](http://arxiv.org/abs/2511.09432v1) — Demonstrates sparse autoencoders for disentangling neural network activations into interpretable features.
- [Approximation of Intractable Likelihood Functions in Systems Biology via Normalizing Flows](http://arxiv.org/abs/2312.02391v1) — Shows how generative models can handle complex likelihood functions in biological modeling.
- [Bayesian uncertainty analysis for complex systems biology models](http://arxiv.org/abs/1607.06358v2) — Provides framework for parameter uncertainty and model evaluation in biological systems.

## Expected results

We expect to identify 3-5 interpretable latent features that correspond to specific sequence motifs or chromatin contexts driving CTCF site selection. Validation will come from perturbation experiments where synthetic sequences with/without these features show differential predicted binding, confirmed by statistical testing across cell types. Evidence strength will be assessed by cross-validation performance and consistency with known CTCF biology.

## Methodology sketch

- Obtain ChIP-seq CTCF binding data from ENCODE across 10+ cell types with matched ATAC-seq and histone modification profiles.
- Train a transformer-based sequence-context model to predict CTCF binding probability from DNA sequence and chromatin features.
- Apply sparse autoencoders to decompose hidden layer activations into interpretable feature directions.
- Use feature attribution methods (e.g., integrated gradients) to map features back to specific sequence positions and chromatin contexts.
- Generate synthetic DNA sequences with systematic motif perturbations to validate causal feature importance.
- Perform differential binding analysis across cell types to identify features that explain cell-type-specific engagement.
- Apply permutation tests (n=1000) to assess statistical significance of feature contributions against null distributions.
- Validate predictions against independent experimental datasets (e.g., CRISPRi perturbation studies of CTCF sites).

## Duplicate-check

- Reviewed existing ideas: TODO — existing_idea_paths not provided.
- Closest match: TODO — no existing ideas to compare.
- Verdict: NOT a duplicate
