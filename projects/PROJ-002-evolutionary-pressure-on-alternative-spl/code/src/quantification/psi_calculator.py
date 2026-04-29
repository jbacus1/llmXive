"""
PSI (Percent Spliced In) calculator for alternative splicing events.
Calculates PSI values from junction counts.
"""
import logging
from typing import Dict, Optional
from dataclasses import dataclass

from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class PSIResult:
    """Result of PSI calculation for a splicing event."""
    event_id: str
    psi_value: float
    included_reads: int
    skipped_reads: int
    total_reads: int
    confidence: str
    
class PSICalculator:
    """Calculate PSI values from junction read counts."""
    
    def __init__(self, min_coverage: int = 20):
        """Initialize PSI calculator.
        
        Args:
            min_coverage: Minimum read coverage threshold (SC-003)
        """
        self.min_coverage = min_coverage
        logger.info(f"Initialized PSI calculator with min_coverage={min_coverage}")
    
    def calculate(
        self,
        included_reads: int,
        skipped_reads: int,
        event_id: str = ""
    ) -> Optional[PSIResult]:
        """Calculate PSI value for a splicing event.
        
        Args:
            included_reads: Number of reads supporting inclusion
            skipped_reads: Number of reads supporting skipping
            event_id: Optional event identifier
        
        Returns:
            PSIResult if coverage threshold met, None otherwise
        """
        total_reads = included_reads + skipped_reads
        
        if total_reads < self.min_coverage:
            logger.warning(
                f"Event {event_id}: Coverage {total_reads} below threshold {self.min_coverage}"
            )
            return None
        
        psi_value = included_reads / total_reads if total_reads > 0 else 0.0
        
        # Determine confidence based on read count
        if total_reads >= 100:
            confidence = 'high'
        elif total_reads >= 50:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        logger.debug(
            f"Event {event_id}: PSI={psi_value:.3f}, "
            f"included={included_reads}, skipped={skipped_reads}, "
            f"total={total_reads}, confidence={confidence}"
        )
        
        return PSIResult(
            event_id=event_id,
            psi_value=psi_value,
            included_reads=included_reads,
            skipped_reads=skipped_reads,
            total_reads=total_reads,
            confidence=confidence
        )
    
    def calculate_delta_psi(
        self,
        psi_group1: float,
        psi_group2: float,
        event_id: str = ""
    ) -> float:
        """Calculate ΔPSI between two groups.
        
        Args:
            psi_group1: PSI value for group 1
            psi_group2: PSI value for group 2
            event_id: Optional event identifier
        
        Returns:
            Absolute ΔPSI value
        """
        delta_psi = abs(psi_group1 - psi_group2)
        logger.debug(
            f"Event {event_id}: ΔPSI={delta_psi:.3f} "
            f"(group1={psi_group1:.3f}, group2={psi_group2:.3f})"
        )
        return delta_psi
