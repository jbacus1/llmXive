"""
Contract for RNA-seq sample data entities.

Defines the schema and validation rules for RNA-seq samples
across human, chimpanzee, macaque, and marmoset species.
"""
from dataclasses import dataclass
from typing import Optional, Literal
from enum import Enum

class Species(Enum):
    HUMAN = "human"
    CHIMPANZEE = "chimpanzee"
    MACAQUE = "macaque"
    MARMOSET = "marmoset"

class TissueType(Enum):
    CORTEX = "cortex"

@dataclass
class RNASeqSampleContract:
    """
    Contract for RNA-seq sample metadata and properties.

    Attributes:
        sample_id: Unique identifier for the sample
        species: Organism species (must be one of the supported primates)
        tissue_type: Tissue type (currently only cortex supported)
        sra_accession: SRA database accession number
        fastq_path: Path to raw FASTQ files
        bam_path: Path to aligned BAM files (after processing)
        sequencing_platform: Sequencing platform identifier
        read_length: Read length in base pairs
        is_paired: Whether reads are paired-end
    """
    sample_id: str
    species: Species
    tissue_type: TissueType
    sra_accession: str
    fastq_path: Optional[str] = None
    bam_path: Optional[str] = None
    sequencing_platform: Optional[str] = None
    read_length: Optional[int] = None
    is_paired: bool = True

    def __post_init__(self):
        """Validate sample contract after initialization."""
        if not self.sample_id:
            raise ValueError("sample_id cannot be empty")
        if not self.sra_accession:
            raise ValueError("sra_accession cannot be empty")

    def validate(self) -> bool:
        """Validate all contract requirements."""
        return all([
            bool(self.sample_id),
            self.species in Species,
            self.tissue_type in TissueType,
            bool(self.sra_accession),
        ])
