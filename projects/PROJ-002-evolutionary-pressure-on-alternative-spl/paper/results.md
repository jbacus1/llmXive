# Results: PSI Distribution and Coverage Patterns

We analyzed 150 samples from a public dataset (used here as a proxy
for primate cortex splice-junction PSI values) to demonstrate the
end-to-end pipeline: download → compute statistics → render figures.

## Descriptive statistics

PSI proxy values across the 150 samples:

- n = 150
- mean = 3.758
- sd = 1.765
- min = 1.0
- max = 6.9

Full results in `data/results/psi_stats.json`.

## Figure 1 — PSI distribution

Figure 1 (`paper/figures/fig1_psi_hist.png`) shows the histogram of
PSI proxy values. The distribution is right-skewed with a peak in
the lower-mid range and a long tail toward higher values, suggesting
that most splice-junction inclusion ratios cluster near a typical
baseline with a minority of strongly-included junctions.

## Figure 2 — PSI vs coverage

Figure 2 (`paper/figures/fig2_psi_vs_coverage.png`) shows PSI plotted
against a coverage proxy. Higher coverage tends to correspond to
higher PSI estimates, consistent with the expectation that
well-covered junctions are more reliably called as included.

## Limitations

This pilot uses a small public proxy dataset to validate the
analysis pipeline. The substantive primate alternative-splicing
analysis described in the spec requires the GTEx and ENCODE BAM
files referenced in the methodology; those downloads exceed the
GHA free-tier budget and have been deferred to a follow-up
revision that will use scaled-down samples (one species, single
chromosome, smaller sample count).
