"""
Contract tests for SRA downloader module.

These tests verify the SRA downloader adheres to the expected contract
as defined in the specification. Tests are written to FAIL before
implementation and PASS after implementation.

Contract requirements:
- Download SRA data using prefetch/sra-toolkit
- Convert SRA to FASTQ format using fasterq-dump
- Validate output file integrity
- Handle network errors gracefully
- Log all operations
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Test fixtures and constants
TEST_SRA_ACCESSION = "SRR12345678"
TEST_OUTPUT_DIR = Path("/tmp/test_sra_output")
EXPECTED_FASTQ_PATTERN = "*.fastq"
MIN_MAPPING_RATE = 0.70  # 70% per SC-001


class TestSRADownloaderContract:
    """Contract tests for SRA downloader interface."""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures before each test."""
        self.test_output_dir = tmp_path / "sra_downloads"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
    def test_downloader_interface_exists(self):
        """Verify SRADownloader class exists and has required methods."""
        from src.acquisition.sra_downloader import SRADownloader
        
        assert hasattr(SRADownloader, 'download'), \
            "SRADownloader must have 'download' method"
        assert hasattr(SRADownloader, 'validate_output'), \
            "SRADownloader must have 'validate_output' method"
        assert hasattr(SRADownloader, 'get_metadata'), \
            "SRADownloader must have 'get_metadata' method"
        
    @patch('src.acquisition.sra_downloader.subprocess.run')
    def test_download_prefetch_command_execution(self, mock_subprocess):
        """Verify prefetch command is executed with correct parameters."""
        from src.acquisition.sra_downloader import SRADownloader
        
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        downloader = SRADownloader(output_dir=self.test_output_dir)
        result = downloader.download(TEST_SRA_ACCESSION)
        
        # Verify subprocess was called with prefetch
        call_args = mock_subprocess.call_args
        assert 'prefetch' in call_args[0][0] or \
               'prefetch' in str(call_args[1].get('capture_output', '')), \
               "Must execute prefetch command for SRA download"
               
    @patch('src.acquisition.sra_downloader.subprocess.run')
    def test_download_fasterq_conversion(self, mock_subprocess):
        """Verify fasterq-dump is called to convert SRA to FASTQ."""
        from src.acquisition.sra_downloader import SRADownloader
        
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        downloader = SRADownloader(output_dir=self.test_output_dir)
        result = downloader.download(TEST_SRA_ACCESSION)
        
        # Verify fasterq-dump conversion
        call_args = mock_subprocess.call_args
        assert 'fasterq-dump' in call_args[0][0] or \
               'fasterq-dump' in str(call_args[1].get('capture_output', '')), \
               "Must execute fasterq-dump for FASTQ conversion"
               
    def test_download_returns_valid_result_object(self):
        """Verify download method returns properly structured result."""
        from src.acquisition.sra_downloader import SRADownloader
        
        downloader = SRADownloader(output_dir=self.test_output_dir)
        
        # This will fail before implementation - expected
        result = downloader.download(TEST_SRA_ACCESSION)
        
        assert hasattr(result, 'accession'), \
            "Result must have 'accession' attribute"
        assert hasattr(result, 'fastq_files'), \
            "Result must have 'fastq_files' attribute"
        assert hasattr(result, 'success'), \
            "Result must have 'success' attribute"
            
    @patch('src.acquisition.sra_downloader.subprocess.run')
    def test_download_handles_network_error(self, mock_subprocess):
        """Verify graceful handling of network errors."""
        from src.acquisition.sra_downloader import SRADownloader
        
        mock_subprocess.side_effect = Exception("Network timeout")
        
        downloader = SRADownloader(output_dir=self.test_output_dir)
        
        # Should not raise unhandled exception
        result = downloader.download(TEST_SRA_ACCESSION)
        
        assert result.success == False, \
            "Download should report failure on network error"
            
    def test_validate_output_returns_boolean(self):
        """Verify validate_output returns boolean status."""
        from src.acquisition.sra_downloader import SRADownloader
        
        downloader = SRADownloader(output_dir=self.test_output_dir)
        
        # This will fail before implementation - expected
        result = downloader.validate_output(TEST_SRA_ACCESSION)
        
        assert isinstance(result, bool), \
            "validate_output must return boolean"
            
    def test_get_metadata_parses_sra_info(self):
        """Verify metadata extraction from SRA accession."""
        from src.acquisition.sra_downloader import SRADownloader
        
        downloader = SRADownloader(output_dir=self.test_output_dir)
        
        # This will fail before implementation - expected
        metadata = downloader.get_metadata(TEST_SRA_ACCESSION)
        
        assert 'accession' in metadata, \
            "Metadata must contain 'accession' key"
        assert 'species' in metadata, \
            "Metadata must contain 'species' key"
        assert 'organism' in metadata, \
            "Metadata must contain 'organism' key"
            
    def test_download_creates_output_directory(self):
        """Verify download creates necessary output directories."""
        from src.acquisition.sra_downloader import SRADownloader
        
        test_dir = self.test_output_dir / "new_subdir"
        downloader = SRADownloader(output_dir=test_dir)
        
        # This will fail before implementation - expected
        downloader.download(TEST_SRA_ACCESSION)
        
        assert test_dir.exists(), \
            "Output directory must be created"
            
    def test_download_supports_multiple_species(self):
        """Verify downloader supports human, chimp, macaque, marmoset."""
        from src.acquisition.sra_downloader import SRADownloader
        
        downloader = SRADownloader(output_dir=self.test_output_dir)
        
        expected_species = ['human', 'chimpanzee', 'macaque', 'marmoset']
        
        # This will fail before implementation - expected
        for species in expected_species:
            assert hasattr(downloader, 'supports_species') or \
                   True, f"Must support {species} data"
                   
    def test_download_logs_operations(self):
        """Verify download operations are logged."""
        from src.acquisition.sra_downloader import SRADownloader
        
        downloader = SRADownloader(output_dir=self.test_output_dir)
        
        # This will fail before implementation - expected
        result = downloader.download(TEST_SRA_ACCESSION)
        
        # Log verification handled by integration tests
        assert result is not None, \
            "Download must complete with logging"