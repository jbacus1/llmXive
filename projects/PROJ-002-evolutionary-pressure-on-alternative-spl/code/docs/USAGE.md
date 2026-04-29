# Usage Guide

## Pipeline Execution

The pipeline runs in three main stages:

### Stage 1: Data Acquisition
```python
from code.src.acquisition.sra_downloader import SRADownloader
from code.src.acquisition.metadata_parser import MetadataParser

parser = MetadataParser('data/metadata.yaml')
samples = parser.parse()

downloader = SRADownloader()
for sample in samples:
    downloader.download(sample)
```

### Stage 2: Alignment and Quantification
```python
from code.src.alignment.star_runner import STARRunner
from code.src.quantification.psi_calculator import PSICalculator

star = STARRunner(genome_path='/path/to/genome')
bam_files = star.align(fastq_files)

psi_calc = PSICalculator()
psi_values = psi_calc.calculate(bam_files)
```

### Stage 3: Evolutionary Analysis
```python
from code.src.analysis.phylo_extractor import PhyloExtractor
from code.src.analysis.enrichment_test import EnrichmentTest

phylo = PhyloExtractor()
conservation_scores = phylo.extract(splice_junctions, flank_bp=500)

enrichment = EnrichmentTest()
results = enrichment.run(splicing_events, conservation_scores)
```

## Configuration

### Environment Variables
```bash
export SRA_API_KEY=your_key
export GENOME_PATH=/path/to/genomes
export LOG_LEVEL=INFO
export RANDOM_SEED=42
```

### Sample Metadata Format
```yaml
samples:
  - id: SRR123456
    species: human
    tissue: cortex
    sra_accession: SRR123456
    genome: GRCh38
```

## Quality Thresholds

| Metric | Threshold | Source |
|--------|-----------|--------|
| Mapping Rate | ≥70% | SC-001 |
| ΔPSI | ≥0.1 | SC-002 |
| Junction Coverage | ≥20 reads | SC-003 |
| FDR | <0.05 | SC-002, SC-003 |

## Output Files

- `data/aligned/*.bam` - Aligned reads
- `data/quantification/psi_values.csv` - PSI measurements
- `data/analysis/differential_splicing.csv` - Differential events
- `data/analysis/selection_metrics.csv` - Conservation scores
