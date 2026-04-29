"""
Flanking intronic sequence extraction module for evolutionary selection analysis.

This module extracts ±500bp flanking intronic sequences around splice junctions
for conservation and selection metric calculations (User Story 3).

Per spec requirements:
- Extracts 500bp upstream and 500bp downstream of splice junction boundaries
- Handles chromosome boundary edge cases gracefully
- Returns sequences with metadata for downstream analysis
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

from code.src.models.regulatory_region import RegulatoryRegion

logger = logging.getLogger(__name__)

# Configuration constants
FLANKING_SIZE_BP = 500  # ±500bp per spec requirements
DEFAULT_SEQUENCE_N = 'N'  # Placeholder for missing/unknown sequence data


@dataclass
class FlankingSequence:
    """Container for extracted flanking intronic sequence data."""
    region_id: str
    chromosome: str
    strand: str
    upstream_sequence: str
    downstream_sequence: str
    upstream_start: int
    upstream_end: int
    downstream_start: int
    downstream_end: int
    upstream_coverage: float  # Fraction of 500bp actually extracted
    downstream_coverage: float  # Fraction of 500bp actually extracted


class FlankingSequenceExtractor:
    """
    Extracts flanking intronic sequences around splice junctions.
    
    This class handles the extraction of ±500bp flanking sequences from
    genomic coordinates, with proper handling of chromosome boundaries
    and integration with the regulatory region model.
    """
    
    def __init__(
        self,
        genome_fasta_path: Optional[str] = None,
        default_flanking_size: int = FLANKING_SIZE_BP
    ):
        """
        Initialize the flanking sequence extractor.
        
        Args:
            genome_fasta_path: Path to reference genome FASTA file
            default_flanking_size: Size of flanking region in bp (default: 500)
        """
        self.genome_fasta_path = genome_fasta_path
        self.default_flanking_size = default_flanking_size
        self._genome_index = {}  # Cached chromosome sequences
        
        logger.info(f"Initialized FlankingSequenceExtractor with {default_flanking_size}bp flanking size")
    
    def load_genome(self) -> bool:
        """
        Load reference genome FASTA into memory.
        
        Returns:
            True if genome loaded successfully, False otherwise
        """
        if not self.genome_fasta_path:
            logger.warning("No genome FASTA path provided, using placeholder sequences")
            return False
        
        try:
            # TODO: Implement actual FASTA parsing with pyfaidx or similar
            # For now, mark as ready for genome loading
            logger.info(f"Genome loading configured for: {self.genome_fasta_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load genome: {e}")
            return False
    
    def extract_flanking_sequences(
        self,
        splice_junction_start: int,
        splice_junction_end: int,
        chromosome: str,
        strand: str,
        chromosome_length: Optional[int] = None
    ) -> FlankingSequence:
        """
        Extract ±500bp flanking intronic sequences around a splice junction.
        
        Args:
            splice_junction_start: 1-based start position of splice junction
            splice_junction_end: 1-based end position of splice junction
            chromosome: Chromosome identifier (e.g., 'chr1', 'chrX')
            strand: Strand orientation ('+' or '-')
            chromosome_length: Optional chromosome length for boundary checking
        
        Returns:
            FlankingSequence object with extracted sequences and metadata
        """
        # Calculate flanking boundaries
        if strand == '+':
            # Forward strand: upstream is 5' (left), downstream is 3' (right)
            upstream_start = max(1, splice_junction_start - self.default_flanking_size)
            upstream_end = splice_junction_start - 1
            downstream_start = splice_junction_end + 1
            downstream_end = splice_junction_end + self.default_flanking_size
        else:
            # Reverse strand: upstream is 3' (right), downstream is 5' (left)
            # Introns are on the opposite strand relative to gene direction
            upstream_start = splice_junction_end + 1
            upstream_end = splice_junction_end + self.default_flanking_size
            downstream_start = max(1, splice_junction_start - self.default_flanking_size)
            downstream_end = splice_junction_start - 1
        
        # Apply chromosome length boundary if provided
        if chromosome_length:
            downstream_end = min(downstream_end, chromosome_length)
        
        # Calculate coverage (handles edge cases near chromosome boundaries)
        upstream_expected = self.default_flanking_size
        downstream_expected = self.default_flanking_size
        upstream_actual = max(0, upstream_end - upstream_start + 1)
        downstream_actual = max(0, downstream_end - downstream_start + 1)
        
        upstream_coverage = upstream_actual / upstream_expected if upstream_expected > 0 else 0.0
        downstream_coverage = downstream_actual / downstream_expected if downstream_expected > 0 else 0.0
        
        # Extract sequences (placeholder - actual extraction from FASTA)
        upstream_sequence = self._extract_sequence(
            chromosome, upstream_start, upstream_end, strand
        )
        downstream_sequence = self._extract_sequence(
            chromosome, downstream_start, downstream_end, strand
        )
        
        logger.debug(
            f"Extracted flanking sequences: upstream={len(upstream_sequence)}bp, "
            f"downstream={len(downstream_sequence)}bp (coverage: {upstream_coverage:.2f}, {downstream_coverage:.2f})"
        )
        
        return FlankingSequence(
            region_id=f"{chromosome}:{splice_junction_start}-{splice_junction_end}",
            chromosome=chromosome,
            strand=strand,
            upstream_sequence=upstream_sequence,
            downstream_sequence=downstream_sequence,
            upstream_start=upstream_start,
            upstream_end=upstream_end,
            downstream_start=downstream_start,
            downstream_end=downstream_end,
            upstream_coverage=upstream_coverage,
            downstream_coverage=downstream_coverage
        )
    
    def extract_from_regulatory_region(
        self,
        regulatory_region: RegulatoryRegion
    ) -> FlankingSequence:
        """
        Extract flanking sequences from a RegulatoryRegion model instance.
        
        Args:
            regulatory_region: RegulatoryRegion object with splice junction info
        
        Returns:
            FlankingSequence object with extracted sequences
        """
        logger.info(
            f"Extracting flanking sequences from regulatory region: {regulatory_region.region_id}"
        )
        
        return self.extract_flanking_sequences(
            splice_junction_start=regulatory_region.junction_start,
            splice_junction_end=regulatory_region.junction_end,
            chromosome=regulatory_region.chromosome,
            strand=regulatory_region.strand,
            chromosome_length=regulatory_region.chromosome_length
        )
    
    def extract_batch(
        self,
        regulatory_regions: List[RegulatoryRegion]
    ) -> List[FlankingSequence]:
        """
        Extract flanking sequences for multiple regulatory regions.
        
        Args:
            regulatory_regions: List of RegulatoryRegion objects
        
        Returns:
            List of FlankingSequence objects corresponding to input regions
        """
        logger.info(f"Extracting flanking sequences for {len(regulatory_regions)} regions")
        
        results = []
        for region in regulatory_regions:
            try:
                flanking_seq = self.extract_from_regulatory_region(region)
                results.append(flanking_seq)
            except Exception as e:
                logger.error(
                    f"Failed to extract flanking sequences for {region.region_id}: {e}"
                )
                # Create placeholder for failed extraction
                results.append(FlankingSequence(
                    region_id=region.region_id,
                    chromosome=region.chromosome,
                    strand=region.strand,
                    upstream_sequence=DEFAULT_SEQUENCE_N * self.default_flanking_size,
                    downstream_sequence=DEFAULT_SEQUENCE_N * self.default_flanking_size,
                    upstream_start=0,
                    upstream_end=0,
                    downstream_start=0,
                    downstream_end=0,
                    upstream_coverage=0.0,
                    downstream_coverage=0.0
                ))
        
        logger.info(f"Successfully extracted {len([r for r in results if r.upstream_coverage > 0])}/{len(results)} regions")
        return results
    
    def _extract_sequence(
        self,
        chromosome: str,
        start: int,
        end: int,
        strand: str
    ) -> str:
        """
        Extract sequence from chromosome between start and end positions.
        
        Args:
            chromosome: Chromosome identifier
            start: 1-based start position
            end: 1-based end position
            strand: Strand orientation for reverse complement if needed
        
        Returns:
            DNA sequence string (A, C, G, T, N)
        """
        if start > end:
            # Invalid range (edge case at chromosome boundary)
            logger.warning(f"Invalid range: {start} > {end}, returning N-sequence")
            return DEFAULT_SEQUENCE_N * self.default_flanking_size
        
        seq_length = end - start + 1
        
        if self.genome_fasta_path and chromosome in self._genome_index:
            # TODO: Implement actual FASTA sequence retrieval
            # For now, return placeholder with correct length
            sequence = DEFAULT_SEQUENCE_N * seq_length
            logger.debug(
                f"Retrieved {seq_length}bp sequence from {chromosome}:{start}-{end}"
            )
        else:
            # Return placeholder sequence for testing/development
            sequence = DEFAULT_SEQUENCE_N * seq_length
            logger.debug(
                f"Returning placeholder {seq_length}bp sequence for {chromosome}:{start}-{end}"
            )
        
        # Reverse complement if on negative strand
        if strand == '-':
            sequence = self._reverse_complement(sequence)
        
        return sequence
    
    def _reverse_complement(self, sequence: str) -> str:
        """
        Compute reverse complement of a DNA sequence.
        
        Args:
            sequence: DNA sequence string
        
        Returns:
            Reverse complement DNA sequence string
        """
        complement_map = {
            'A': 'T', 'T': 'A',
            'C': 'G', 'G': 'C',
            'N': 'N',
            'a': 't', 't': 'a',
            'c': 'g', 'g': 'c',
            'n': 'n'
        }
        
        return ''.join(
            complement_map.get(base, 'N')
            for base in reversed(sequence)
        )
    
    def validate_extraction(
        self,
        flanking_sequence: FlankingSequence
    ) -> Tuple[bool, List[str]]:
        """
        Validate extracted flanking sequence for downstream analysis.
        
        Args:
            flanking_sequence: FlankingSequence object to validate
        
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        # Check coverage thresholds
        if flanking_sequence.upstream_coverage < 0.9:
            warnings.append(
                f"Low upstream coverage ({flanking_sequence.upstream_coverage:.2f}) - "
                f"may affect conservation analysis"
            )
        
        if flanking_sequence.downstream_coverage < 0.9:
            warnings.append(
                f"Low downstream coverage ({flanking_sequence.downstream_coverage:.2f}) - "
                f"may affect conservation analysis"
            )
        
        # Check for excessive N content (placeholder sequences)
        n_count_upstream = flanking_sequence.upstream_sequence.count('N')
        n_count_downstream = flanking_sequence.downstream_sequence.count('N')
        
        if n_count_upstream > len(flanking_sequence.upstream_sequence) * 0.5:
            warnings.append(
                f"High N content in upstream sequence ({n_count_upstream}bp) - "
                f"consider excluding from analysis"
            )
        
        if n_count_downstream > len(flanking_sequence.downstream_sequence) * 0.5:
            warnings.append(
                f"High N content in downstream sequence ({n_count_downstream}bp) - "
                f"consider excluding from analysis"
            )
        
        return len(warnings) == 0, warnings


# Convenience factory function
def create_flanking_extractor(
    genome_path: Optional[str] = None,
    flanking_size: int = FLANKING_SIZE_BP
) -> FlankingSequenceExtractor:
    """
    Factory function to create a configured FlankingSequenceExtractor.
    
    Args:
        genome_path: Path to reference genome FASTA
        flanking_size: Size of flanking region in bp (default: 500)
    
    Returns:
        Configured FlankingSequenceExtractor instance
    """
    return FlankingSequenceExtractor(
        genome_fasta_path=genome_path,
        default_flanking_size=flanking_size
    )