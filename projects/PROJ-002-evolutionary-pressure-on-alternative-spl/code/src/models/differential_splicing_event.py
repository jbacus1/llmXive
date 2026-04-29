"""
Differential Splicing Event Model

This module defines the data model for differential splicing events
identified during the comparative analysis of alternative splicing
across primate lineages.

Based on User Story 2 requirements:
- ΔPSI threshold ≥ 0.1 (SC-002)
- Minimum read coverage ≥ 20 reads per junction
- Benjamini-Hochberg FDR correction (p < 0.05)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List, Any
from datetime import datetime


class SplicingEventType(Enum):
    """Types of alternative splicing events."""
    SKIP_EXON = "skip_exon"
    INCLUDE_EXON = "include_exon"
    ALTERNATIVE_5SS = "alternative_5ss"
    ALTERNATIVE_3SS = "alternative_3ss"
    MUTUALLY_EXCLUSIVE = "mutually_exclusive"
    RETAINED_INTRON = "retained_intron"


class Species(Enum):
    """Supported primate species for analysis."""
    HUMAN = "human"
    CHIMPANZEE = "chimpanzee"
    MACAQUE = "macaque"
    MARMOSET = "marmoset"


@dataclass
class PSIValue:
    """Percent Spliced In value for a specific condition."""
    species: Species
    condition: str  # e.g., "cortex", "control", etc.
    psi: float
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    read_count: int = 0

    def __post_init__(self):
        if not 0.0 <= self.psi <= 1.0:
            raise ValueError(f"PSI value must be between 0 and 1, got {self.psi}")
        if self.read_count < 0:
            raise ValueError(f"Read count cannot be negative, got {self.read_count}")


@dataclass
class CoverageInfo:
    """Coverage information for splice junctions."""
    junction_id: str
    inclusion_reads: int
    exclusion_reads: int
    total_reads: int

    @property
    def meets_minimum_coverage(self) -> bool:
        """Check if coverage meets the minimum threshold (≥20 reads)."""
        return self.total_reads >= 20


@dataclass
class DifferentialSplicingEvent:
    """
    Model representing a differential splicing event between conditions.

    This captures the key metrics from rMATS output and applies the
    validation thresholds specified in the project requirements:
    - ΔPSI ≥ 0.1 (absolute difference in PSI)
    - Coverage ≥ 20 reads per junction
    - FDR < 0.05 (Benjamini-Hochberg corrected p-value)
    """
    # Unique identifiers
    event_id: str
    junction_id: str
    gene_id: str
    gene_name: str

    # Splicing event classification
    event_type: SplicingEventType
    exon_start: int
    exon_end: int
    chromosome: str

    # PSI values for comparison groups
    psi_group_1: List[PSIValue] = field(default_factory=list)
    psi_group_2: List[PSIValue] = field(default_factory=list)

    # Differential splicing metrics
    delta_psi: float  # Absolute difference in PSI
    p_value: float
    fdr: float  # Benjamini-Hochberg corrected p-value

    # Coverage information
    coverage_group_1: List[CoverageInfo] = field(default_factory=list)
    coverage_group_2: List[CoverageInfo] = field(default_factory=list)

    # Statistical test results
    test_statistic: Optional[float] = None
    test_method: str = "fixed_effect_model"

    # Validation status
    passes_delta_psi_threshold: bool = field(init=False)
    passes_coverage_threshold: bool = field(init=False)
    passes_fdr_threshold: bool = field(init=False)
    is_significant: bool = field(init=False)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    analysis_version: str = "1.0.0"
    source_file: Optional[str] = None
    species_comparison: tuple = field(default=())

    def __post_init__(self):
        """Validate thresholds and compute derived fields."""
        self.passes_delta_psi_threshold = abs(self.delta_psi) >= 0.1
        self.passes_coverage_threshold = self._check_coverage_threshold()
        self.passes_fdr_threshold = self.fdr < 0.05
        self.is_significant = (
            self.passes_delta_psi_threshold and
            self.passes_coverage_threshold and
            self.passes_fdr_threshold
        )

    def _check_coverage_threshold(self, min_reads: int = 20) -> bool:
        """
        Check if all coverage groups meet the minimum read threshold.

        Args:
            min_reads: Minimum required reads per junction (default: 20)

        Returns:
            True if all coverage groups meet threshold
        """
        all_coverage = self.coverage_group_1 + self.coverage_group_2
        if not all_coverage:
            return False
        return all(cov.meets_minimum_coverage for cov in all_coverage)

    def get_psi_summary(self) -> Dict[str, float]:
        """Get summary statistics for PSI values."""
        def avg_psi(psi_list: List[PSIValue]) -> float:
            if not psi_list:
                return 0.0
            return sum(p.psi for p in psi_list) / len(psi_list)

        return {
            "group_1_avg_psi": avg_psi(self.psi_group_1),
            "group_2_avg_psi": avg_psi(self.psi_group_2),
            "delta_psi": self.delta_psi,
            "p_value": self.p_value,
            "fdr": self.fdr,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "junction_id": self.junction_id,
            "gene_id": self.gene_id,
            "gene_name": self.gene_name,
            "event_type": self.event_type.value,
            "chromosome": self.chromosome,
            "exon_start": self.exon_start,
            "exon_end": self.exon_end,
            "psi_summary": self.get_psi_summary(),
            "passes_delta_psi_threshold": self.passes_delta_psi_threshold,
            "passes_coverage_threshold": self.passes_coverage_threshold,
            "passes_fdr_threshold": self.passes_fdr_threshold,
            "is_significant": self.is_significant,
            "species_comparison": [s.value for s in self.species_comparison] if self.species_comparison else [],
            "analysis_version": self.analysis_version,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_rmats_output(cls, row: Dict[str, Any]) -> "DifferentialSplicingEvent":
        """
        Create event from rMATS output row.

        Args:
            row: Dictionary from rMATS output file

        Returns:
            DifferentialSplicingEvent instance
        """
        # Parse PSI values
        psi_group_1 = []
        psi_group_2 = []

        # Expected rMATS columns: INCLEVEL1, INCLEVEL2, IICount1, IICount2, etc.
        inc_level_1 = float(row.get("INCLEVEL1", 0))
        inc_level_2 = float(row.get("INCLEVEL2", 0))
        delta_inc = float(row.get("IncLevelDifference", 0))

        # Parse coverage
        coverage_group_1 = []
        coverage_group_2 = []

        try:
            coverage_group_1.append(CoverageInfo(
                junction_id=row.get("JunctionID", ""),
                inclusion_reads=int(row.get("IICount1", 0)),
                exclusion_reads=int(row.get("DECOUNT1", 0)),
                total_reads=int(row.get("IICount1", 0)) + int(row.get("DECOUNT1", 0))
            ))
            coverage_group_2.append(CoverageInfo(
                junction_id=row.get("JunctionID", ""),
                inclusion_reads=int(row.get("IICount2", 0)),
                exclusion_reads=int(row.get("DECOUNT2", 0)),
                total_reads=int(row.get("IICount2", 0)) + int(row.get("DECOUNT2", 0))
            ))
        except (KeyError, ValueError):
            pass

        # Parse event type from rMATS
        event_type = SplicingEventType(row.get("Type", "skip_exon").lower())

        return cls(
            event_id=row.get("ID", ""),
            junction_id=row.get("JunctionID", ""),
            gene_id=row.get("GeneID", ""),
            gene_name=row.get("GeneName", ""),
            event_type=event_type,
            exon_start=int(row.get("ExonStart", 0)),
            exon_end=int(row.get("ExonEnd", 0)),
            chromosome=row.get("Chromosome", ""),
            psi_group_1=psi_group_1,
            psi_group_2=psi_group_2,
            delta_psi=abs(delta_inc),
            p_value=float(row.get("PValue", 1.0)),
            fdr=float(row.get("FDR", 1.0)),
            coverage_group_1=coverage_group_1,
            coverage_group_2=coverage_group_2,
            test_method="fixed_effect_model",
        )

    def validate_against_spec(self) -> Dict[str, bool]:
        """
        Validate event against all specification requirements.

        Returns:
            Dictionary with validation results per criterion
        """
        return {
            "SC-002-delta_psi": self.passes_delta_psi_threshold,
            "SC-002-coverage": self.passes_coverage_threshold,
            "SC-002-fdr": self.passes_fdr_threshold,
            "all_criteria": self.is_significant,
        }