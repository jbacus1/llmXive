"""
Data Model Contracts for Evolutionary Pressure on Alternative Splicing Project.

This module defines interface contracts for all major data entities
used throughout the pipeline. Contracts ensure type safety and validation
across component boundaries.
"""
from .rna_seq_sample_contract import RNASeqSampleContract
from .splice_junction_contract import SpliceJunctionContract
from .differential_splicing_contract import DifferentialSplicingContract
from .sample_metadata_contract import SampleMetadataContract
from .alignment_result_contract import AlignmentResultContract
from .psi_result_contract import PSIResultContract
from .enrichment_contract import EnrichmentContract

__all__ = [
    'RNASeqSampleContract',
    'SpliceJunctionContract',
    'DifferentialSplicingContract',
    'SampleMetadataContract',
    'AlignmentResultContract',
    'PSIResultContract',
    'EnrichmentContract',
]
