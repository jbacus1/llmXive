"""
PSI Calculator Module

Calculates Percent Spliced In (PSI) values from junction read counts
for alternative splicing event quantification.

PSI = (Inclusion Reads) / (Inclusion Reads + Exclusion Reads)

This module integrates with rMATS output and splice junction models
to produce normalized splicing quantification metrics.
"""

from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

from ..models.splice_junction import SpliceJunction

logger = logging.getLogger(__name__)


@dataclass
class PSIResult:
    """Result of PSI calculation for a splicing event."""

    event_id: str
    psi_value: float  # 0.0 to 1.0
    inclusion_reads: int
    exclusion_reads: int
    total_reads: int
    coverage: int

    def __post_init__(self):
        """Validate PSI value is in valid range."""
        if not 0.0 <= self.psi_value <= 1.0:
            logger.warning(
                f"PSI value {self.psi_value} out of range for event {self.event_id}"
            )
            self.psi_value = max(0.0, min(1.0, self.psi_value))

class PSICalculator:
    """
    Calculate Percent Spliced In (PSI) values from junction read counts.

    PSI represents the proportion of transcripts that include a particular
    exon or splice junction, ranging from 0.0 (never included) to 1.0
    (always included).

    Attributes:
        min_coverage: Minimum total reads required for valid PSI (default: 20)
        handle_missing: Whether to return None for missing data (default: True)
    """

    def __init__(self, min_coverage: int = 20, handle_missing: bool = True):
        """
        Initialize PSI calculator.

        Args:
            min_coverage: Minimum total junction reads for valid PSI calculation
            handle_missing: If True, return None for missing/zero coverage;
                           if False, return 0.0 PSI
        """
        self.min_coverage = min_coverage
        self.handle_missing = handle_missing
        logger.info(f"PSICalculator initialized with min_coverage={min_coverage}")

    def calculate_psi(
        self, inclusion_reads: int, exclusion_reads: int
    ) -> Optional[float]:
        """
        Calculate PSI from inclusion and exclusion junction reads.

        PSI = inclusion_reads / (inclusion_reads + exclusion_reads)

        Args:
            inclusion_reads: Number of reads supporting inclusion junction
            exclusion_reads: Number of reads supporting exclusion junction

        Returns:
            PSI value (0.0 to 1.0) or None if coverage is insufficient
        """
        total_reads = inclusion_reads + exclusion_reads

        if total_reads == 0:
            if self.handle_missing:
                logger.debug(
                    "Zero reads for PSI calculation - returning None"
                )
                return None
            return 0.0

        if total_reads < self.min_coverage:
            logger.debug(
                f"Coverage {total_reads} below threshold {self.min_coverage}"
            )
            if self.handle_missing:
                return None

        psi_value = inclusion_reads / total_reads
        logger.debug(
            f"PSI calculated: {psi_value:.4f} (inclusion={inclusion_reads}, "
            f"exclusion={exclusion_reads}, total={total_reads})"
        )

        return psi_value

    def calculate_psi_from_junction(
        self, junction: SpliceJunction
    ) -> Optional[PSIResult]:
        """
        Calculate PSI from a SpliceJunction entity.

        Args:
            junction: SpliceJunction object with read count data

        Returns:
            PSIResult object or None if calculation not possible
        """
        inclusion = junction.inclusion_read_count
        exclusion = junction.exclusion_read_count

        psi_value = self.calculate_psi(inclusion, exclusion)
        if psi_value is None:
            logger.warning(
                f"Could not calculate PSI for junction {junction.junction_id}"
            )
            return None

        result = PSIResult(
            event_id=junction.junction_id,
            psi_value=psi_value,
            inclusion_reads=inclusion,
            exclusion_reads=exclusion,
            total_reads=inclusion + exclusion,
            coverage=inclusion + exclusion,
        )

        logger.info(
            f"PSI calculated for {junction.junction_id}: "
            f"{psi_value:.4f} (coverage={result.total_reads})"
        )
        return result

    def calculate_psi_batch(
        self, junctions: List[SpliceJunction]
    ) -> List[PSIResult]:
        """
        Calculate PSI for multiple junctions in batch.

        Args:
            junctions: List of SpliceJunction objects

        Returns:
            List of PSIResult objects (only for junctions with valid PSI)
        """
        results = []
        success_count = 0
        skipped_count = 0

        for junction in junctions:
            result = self.calculate_psi_from_junction(junction)
            if result is not None:
                results.append(result)
                success_count += 1
            else:
                skipped_count += 1

        logger.info(
            f"Batch PSI calculation complete: {success_count} successful, "
            f"{skipped_count} skipped"
        )
        return results

    def calculate_delta_psi(
        self,
        psi_condition_a: float,
        psi_condition_b: float,
        min_delta_psi: float = 0.1,
    ) -> Tuple[float, bool]:
        """
        Calculate delta PSI between two conditions.

        Args:
            psi_condition_a: PSI value for condition A
            psi_condition_b: PSI value for condition B
            min_delta_psi: Minimum absolute delta PSI threshold (default: 0.1)

        Returns:
            Tuple of (delta_psi, meets_threshold)
        """
        delta_psi = abs(psi_condition_a - psi_condition_b)
        meets_threshold = delta_psi >= min_delta_psi

        logger.debug(
            f"Delta PSI: {delta_psi:.4f} (condition_a={psi_condition_a:.4f}, "
            f"condition_b={psi_condition_b:.4f}, meets_threshold={meets_threshold})"
        )

        return delta_psi, meets_threshold

    def validate_psi_event(
        self,
        psi_value: float,
        coverage: int,
        delta_psi: Optional[float] = None,
        fdr: Optional[float] = None,
        min_coverage: int = 20,
        min_delta_psi: float = 0.1,
        max_fdr: float = 0.05,
    ) -> bool:
        """
        Validate a PSI event against quality thresholds.

        Validates:
            - Coverage >= min_coverage (default: 20)
            - Delta PSI >= min_delta_psi (if provided, default: 0.1)
            - FDR < max_fdr (if provided, default: 0.05)

        Args:
            psi_value: PSI value to validate
            coverage: Total junction read coverage
            delta_psi: Delta PSI value (optional)
            fdr: FDR-corrected p-value (optional)
            min_coverage: Minimum coverage threshold
            min_delta_psi: Minimum delta PSI threshold
            max_fdr: Maximum acceptable FDR

        Returns:
            True if event passes all validation checks
        """
        # Check coverage
        if coverage < min_coverage:
            logger.debug(
                f"Validation failed: coverage {coverage} < {min_coverage}"
            )
            return False

        # Check delta PSI if provided
        if delta_psi is not None:
            if delta_psi < min_delta_psi:
                logger.debug(
                    f"Validation failed: delta_psi {delta_psi:.4f} < {min_delta_psi}"
                )
                return False

        # Check FDR if provided
        if fdr is not None:
            if fdr >= max_fdr:
                logger.debug(
                    f"Validation failed: FDR {fdr:.4f} >= {max_fdr}"
                )
                return False

        logger.debug(
            f"Validation passed for PSI event (coverage={coverage}, "
            f"psi={psi_value:.4f})"
        )
        return True