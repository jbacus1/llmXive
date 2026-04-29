# Data Model: Figure ↔ Data Binding

**Date**: 2024-01-15  
**Context**: Captures the binding between manuscript figures and source data files in `data/`.

## Figure Specifications

### Figure 1: Pipeline Overview Diagram
- **Purpose**: Illustrate end-to-end workflow (SRA → STAR → rMATS → Comparative).
- **Source File**: `data/pipeline_workflow.json` (Metadata) + `scripts/figures/pipeline.py`
- **Generation Script**: `scripts/figures/pipeline.py`
- **Output Format**: PDF (Vector)
- **Caption Requirement**: Names `data/` sources and tool versions (STAR v2.7.10a, rMATS v4.1.2).

### Figure 2: Alignment Statistics
- **Purpose**: Demonstrate STAR throughput (>10M reads/min) and memory usage.
- **Source File**: `data/alignment_stats.csv`
- **Generation Script**: `scripts/figures/alignment_stats.py`
- **Output Format**: PDF (Vector)
- **Caption Requirement**: References `data/alignment_stats.csv` and STAR log checksums.

### Figure 3: Splicing Event Distribution
- **Purpose**: Show rMATS quantification coverage by type (SE, MXE, A5SS, A3SS).
- **Source File**: `data/splicing_event_counts.csv`
- **Generation Script**: `scripts/figures/splicing_distribution.py`
- **Output Format**: PDF (Vector)
- **Caption Requirement**: References `data/splicing_event_counts.csv` and rMATS v4.1.2.

### Figure 4: Conservation Heatmap
- **Purpose**: Visualize evolutionary pressure patterns across species pairs.
- **Source File**: `data/orthology_conservation_matrix.csv`
- **Generation Script**: `scripts/figures/conservation_heatmap.py`
- **Output Format**: PDF (Vector)
- **Caption Requirement**: References Ensembl Compara orthology mapping and `data/` matrix.

### Figure 5: Differential Splicing Significance
- **Purpose**: Highlight candidate genes under evolutionary selection.
- **Source File**: `data/differential_splicing_results.csv`
- **Generation Script**: `scripts/figures/differential_significance.py`
- **Output Format**: PDF (Vector)
- **Caption Requirement**: References statistical test (FDR < 0.05) and `data/` results.

## Data Integrity Rules

1. **Checksums**: Every source CSV/JSON in `data/` MUST have a corresponding `.sha256` file.
2. **Versioning**: Scripts MUST declare `matplotlib==3.7.0` and `seaborn==0.12.2` in `requirements.txt`.
3. **Traceability**: Each figure caption MUST list the specific `data/` filename used.
