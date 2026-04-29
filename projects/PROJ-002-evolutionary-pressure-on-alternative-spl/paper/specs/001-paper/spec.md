# Feature Specification: Evolutionary Pressure on Alternative Splicing in Comparative Genomics

**Feature Branch**: `paper-evolutionary-pressure-alternative-splicing`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: Research-stage artifacts for PROJ-002 evolutionary pressure analysis

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reproducibility Verification (Priority: P1)

A peer reviewer can reproduce the primary splicing quantification results from the raw SRA data using the documented pipeline and tool versions.

**Why this priority**: Reproducibility is the foundation of scientific credibility. Without this, no other claims in the paper can be validated.

**Independent Test**: Reviewer can execute the pipeline script with fixed random seeds and generate identical alignment statistics (STAR throughput > 10M reads/min) and rMATS splicing event counts within acceptable variance.

**Acceptance Scenarios**:

1. **Given** raw FASTQ files from SRA and the pinned tool versions (STAR v2.7.10a, rMATS v4.1.2), **When** reviewer runs the alignment and splicing quantification pipeline, **Then** the output checksums match the checksums in the paper's supplementary materials (per Principle III)
2. **Given** the fixed random seeds documented in Methods, **When** reviewer reruns the pipeline, **Then** alignment and splicing quantification results match within 0.1% variance
3. **Given** the memory constraints (< 64GB per alignment job), **When** reviewer runs on equivalent hardware, **Then** the pipeline completes without exceeding memory limits

---

### User Story 2 - Methods Transparency (Priority: P1)

A student with basic bioinformatics knowledge can follow the Methods section without requiring prior context about the project setup.

**Why this priority**: Educational value and broader accessibility of the research. Enables follow-up researchers to build upon this work.

**Independent Test**: Student can independently identify all tool versions, data sources, and processing steps from the Methods section alone.

**Acceptance Scenarios**:

1. **Given** only the Methods section, **When** student reads the pipeline description, **Then** they can identify STAR v2.7.10a, rMATS v4.1.2, SAMtools v1.17, Bedtools v2.31.0, and SRA Toolkit v3.0.0
2. **Given** the orthology mapping approach, **When** student reviews the Methods, **Then** they can trace that Ensembl Compara was used per Principle VI
3. **Given** the end-to-end pipeline documentation, **When** student follows the workflow, **Then** they understand the < 48h completion constraint for the full dataset

---

### User Story 3 - Claims Verification (Priority: P2)

A reviewer can locate every cited fact and verify each inferential claim about evolutionary pressure on alternative splicing against the supporting data.

**Why this priority**: Ensures the paper's scientific claims are evidence-based and not overinterpreted.

**Independent Test**: Reviewer can trace each claim in the Results/Discussion to a specific figure and underlying data file.

**Acceptance Scenarios**:

1. **Given** a claim about differential splicing between species, **When** reviewer examines the corresponding figure, **Then** the figure displays data from actual rMATS output files in the `data/` directory
2. **Given** a claim about conservation of splicing events, **When** reviewer checks the orthology mapping, **Then** they can verify Ensembl Compara was used as documented
3. **Given** any statistical claim in Results, **When** reviewer examines the raw data, **Then** they can confirm the statistics were computed on checksummed artifacts per Principle III

---

### User Story 4 - Comparative Analysis Clarity (Priority: P2)

A follow-up researcher can understand the comparative framework between species used to assess evolutionary pressure.

**Why this priority**: Enables meta-analysis and extension of the work to additional species or splicing event types.

**Independent Test**: Researcher can identify which species were compared, what splicing event types were analyzed, and how orthology was established.

**Acceptance Scenarios**:

1. **Given** the Results section, **When** researcher reviews the species comparison, **Then** they can identify the exact species pairs analyzed
2. **Given** the splicing event analysis, **When** researcher examines the Methods, **Then** they understand which rMATS event types were included (exon skipping, mutually exclusive exons, etc.)
3. **Given** the evolutionary pressure interpretation, **When** researcher checks the Discussion, **Then** they can distinguish between observed splicing differences and inferred evolutionary selection

---

### User Story 5 - Supplementary Materials Completeness (Priority: P3)

A student can access all supplementary tables and figures needed to understand the full scope of the analysis.

**Why this priority**: Ensures complete transparency and supports educational use of the paper.

**Independent Test**: Student can locate and understand all supplementary materials referenced in the main text.

**Acceptance Scenarios**:

1. **Given** a figure reference in the main text, **When** student locates the supplementary material, **Then** they can identify the corresponding data source
2. **Given** a table of splicing events, **When** student examines the supplementary file, **Then** they understand the filtering criteria used
3. **Given** the tool version documentation, **When** student checks supplementary materials, **Then** they can verify all versions match the code/requirements.txt

---

### Edge Cases

- What happens when a figure's data turns out to be ambiguous between evolutionary pressure and technical artifact (e.g., batch effects in SRA data)?
- How does the paper handle cases where orthology mapping fails for certain genes, potentially biasing comparative analysis?
- What if the proofreader flags repeated content between Methods and Results sections?
- What happens if STAR alignment throughput falls below 10M reads/min threshold for certain samples?
- How are edge cases handled when rMATS fails to detect splicing events for lowly-expressed genes?

---

## Required Sections

- **Abstract**: Summary of evolutionary pressure findings on alternative splicing with key quantitative results
- **Introduction**: Background on alternative splicing, evolutionary conservation, and research questions
- **Methods**: Detailed pipeline description including STAR v2.7.10a alignment, rMATS v4.1.2 splicing quantification, orthology mapping via Ensembl Compara
- **Results**: Differential splicing analysis across species, conservation patterns, statistical significance
- **Discussion**: Interpretation of evolutionary pressure evidence, limitations, future directions
- **References**: All cited literature including tool documentation and prior splicing studies

---

## Required Figures

1. **Figure 1**: Pipeline overview diagram showing SRA data → STAR alignment → rMATS splicing quantification → comparative analysis (Purpose: Illustrate end-to-end workflow; Source: Methods section and code structure)

2. **Figure 2**: Alignment statistics across samples showing STAR throughput and memory usage (Purpose: Demonstrate pipeline performance meets > 10M reads/min constraint; Source: STAR log files in `data/`)

3. **Figure 3**: Splicing event distribution by type (exon skipping, mutually exclusive exons, alternative 5'/3' splice sites) (Purpose: Show rMATS quantification coverage; Source: rMATS output files in `data/`)

4. **Figure 4**: Comparative splicing conservation heatmap across species pairs (Purpose: Visualize evolutionary pressure patterns; Source: Orthology-mapped splicing event data via Ensembl Compara)

5. **Figure 5**: Differential splicing events with statistical significance (Purpose: Highlight candidate genes under evolutionary selection; Source: rMATS statistical output in `data/`)

---

## Required Claims

1. **Claim 1**: Alternative splicing patterns show significant conservation across orthologous genes in compared species (traceable to Figure 4, rMATS orthology-mapped data)

2. **Claim 2**: Certain splicing event types exhibit stronger evolutionary pressure signals than others (traceable to Figure 3, Figure 5, rMATS event-type analysis)

3. **Claim 3**: The pipeline achieves reproducible results within 0.1% variance when executed with fixed random seeds (traceable to alignment statistics, checksum verification per Principle III)

4. **Claim 4**: Orthology mapping via Ensembl Compara enables reliable cross-species splicing event comparison (traceable to Methods section, orthology mapping documentation)

5. **Claim 5**: The full dataset analysis completes within the 48-hour constraint using < 64GB memory per alignment job (traceable to pipeline performance logs)

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Paper MUST include all required sections (Abstract, Introduction, Methods, Results, Discussion, References) with minimum word counts per section
- **FR-002**: Paper MUST document all tool versions (STAR v2.7.10a, rMATS v4.1.2, SAMtools v1.17, Bedtools v2.31.0, SRA Toolkit v3.0.0) in Methods
- **FR-003**: Paper MUST include all five required figures with captions that reference their data sources in `data/`
- **FR-004**: Paper MUST provide checksums (SHA-256) for all key artifacts to enable reproducibility verification per Principle III
- **FR-005**: Paper MUST explicitly state random seeds used for pipeline reproducibility per Principle I
- **FR-006**: Paper MUST trace each inferential claim to specific figures and data files in Results/Discussion
- **FR-007**: Paper MUST include supplementary materials with complete splicing event tables and statistical details

### Key Entities *(include if feature involves data)*

- **Splicing Event**: Quantified alternative splicing event with type, coordinates, and statistical metrics from rMATS
- **Orthologous Gene**: Gene pair across species mapped via Ensembl Compara for comparative analysis
- **Alignment Job**: Single STAR alignment process with throughput and memory constraints
- **Dataset**: Complete SRA-derived RNA-seq collection across all species analyzed

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All five required figures are present with captions that reference specific data files in `data/`
- **SC-002**: All five required claims are traceable to supporting evidence (figures or tables) in the paper
- **SC-003**: Methods section contains complete tool version information matching code/requirements.txt
- **SC-004**: Pipeline reproducibility is verifiable via checksums and documented random seeds
- **SC-005**: No more than 3 `[NEEDS CLARIFICATION]` markers remain after Paper-Clarifier review

---

## Assumptions

- Researchers accessing the paper have access to the SRA data referenced in the methods
- The orthology mapping via Ensembl Compara is complete for all genes analyzed (may have Orthology mapping via Ensembl Compara was performed for all genes included in the comparative analysis (coverage percentage to be confirmed from research-stage artifacts).)
- The rMATS output files in `data/` contain all splicing events analyzed in the Results section
- The code/requirements.txt accurately reflects the tool versions used in the research pipeline
- _(Resolved by default; LLM clarifier could not pin a value: Exact species pairs analyzed not specified in research artifacts - will need confirmation from research-plan)_
- _(Resolved by default; LLM clarifier could not pin a value: Specific splicing event types analyzed by rMATS not enumerated - will need confirmation from research-tasks)_

---

## Clarification Items for Paper-Clarifier

1. Specific species pairs analyzed for comparative splicing pressure require confirmation from research-plan artifacts (see User Story 4 acceptance scenarios).
2. rMATS splicing event types analyzed include exon skipping, mutually exclusive exons, alternative 5'/3' splice sites, and retained intron (to be enumerated from research-tasks artifacts).
3. Expected orthology mapping coverage percentage via Ensembl Compara requires confirmation from research-stage artifacts.
