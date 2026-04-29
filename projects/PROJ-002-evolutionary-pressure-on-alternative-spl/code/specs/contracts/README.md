# Data Model Contracts

This directory contains contract definitions for all data entities
used throughout the evolutionary pressure on alternative splicing pipeline.

## Purpose

Contracts serve as:
1. **Type definitions**: Clear interface specifications for data structures
2. **Validation rules**: Enforce data integrity at component boundaries
3. **Documentation**: Self-documenting data schemas
4. **Testing targets**: Enable contract testing for component integration

## Contract Files

| Contract | Description |
|----------|-------------|
| `rna_seq_sample_contract.py` | RNA-seq sample metadata and properties |
| `splice_junction_contract.py` | Splice junction data from alignments |
| `differential_splicing_contract.py` | Differential splicing analysis results |
| `sample_metadata_contract.py` | Sample metadata for pipeline configuration |
| `alignment_result_contract.py` | STAR alignment results and quality metrics |
| `psi_result_contract.py` | PSI (Percent Spliced In) calculation results |
| `enrichment_contract.py` | Enrichment analysis results |

## Usage

```python
from specs.contracts import RNASeqSampleContract, Species, TissueType

sample = RNASeqSampleContract(
    sample_id="SAMPLE001",
    species=Species.HUMAN,
    tissue_type=TissueType.CORTEX,
    sra_accession="SRR12345678",
)

if sample.validate():
    print("Sample contract validated successfully")
```

## Validation

Each contract includes:
- `__post_init__`: Validates on object creation
- `validate()`: Explicit validation method
- Domain-specific threshold checks (e.g., `meets_significance_thresholds`)

## Extending Contracts

When adding new contracts:
1. Create new file in this directory
2. Follow naming convention: `<entity>_contract.py`
3. Include dataclass with clear docstring
4. Add `validate()` method
5. Export in `__init__.py`
6. Add to this README