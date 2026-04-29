"""
Unit tests for SQLite sample schema module.
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from code.src.db.sample_schema import (
    init_database,
    get_sample,
    insert_sample,
    update_sample_status,
    get_samples_by_species,
    get_unaligned_samples,
    SCHEMA_VERSION,
)

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)

@pytest.fixture
def db_conn(temp_db):
    """Provide initialized database connection."""
    conn = init_database(temp_db)
    yield conn
    conn.close()

class TestDatabaseInitialization:
    """Test database initialization and schema creation."""

    def test_init_creates_database_file(self, temp_db):
        """Database file should be created after init."""
        conn = init_database(temp_db)
        conn.close()
        assert Path(temp_db).exists()

    def test_init_creates_schema_version_table(self, db_conn):
        """Schema version table should exist after init."""
        cursor = db_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
        assert cursor.fetchone() is not None

    def test_init_creates_samples_table(self, db_conn):
        """Samples table should exist after init."""
        cursor = db_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='samples'")
        assert cursor.fetchone() is not None

    def test_init_creates_reference_genomes_table(self, db_conn):
        """Reference genomes table should exist after init."""
        cursor = db_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reference_genomes'")
        assert cursor.fetchone() is not None

    def test_init_creates_alignment_runs_table(self, db_conn):
        """Alignment runs table should exist after init."""
        cursor = db_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alignment_runs'")
        assert cursor.fetchone() is not None

    def test_schema_version_recorded(self, db_conn):
        """Schema version should be recorded in schema_version table."""
        cursor = db_conn.cursor()
        cursor.execute("SELECT version FROM schema_version WHERE id = 1")
        row = cursor.fetchone()
        assert row is not None
        assert row['version'] == SCHEMA_VERSION

    def test_indexes_created(self, db_conn):
        """Indexes should be created for common queries."""
        cursor = db_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row['name'] for row in cursor.fetchall()]
        assert 'idx_samples_species' in indexes
        assert 'idx_samples_status' in indexes

class TestSampleOperations:
    """Test sample CRUD operations."""

    def test_insert_sample(self, db_conn):
        """Should be able to insert a new sample."""
        sample_data = {
            'sample_id': 'TEST_001',
            'species': 'human',
            'tissue': 'cortex',
            'sra_accession': 'ERR000001',
            'library_strategy': 'RNA-Seq',
        }
        sample_id = insert_sample(db_conn, sample_data)
        assert sample_id == 'TEST_001'

    def test_get_sample(self, db_conn):
        """Should retrieve sample by ID."""
        sample_data = {
            'sample_id': 'TEST_002',
            'species': 'chimpanzee',
            'tissue': 'cortex',
            'sra_accession': 'ERR000002',
        }
        insert_sample(db_conn, sample_data)
        sample = get_sample(db_conn, 'TEST_002')
        assert sample is not None
        assert sample['species'] == 'chimpanzee'

    def test_get_sample_not_found(self, db_conn):
        """Should return None for non-existent sample."""
        sample = get_sample(db_conn, 'NONEXISTENT')
        assert sample is None

    def test_update_sample_status(self, db_conn):
        """Should update sample status."""
        sample_data = {
            'sample_id': 'TEST_003',
            'species': 'human',
            'tissue': 'cortex',
            'sra_accession': 'ERR000003',
        }
        insert_sample(db_conn, sample_data)
        result = update_sample_status(db_conn, 'TEST_003', 'downloaded')
        assert result is True

    def test_update_sample_status_not_found(self, db_conn):
        """Should return False for non-existent sample."""
        result = update_sample_status(db_conn, 'NONEXISTENT', 'downloaded')
        assert result is False

    def test_get_samples_by_species(self, db_conn):
        """Should retrieve all samples for a species."""
        insert_sample(db_conn, {
            'sample_id': 'H1',
            'species': 'human',
            'tissue': 'cortex',
            'sra_accession': 'ERR000001',
        })
        insert_sample(db_conn, {
            'sample_id': 'H2',
            'species': 'human',
            'tissue': 'cortex',
            'sra_accession': 'ERR000002',
        })
        insert_sample(db_conn, {
            'sample_id': 'C1',
            'species': 'chimpanzee',
            'tissue': 'cortex',
            'sra_accession': 'ERR000003',
        })
        
        human_samples = get_samples_by_species(db_conn, 'human')
        assert len(human_samples) == 2
        for s in human_samples:
            assert s['species'] == 'human'

    def test_get_unaligned_samples(self, db_conn):
        """Should retrieve samples that haven't been aligned."""
        insert_sample(db_conn, {
            'sample_id': 'P1',
            'species': 'human',
            'tissue': 'cortex',
            'sra_accession': 'ERR000001',
            'sample_status': 'pending',
        })
        insert_sample(db_conn, {
            'sample_id': 'D1',
            'species': 'human',
            'tissue': 'cortex',
            'sra_accession': 'ERR000002',
            'sample_status': 'downloaded',
        })
        insert_sample(db_conn, {
            'sample_id': 'A1',
            'species': 'human',
            'tissue': 'cortex',
            'sra_accession': 'ERR000003',
            'sample_status': 'aligned',
        })
        
        unaligned = get_unaligned_samples(db_conn)
        assert len(unaligned) == 2
        sample_ids = {s['sample_id'] for s in unaligned}
        assert 'P1' in sample_ids
        assert 'D1' in sample_ids
        assert 'A1' not in sample_ids

    def test_sample_status_constraints(self, db_conn):
        """Sample status should be constrained to valid values."""
        with pytest.raises(sqlite3.IntegrityError):
            insert_sample(db_conn, {
                'sample_id': 'INVALID',
                'species': 'invalid_species',
                'tissue': 'cortex',
                'sra_accession': 'ERR000001',
            })

    def test_species_constraints(self, db_conn):
        """Species should be constrained to valid values."""
        with pytest.raises(sqlite3.IntegrityError):
            insert_sample(db_conn, {
                'sample_id': 'INVALID',
                'species': 'mouse',
                'tissue': 'cortex',
                'sra_accession': 'ERR000001',
            })

class TestDatabaseCleanup:
    """Test database cleanup operations."""

    def test_close_database(self, temp_db):
        """Should close database connection without error."""
        conn = init_database(temp_db)
        from code.src.db.sample_schema import close_database
        close_database(conn)
        # Connection should be closed
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")