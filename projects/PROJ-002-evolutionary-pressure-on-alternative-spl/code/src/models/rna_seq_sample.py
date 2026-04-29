"""
RNA-seq Sample Entity Model

This module defines the core data model for RNA-seq samples in the
evolutionary pressure on alternative splicing analysis pipeline.

Supported species: human, chimpanzee, macaque, marmoset
Tissue type: cortex (primary)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from pathlib import Path
import hashlib
from datetime import datetime

from utils.config import get_config


class Species(Enum):
    """Supported primate species for analysis."""
    HUMAN = "human"
    CHIMPANZEE = "chimpanzee"
    MACAQUE = "macaque"
    MARMOSET = "marmoset"

@classmethod
def from_string(cls, species_str: str) -> "Species":
    """Convert string to Species enum (case-insensitive)."""
    mapping = {
        "human": cls.HUMAN,
        "chimpanzee": cls.CHIMPANZEE,
        "macaque": cls.MACAQUE,
        "marmoset": cls.MARMOSET,
        "pan_troglodytes": cls.CHIMPANZEE,
        "macaca_mulatta": cls.MACAQUE,
        "callithrix_jacchus": cls.MARMOSET,
    }
    species_lower = species_str.lower()
    if species_lower not in mapping:
        raise ValueError(f"Unsupported species: {species_str}")
    return mapping[species_lower]

class TissueType(Enum):
    """Supported tissue types."""
    CORTEX = "cortex"
    PREFRONTAL_CORTEX = "prefrontal_cortex"
    HIPPOCAMPUS = "hippocampus"

@dataclass
class RNASeqSample:
    """
    Entity representing an RNA-seq sample from primate cortex tissue.
    
    Attributes:
        sample_id: Unique identifier for this sample (T### format)
        species: Primate species (human, chimpanzee, macaque, marmoset)
        tissue_type: Type of tissue sampled
        sra_accession: SRA database accession number (e.g., SRR1234567)
        srun_id: SRA run identifier
        biosample_id: NCBI BioSample identifier
        fastq_files: List of FASTQ file paths (paired-end: [R1, R2])
        bam_file: Path to aligned BAM file after STAR alignment
        metadata: Additional sample metadata
        created_at: Timestamp when sample record was created
        checksum: SHA-256 checksum of sample data for integrity verification
    """
    
    sample_id: str
    species: Species
    tissue_type: TissueType = TissueType.CORTEX
    sra_accession: Optional[str] = None
    srun_id: Optional[str] = None
    biosample_id: Optional[str] = None
    fastq_files: List[str] = field(default_factory=list)
    bam_file: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    checksum: Optional[str] = None
    
    def __post_init__(self):
        """Validate sample data after initialization."""
        self._validate_sample_id()
        self._validate_species()
        self._validate_tissue_type()
    
    def _validate_sample_id(self):
        """Validate sample ID format."""
        if not self.sample_id:
            raise ValueError("sample_id is required")
        if not isinstance(self.sample_id, str):
            raise TypeError("sample_id must be a string")
    
    def _validate_species(self):
        """Ensure species is a valid Species enum."""
        if not isinstance(self.species, Species):
            raise TypeError("species must be a Species enum instance")
    
    def _validate_tissue_type(self):
        """Ensure tissue_type is a valid TissueType enum."""
        if not isinstance(self.tissue_type, TissueType):
            raise TypeError("tissue_type must be a TissueType enum instance")
    
    @property
    def is_paired_end(self) -> bool:
        """Check if sample has paired-end sequencing."""
        return len(self.fastq_files) == 2
    
    @property
    def fastq_r1(self) -> Optional[str]:
        """Get R1 FASTQ file path."""
        return self.fastq_files[0] if self.fastq_files else None
    
    @property
    def fastq_r2(self) -> Optional[str]:
        """Get R2 FASTQ file path."""
        return self.fastq_files[1] if len(self.fastq_files) > 1 else None
    
    def compute_checksum(self, content: bytes) -> str:
        """Compute SHA-256 checksum for data integrity."""
        self.checksum = hashlib.sha256(content).hexdigest()
        return self.checksum
    
    def update_fastq_files(self, files: List[str]) -> None:
        """Update FASTQ file paths."""
        if len(files) > 2:
            raise ValueError("Expected 1 or 2 FASTQ files (single or paired-end)")
        self.fastq_files = [str(Path(f).resolve()) for f in files]
    
    def set_bam_file(self, bam_path: str) -> None:
        """Set aligned BAM file path after STAR alignment."""
        self.bam_file = str(Path(bam_path).resolve())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert sample to dictionary representation."""
        return {
            "sample_id": self.sample_id,
            "species": self.species.value,
            "tissue_type": self.tissue_type.value,
            "sra_accession": self.sra_accession,
            "srun_id": self.srun_id,
            "biosample_id": self.biosample_id,
            "fastq_files": self.fastq_files,
            "bam_file": self.bam_file,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "checksum": self.checksum,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RNASeqSample":
        """Create RNASeqSample from dictionary."""
        return cls(
            sample_id=data["sample_id"],
            species=Species(data["species"]),
            tissue_type=TissueType(data.get("tissue_type", "cortex")),
            sra_accession=data.get("sra_accession"),
            srun_id=data.get("srun_id"),
            biosample_id=data.get("biosample_id"),
            fastq_files=data.get("fastq_files", []),
            bam_file=data.get("bam_file"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.utcnow(),
            checksum=data.get("checksum"),
        )
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"RNASeqSample(id={self.sample_id}, "
            f"species={self.species.value}, "
            f"tissue={self.tissue_type.value}, "
            f"sra={self.sra_accession})"
        )
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on sample_id and checksum."""
        if not isinstance(other, RNASeqSample):
            return NotImplemented
        return self.sample_id == other.sample_id and self.checksum == other.checksum

# Factory functions for common use cases

def create_human_cortex_sample(
    sample_id: str,
    sra_accession: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> RNASeqSample:
    """Create a human cortex RNA-seq sample."""
    return RNASeqSample(
        sample_id=sample_id,
        species=Species.HUMAN,
        tissue_type=TissueType.CORTEX,
        sra_accession=sra_accession,
        metadata=metadata or {},
    )

def create_sample_from_srun(
    sample_id: str,
    srun_id: str,
    species_str: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> RNASeqSample:
    """Create a sample from SRA run identifier."""
    return RNASeqSample(
        sample_id=sample_id,
        species=Species.from_string(species_str),
        srun_id=srun_id,
        metadata=metadata or {},
    )