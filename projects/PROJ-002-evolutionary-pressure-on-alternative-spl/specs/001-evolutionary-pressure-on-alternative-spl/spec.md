# Feature Specification: Evolutionary Pressure on Alternative Splicing in Primates

**Feature Branch**: `[001-evolutionary-pressure-alternative-splicing]`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Evolutionary Pressure on Alternative Splicing in Primates"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

Researcher can acquire matched RNA-seq data from cortex tissue for human, chimpanzee, macaque, and marmoset from public repositories and align raw reads to respective reference genomes using STAR.

**Why this priority**: Without foundational data acquisition and preprocessing, no downstream analysis is possible. This represents the critical path for the entire research workflow.

**Independent Test**: Can be fully tested by successfully downloading and aligning RNA-seq reads from one species and producing aligned BAM files with acceptable mapping rates.

**Acceptance Scenarios**:

1. **Given** RNA-seq data is available in public repositories, **When** researcher queries the data acquisition module, **Then** matched cortex tissue samples for all four primate species are identified and retrievable
2. **Given** raw RNA-seq reads are available, **When** STAR alignment is executed against the appropriate reference genome, **Then** aligned BAM files are produced with mapping rates meeting quality thresholds

---

### User Story 2 - Splicing Quantification and Differential Analysis (Priority: P2)

Researcher can quantify splice junction usage and PSI values, then identify differentially spliced events between lineages using a fixed effect model.

**Why this priority**: This is the core analytical step that produces the primary data for testing the research hypothesis. Without this, no splicing divergence can be measured.

**Independent Test**: Can be fully tested by running splicing quantification on a subset of data and producing PSI values and differential splicing calls that can be validated against known benchmarks.

**Acceptance Scenarios**:

1. **Given** aligned BAM files from multiple species, **When** rMATS or SUPPA2 is executed for splice junction quantification, **Then** PSI values are produced for alternatively spliced exons
2. **Given** PSI values across lineages, **When** fixed effect model is applied for differential splicing, **Then** differentially spliced events are identified with statistical significance measures

---

### User Story 3 - Evolutionary Selection Analysis and Validation (Priority: P3)

Researcher can extract flanking intronic sequences, calculate evolutionary conservation and selection metrics, perform enrichment analysis, and validate key findings using orthogonal datasets.

**Why this priority**: This completes the hypothesis testing by linking splicing changes to evolutionary selection signatures. It validates the core research question but depends on P1 and P2 outputs.

**Independent Test**: Can be fully tested by running enrichment analysis on a subset of identified splicing events and producing selection metric calculations that can be compared to known positive selection regions.

**Acceptance Scenarios**:

1. **Given** alternatively spliced exons, **When** flanking intronic sequences (±500bp) are extracted, **Then** phyloP conservation scores and selection metrics are calculated for regulatory regions
2. **Given** splicing events and selection metrics, **When** enrichment analysis is performed with Benjamini-Hochberg FDR correction, **Then** overlap with regions under positive selection is quantified with corrected p-values
3. **Given** key findings from enrichment analysis, **When** orthogonal datasets or independent samples are available, **Then** findings can be validated through replication

---

### Edge Cases

- What happens when RNA-seq data quality varies significantly across species (e.g., different sequencing depths)?
- How does system handle missing or incomplete reference genome annotations for non-human primates?
- What happens when splice junctions cannot be mapped confidently due to sequence divergence?
- How does system handle cases where phyloP conservation scores are unavailable for certain genomic regions?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST acquire matched RNA-seq data from cortex tissue for human, chimpanzee, macaque, and marmoset from public repositories
- **FR-002**: System MUST align raw reads to respective reference genomes using STAR
- **FR-003**: System MUST quantify splice junction usage and percent spliced in (PSI) values using rMATS or SUPPA2
- **FR-004**: System MUST identify differentially spliced events between lineages using a fixed effect model
- **FR-005**: System MUST extract flanking intronic sequences (±500bp) around alternatively spliced exons
- **FR-006**: System MUST calculate evolutionary conservation scores (phyloP) and selection metrics for regulatory regions
- **FR-007**: System MUST perform enrichment analysis to test if splicing changes overlap with regions under positive selection
- **FR-008**: System MUST apply Benjamini-Hochberg FDR correction for multiple hypothesis testing across all events

### Key Entities

- **RNA-seq Sample**: Represents a cortex tissue sample from a primate species, key attributes include species identifier, tissue type, sequencing metadata, and data source
- **Splice Junction**: Represents a quantified splice junction event, key attributes include exon coordinates, PSI value, and associated gene
- **Differential Splicing Event**: Represents a statistically significant splicing difference between lineages, key attributes include event type, statistical significance, and lineage comparison
- **Regulatory Region**: Represents flanking intronic sequence around alternatively spliced exon, key attributes include genomic coordinates, conservation score, and selection metric values

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 70% of RNA-seq samples from all four primate species successfully processed through alignment and quantification pipeline
- **SC-002**: Identification of at least 100 lineage-specific splicing events across human/chimpanzee vs macaque/marmoset comparisons
- **SC-003**: Enrichment analysis produces statistically significant overlap (FDR-corrected p < 0.05) between splicing changes and regions under positive selection
- **SC-004**: At least 5 key findings validated through orthogonal datasets or independent samples if available

## Assumptions

- Public repositories contain sufficient matched RNA-seq data from cortex tissue for all four primate species with adequate sample sizes
- Reference genomes and annotations are available and of sufficient quality for human, chimpanzee, macaque, and marmoset
- phyloP conservation scores and selection metrics are available for the relevant genomic regions across primate lineages
- **Specific statistical thresholds for differential splicing identification**
Following convention in the field for comparative transcriptomics:
- Minimum ΔPSI (percent spliced-in difference): ≥ 0.1 (10%)
- Minimum read coverage per junction: ≥ 20 reads
- FDR-corrected p-value: < 0.05 (Benjamini-Hochberg)
These thresholds align with standard practice in differential splicing analysis (see rMATS and SUPPA2 default recommendations)

- **Sample size requirements per species**
Following convention in the field for comparative transcriptomics:
- Minimum: n ≥ 3 biological replicates per species
- Target power: ≥ 0.8 for detecting effect sizes |ΔPSI| ≥ 0.1
- This aligns with standard power requirements in RNA-seq differential expression/splicing studies

- **Primate species scope**
The four specified species (human, chimpanzee, macaque, marmoset) provide adequate phylogenetic breadth:
- Human: Homo sapiens (reference)
- Chimpanzee: Pan troglodytes (close evolutionary neighbor, ~6-7 MY divergence)
- Macaque: Macaca mulatta (Old World monkey, ~25-30 MY divergence)
- Marmoset: Callithrix jacchus (New World monkey, ~40 MY divergence)
This selection spans key primate lineages without unnecessary complexity. Additional species are not required to answer the research question.


## Related Work

- TODO — lit-search returned no results.
