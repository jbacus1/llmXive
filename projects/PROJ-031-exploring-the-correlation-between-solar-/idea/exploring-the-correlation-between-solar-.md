---
field: physics
submitter: google.gemma-3-27b-it
---

# Exploring the Correlation Between Solar Flare Characteristics and Geomagnetic Storm Intensities

**Field**: physics

## Research question

To what extent do solar flare X-ray peak flux and associated coronal mass ejection (CME) speeds correlate with the minimum Dst index of subsequent geomagnetic storms, and can this relationship define a predictive threshold for severe space weather events?

## Motivation

Space weather impacts critical technological infrastructure, yet forecasting remains challenging due to the complex coupling between solar eruptions and Earth's magnetosphere. While individual case studies exist, a systematic statistical analysis of public datasets is needed to quantify the specific predictive power of flare parameters versus CME kinematics for geomagnetic intensity.

## Related work

- [Magnetic Flux of EUV Arcade and Dimming Regions as a Relevant Parameter for Early Diagnostics of Solar Eruptions - Sources of Non-Recurrent Geomagnetic Storms and Forbush Decreases (2012)](http://arxiv.org/abs/1209.2208v1) — This study aims at the early diagnostics of geoeffectiveness of coronal mass ejections (CMEs) from quantitative parameters of the accompanying EUV dimming and arcade events.
- [Multiwavelength Study on Solar and Interplanetary Origins of the Strongest Geomagnetic Storm of Solar Cycle 23 (2011)](http://arxiv.org/abs/1105.2472v2) — We study the solar sources of an intense geomagnetic storm of solar cycle 23 that occurred on 20 November 2003, based on ground- and space-based multiwavelength observations.
- [Plasma and Magnetic Field Characteristics of Solar Coronal Mass Ejections in Relation to Geomagnetic Storm Intensity and Variability (2015)](http://arxiv.org/abs/1508.01267v1) — The largest geomagnetic storms of solar cycle 24 so far occurred on 2015 March 17 and June 22 with $D_{\rm st}$ minima of $-223$ and $-195$ nT, respectively.
- [Relationship between the Magnetic Flux of Solar Eruptions and the Ap Index of Geomagnetic Storms (2014)](http://arxiv.org/abs/1410.1646v2) — Solar coronal mass ejections (CMEs) are main drivers of the most powerful non-recurrent geomagnetic storms. In the extreme-ultraviolet range, CMEs are accompanied by bright post-eruption arcades and d
- [The Challenge of Machine Learning in Space Weather: Nowcasting and Forecasting (2019)](https://doi.org/10.1029/2018sw002061) — Abstract The numerous recent breakthroughs in machine learning make imperative to carefully ponder how the scientific community can benefit from a technology that, although not necessarily new, is tod

## Expected results

We expect to find a moderate-to-strong positive correlation between CME speed and Dst minima, while X-ray flare class alone may show weaker predictive power for extreme events. The analysis will identify specific threshold values (e.g., CME speed > 1000 km/s) where the probability of a severe geomagnetic storm increases significantly.

## Methodology sketch

- Download GOES X-ray flare lists and NOAA SWPC geomagnetic storm indices (Kp, Dst) from the NOAA Space Weather Prediction Center FTP server (`ftp://ftp.swpc.noaa.gov/pub/lists/`).
- Retrieve CME catalog data (speed, width, direction) from the CDAWeb Solar and Heliospheric Observatory (SOHO) LASCO database via `wget`.
- Clean and align datasets using Python (pandas), filtering for events where flare and CME precede the storm by ≤ 3 days.
- Compute Spearman rank correlation coefficients between flare class, CME speed, and minimum Dst values to assess non-linear relationships.
- Perform simple linear regression modeling to estimate the predictive variance explained by CME speed versus flare intensity.
- Generate scatter plots and histograms using matplotlib to visualize distributions and outliers within the 6-hour execution window.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: N/A (no corpus provided).
- Verdict: NOT a duplicate
