--- a/spec.md
+++ b/spec.md
@@ -95,7 +95,7 @@
 - **FR-009**: System MUST define Synthetic anomaly injection parameters:
 - Mean shift: 2.5 standard deviations from baseline mean
 - Variance spike: 3x baseline variance
 - Duration: 5-15 consecutive time points (5-10% of window length)
 
 Rationale: These magnitudes follow standard practice in anomaly 
 detection research where anomalies must be detectable but not 
 trivial. This represents the community convention for synthetic 
 anomaly generation in time series benchmarking.
- for consistent testing.
