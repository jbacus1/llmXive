"""
Database module for sample tracking and pipeline metadata.
"""

from .sample_schema import (
    init_database,
    get_sample,
    insert_sample,
    update_sample_status,
    get_samples_by_species,
    get_unaligned_samples,
    close_database,
    SCHEMA_VERSION,
)

__all__ = [
    'init_database',
    'get_sample',
    'insert_sample',
    'update_sample_status',
    'get_samples_by_species',
    'get_unaligned_samples',
    'close_database',
    'SCHEMA_VERSION',
]
