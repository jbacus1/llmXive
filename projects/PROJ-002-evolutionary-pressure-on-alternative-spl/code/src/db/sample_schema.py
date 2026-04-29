"""
SQLite database schema for sample tracking in evolutionary pressure analysis.

This module defines the schema for tracking RNA-seq samples across species
(human, chimpanzee, macaque, marmoset) with metadata for reproducibility
and pipeline operations.
"""

import sqlite3
from pathlib import Path
from typing import Optional


SCHEMA_VERSION = "1.0.0"


CREATE_TABLES_SQL = """
-- Samples table: Core sample metadata
CREATE TABLE IF NOT EXISTS samples (
    sample_id TEXT PRIMARY KEY,
    species TEXT NOT NULL CHECK (species IN ('human', 'chimpanzee', 'macaque', 'marmoset')),
    tissue TEXT NOT NULL DEFAULT 'cortex',
    sra_accession TEXT NOT NULL,
    sra_run_id TEXT,
    library_id TEXT,
    sequencing_center TEXT,
    library_strategy TEXT DEFAULT 'RNA-Seq',
    library_source TEXT DEFAULT 'TRANSCRIPTOMIC',
    library_selection TEXT DEFAULT 'cDNA',
    instrument_model TEXT,
    read_length INTEGER,
    read_type TEXT CHECK (read_type IN ('single', 'paired')),
    total_reads INTEGER,
    mapped_reads INTEGER,
    mapping_rate REAL,
    bam_file_path TEXT,
    sample_status TEXT DEFAULT 'pending' CHECK (sample_status IN ('pending', 'downloaded', 'aligned', 'quantified', 'failed')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    checksum_sha256 TEXT
);

-- Species reference genomes table
CREATE TABLE IF NOT EXISTS reference_genomes (
    species TEXT PRIMARY KEY CHECK (species IN ('human', 'chimpanzee', 'macaque', 'marmoset')),
    genome_assembly TEXT NOT NULL,
    fasta_path TEXT NOT NULL,
    annotation_gtf TEXT NOT NULL,
    star_index_path TEXT,
    version TEXT,
    download_date TEXT,
    checksum_sha256 TEXT
);

-- Alignment runs table
CREATE TABLE IF NOT EXISTS alignment_runs (
    run_id TEXT PRIMARY KEY,
    sample_id TEXT NOT NULL REFERENCES samples(sample_id) ON DELETE CASCADE,
    star_version TEXT NOT NULL,
    genome_assembly TEXT NOT NULL,
    alignment_date TEXT NOT NULL DEFAULT (datetime('now')),
    parameters TEXT,  -- JSON string of STAR parameters
    log_file_path TEXT,
    sj_out_path TEXT,
    total_reads INTEGER,
    uniquely_mapped INTEGER,
    multi_mapped INTEGER,
    unmapped INTEGER,
    mapping_rate REAL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    error_message TEXT
);

-- Pipeline runs table for reproducibility
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id TEXT PRIMARY KEY,
    pipeline_version TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    start_time TEXT NOT NULL DEFAULT (datetime('now')),
    end_time TEXT,
    status TEXT DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    error_message TEXT,
    samples_processed INTEGER DEFAULT 0,
    samples_failed INTEGER DEFAULT 0
);

-- Pipeline run samples mapping
CREATE TABLE IF NOT EXISTS pipeline_run_samples (
    run_id TEXT NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    sample_id TEXT NOT NULL REFERENCES samples(sample_id) ON DELETE CASCADE,
    stage TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    PRIMARY KEY (run_id, sample_id, stage)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_samples_species ON samples(species);
CREATE INDEX IF NOT EXISTS idx_samples_status ON samples(sample_status);
CREATE INDEX IF NOT EXISTS idx_samples_sra ON samples(sra_accession);
CREATE INDEX IF NOT EXISTS idx_alignment_runs_sample ON alignment_runs(sample_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_run_samples_sample ON pipeline_run_samples(sample_id);
"""

CREATE_SCHEMA_VERSION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    version TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT OR IGNORE INTO schema_version (id, version) VALUES (1, ?);
"""

def init_database(db_path: str) -> sqlite3.Connection:
    """
    Initialize SQLite database with sample tracking schema.
    
    Args:
        db_path: Path to SQLite database file (will be created if not exists)
    
    Returns:
        sqlite3.Connection object
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    
    # Create schema version table and record
    cursor.execute(
        CREATE_SCHEMA_VERSION_TABLE_SQL,
        (SCHEMA_VERSION,)
    )
    
    # Create all tables
    cursor.execute(CREATE_TABLES_SQL)
    
    conn.commit()
    return conn


def get_sample(conn: sqlite3.Connection, sample_id: str) -> Optional[dict]:
    """Retrieve a sample by ID."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM samples WHERE sample_id = ?",
        (sample_id,)
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def insert_sample(conn: sqlite3.Connection, sample_data: dict) -> str:
    """
    Insert a new sample into the database.
    
    Args:
        conn: Database connection
        sample_data: Dict with sample fields (sample_id required)
    
    Returns:
        The inserted sample_id
    """
    cursor = conn.cursor()
    
    columns = ', '.join(sample_data.keys())
    placeholders = ', '.join(['?' for _ in sample_data])
    
    cursor.execute(
        f"INSERT INTO samples ({columns}) VALUES ({placeholders})",
        list(sample_data.values())
    )
    
    conn.commit()
    return sample_data['sample_id']


def update_sample_status(conn: sqlite3.Connection, sample_id: str, status: str) -> bool:
    """Update sample status and updated_at timestamp."""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE samples SET sample_status = ?, updated_at = datetime('now') WHERE sample_id = ?",
        (status, sample_id)
    )
    conn.commit()
    return cursor.rowcount > 0


def get_samples_by_species(conn: sqlite3.Connection, species: str) -> list:
    """Get all samples for a given species."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM samples WHERE species = ?",
        (species,)
    )
    return [dict(row) for row in cursor.fetchall()]


def get_unaligned_samples(conn: sqlite3.Connection) -> list:
    """Get all samples that haven't been aligned yet."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM samples WHERE sample_status IN ('pending', 'downloaded')",
    )
    return [dict(row) for row in cursor.fetchall()]

def close_database(conn: sqlite3.Connection):
    """Close database connection."""
    if conn:
        conn.close()
