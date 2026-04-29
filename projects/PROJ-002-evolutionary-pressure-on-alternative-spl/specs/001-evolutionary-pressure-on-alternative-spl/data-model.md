# Data Model: Evolutionary Pressure on Alternative Splicing in Primates

## Overview

This document defines the core entities, relationships, and storage formats for the project. All data artifacts MUST adhere to the schemas defined in `contracts/`.

## Core Entities

### RNA-seq Sample
Represents a biological sample from a specific primate species.
- **Attributes**:
  - `sample_id`: Unique identifier (string)
  - `species`: One of {human, chimp, macaque, marmoset}
  - `tissue`: "cortex"
  - `accession`: SRA/ENA accession number (string)
  - `fastq_path`: Path to raw FASTQ file
  - `bam_path`: Path to aligned BAM file
  - `checksum`: SHA-256 hash of raw file
  - `replicate_id`: Biological replicate index (integer)

### Splice Junction
Represents a quantified splice event.
- **Attributes**:
  - `junction_id`: Unique identifier
  - `gene_id`: Ensembl/RefSeq gene ID
  - `chromosome`: Chromosome name
  - `start`: Genomic start coordinate
  - `end`: Genomic end coordinate
  - `strand`: + or -
  - `psi_human`: PSI value (float)
  - `psi_chimp`: PSI value (float)
  - `psi_macaque`: PSI value (float)
  - `psi_marmoset`: PSI value (float)
  - `coverage`: Minimum read coverage across samples (integer)

### Differential Splicing Event
Represents a statistically significant difference between lineages.
- **Attributes**:
  - `event_id`: Unique identifier
  - `junction_id`: FK to Splice Junction
  - `lineage_comparison`: String (e.g., "Human/Chimp vs Macaque/Marmoset")
  - `delta_psi`: Difference in PSI (float)
  - `p_value`: Raw p-value (float)
  - `fdr`: FDR-corrected p-value (float)
  - `significant`: Boolean (FDR < 0.05)

### Regulatory Region
Represents the genomic context around the splicing event.
- **Attributes**:
  - `region_id`: Unique identifier
  - `junction_id`: FK to Splice Junction
  - `sequence`: Flanking intronic sequence (±500bp)
  - `phylop_score`: Conservation score (float)
  - `selection_signal`: Boolean (under positive selection)

## Relationships

- **RNA-seq Sample** (1) -- (N) **Splice Junction** (via alignment/quantification)
- **Splice Junction** (1) -- (1) **Differential Splicing Event** (via analysis)
- **Splice Junction** (1) -- (1) **Regulatory Region** (via extraction)
- **Differential Splicing Event** (N) -- (N) **Regulatory Region** (via enrichment analysis)

## Storage Formats

| Artifact | Format | Location |
|----------|--------|----------|
| Raw Reads | FASTQ | `data/raw/` |
| Alignments | BAM | `data/processed/alignments/` |
| Sample Metadata | YAML | `data/metadata.yaml` |
| PSI Values | CSV | `data/processed/psi_matrix.csv` |
| Differential Events | JSON | `data/processed/differential_events.json` |
| Checksums | JSON | `state/projects/PROJ-002-evolutionary-pressure-on-alternative-spl.yaml` |

## Validation Rules

- All genomic coordinates MUST be 1-based (BED format) or 0-based (Python) consistently documented.
- All checksums MUST be SHA-256.
- All statistical values MUST be rounded to 6 decimal places for storage, full precision for calculation.
- No PII allowed in `data/` or `code/`.
