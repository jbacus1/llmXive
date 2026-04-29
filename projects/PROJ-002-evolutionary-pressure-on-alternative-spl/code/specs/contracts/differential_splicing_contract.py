"""
Contract for differential splicing event data entities.

Defines the schema and validation rules for differential splicing
analysis results between species or conditions.
"""
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class DifferentialSplicingContract:
    """
    Contract for differential splicing events.

    Attributes:
        event_id: Unique identifier for the splicing event
        event_type: Type of splicing event (SE, A5SS, A3SS, MXE, RI)
        gene_id: Associated gene identifier
        gene_symbol: Gene symbol
        chromosome: Chromosome name
        psi_species1: PSI value for first species/condition
        psi_species2: PSI value for second species/condition
        delta_psi: Difference in PSI values
        p_value: Raw p-value from statistical test
        fdr: Adjusted p-value (FDR)
        read_count_species1: Read coverage for first species
        read_count_species2: Read coverage for second species
        significant: Whether the event passes significance thresholds
    """
    event_id: str
    event_type: str
    gene_id: str
    gene_symbol: str
    chromosome: str
    psi_species1: float
    psi_species2: float
    delta_psi: float
    p_value: float
    fdr: float
    read_count_species1: int
    read_count_species2: int
    significant: bool = False

    def __post_init__(self):
        """Validate differential splicing contract after initialization."""
        if not 0 <= self.psi_species1 <= 100:
            raise ValueError("psi_species1 must be between 0 and 100")
        if not 0 <= self.psi_species2 <= 100:
            raise ValueError("psi_species2 must be between 0 and 100")
        if not 0 <= self.p_value <= 1:
            raise ValueError("p_value must be between 0 and 1")
        if not 0 <= self.fdr <= 1:
            raise ValueError("fdr must be between 0 and 1")

    def validate(self) -> bool:
        """Validate all contract requirements."""
        return all([
            bool(self.event_id),
            self.event_type in ['SE', 'A5SS', 'A3SS', 'MXE', 'RI'],
            bool(self.gene_id),
            bool(self.chromosome),
            0 <= self.psi_species1 <= 100,
            0 <= self.psi_species2 <= 100,
            0 <= self.p_value <= 1,
            0 <= self.fdr <= 1,
            self.read_count_species1 >= 0,
            self.read_count_species2 >= 0,
        ])

    def meets_significance_thresholds(self, delta_psi_threshold: float = 0.1,
                                      fdr_threshold: float = 0.05,
                                      coverage_threshold: int = 20) -> bool:
        """
        Check if event meets significance thresholds per SC-001.

        Args:
            delta_psi_threshold: Minimum |ΔPSI| required (default 0.1)
            fdr_threshold: Maximum FDR allowed (default 0.05)
            coverage_threshold: Minimum read coverage (default 20)

        Returns:
            True if event passes all thresholds
        """
        return (
            abs(self.delta_psi) >= delta_psi_threshold and
            self.fdr < fdr_threshold and
            self.read_count_species1 >= coverage_threshold and
            self.read_count_species2 >= coverage_threshold
        )
