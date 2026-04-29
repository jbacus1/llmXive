# Pipeline Documentation

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SRA Downloader│───▶│  STAR Alignment │───▶│   PSI Calculator│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                        ┌─────────────────┐    ┌─────────────────┐
                        │   Quality Ctrl  │    │Diff Splicing    │
                        └─────────────────┘    └─────────────────┘
                                                      │
                                                      ▼
                                              ┌─────────────────┐
                                              │Phylo Extraction │
                                              └─────────────────┘
                                                      │
                                                      ▼
                                              ┌─────────────────┐
                                              │ Enrichment Test │
                                              └─────────────────┘
```

## Data Flow

1. **Input**: SRA accession numbers from metadata.yaml
2. **Acquisition**: Download FASTQ files from SRA
3. **Alignment**: Map reads to species-specific reference genome
4. **QC**: Validate mapping rate ≥70%
5. **Quantification**: Calculate PSI values per splice junction
6. **Differential Analysis**: Compare PSI across lineages
7. **Evolutionary Analysis**: Extract conservation scores
8. **Enrichment**: Test for selection pressure
9. **Output**: Differential splicing events with selection metrics

## State Management

All intermediate and final outputs are tracked in SQLite database (`state/projects/`). Checksums are computed for all data files to ensure reproducibility.

## Logging

Logs are written to `logs/pipeline.log` with configurable levels (DEBUG, INFO, WARNING, ERROR).

## Error Handling

- Failed downloads are retried up to 3 times
- Low mapping rate samples are flagged and logged
- Missing phyloP scores are handled with median imputation
- All errors are logged with full stack traces

## Reproducibility

- Random seeds are set via config
- All data files have SHA256 checksums
- Pipeline version is recorded in metadata
- Full audit trail in `state/projects/`