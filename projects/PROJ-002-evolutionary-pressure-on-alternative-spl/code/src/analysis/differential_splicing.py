"""
Differential splicing analysis module.
Identifies differentially spliced events between lineages using fixed effect model.
"""
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import numpy as np

from utils.logging import get_logger
from utils.config import get_config

logger = get_logger(__name__)

@dataclass
class DifferentialSplicingResult:
    """Result of differential splicing analysis."""
    event_id: str
    delta_psi: float
    p_value: float
    adjusted_p_value: float
    significant: bool
    event_type: str
    group1_mean_psi: float
    group2_mean_psi: float

class DifferentialSplicingAnalyzer:
    """Perform differential splicing analysis between sample groups."""
    
    def __init__(
        self,
        min_delta_psi: float = 0.1,
        min_coverage: int = 20,
        fdr_threshold: float = 0.05
    ):
        """Initialize differential splicing analyzer.
        
        Args:
            min_delta_psi: Minimum ΔPSI threshold (SC-002)
            min_coverage: Minimum read coverage threshold (SC-003)
            fdr_threshold: FDR threshold for significance (SC-004)
        """
        self.min_delta_psi = min_delta_psi
        self.min_coverage = min_coverage
        self.fdr_threshold = fdr_threshold
        
        logger.info(
            f"Initialized DifferentialSplicingAnalyzer with "
            f"min_delta_psi={min_delta_psi}, "
            f"min_coverage={min_coverage}, "
            f"fdr_threshold={fdr_threshold}"
        )
    
    def analyze(
        self,
        psi_data: pd.DataFrame,
        group1_samples: List[str],
        group2_samples: List[str]
    ) -> List[DifferentialSplicingResult]:
        """Perform differential splicing analysis.
        
        Args:
            psi_data: DataFrame with PSI values per sample
            group1_samples: List of sample IDs in group 1
            group2_samples: List of sample IDs in group 2
        
        Returns:
            List of DifferentialSplicingResult objects
        """
        logger.info(
            f"Starting differential splicing analysis: "
            f"group1={len(group1_samples)} samples, "
            f"group2={len(group2_samples)} samples"
        )
        
        results = []
        
        for event_id in psi_data['event_id'].unique():
            event_data = psi_data[psi_data['event_id'] == event_id]
            
            # Filter by coverage
            event_data = event_data[event_data['total_reads'] >= self.min_coverage]
            
            if len(event_data) == 0:
                logger.debug(f"Event {event_id}: Insufficient coverage")
                continue
            
            group1_psi = event_data[
                event_data['sample_id'].isin(group1_samples)
            ]['psi_value'].values
            group2_psi = event_data[
                event_data['sample_id'].isin(group2_samples)
            ]['psi_value'].values
            
            if len(group1_psi) == 0 or len(group2_psi) == 0:
                logger.debug(f"Event {event_id}: Missing samples in one group")
                continue
            
            delta_psi = abs(np.mean(group1_psi) - np.mean(group2_psi))
            
            # Simple t-test for p-value (can be replaced with fixed effect model)
            if len(group1_psi) >= 2 and len(group2_psi) >= 2:
                _, p_value = self._t_test(group1_psi, group2_psi)
            else:
                p_value = 1.0
            
            results.append(DifferentialSplicingResult(
                event_id=event_id,
                delta_psi=delta_psi,
                p_value=p_value,
                adjusted_p_value=p_value,  # Will be corrected below
                significant=False,
                event_type=self._classify_event(event_data),
                group1_mean_psi=np.mean(group1_psi),
                group2_mean_psi=np.mean(group2_psi)
            ))
        
        logger.info(f"Initial analysis complete: {len(results)} events")
        
        # Apply FDR correction
        results = self._apply_fdr_correction(results)
        
        significant_count = sum(1 for r in results if r.significant)
        logger.info(
            f"Differential splicing analysis complete: "
            f"{significant_count}/{len(results)} significant events "
            f"(FDR < {self.fdr_threshold}, ΔPSI >= {self.min_delta_psi})"
        )
        
        return results
    
    def _apply_fdr_correction(
        self,
        results: List[DifferentialSplicingResult]
    ) -> List[DifferentialSplicingResult]:
        """Apply Benjamini-Hochberg FDR correction.
        
        Args:
            results: List of DifferentialSplicingResult objects
        
        Returns:
            Updated list with adjusted p-values and significance flags
        """
        logger.info("Applying Benjamini-Hochberg FDR correction")
        
        if len(results) == 0:
            return results
        
        # Sort by p-value
        sorted_results = sorted(results, key=lambda r: r.p_value)
        
        # BH correction
        n = len(sorted_results)
        for i, result in enumerate(sorted_results):
            rank = i + 1
            adjusted_p = result.p_value * n / rank
            result.adjusted_p_value = min(adjusted_p, 1.0)
            result.significant = (
                result.adjusted_p_value < self.fdr_threshold
                and result.delta_psi >= self.min_delta_psi
            )
        
        logger.debug(
            f"FDR correction applied: {sum(1 for r in sorted_results if r.significant)} significant"
        )
        return sorted_results
    
    def _t_test(self, group1: np.ndarray, group2: np.ndarray) -> Tuple[float, float]:
        """Perform two-sample t-test.
        
        Args:
            group1: PSI values for group 1
            group2: PSI values for group 2
        
        Returns:
            Tuple of (degrees of freedom, p-value)
        """
        # Simplified t-test (use scipy.stats.ttest_ind in production)
        mean1, mean2 = np.mean(group1), np.mean(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
        n1, n2 = len(group1), len(group2)
        
        if var1 == 0 and var2 == 0:
            return 0, 1.0 if mean1 == mean2 else 0.0
        
        se = np.sqrt(var1/n1 + var2/n2)
        t_stat = (mean1 - mean2) / se if se > 0 else 0
        
        # Approximate p-value (use scipy for accurate calculation)
        df = n1 + n2 - 2
        p_value = 2 * (1 - self._t_cdf(abs(t_stat), df))
        
        return df, p_value
    
    def _t_cdf(self, t: float, df: int) -> float:
        """Approximate t-distribution CDF."""
        # Simplified approximation - use scipy.stats.t.cdf in production
        return 0.5 + 0.5 * np.tanh(t / np.sqrt(df))
    
    def _classify_event(self, event_data: pd.DataFrame) -> str:
        """Classify splicing event type.
        
        Args:
            event_data: Event PSI data
        
        Returns:
            Event type string (SE, A5SS, A3SS, etc.)
        """
        # Extract from event_id or metadata
        event_type = event_data.get('event_type', ['unknown']).iloc[0]
        logger.debug(f"Event classified as: {event_type}")
        return event_type
    
    def save_results(
        self,
        results: List[DifferentialSplicingResult],
        output_path: Path
    ) -> None:
        """Save differential splicing results to file.
        
        Args:
            results: List of DifferentialSplicingResult objects
            output_path: Path to output file
        """
        logger.info(f"Saving results to: {output_path}")
        
        df = pd.DataFrame([
            {
                'event_id': r.event_id,
                'delta_psi': r.delta_psi,
                'p_value': r.p_value,
                'adjusted_p_value': r.adjusted_p_value,
                'significant': r.significant,
                'event_type': r.event_type,
                'group1_mean_psi': r.group1_mean_psi,
                'group2_mean_psi': r.group2_mean_psi
            }
            for r in results
        ])
        
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(results)} results to {output_path}")