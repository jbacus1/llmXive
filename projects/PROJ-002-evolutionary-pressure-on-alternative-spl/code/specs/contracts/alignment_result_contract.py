"""
Contract for alignment result data entities.

Defines the schema and validation rules for STAR alignment
results and quality metrics.
"""
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class AlignmentStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"

@dataclass
class AlignmentResultContract:
    """
    Contract for alignment results.

    Attributes:
        sample_id: Sample identifier
        alignment_status: Status of the alignment run
        bam_path: Path to output BAM file
        log_path: Path to STAR log file
        total_reads: Total input reads
        mapped_reads: Successfully mapped reads
        unmapped_reads: Unmapped reads
        mapping_rate: Percentage of mapped reads
        multi_mapped_reads: Reads mapping to multiple locations
        star_version: STAR version used
        reference_genome: Reference genome identifier
        error_message: Error message if alignment failed
    """
    sample_id: str
    alignment_status: AlignmentStatus
    bam_path: Optional[str] = None
    log_path: Optional[str] = None
    total_reads: int = 0
    mapped_reads: int = 0
    unmapped_reads: int = 0
    mapping_rate: float = 0.0
    multi_mapped_reads: int = 0
    star_version: Optional[str] = None
    reference_genome: Optional[str] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        """Validate alignment result contract after initialization."""
        if not self.sample_id:
            raise ValueError("sample_id cannot be empty")
        if self.total_reads < 0:
            raise ValueError("total_reads cannot be negative")
        if self.mapped_reads < 0:
            raise ValueError("mapped_reads cannot be negative")

    def validate(self) -> bool:
        """Validate all contract requirements."""
        return all([
            bool(self.sample_id),
            self.alignment_status in AlignmentStatus,
            self.total_reads >= 0,
            self.mapped_reads >= 0,
            self.unmapped_reads >= 0,
            0 <= self.mapping_rate <= 100,
        ])

    def meets_quality_threshold(self, min_mapping_rate: float = 70.0) -> bool:
        """
        Check if alignment meets quality thresholds per SC-001.

        Args:
            min_mapping_rate: Minimum acceptable mapping rate (default 70%)

        Returns:
            True if alignment passes quality threshold
        """
        return self.mapping_rate >= min_mapping_rate
