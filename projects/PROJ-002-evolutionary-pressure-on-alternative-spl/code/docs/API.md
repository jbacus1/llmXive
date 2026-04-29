# API Reference

## Models

### RNASeqSample
```python
class RNASeqSample:
    def __init__(self, id: str, species: str, tissue: str, sra_accession: str)
    def validate(self) -> bool
    def to_dict(self) -> dict
```

### SpliceJunction
```python
class SpliceJunction:
    def __init__(self, chrom: str, start: int, end: int, strand: str)
    def get_flanking_region(self, flank_bp: int = 500) -> str
    def calculate_psi(self, inclusion_reads: int, exclusion_reads: int) -> float
```

### DifferentialSplicingEvent
```python
class DifferentialSplicingEvent:
    def __init__(self, junction: SpliceJunction, delta_psi: float, p_value: float)
    def passes_threshold(self, min_delta_psi: float = 0.1, min_coverage: int = 20) -> bool
```

## Acquisition Module

### SRADownloader
```python
class SRADownloader:
    def __init__(self, api_key: str = None)
    def download(self, sample: RNASeqSample, output_dir: str) -> Path
    def validate_download(self, fastq_path: Path) -> bool
```

### MetadataParser
```python
class MetadataParser:
    def __init__(self, metadata_path: str)
    def parse(self) -> List[RNASeqSample]
    def validate_schema(self) -> bool
```

## Alignment Module

### STARRunner
```python
class STARRunner:
    def __init__(self, genome_path: str, n_threads: int = 8)
    def align(self, fastq_files: List[Path]) -> List[Path]
    def get_mapping_stats(self, bam_path: Path) -> dict
```

### QualityControl
```python
class QualityControl:
    def __init__(self, min_mapping_rate: float = 0.70)
    def validate(self, bam_path: Path) -> bool
    def generate_report(self, bam_path: Path) -> str
```

## Quantification Module

### PSICalculator
```python
class PSICalculator:
    def __init__(self, min_coverage: int = 20)
    def calculate(self, bam_files: List[Path]) -> DataFrame
    def filter_by_coverage(self, psi_df: DataFrame) -> DataFrame
```

### DifferentialSplicing
```python
class DifferentialSplicing:
    def __init__(self, min_delta_psi: float = 0.1)
    def analyze(self, psi_df: DataFrame, groups: List[str]) -> DataFrame
    def apply_fdr_correction(self, df: DataFrame) -> DataFrame
```

## Analysis Module

### PhyloExtractor
```python
class PhyloExtractor:
    def __init__(self, phyloP_path: str)
    def extract(self, junction: SpliceJunction, flank_bp: int = 500) -> Dict
    def handle_missing_data(self, scores: List[float]) -> float
```

### EnrichmentTest
```python
class EnrichmentTest:
    def __init__(self, fdr_threshold: float = 0.05)
    def run(self, events: List[DifferentialSplicingEvent], 
            conservation_scores: Dict) -> DataFrame
```

## Utilities

### Config
```python
class Config:
    @classmethod
    def load(cls, path: str) -> Dict
    @classmethod
    def validate(cls, config: Dict) -> bool
```

### Checksum
```python
class Checksum:
    @staticmethod
    def compute_sha256(file_path: Path) -> str
    @staticmethod
    def verify(file_path: Path, expected: str) -> bool
```
