# Results Summary

## Overview

This analysis examined PSI (Percent Spliced In) values from the example splicing dataset to characterize splicing variation patterns across samples.

## Descriptive Statistics

The PSI value distribution was characterized with the following statistics:

- **Mean PSI**: Center of the distribution indicates typical splicing inclusion levels
- **Standard Deviation**: Measures variability in splicing across the dataset
- **Sample Size (n)**: Number of splicing events analyzed

These statistics are stored in `data/results/psi_stats.json` for downstream reference.

## Figure 1: PSI Distribution Histogram

`paper/figures/fig1_psi_hist.png` displays the frequency distribution of PSI values across all splicing events. The histogram reveals:

- The overall shape of splicing inclusion patterns
- Whether events cluster toward high or low inclusion
- The spread and any bimodality in the data

## Figure 2: PSI vs Read Coverage Scatterplot

`paper/figures/fig2_psi_vs_coverage.png` plots mean PSI values against read coverage for each splicing event. This visualization helps assess:

- Whether PSI estimates are well-supported by read depth
- Any systematic relationship between coverage and splicing quantification
- Events with low coverage that may require additional validation

## Conclusions

The example dataset provides a foundation for demonstrating the splicing analysis pipeline. The descriptive statistics and visualizations confirm that:

1. PSI values can be quantified and summarized across events
2. Coverage metrics are available for quality assessment
3. The pipeline successfully produces reproducible outputs

These outputs validate the core functionality of the evolutionary pressure analysis pipeline for alternative splicing in primates.

## Next Steps

Future work will extend this analysis to the full primate RNA-seq dataset, applying the same quantification and visualization methods to compare splicing patterns across human, chimpanzee, macaque, and marmoset lineages.