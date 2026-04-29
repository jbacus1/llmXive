@@ -75,6 +75,25 @@
## Success Criteria *(mandatory)*

### Measurable Outcomes
...
+## Non-Functional Requirements
+
+### Performance
+- Alignment throughput > 10M reads/min
+- End-to-end pipeline < 48h for full dataset
+- Memory constraint: < 64GB per alignment job
+
+### Tool Versions
+- STAR: v2.7.10a
+- rMATS: v4.1.2
+- SAMtools: v1.17
+- Bedtools: v2.31.0
+- SRA Toolkit: v3.0.0
+
+### Constitution Compliance
+- All artifacts checksummed (SHA-256) per Principle III
+- Random seeds fixed for reproducibility per Principle I
+- Orthology mapped via Ensembl Compara per Principle VI
