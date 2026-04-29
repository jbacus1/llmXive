---
field: chemistry
keywords: [chemistry]
submitter: system:brainstorm-seed
---

# Machine-Learned Potentials for Transition-Metal Catalysis

**Field**: chemistry

## Research question

Can graph-neural-network potentials trained on density-functional theory (DFT) data for Pd, Ni, and Cu elementary steps reproduce DFT free-energy barriers to within 2 kcal/mol on held-out transition-metal catalytic reactions?

## Motivation

DFT calculations provide accurate energetics for transition-metal catalytic cycles but are too computationally expensive for high-throughput screening of reaction conditions. Machine-learned interatomic potentials offer a pathway to accelerate these calculations while preserving accuracy, addressing a critical bottleneck in catalyst design and reaction optimization.

## Related work

- [Guest Editorial: Special Topic on Data-enabled Theoretical Chemistry (2018)](http://arxiv.org/abs/1806.02690v2) — Provides a foundational survey of data-enabled approaches in theoretical chemistry, including glossary of relevant ML terminology.
- [Application of Artificial Neural Networks for Catalysis (2021)](http://arxiv.org/abs/2110.00924v1) — Demonstrates ANN applications for improving catalyst performance in chemical industry contexts.
- [Machine Learning Potentials for Heterogeneous Catalysis (2024)](http://arxiv.org/abs/2411.00720v1) — Reviews ML potential approaches specifically for heterogeneous catalysis systems.
- [Reliable and Efficient Automated Transition-State Searches with Machine-Learned Interatomic Potentials (2026)](http://arxiv.org/abs/2604.00405v1) — Addresses transition-state search automation using ML potentials, directly relevant to barrier prediction.

## Expected results

We expect the GNN potential to achieve mean absolute errors ≤2 kcal/mol on held-out barrier heights for Pd, Ni, and Cu systems. Success will be confirmed by comparing predicted free-energy profiles against DFT benchmarks across at least 50 diverse elementary steps; failure will be indicated by systematic underestimation of barrier heights exceeding 3 kcal/mol.

## Methodology sketch

- Curate a benchmark dataset of 100+ DFT-computed transition-metal elementary steps (Pd, Ni, Cu) with geometries, energies, and free-energy corrections.
- Construct graph representations of molecular structures using atomic species, connectivity, and local coordination environments.
- Train a graph-neural-network potential on 80% of the dataset with DFT energies and forces as targets.
- Validate on held-out 20% set, computing predicted barrier heights and free energies.
- Compare GNN predictions against DFT benchmarks using mean absolute error and correlation metrics.
- Perform uncertainty quantification via ensemble predictions or dropout-based variance estimates.
- Apply statistical tests (paired t-test or Wilcoxon signed-rank) to assess significance of error distributions.
- Document computational speedup relative to full DFT calculations for equivalent sampling.

## Duplicate-check

- Reviewed existing ideas: [None provided in context].
- Closest match: None identified.
- Verdict: NOT a duplicate.
