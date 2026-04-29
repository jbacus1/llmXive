"""
Contract for enrichment analysis results.

Defines the schema and validation rules for enrichment
analysis of regulatory sequences and selection metrics.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class EnrichmentResultContract:
    """
    Contract for enrichment analysis results.

    Attributes:
        analysis_id: Unique analysis identifier
        gene_set: Gene set being tested
        background_set: Background gene set
        test_type: Type of enrichment test (Fisher, GSEA, etc.)
        p_value: Raw p-value
        fdr: Adjusted p-value (Benjamini-Hochberg)
        odds_ratio: Enrichment odds ratio
        genes_in_set: Genes from the input set
        genes_in_background: Genes in background set
        significant: Whether result is significant
        metadata: Additional analysis metadata
    """
    analysis_id: str
    gene_set: str
    background_set: str
    test_type: str
    p_value: float
    fdr: float
    odds_ratio: float
    genes_in_set: List[str]
    genes_in_background: List[str]
    significant: bool = False
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Validate enrichment result contract after initialization."""
        if not self.analysis_id:
            raise ValueError("analysis_id cannot be empty")
        if not 0 <= self.p_value <= 1:
            raise ValueError("p_value must be between 0 and 1")
        if not 0 <= self.fdr <= 1:
            raise ValueError("fdr must be between 0 and 1")
        if self.metadata is None:
            self.metadata = {}

    def validate(self) -> bool:
        """Validate all contract requirements."""
        return all([
            bool(self.analysis_id),
            bool(self.gene_set),
            bool(self.background_set),
            0 <= self.p_value <= 1,
            0 <= self.fdr <= 1,
            self.odds_ratio >= 0,
        ])

    def meets_significance_threshold(self, fdr_threshold: float = 0.05) -> bool:
        """
        Check if enrichment result meets significance threshold per SC-003.

        Args:
            fdr_threshold: Maximum FDR allowed (default 0.05)

        Returns:
            True if result is statistically significant
        """
        return self.fdr < fdr_threshold
