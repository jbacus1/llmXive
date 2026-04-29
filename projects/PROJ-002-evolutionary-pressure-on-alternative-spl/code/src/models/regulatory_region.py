"""
Regulatory Region Entity Model

Represents regulatory regions flanking splice junctions for evolutionary
selection analysis in primate alternative splicing studies.

This model supports:
- Flanking intronic sequence extraction (±500bp)
- Conservation score tracking (phyloP, phyloP100, etc.)
- Enrichment analysis data structures
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class RegulatoryRegionType(Enum):
    """Types of regulatory regions around splice junctions."""
    FLANKING_INTRON_5P = "flanking_intron_5p"
    FLANKING_INTRON_3P = "flanking_intron_3p"
    EXON = "exon"
    BRANCH_POINT = "branch_point"
    POLYPYRIMIDINE_TRACT = "polypyrimidine_tract"
    CUSTOM = "custom"


@dataclass
class RegulatoryRegion:
    """
    Entity representing a regulatory region associated with a splice junction.
    
    Attributes:
        region_id: Unique identifier for this regulatory region
        splice_junction_id: Reference to the associated splice junction
        region_type: Type of regulatory region (see RegulatoryRegionType)
        chromosome: Chromosome/contig name
        start_pos: 1-based start position (inclusive)
        end_pos: 1-based end position (inclusive)
        strand: '+' or '-' for genomic strand
        sequence: DNA sequence of the region (optional)
        phyloP_scores: List of phyloP conservation scores per base (optional)
        mean_phyloP: Mean phyloP score across the region (optional)
        max_phyloP: Maximum phyloP score in the region (optional)
        missing_data_ratio: Proportion of positions with missing conservation data
        metadata: Additional key-value metadata
    """
    region_id: str
    splice_junction_id: str
    region_type: RegulatoryRegionType
    chromosome: str
    start_pos: int
    end_pos: int
    strand: str
    sequence: Optional[str] = None
    phyloP_scores: Optional[List[float]] = None
    mean_phyloP: Optional[float] = None
    max_phyloP: Optional[float] = None
    missing_data_ratio: float = 0.0
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and compute derived fields."""
        # Validate genomic coordinates
        if self.start_pos < 1:
            raise ValueError("start_pos must be >= 1 (1-based coordinates)")
        if self.end_pos < self.start_pos:
            raise ValueError("end_pos must be >= start_pos")
        
        # Validate strand
        if self.strand not in ['+', '-']:
            raise ValueError("strand must be '+' or '-'")
        
        # Validate region type
        if not isinstance(self.region_type, RegulatoryRegionType):
            raise ValueError("region_type must be a RegulatoryRegionType enum")
        
        # Validate missing_data_ratio
        if not 0.0 <= self.missing_data_ratio <= 1.0:
            raise ValueError("missing_data_ratio must be between 0.0 and 1.0")
        
        # Compute mean/max phyloP if scores provided
        if self.phyloP_scores is not None and len(self.phyloP_scores) > 0:
            valid_scores = [s for s in self.phyloP_scores if s is not None]
            if valid_scores:
                self.mean_phyloP = sum(valid_scores) / len(valid_scores)
                self.max_phyloP = max(valid_scores)
                self.missing_data_ratio = 1.0 - (len(valid_scores) / len(self.phyloP_scores))
        
        # Validate sequence length matches coordinates if provided
        if self.sequence is not None:
            expected_len = self.end_pos - self.start_pos + 1
            if len(self.sequence) != expected_len:
                raise ValueError(
                    f"sequence length ({len(self.sequence)}) does not match "
                    f"region size ({expected_len})"
                )
    
    @property
    def length(self) -> int:
        """Return the length of the regulatory region in base pairs."""
        return self.end_pos - self.start_pos + 1
    
    @property
    def coordinates(self) -> str:
        """Return genomic coordinates in UCSC format."""
        return f"{self.chromosome}:{self.start_pos}-{self.end_pos}({self.strand})"
    
    @classmethod
    def from_flanking_intron(
        cls,
        region_id: str,
        splice_junction_id: str,
        chromosome: str,
        junction_pos: int,
        flank_size: int = 500,
        is_5prime: bool = True,
        strand: str = '+',
        **kwargs
    ) -> 'RegulatoryRegion':
        """
        Factory method to create a flanking intron regulatory region.
        
        Args:
            region_id: Unique identifier for this region
            splice_junction_id: Associated splice junction ID
            chromosome: Chromosome name
            junction_pos: Position of the splice junction
            flank_size: Size of flanking region in bp (default 500)
            is_5prime: True for 5' flanking intron, False for 3'
            strand: Genomic strand
            **kwargs: Additional fields for RegulatoryRegion
        
        Returns:
            RegulatoryRegion instance for the flanking intron
        """
        if is_5prime:
            # 5' flanking intron: upstream of the junction
            if strand == '+':
                start_pos = junction_pos - flank_size
                end_pos = junction_pos - 1
            else:
                start_pos = junction_pos + 1
                end_pos = junction_pos + flank_size
            region_type = RegulatoryRegionType.FLANKING_INTRON_5P
        else:
            # 3' flanking intron: downstream of the junction
            if strand == '+':
                start_pos = junction_pos + 1
                end_pos = junction_pos + flank_size
            else:
                start_pos = junction_pos - flank_size
                end_pos = junction_pos - 1
            region_type = RegulatoryRegionType.FLANKING_INTRON_3P
        
        return cls(
            region_id=region_id,
            splice_junction_id=splice_junction_id,
            region_type=region_type,
            chromosome=chromosome,
            start_pos=start_pos,
            end_pos=end_pos,
            strand=strand,
            **kwargs
        )
    
    def to_dict(self) -> dict:
        """Convert the regulatory region to a dictionary representation."""
        return {
            'region_id': self.region_id,
            'splice_junction_id': self.splice_junction_id,
            'region_type': self.region_type.value,
            'chromosome': self.chromosome,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'strand': self.strand,
            'length': self.length,
            'coordinates': self.coordinates,
            'sequence': self.sequence,
            'mean_phyloP': self.mean_phyloP,
            'max_phyloP': self.max_phyloP,
            'missing_data_ratio': self.missing_data_ratio,
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RegulatoryRegion':
        """
        Create a RegulatoryRegion from a dictionary.
        
        Args:
            data: Dictionary with regulatory region fields
        
        Returns:
            RegulatoryRegion instance
        """
        region_type = data.get('region_type')
        if isinstance(region_type, str):
            region_type = RegulatoryRegionType(region_type)
        
        return cls(
            region_id=data['region_id'],
            splice_junction_id=data['splice_junction_id'],
            region_type=region_type,
            chromosome=data['chromosome'],
            start_pos=data['start_pos'],
            end_pos=data['end_pos'],
            strand=data['strand'],
            sequence=data.get('sequence'),
            phyloP_scores=data.get('phyloP_scores'),
            mean_phyloP=data.get('mean_phyloP'),
            max_phyloP=data.get('max_phyloP'),
            missing_data_ratio=data.get('missing_data_ratio', 0.0),
            metadata=data.get('metadata', {}),
        )