"""
Differential splicing analysis module for evolutionary pressure study.

Implements statistical testing for differential splicing events between
primate lineages with configurable thresholds for coverage and effect size.
"""

import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats

from ..models.differential_splicing_event import DifferentialSplicingEvent
from ..models.splice_junction import SpliceJunction

logger = logging.getLogger(__name__)

# Default thresholds per spec requirements
DEFAULT_MIN_READ_COVERAGE = 20  # Minimum reads per junction (T033)
DEFAULT_MIN_DELTA_PSI = 0.1      # Minimum ΔPSI threshold (T032)
DEFAULT_FDR_THRESHOLD = 0.05     # Benjamini-Hochberg FDR threshold (T034)

class DifferentialSplicingAnalyzer:
    """
    Analyzes differential splicing events between sample groups.
    
    Applies minimum read coverage threshold (≥20 reads per junction)
    as specified in SC-001 to ensure statistical reliability.
    """
    
    def __init__(
        self,
        min_read_coverage: int = DEFAULT_MIN_READ_COVERAGE,
        min_delta_psi: float = DEFAULT_MIN_DELTA_PSI,
        fdr_threshold: float = DEFAULT_FDR_THRESHOLD
    ):
        """
        Initialize the differential splicing analyzer.
        
        Args:
            min_read_coverage: Minimum reads per junction (default: 20)
            min_delta_psi: Minimum absolute ΔPSI (default: 0.1)
            fdr_threshold: Benjamini-Hochberg FDR threshold (default: 0.05)
        """
        self.min_read_coverage = min_read_coverage
        self.min_delta_psi = min_delta_psi
        self.fdr_threshold = fdr_threshold
        
        logger.info(
            f"DifferentialSplicingAnalyzer initialized with "
            f"min_read_coverage={min_read_coverage}, "
            f"min_delta_psi={min_delta_psi}, "
            f"fdr_threshold={fdr_threshold}"
        )
    
    def filter_by_read_coverage(
        self,
        junctions: List[SpliceJunction]
    ) -> List[SpliceJunction]:
        """
        Filter splice junctions by minimum read coverage threshold.
        
        This implements T033 requirement: minimum ≥20 reads per junction.
        Junctions below this threshold are excluded from differential
        analysis to ensure statistical reliability.
        
        Args:
            junctions: List of SpliceJunction objects with read counts
        
        Returns:
            Filtered list containing only junctions meeting coverage threshold
        """
        original_count = len(junctions)
        filtered = [
            j for j in junctions
            if j.total_read_count >= self.min_read_coverage
        ]
        removed_count = original_count - len(filtered)
        
        logger.info(
            f"Read coverage filter applied: {removed_count} junctions removed "
            f"(threshold: ≥{self.min_read_coverage} reads). "
            f"Remaining: {len(filtered)} of {original_count}"
        )
        
        return filtered
    
    def calculate_psi_with_coverage_check(
        self,
        junction: SpliceJunction
    ) -> Optional[float]:
        """
        Calculate PSI value for a junction if it meets coverage requirements.
        
        Args:
            junction: SpliceJunction object with read counts
        
        Returns:
            PSI value if coverage threshold met, None otherwise
        """
        if junction.total_read_count < self.min_read_coverage:
            logger.debug(
                f"Junction {junction.junction_id} excluded: "
                f"read_count={junction.total_read_count} < "
                f"threshold={self.min_read_coverage}"
            )
            return None
        
        # PSI = included_reads / total_reads
        if junction.total_read_count == 0:
            return None
        
        return junction.included_reads / junction.total_read_count
    
    def analyze_differential_splicing(
        self,
        junctions_group_a: List[SpliceJunction],
        junctions_group_b: List[SpliceJunction],
        group_a_name: str = "Group A",
        group_b_name: str = "Group B"
    ) -> List[DifferentialSplicingEvent]:
        """
        Perform differential splicing analysis between two sample groups.
        
        Applies all thresholds:
        - Minimum read coverage (≥20 reads per junction) - T033
        - Minimum ΔPSI (≥0.1) - T032
        - FDR correction (p < 0.05) - T034
        
        Args:
            junctions_group_a: SpliceJunctions from group A samples
            junctions_group_b: SpliceJunctions from group B samples
            group_a_name: Display name for group A
            group_b_name: Display name for group B
        
        Returns:
            List of DifferentialSplicingEvent objects meeting all thresholds
        """
        logger.info(
            f"Starting differential splicing analysis: "
            f"{group_a_name} ({len(junctions_group_a)} junctions) vs "
            f"{group_b_name} ({len(junctions_group_b)} junctions)"
        )
        
        # Apply read coverage threshold first (T033)
        filtered_a = self.filter_by_read_coverage(junctions_group_a)
        filtered_b = self.filter_by_read_coverage(junctions_group_b)
        
        # Find common junctions for comparison
        junction_ids_a = {j.junction_id for j in filtered_a}
        junction_ids_b = {j.junction_id for j in filtered_b}
        common_junction_ids = junction_ids_a & junction_ids_b
        
        logger.info(
            f"Common junctions after coverage filter: {len(common_junction_ids)}"
        )
        
        events = []
        for junction_id in common_junction_ids:
            junction_a = next(j for j in filtered_a if j.junction_id == junction_id)
            junction_b = next(j for j in filtered_b if j.junction_id == junction_id)
            
            # Calculate PSI values
            psi_a = self.calculate_psi_with_coverage_check(junction_a)
            psi_b = self.calculate_psi_with_coverage_check(junction_b)
            
            if psi_a is None or psi_b is None:
                continue
            
            delta_psi = psi_b - psi_a
            
            # Create event object
            event = DifferentialSplicingEvent(
                junction_id=junction_id,
                psi_group_a=psi_a,
                psi_group_b=psi_b,
                delta_psi=delta_psi,
                read_count_a=junction_a.total_read_count,
                read_count_b=junction_b.total_read_count,
                group_a_name=group_a_name,
                group_b_name=group_b_name
            )
            events.append(event)
        
        # Apply ΔPSI threshold (T032)
        events = [e for e in events if abs(e.delta_psi) >= self.min_delta_psi]
        
        # Apply FDR correction (T034)
        events = self.apply_fdr_correction(events)
        
        logger.info(
            f"Differential splicing analysis complete: "
            f"{len(events)} significant events identified"
        )
        
        return events
    
    def apply_fdr_correction(
        self,
        events: List[DifferentialSplicingEvent]
    ) -> List[DifferentialSplicingEvent]:
        """
        Apply Benjamini-Hochberg FDR correction to p-values.
        
        This implements T034 requirement for FDR < 0.05 threshold.
        
        Args:
            events: List of DifferentialSplicingEvent objects with p-values
        
        Returns:
            Filtered list with events passing FDR threshold
        """
        if not events:
            return events
        
        # Calculate p-values if not present
        for event in events:
            if event.p_value is None:
                event.p_value = self._calculate_p_value(event)
        
        # Sort by p-value
        sorted_events = sorted(events, key=lambda e: e.p_value)
        
        # Benjamini-Hochberg procedure
        n = len(sorted_events)
        for i, event in enumerate(sorted_events):
            adjusted_p = event.p_value * n / (i + 1)
            event.adjusted_p_value = min(adjusted_p, 1.0)
        
        # Filter by FDR threshold
        significant = [
            e for e in sorted_events
            if e.adjusted_p_value <= self.fdr_threshold
        ]
        
        logger.info(
            f"FDR correction applied: {len(significant)} events "
            f"pass threshold (FDR ≤ {self.fdr_threshold})"
        )
        
        return significant
    
    def _calculate_p_value(self, event: DifferentialSplicingEvent) -> float:
        """
        Calculate p-value for differential splicing event using
        fixed effect model approximation.
        
        Args:
            event: DifferentialSplicingEvent with PSI and read counts
        
        Returns:
            Two-tailed p-value for the differential splicing test
        """
        # Simple z-test approximation for PSI difference
        psi_a = event.psi_group_a
        psi_b = event.psi_group_b
        n_a = event.read_count_a
        n_b = event.read_count_b
        
        # Standard error for PSI difference
        se_a = np.sqrt(psi_a * (1 - psi_a) / n_a) if n_a > 0 else 0
        se_b = np.sqrt(psi_b * (1 - psi_b) / n_b) if n_b > 0 else 0
        se_diff = np.sqrt(se_a**2 + se_b**2)
        
        if se_diff == 0:
            return 1.0
        
        # Z-score
        z_score = abs(event.delta_psi) / se_diff
        
        # Two-tailed p-value
        p_value = 2 * (1 - stats.norm.cdf(z_score))
        
        return p_value
    
    def validate_thresholds(self) -> Dict[str, bool]:
        """
        Validate that all configured thresholds meet spec requirements.
        
        Returns:
            Dictionary of threshold validation results
        """
        results = {
            "read_coverage_min_20": self.min_read_coverage >= 20,
            "delta_psi_min_01": self.min_delta_psi >= 0.1,
            "fdr_max_05": self.fdr_threshold <= 0.05
        }
        
        all_valid = all(results.values())
        logger.info(f"Threshold validation: {'PASSED' if all_valid else 'FAILED'}")
        
        return results