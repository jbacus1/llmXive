"""
Splice Junction Entity Model

This module defines the SpliceJunction entity model for representing
alternative splicing junctions in RNA-seq data analysis.

Supports standard rMATS junction types:
- SE: Skipped Exon
- A5SS: Alternative 5' Splice Site
- A3SS: Alternative 3' Splice Site
- MXE: Mutually Exclusive Exons
- RI: Retained Intron
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class JunctionType(Enum):
    """Standard rMATS splice junction types."""
    SE = "SE"           # Skipped Exon
    A5SS = "A5SS"       # Alternative 5' Splice Site
    A3SS = "A3SS"       # Alternative 3' Splice Site
    MXE = "MXE"         # Mutually Exclusive Exons
    RI = "RI"           # Retained Intron

    @classmethod
    def from_string(cls, value: str) -> "JunctionType":
        """Convert string to JunctionType, handling common variations."""
        value = value.upper().strip()
        mapping = {
            "SKIPPED_EXON": cls.SE,
            "SE": cls.SE,
            "A5": cls.A5SS,
            "A5SS": cls.A5SS,
            "ALTERNATIVE_5": cls.A5SS,
            "A3": cls.A3SS,
            "A3SS": cls.A3SS,
            "ALTERNATIVE_3": cls.A3SS,
            "MXE": cls.MXE,
            "MUTUALLY_EXCLUSIVE": cls.MXE,
            "RI": cls.RI,
            "RETAINED_INTRON": cls.RI,
        }
        if value not in mapping:
            raise ValueError(f"Unknown junction type: {value}")
        return mapping[value]


class Species(Enum):
    """Supported primate species for this project."""
    HUMAN = "human"
    CHIMPANZEE = "chimpanzee"
    MACAQUE = "macaque"
    MARMOSET = "marmoset"

    @classmethod
    def from_string(cls, value: str) -> "Species":
        """Convert string to Species, handling common variations."""
        value = value.lower().strip()
        mapping = {
            "human": cls.HUMAN,
            "homo_sapiens": cls.HUMAN,
            "hs": cls.HUMAN,
            "chimpanzee": cls.CHIMPANZEE,
            "pan_troglodytes": cls.CHIMPANZEE,
            "pt": cls.CHIMPANZEE,
            "macaque": cls.MACAQUE,
            "rhesus_macaque": cls.MACAQUE,
            "macaca_mulatta": cls.MACAQUE,
            "mm": cls.MACAQUE,
            "marmoset": cls.MARMOSET,
            "callithrix_jacchus": cls.MARMOSET,
            "cj": cls.MARMOSET,
        }
        if value not in mapping:
            raise ValueError(f"Unknown species: {value}")
        return mapping[value]


@dataclass
class SpliceJunction:
    """
    Entity model representing a single splice junction from RNA-seq data.

    Attributes:
        junction_id: Unique identifier for this junction instance
        event_id: ID of the splicing event this junction belongs to
        species: Primate species of origin
        sample_id: Sample identifier
        chromosome: Chromosome name (e.g., 'chr1', 'chrX')
        start: 0-based start coordinate of the junction
        end: 0-based end coordinate of the junction
        strand: Strand orientation ('+', '-', or '.')
        junction_type: Type of alternative splicing event
        exon_number: Exon number within the gene (optional)
        gene_id: Ensembl or gene symbol identifier
        gene_name: Human-readable gene name
        inclusion_reads: Number of reads supporting inclusion
        exclusion_reads: Number of reads supporting exclusion
        total_reads: Total reads covering this junction
        psi_value: Percent Spliced In value (0.0 to 1.0), optional
        quality_score: Quality metric for junction confidence
        created_at: Timestamp when this junction was created/processed
        metadata: Additional free-form metadata
    """

    # Core identifiers
    junction_id: str
    event_id: str
    species: Species
    sample_id: str

    # Genomic coordinates
    chromosome: str
    start: int
    end: int
    strand: str

    # Junction classification
    junction_type: JunctionType
    exon_number: Optional[int] = None
    gene_id: Optional[str] = None
    gene_name: Optional[str] = None

    # Read counts and quantification
    inclusion_reads: int = 0
    exclusion_reads: int = 0
    total_reads: int = 0
    psi_value: Optional[float] = None

    # Quality metrics
    quality_score: float = 1.0

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate junction after initialization."""
        self._validate_coordinates()
        self._validate_strand()
        self._validate_read_counts()
        self._validate_psi()

    def _validate_coordinates(self):
        """Ensure start < end for valid genomic coordinates."""
        if self.start < 0:
            raise ValueError(f"Invalid start coordinate: {self.start}")
        if self.end < 0:
            raise ValueError(f"Invalid end coordinate: {self.end}")
        if self.start >= self.end:
            raise ValueError(
                f"Invalid coordinates: start ({self.start}) >= end ({self.end})"
            )

    def _validate_strand(self):
        """Ensure strand is a valid value."""
        valid_strands = {"+", "-", "."}
        if self.strand not in valid_strands:
            raise ValueError(
                f"Invalid strand: {self.strand}. Must be one of {valid_strands}"
            )

    def _validate_read_counts(self):
        """Ensure read counts are non-negative."""
        if self.inclusion_reads < 0:
            raise ValueError(
                f"Invalid inclusion_reads: {self.inclusion_reads}"
            )
        if self.exclusion_reads < 0:
            raise ValueError(
                f"Invalid exclusion_reads: {self.exclusion_reads}"
            )
        if self.total_reads < 0:
            raise ValueError(f"Invalid total_reads: {self.total_reads}")

    def _validate_psi(self):
        """Ensure PSI value is in valid range if provided."""
        if self.psi_value is not None:
            if not (0.0 <= self.psi_value <= 1.0):
                raise ValueError(
                    f"Invalid psi_value: {self.psi_value}. Must be between 0 and 1"
                )

    @property
    def junction_length(self) -> int:
        """Calculate junction length in base pairs."""
        return self.end - self.start

    @property
    def junction_key(self) -> str:
        """Generate a unique key for this junction location."""
        return f"{self.chromosome}:{self.start}-{self.end}:{self.strand}"

    @property
    def coverage(self) -> int:
        """Total junction coverage (inclusion + exclusion reads)."""
        return self.inclusion_reads + self.exclusion_reads

    @property
    def is_significant(self, min_coverage: int = 20) -> bool:
        """
        Check if junction meets minimum coverage threshold.

        Args:
            min_coverage: Minimum read coverage threshold (default: 20)

        Returns:
            True if junction meets coverage requirements
        """
        return self.coverage >= min_coverage

    def to_dict(self) -> dict:
        """Convert junction to dictionary representation."""
        return {
            "junction_id": self.junction_id,
            "event_id": self.event_id,
            "species": self.species.value,
            "sample_id": self.sample_id,
            "chromosome": self.chromosome,
            "start": self.start,
            "end": self.end,
            "strand": self.strand,
            "junction_type": self.junction_type.value,
            "exon_number": self.exon_number,
            "gene_id": self.gene_id,
            "gene_name": self.gene_name,
            "inclusion_reads": self.inclusion_reads,
            "exclusion_reads": self.exclusion_reads,
            "total_reads": self.total_reads,
            "psi_value": self.psi_value,
            "quality_score": self.quality_score,
            "coverage": self.coverage,
            "junction_length": self.junction_length,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SpliceJunction":
        """Create SpliceJunction from dictionary."""
        return cls(
            junction_id=data["junction_id"],
            event_id=data["event_id"],
            species=Species.from_string(data["species"]),
            sample_id=data["sample_id"],
            chromosome=data["chromosome"],
            start=data["start"],
            end=data["end"],
            strand=data["strand"],
            junction_type=JunctionType.from_string(data["junction_type"]),
            exon_number=data.get("exon_number"),
            gene_id=data.get("gene_id"),
            gene_name=data.get("gene_name"),
            inclusion_reads=data.get("inclusion_reads", 0),
            exclusion_reads=data.get("exclusion_reads", 0),
            total_reads=data.get("total_reads", 0),
            psi_value=data.get("psi_value"),
            quality_score=data.get("quality_score", 1.0),
            created_at=datetime.fromisoformat(data.get("created_at"))
            if data.get("created_at")
            else datetime.utcnow(),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        """String representation of the junction."""
        return (
            f"SpliceJunction(id={self.junction_id}, "
            f"loc={self.chromosome}:{self.start}-{self.end}, "
            f"type={self.junction_type.value}, "
            f"coverage={self.coverage})"
        )

    def __eq__(self, other) -> bool:
        """Compare junctions by their genomic location."""
        if not isinstance(other, SpliceJunction):
            return False
        return (
            self.chromosome == other.chromosome
            and self.start == other.start
            and self.end == other.end
            and self.strand == other.strand
        )

    def __hash__(self) -> int:
        """Hash based on genomic location for use in sets/dicts."""
        return hash((self.chromosome, self.start, self.end, self.strand))