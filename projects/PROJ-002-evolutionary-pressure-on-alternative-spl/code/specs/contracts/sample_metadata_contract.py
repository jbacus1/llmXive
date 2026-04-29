"""
Contract for sample metadata schema.

Defines the structure for sample metadata stored in
data/metadata.yaml and used throughout the pipeline.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

class Species(Enum):
    HUMAN = "human"
    CHIMPANZEE = "chimpanzee"
    MACAQUE = "macaque"
    MARMOSET = "marmoset"

@dataclass
class SampleMetadataContract:
    """
    Contract for sample metadata.

    Attributes:
        sample_id: Unique sample identifier
        species: Species of origin
        tissue_type: Tissue type (e.g., cortex)
        sra_accession: SRA database accession
        fastq_files: List of FASTQ file paths
        genome_reference: Reference genome assembly used
        annotation_gtf: GTF annotation file path
        project_id: Project identifier
        created_at: Creation timestamp
        updated_at: Last update timestamp
        metadata: Additional free-form metadata
    """
    sample_id: str
    species: Species
    tissue_type: str
    sra_accession: str
    fastq_files: List[str] = field(default_factory=list)
    genome_reference: Optional[str] = None
    annotation_gtf: Optional[str] = None
    project_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate sample metadata contract after initialization."""
        if not self.sample_id:
            raise ValueError("sample_id cannot be empty")
        if not self.sra_accession:
            raise ValueError("sra_accession cannot be empty")

    def validate(self) -> bool:
        """Validate all contract requirements."""
        return all([
            bool(self.sample_id),
            self.species in Species,
            bool(self.tissue_type),
            bool(self.sra_accession),
        ])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            'sample_id': self.sample_id,
            'species': self.species.value,
            'tissue_type': self.tissue_type,
            'sra_accession': self.sra_accession,
            'fastq_files': self.fastq_files,
            'genome_reference': self.genome_reference,
            'annotation_gtf': self.annotation_gtf,
            'project_id': self.project_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SampleMetadataContract':
        """Create instance from dictionary."""
        return cls(
            sample_id=data['sample_id'],
            species=Species(data['species']),
            tissue_type=data['tissue_type'],
            sra_accession=data['sra_accession'],
            fastq_files=data.get('fastq_files', []),
            genome_reference=data.get('genome_reference'),
            annotation_gtf=data.get('annotation_gtf'),
            project_id=data.get('project_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            metadata=data.get('metadata', {}),
        )
