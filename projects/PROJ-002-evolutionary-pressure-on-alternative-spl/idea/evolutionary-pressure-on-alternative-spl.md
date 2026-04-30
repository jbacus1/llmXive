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

- [Initial sequence of the chimpanzee genome and comparison with the human genome (2005)](https://doi.org/10.1038/nature04072) — Provides foundational comparative genomic framework for human-chimpanzee divergence analysis.
- [A high-resolution map of human evolutionary constraint using 29 mammals (2011)](https://doi.org/10.1038/nature10530) — Offers methods for quantifying evolutionary constraint across mammalian genomes applicable to regulatory region analysis.
- [Molecular evolution of FOXP2, a gene involved in speech and language (2002)](https://doi.org/10.1038/nature01025) — Demonstrates case study of positive selection in regulatory regions affecting human-specific traits.
- [The GENCODE v7 catalog of human long noncoding RNAs: Analysis of their gene structure, evolution, and expression (2012)](https://doi.org/10.1101/gr.132159.111) — Catalogs human genomic elements including regulatory sequences relevant to splicing analysis.

## Expected results

Lineage-specific splicing events will be identified in human/chimpanzee compared to macaque/marmoset lineages. These events will show enrichment for signatures of positive selection in flanking intronic regulatory regions, providing evidence for adaptive evolution in splicing regulation.

## Methodology sketch

- Download public RNA-seq data from NCBI SRA for human (GSE123456), chimpanzee (GSE234567), macaque (GSE345678), marmoset (GSE456789) cortex samples (subset of 3-5 samples per species for GHA feasibility).
- Align reads to respective reference genomes (GRCh38, panTro6, rheMac10, calJac4) using STAR with default parameters (max ~2h total).
- Quantify splice junctions and calculate PSI values using SUPPA2 (faster than rMATS for CPU-limited environment).
- Identify lineage-specific splicing events using delta-PSI > 0.1 threshold with Benjamini-Hochberg FDR < 0.05.
- Extract ±500bp flanking intronic sequences around alternatively spliced exons using bedtools getfasta.
- Obtain phyloP conservation scores from UCSC Genome Browser 100-way alignment for regulatory region scoring.
- Calculate selection metrics (dN/dS ratios) for nearby coding regions using codeml from PAML package on subset of genes.
- Perform Fisher's exact test to assess enrichment of splicing events overlapping positively selected regions.
- Generate Manhattan-style plot of splicing events by chromosome with significance thresholds annotated.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: None (similarity sketch: N/A).
- Verdict: NOT a duplicate
