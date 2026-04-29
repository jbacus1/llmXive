"""
Contract tests for SRA downloader interface.

These tests define the expected contract that the SRADownloader implementation
must satisfy. They should FAIL before implementation and PASS after.

Tests verify:
1. Input validation (accession IDs, output paths)
2. Error handling for invalid inputs
3. Interface contract compliance
"""

import pytest
import os
import tempfile
from pathlib import Path

# Import will fail initially - this is expected before implementation
try:
    from code.src.acquisition.sra_downloader import SRADownloader
    SRA_DOWNLOADER_EXISTS = True
except ImportError:
    SRA_DOWNLOADER_EXISTS = False


class TestSRADownloaderContract:
    """Contract tests for SRADownloader interface."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_sra_downloader_class_exists(self):
        """Contract: SRADownloader class must exist."""
        assert SRA_DOWNLOADER_EXISTS, (
            "SRADownloader class must be implemented in "
            "code/src/acquisition/sra_downloader.py"
        )
    
    def test_sra_downloader_initialization(self, temp_output_dir):
        """Contract: SRADownloader must initialize with required parameters."""
        if not SRA_DOWNLOADER_EXISTS:
            pytest.skip("SRADownloader not yet implemented")
        
        # Contract: Must accept output directory
        downloader = SRADownloader(output_dir=temp_output_dir)
        assert downloader is not None
    
    def test_sra_downloader_initialization_with_retry_config(self, temp_output_dir):
        """Contract: SRADownloader must accept retry configuration."""
        if not SRA_DOWNLOADER_EXISTS:
            pytest.skip("SRADownloader not yet implemented")
        
        # Contract: Must accept retry parameters
        downloader = SRADownloader(
            output_dir=temp_output_dir,
            max_retries=3,
            retry_delay=5
        )
        assert downloader is not None
    
    def test_download_with_valid_accession(self, temp_output_dir):
        """Contract: Download must accept valid SRA accession ID."""
        if not SRA_DOWNLOADER_EXISTS:
            pytest.skip("SRADownloader not yet implemented")
        
        downloader = SRADownloader(output_dir=temp_output_dir)
        
        # Contract: download() method must exist
        assert hasattr(downloader, 'download'), (
            "SRADownloader must have a download() method"
        )
    
    def test_download_with_invalid_accession_format(self, temp_output_dir):
        """Contract: Download must reject invalid accession format."""
        if not SRA_DOWNLOADER_EXISTS:
            pytest.skip("SRADownloader not yet implemented")
        
        downloader = SRADownloader(output_dir=temp_output_dir)
        
        # Contract: Must raise ValueError for invalid accession format
        with pytest.raises(ValueError):
            downloader.download(accession_id="INVALID")
    
    def test_download_with_empty_accession(self, temp_output_dir):
        """Contract: Download must reject empty accession ID."""
        if not SRA_DOWNLOADER_EXISTS:
            pytest.skip("SRADownloader not yet implemented")
        
        downloader = SRADownloader(output_dir=temp_output_dir)
        
        # Contract: Must raise ValueError for empty accession
        with pytest.raises(ValueError):
            downloader.download(accession_id="")
    
    def test_download_with_none_accession(self, temp_output_dir):
        """Contract: Download must reject None accession ID."""
        if not SRA_DOWNLOADER_EXISTS:
            pytest.skip("SRADownloader not yet implemented")
        
        downloader = SRADownloader(output_dir=temp_output_dir)
        
        # Contract: Must raise ValueError for None accession
        with pytest.raises(ValueError):
            downloader.download(accession_id=None)
    
    def test_download_returns_download_info(self, temp_output_dir):
        """Contract: Download must return structured download info."""
        if not SRA_DOWNLOADER_EXISTS:
            pytest.skip("SRADownloader not yet implemented")
        
        downloader = SRADownloader(output_dir=temp_output_dir)
        
        # Contract: download() must return a dict with required keys
        # Note: This will fail until implementation is complete
        result = downloader.download(accession_id="ERR000001")
        assert isinstance(result, dict), (
            "download() must return a dict with download metadata"
        )
        assert "accession_id" in result, (
            "Result must include accession_id"
        )
        assert "output_path" in result, (
            "Result must include output_path"
        )
        assert "status" in result, (
            "Result must include status field"
        )
    
    def test_download_with_nonexistent_output_dir(self):
        """Contract: Download must fail gracefully for invalid output dir."""
        if not SRA_DOWNLOADER_EXISTS:
            pytest.skip("SRADownloader not yet implemented")
        
        # Contract: Must handle non-existent output directory
        with pytest.raises((ValueError, FileNotFoundError)):
            downloader = SRADownloader(output_dir="/nonexistent/path/12345")
    
    def test_batch_download_method_exists(self, temp_output_dir):
        """Contract: Batch download method must exist for multiple accessions."""
        if not SRA_DOWNLOADER_EXISTS:
            pytest.skip("SRADownloader not yet implemented")
        
        downloader = SRADownloader(output_dir=temp_output_dir)
        
        # Contract: Must have batch_download() for processing multiple samples
        assert hasattr(downloader, 'batch_download'), (
            "SRADownloader must have a batch_download() method for "
            "processing multiple accessions"
        )
    
    def test_download_with_species_parameter(self, temp_output_dir):
        """Contract: Download must accept species parameter for metadata."""
        if not SRA_DOWNLOADER_EXISTS:
            pytest.skip("SRADownloader not yet implemented")
        
        downloader = SRADownloader(output_dir=temp_output_dir)
        
        # Contract: Must accept species parameter
        # This ensures species tagging for downstream analysis
        result = downloader.download(
            accession_id="ERR000001",
            species="homo_sapiens"
        )
        assert "species" in result, (
            "Result must include species metadata"
        )
    
    def test_download_logging(self, temp_output_dir):
        """Contract: Download must log operations for audit trail."""
        if not SRA_DOWNLOADER_EXISTS:
            pytest.skip("SRADownloader not yet implemented")
        
        downloader = SRADownloader(output_dir=temp_output_dir)
        
        # Contract: Must have logging capability
        assert hasattr(downloader, 'logger') or hasattr(downloader, 'log'), (
            "SRADownloader must have logging capability for audit trail"
        )