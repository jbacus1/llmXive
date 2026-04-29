"""
Contract for PSI (Percent Spliced In) calculation results.

Defines the schema and validation rules for PSI values
calculated from junction read counts.
"""
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class PSIResultContract:
    """
    Contract for PSI calculation results.

    Attributes:
        sample_id: Sample identifier
        event_id: Splicing event identifier
        event_type: Type of splicing event
        included_reads: Reads supporting inclusion
        excluded_reads: Reads supporting exclusion
        total_reads: Total reads for this event
        psi_value: Calculated PSI value (0-100)
        confidence_interval: 95% confidence interval
        coverage_depth: Average read coverage
    """
    sample_id: str
    event_id: str
    event_type: str
    included_reads: int
    excluded_reads: int
    total_reads: int
    psi_value: float
    confidence_interval: Optional[tuple] = None
    coverage_depth: float = 0.0

    def __post_init__(self):
        """Validate PSI result contract after initialization."""
        if self.included_reads < 0:
            raise ValueError("included_reads cannot be negative")
        if self.excluded_reads < 0:
            raise ValueError("excluded_reads cannot be negative")
        if not 0 <= self.psi_value <= 100:
            raise ValueError("psi_value must be between 0 and 100")

    def validate(self) -> bool:
        """Validate all contract requirements."""
        return all([
            bool(self.sample_id),
            bool(self.event_id),
            self.included_reads >= 0,
            self.excluded_reads >= 0,
            self.total_reads >= 0,
            0 <= self.psi_value <= 100,
        ])

    def meets_coverage_threshold(self, min_coverage: int = 20) -> bool:
        """
        Check if event meets minimum coverage threshold.

        Args:
            min_coverage: Minimum required read coverage (default 20)

        Returns:
            True if coverage threshold is met
        """
        return self.total_reads >= min_coverage
