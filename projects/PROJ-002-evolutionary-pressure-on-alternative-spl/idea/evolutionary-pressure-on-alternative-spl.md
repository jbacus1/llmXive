---
field: biology
keywords: [biology]
submitter: system:brainstorm-seed
---

# Evolutionary Pressure on Alternative Splicing in Primates

**Field**: biology

## Research question

To what extent does alternative splicing divergence in primate cortex correlate with positive selection on splicing regulatory elements?

## Motivation

Alternative splicing significantly increases proteomic complexity, yet the evolutionary drivers of splicing divergence across primates remain poorly understood. This study addresses the gap in understanding lineage-specific splicing regulation by linking transcriptomic changes to genomic signatures of selection.

## Related work

- TODO — lit-search returned no results.

## Expected results

Lineage-specific splicing events will be identified in human/chimpanzee compared to macaque/marmoset lineages. These events will show enrichment for signatures of positive selection in flanking intronic regulatory regions, providing evidence for adaptive evolution in splicing regulation.

## Methodology sketch

- Acquire matched RNA-seq data from cortex tissue for human, chimpanzee, macaque, and marmoset from public repositories.
- Align raw reads to respective reference genomes using STAR.
- Quantify splice junction usage and percent spliced in (PSI) values with rMATS or SUPPA2.
- Identify differentially spliced events between lineages using a fixed effect model.
- Extract flanking intronic sequences (±500bp) around alternatively spliced exons.
- Calculate evolutionary conservation scores (phyloP) and selection metrics for regulatory regions.
- Perform enrichment analysis to test if splicing changes overlap with regions under positive selection.
- Apply Benjamini-Hochberg FDR correction for multiple hypothesis testing across all events.
- Validate key findings using orthogonal datasets or independent samples if available.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: None (similarity sketch: N/A).
- Verdict: NOT a duplicate
