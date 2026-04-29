# Implementation Plan: Mechanistic Interpretability of CTCF Binding-Site Selection

**Branch**: `001-ctcf-binding-interpretability` | **Date**: 2024-05-22 | **Spec**: specs/001-ctcf-binding-interpretability/spec.md
**Input**: Feature specification from `/specs/001-ctcf-binding-interpretability/spec.md`

## Summary

This project implements a transformer-based sequence-context model to predict CTCF binding probability from DNA sequence and chromatin features, followed by mechanistic interpretability analysis using sparse autoencoders to identify latent features driving binding. The system ingests ENCODE ChIP-seq, ATAC-seq, and histone modification data for 10+ cell types, trains a predictive model, and validates findings through synthetic perturbation experiments.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyTorch 2.1, transformers 4.36, scikit-learn 1.3, pandas 2.1, numpy 1.24  
**Storage**: Local filesystem with manifest.json tracking; ENCODE data via public API  
**Testing**: pytest 7.4, contract tests against schema definitions  
**Target Platform**: Linux server with GPU support  
**Project Type**: computational biology research pipeline  
**Performance Goals**: Model convergence within 48 hours; inference <10 seconds per kilobase  
**Constraints**: Memory <200GB for training; fixed context window 2048bp  
**Scale/Scope**: 10+ cell types, 1M+ sequence contexts, 3-5 interpretable latent features

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Notes |
|-----------|-------------------|---------------------|
| I. Reproducibility | COMPLIANT | Random seeds pinned in code; ENCODE accessions tracked in data/manifest.json; reproducible on fresh GitHub Actions runner |
| II. Verified Accuracy | COMPLIANT | All external citations will be validated by Reference-Validator; no fabricated URLs; title-token-overlap ≥0.7 threshold enforced |
| III. Data Hygiene | COMPLIANT | All files under data/ checksummed; checksums recorded in state/ artifact_hashes; raw data preserved unchanged |
| IV. Single Source of Truth | COMPLIANT | All figures/statistics trace to exactly one data row and one code block; derived numbers not hand-typed |
| V. Versioning Discipline | COMPLIANT | Every artifact carries content hash; state YAML updated on artifact changes; Advancement-Evaluator invalidates stale records |
| VI. Biological Validity | COMPLIANT | Predictions validated against independent ENCODE ChIP-seq and CRISPRi perturbation studies; causal claims supported by perturbation evidence |

## Project Structure

### Documentation (this feature)

```text
specs/001-ctcf-binding-interpretability/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── sequence_context.schema.yaml
│   ├── latent_feature.schema.yaml
│   └── binding_prediction.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py              # ENCODE data ingestion (FR-001)
│   │   └── preprocess.py          # Normalization and alignment (FR-001)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── transformer.py         # Transformer architecture (FR-002)
│   │   └── sae.py                 # Sparse autoencoder (FR-003)
│   ├── training/
│   │   ├── __init__.py
│   │   ├── train.py               # Model training loop (FR-002)
│   │   └── inference.py           # Prediction script (FR-002)
│   ├── interpretation/
│   │   ├── __init__.py
│   │   ├── feature_attribution.py # Feature attribution analysis (FR-003)
│   │   └── perturbation.py        # Synthetic perturbation (FR-004)
│   └── validation/
│       ├── __init__.py
│       ├── significance.py        # Statistical testing (FR-005)
│       └── motif_analysis.py      # Motif correspondence (FR-003)
├── data/
│   ├── manifest.json              # Accession numbers and checksums
│   └── processed/                 # Derived datasets (checksummed)
├── tests/
│   ├── unit/
│   │   ├── test_loader.py
│   │   ├── test_transformer.py
│   │   └── test_sae.py
│   ├── contract/
│   │   ├── test_sequence_context.py
│   │   ├── test_latent_feature.py
│   │   └── test_binding_prediction.py
│   └── integration/
│       └── test_pipeline.py
└── state/
    └── projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin.yaml
```

**Structure Decision**: Single project structure (Option 1) selected as this is a computational research pipeline without frontend requirements. All modules organized by functional responsibility under code/. Contract tests in tests/contract/ validate against schema definitions in contracts/.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Sparse Autoencoder layer | Required for mechanistic interpretability (FR-003) | Standard feature attribution insufficient to identify latent feature directions |
| Multi-cell-type support | Required for generalization validation (SC-001) | Single cell-type analysis would not validate cross-cell-type predictive power |
| Synthetic perturbation pipeline | Required for causal validation (FR-004, SC-003) | Correlation alone does not establish mechanistic causality |
