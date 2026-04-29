# Research: Evolutionary Pressure on Alternative Splicing in Primates

## Research Objective

To determine if alternative splicing divergence between primate lineages (Human, Chimpanzee, Macaque, Marmoset) is enriched in genomic regions under positive evolutionary selection, using RNA-seq data from cortex tissue.

## Data Sources & Acquisition

### Public Repositories
Data will be acquired from Sequence Read Archive (SRA) and European Nucleotide Archive (ENA).
- **Search Criteria**: Cortex tissue, RNA-seq, Homo sapiens, Pan troglodytes, Macaca mulatta, Callithrix jacchus.
- **Quality Filters**: Minimum 3 biological replicates per species, minimum 20M reads per sample.
- **Accession Tracking**: All accessions recorded in `data/metadata.yaml` with SHA-256 checksums.

### Reference Genomes & Annotations
- **Human**: GRCh38 (Ensembl release compatible)
- **Chimpanzee**: PanTro6
- **Macaque**: Mmul_10
- **Marmoset**: Callithrix_jacchus_CallJac3
- **Annotation**: GTF files aligned with respective genome versions. Orthology mapping via Ensembl Compara.

### Conservation Scores
- **phyloP**: 100-way vertebrate alignment scores (or primate-specific subset) from UCSC or Ensembl.
- **Handling Missing Data**: Regions without scores will be flagged and excluded from selection analysis, recorded in `data/processed/exclusions.log`.

## Methodology & Tools

### Alignment
- **Tool**: STAR (v2.7.10a)
- **Parameters**: `--outSAMtype BAM SortedByCoordinate`, `--twopassMode Basic`.
- **QC**: Mapping rates recorded. Samples < 70% mapping rate flagged for review.

### Splicing Quantification
- **Tool**: rMATS (v4.1.2)
- **Metric**: Percent Spliced In (PSI).
- **Thresholds**: ΔPSI ≥ 0.1, Read Coverage ≥ 20, FDR < 0.05.
- **Output**: Event-level statistics (IncLevel1, IncLevel2, PValue, FDR).

### Differential Analysis
- **Model**: Fixed effect model with phylogenetic correction (PGLS if applicable).
- **Lineages**: Human/Chimp vs Macaque/Marmoset.
- **Correction**: Benjamini-Hochberg FDR applied across all events.

### Evolutionary Analysis
- **Extraction**: Flanking intronic sequences (±500bp) around alternatively spliced exons using Bedtools.
- **Enrichment**: Fisher's exact test or Hypergeometric test for overlap with positive selection regions.
- **Validation**: Cross-reference with independent datasets (e.g., ENCODE, GTEx) if available.

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| Data Quality Variance | Implement strict QC thresholds; downsample high-depth samples to match low-depth. |
| Missing Annotations | Use conservative gene models; exclude genes without orthologs across all 4 species. |
| Sequence Divergence | Align reads to species-specific genomes; avoid cross-mapping. |
| Conservation Score Gaps | Document missing regions; do not impute scores. |

## Ethical & Compliance Considerations

- **Human Data**: All human data must be de-identified and sourced from public repositories (no PII).
- **Animal Data**: Non-human primate data sourced from public repositories; no new animal experiments conducted.
- **Reproducibility**: All scripts must be version controlled and executable via `code/requirements.txt`.
