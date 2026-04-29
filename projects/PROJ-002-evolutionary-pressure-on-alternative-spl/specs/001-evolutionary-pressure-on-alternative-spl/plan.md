# Implementation Plan: Evolutionary Pressure on Alternative Splicing in Primates

**Branch**: `[001-evolutionary-pressure-alternative-splicing]` | **Date**: 2025-01-15 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-evolutionary-pressure-alternative-splicing/spec.md`

## Summary

This feature implements a computational pipeline to quantify evolutionary pressure on alternative splicing events across four primate species (Human, Chimpanzee, Macaque, Marmoset). The workflow acquires matched RNA-seq cortex tissue data, aligns reads using STAR, quantifies splice junctions and PSI values using rMATS/SUPPA2, identifies differentially spliced events via fixed effect models, and performs enrichment analysis against regions under positive selection using phyloP conservation scores. The output validates the hypothesis that splicing divergence correlates with evolutionary selection signatures.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pysam==0.21.0`, `pandas==2.1.0`, `numpy==1.24.0`, `scipy==1.11.0`, `biopython==1.81`, `statsmodels==0.14.0`, `pyyaml==6.0.1`, `pytest==7.4.0`  
**External Tools**: STAR (v2.7.10a), rMATS (v4.1.2), SAMtools (v1.17), Bedtools (v2.31.0), SRA Toolkit (v3.0.0)  
**Storage**: Local filesystem (HPC scratch), BAM/FASTQ (raw), CSV/JSON (intermediate), SQLite (metadata)  
**Testing**: `pytest`, `pytest-benchmark`, contract tests against `contracts/` schemas  
**Target Platform**: Linux server (HPC/Cloud, x86_64)  
**Project Type**: Computational Biology Pipeline / CLI  
**Performance Goals**: Alignment throughput > 10M reads/min, end-to-end pipeline < 48h for full dataset  
**Constraints**: Memory < 64GB per alignment job, strict reproducibility via random seeds, immutable raw data  
**Scale/Scope**: 4 species, ~50-100 samples per species, ~100GB raw data volume

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Note |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | `code/` will pin `requirements.txt` versions. Random seeds for statistical models will be fixed in config. External datasets fetched via SRA Toolkit accessions. |
| **II. Verified Accuracy** | PASS | No external citations added in this plan. Any future citations will be validated by Reference-Validator before `research_accepted`. |
| **III. Data Hygiene** | PASS | All files under `data/` will be checksummed (SHA-256). Raw data preserved; derivations written to new filenames. PII scan enabled. |
| **IV. Single Source of Truth** | PASS | Results trace to specific rows in `data/` via `artifact_hashes`. No hand-typed statistics in reports. |
| **V. Versioning** | PASS | Artifacts carry content hashes. State file `state/projects/PROJ-002-evolutionary-pressure-on-alternative-spl.yaml` updated on changes. |
| **VI. Cross-Species Data Harmonization** | PASS | Genome versions (GRCh38, PanTro6, etc.) documented in `data/metadata.yaml`. Orthology mapped via Ensembl Compara before aggregation. |
| **VII. Phylogenetic Statistical Independence** | PASS | Statistical models (fixed effect + phylogenetic correction) will account for shared evolutionary history. Branch-specific signals validated against neutral expectations. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evolutionary-pressure-alternative-splicing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── differential_splicing_event.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-002-evolutionary-pressure-on-alternative-spl/
├── code/
│   ├── requirements.txt
│   ├── setup.py
│   ├── src/
│   │   ├── __init__.py
│   │   ├── acquisition/
│   │   │   ├── sra_downloader.py
│   │   │   └── metadata_parser.py
│   │   ├── alignment/
│   │   │   ├── star_runner.py
│   │   │   └── quality_control.py
│   │   ├── quantification/
│   │   │   ├── rmats_wrapper.py
│   │   │   └── psi_calculator.py
│   │   ├── analysis/
│   │   │   ├── differential_splicing.py
│   │   │   ├── phylo_extractor.py
│   │   │   └── enrichment_test.py
│   │   └── utils/
│   │       ├── config.py
│   │       └── checksum.py
│   └── tests/
│       ├── contract/
│       ├── integration/
│       └── unit/
├── data/
│   ├── raw/              # Downloaded FASTQ/BAM (immutable)
│   ├── processed/        # Alignments, PSI matrices
│   └── metadata.yaml     # Sample info, checksums
├── state/
│   └── projects/
│       └── PROJ-002-evolutionary-pressure-on-alternative-spl.yaml
└── specs/
    └── 001-evolutionary-pressure-alternative-splicing/
        └── [documentation files]
```

**Structure Decision**: Single project structure (`projects/PROJ-002.../code/`) selected to maintain tight coupling between pipeline code and data artifacts within the project scope, ensuring compliance with Constitution Principle I (Reproducibility) and IV (Single Source of Truth).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
