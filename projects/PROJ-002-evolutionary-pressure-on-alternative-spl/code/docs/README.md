# Evolutionary Pressure on Alternative Splicing in Primates

## Overview

This project analyzes evolutionary pressure on alternative splicing events across primate lineages (human, chimpanzee, macaque, and marmoset). The pipeline acquires RNA-seq data, aligns reads, quantifies splice junction usage, identifies differentially spliced events, and performs evolutionary selection analysis.

## Project Structure

```
projects/PROJ-002-evolutionary-pressure-on-alternative-spl/
├── code/
│   ├── src/
│   │   ├── acquisition/       # SRA downloader, metadata parser
│   │   ├── alignment/         # STAR alignment, quality control
│   │   ├── analysis/          # PhyloP extraction, enrichment, validation
│   │   ├── models/            # Data models (RNA-seq, splice junction, etc.)
│   │   ├── quantification/    # PSI calculator, rMATS wrapper
│   │   └── utils/             # Config, checksum, logging utilities
│   ├── tests/                 # Unit, integration, and contract tests
│   ├── docs/                  # This documentation
│   └── requirements.txt       # Python dependencies
├── data/
│   └── metadata.yaml          # Sample metadata schema
└── state/
```

## User Stories

### User Story 1: Data Acquisition and Preprocessing Pipeline (MVP)
- Acquire matched RNA-seq data from cortex tissue for 4 primate species
- Align raw reads to reference genomes using STAR
- Quality control with mapping rate threshold ≥70%

### User Story 2: Splicing Quantification and Differential Analysis
- Quantify splice junction usage and PSI values
- Identify differentially spliced events using fixed effect model
- Apply thresholds: ΔPSI ≥0.1, coverage ≥20 reads, FDR <0.05

### User Story 3: Evolutionary Selection Analysis and Validation
- Extract flanking intronic sequences (±500bp)
- Calculate evolutionary conservation (phyloP) and selection metrics
- Perform enrichment analysis and validate with orthogonal datasets

## Quick Start

```bash
# Install dependencies
pip install -r code/requirements.txt

# Run the pipeline
python -m code.src.pipeline.main

# Run tests
pytest code/tests/
```

## Configuration

See `code/data/metadata.yaml` for sample metadata schema and `code/src/utils/config.py` for configuration management.

## Success Criteria

- SC-001: Mapping rate ≥70% per sample
- SC-002: ΔPSI ≥0.1 for differential splicing calls
- SC-003: FDR <0.05 for enrichment analysis
- SC-004: Coverage ≥20 reads per junction

## Contact

For questions, refer to the design documents in `/specs/001-evolutionary-pressure-alternative-splicing/`.
