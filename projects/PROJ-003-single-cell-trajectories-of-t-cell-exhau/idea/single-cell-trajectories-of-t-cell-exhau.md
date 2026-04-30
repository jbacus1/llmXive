---
field: biology
keywords: [biology]
submitter: system:brainstorm-seed
---

# Single-Cell Trajectories of T-Cell Exhaustion

**Field**: biology

## Research question

What are the distinct transcriptional trajectories of T-cell exhaustion in chronic infection and tumor microenvironments, and which regulatory events occur earliest at the fork-points that determine checkpoint therapy responsiveness?

## Motivation

T-cell exhaustion is a central mechanism of immune dysfunction in chronic viral infections and cancer, yet the sequence of molecular events leading to the exhausted state remains unclear. Resolving the canonical trajectory and identifying early fork-points could reveal optimal therapeutic windows for checkpoint blockade reversal.

## Related work

- [Defining 'T cell exhaustion' (2019)](https://doi.org/10.1038/s41577-019-0221-9) — Establishes the molecular and functional definition of T-cell exhaustion states.
- [NASH limits anti-tumour surveillance in immunotherapy-treated HCC (2021)](https://doi.org/10.1038/s41586-021-03362-0) — Demonstrates how metabolic disease environments shape T-cell dysfunction and checkpoint response.
- [ArchR is a scalable software package for integrative single-cell chromatin accessibility analysis (2021)](https://doi.org/10.1038/s41588-021-00790-6) — Provides scalable computational framework for single-cell regulatory landscape analysis (related to scVelo use case).
- [The immunopathology of sepsis and potential therapeutic targets (2017)](https://doi.org/10.1038/nri.2017.36) — Discusses immune dysregulation patterns relevant to chronic T-cell dysfunction states.

## Expected results

We expect to identify 2–3 distinct exhaustion trajectories with different fork-point timing for PD-1 upregulation versus metabolic reprogramming. Confirmation will require consistent trajectory ordering across at least 3 independent public datasets (n>10,000 T-cells total) with statistical significance (p<0.01) in branch-point assignment using bootstrap resampling.

## Methodology sketch

- Download public scRNA-seq PD-1+ T-cell datasets from GEO/SRA (accession IDs: GSE136103, GSE127465, GSE111075) using `wget`/`curl`
- Preprocess count matrices: filter cells with >20% mitochondrial reads, normalize using Seurat v4 (R)
- Run scVelo (Python) on each dataset to estimate RNA velocity and pseudotime ordering
- Apply Markov-chain pseudotime aligner to integrate trajectories across datasets
- Identify branch points using RNA velocity vector field divergence >2 standard deviations
- Extract gene expression at fork-points and rank by differential timing (early vs. late)
- Validate fork-point genes using published checkpoint therapy response signatures
- Generate trajectory plots and branch-point heatmaps for visualization
- Compute statistical significance of branch ordering via 1000x bootstrap resampling
- Document all steps in reproducible R/Python notebook for GitHub Actions execution

## Duplicate-check

- Reviewed existing ideas: [T-cell exhaustion dynamics, Single-cell immune atlas, Checkpoint therapy prediction]
- Closest match: T-cell exhaustion dynamics (similarity sketch: both address exhaustion trajectories but this proposal adds scVelo + Markov alignment for temporal ordering)
- Verdict: NOT a duplicate
