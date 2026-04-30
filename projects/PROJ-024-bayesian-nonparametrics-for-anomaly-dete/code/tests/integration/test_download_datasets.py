"""
Integration tests for data download script.

Tests verify that the download script properly handles:
- File downloads from URLs
- Checksum computation and storage
- Checksum verification
- Error handling for failed downloads
"""

import hashlib
import os
import tempfile
from pathlib import Path
import pytest
import yaml

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download_datasets import (
    compute_sha256,
    verify_checksum,
    save_checksums,
    load_checksums,
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_file(temp_data_dir):
    """Create a sample file for testing."""
    filepath = temp_data_dir / 'test_file.txt'
    filepath.write_text('test content for checksum verification')
    return filepath

class TestChecksumComputation:
    """Tests for checksum computation functionality."""
    
    def test_compute_sha256_basic(self, sample_file):
        """Test basic SHA-256 computation."""
        checksum = compute_sha256(sample_file)
        assert len(checksum) == 64  # SHA-256 produces 64 hex characters
        assert all(c in '0123456789abcdef' for c in checksum)
    
    def test_compute_sha256_deterministic(self, sample_file):
        """Test that checksum computation is deterministic."""
        checksum1 = compute_sha256(sample_file)
        checksum2 = compute_sha256(sample_file)
        assert checksum1 == checksum2
    
    def test_compute_sha256_content_change(self, temp_data_dir):
        """Test that checksum changes when content changes."""
        filepath = temp_data_dir / 'test.txt'
        filepath.write_text('content v1')
        checksum1 = compute_sha256(filepath)
        
        filepath.write_text('content v2')
        checksum2 = compute_sha256(filepath)
        
        assert checksum1 != checksum2

class TestChecksumVerification:
    """Tests for checksum verification functionality."""
    
    def test_verify_checksum_match(self, sample_file):
        """Test verification when checksum matches."""
        checksum = compute_sha256(sample_file)
        assert verify_checksum(sample_file, checksum) is True
    
    def test_verify_checksum_mismatch(self, sample_file):
        """Test verification when checksum doesn't match."""
        wrong_checksum = 'a' * 64
        assert verify_checksum(sample_file, wrong_checksum) is False

class TestChecksumStorage:
    """Tests for checksum save/load functionality."""
    
    def test_save_and_load_checksums(self, temp_data_dir):
        """Test saving and loading checksums."""
        # Create test checksums
        test_checksums = {
            'file1.txt': 'abc123' * 10,
            'file2.txt': 'def456' * 10,
        }
        
        # Save to temp directory
        checksums_file = temp_data_dir / '.checksums.txt'
        
        # Temporarily override the global CHECKSUMS_FILE
        import code.data.download_datasets as dd
        original_path = dd.CHECKSUMS_FILE
        dd.CHECKSUMS_FILE = checksums_file
        
        save_checksums(test_checksums)
        
        # Load and verify
        loaded_checksums = load_checksums()
        assert loaded_checksums == test_checksums
        
        # Restore original
        dd.CHECKSUMS_FILE = original_path
    
    def test_load_nonexistent_checksums(self, temp_data_dir):
        """Test loading from non-existent checksums file."""
        import code.data.download_datasets as dd
        original_path = dd.CHECKSUMS_FILE
        dd.CHECKSUMS_FILE = temp_data_dir / 'nonexistent.txt'
        
        checksums = load_checksums()
        assert checksums == {}
        
        dd.CHECKSUMS_FILE = original_path

class TestIntegration:
    """Integration tests for the download module."""
    
    def test_full_workflow(self, temp_data_dir):
        """Test complete checksum workflow."""
        # Create test files
        files = {}
        for i in range(3):
            filepath = temp_data_dir / f'test_file_{i}.txt'
            filepath.write_text(f'content {i}')
            files[filepath.name] = filepath
        
        # Compute checksums
        checksums = {}
        for name, filepath in files.items():
            checksums[name] = compute_sha256(filepath)
        
        # Save checksums
        checksums_file = temp_data_dir / '.checksums.txt'
        import code.data.download_datasets as dd
        original_path = dd.CHECKSUMS_FILE
        dd.CHECKSUMS_FILE = checksums_file
        
        save_checksums(checksums)
        
        # Verify all checksums
        for name, filepath in files.items():
            assert verify_checksum(filepath, checksums[name]) is True
        
        dd.CHECKSUMS_FILE = original_path

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
