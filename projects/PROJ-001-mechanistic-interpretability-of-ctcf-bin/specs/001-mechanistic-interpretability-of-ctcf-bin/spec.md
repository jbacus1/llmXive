--- a/spec.md
+++ b/spec.md
@@ -35,7 +35,7 @@
  1. **Given** valid ENCODE data paths for 10+ cell types, **When** the ingestion script runs, **Then** data is normalized and aligned to a common genomic coordinate system.
  2. **Given** missing data for a specific cell type, **When** the ingestion script runs, **Then** the system logs a warning but continues processing available cell types.
- 3. **Given** mismatched sequence lengths, **When** preprocessing occurs, **Then** sequences are padded or truncated to a fixed context window size.
+ 3. **Given** mismatched sequence lengths, **When** preprocessing occurs, **Then** sequences are padded or truncated to a fixed context window size of 2048bp.
