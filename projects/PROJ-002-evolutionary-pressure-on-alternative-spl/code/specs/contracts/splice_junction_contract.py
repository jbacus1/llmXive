"""
Contract for splice junction data entities.

Defines the schema and validation rules for splice junction
information extracted from RNA-seq alignments.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class SpliceJunctionContract:
    """
    Contract for splice junction data.

    Attributes:
        junction_id: Unique identifier for the junction
        chromosome: Chromosome name
        start_position: 1-based start position (donor site)
        end_position: 1-based end position (acceptor site)
        strand: Strand orientation (+ or -)
        motif: Splice motif (GT-AG, GC-AG, AT-AC)
        read_count: Number of reads supporting this junction
        sample_id: ID of the sample this junction belongs to
    """
    junction_id: str
    chromosome: str
    start_position: int
    end_position: int
    strand: str
    motif: str
    read_count: int
    sample_id: str

    def __post_init__(self):
        """Validate splice junction contract after initialization."""
        if self.start_position >= self.end_position:
            raise ValueError("start_position must be less than end_position")
        if self.strand not in ['+', '-']:
            raise ValueError("strand must be '+' or '-'")
        if self.read_count < 0:
            raise ValueError("read_count cannot be negative")

    def validate(self) -> bool:
        """Validate all contract requirements."""
        return all([
            bool(self.junction_id),
            bool(self.chromosome),
            self.start_position > 0,
            self.end_position > self.start_position,
            self.strand in ['+', '-'],
            self.motif in ['GT-AG', 'GC-AG', 'AT-AC'],
            self.read_count >= 0,
            bool(self.sample_id),
        ])
