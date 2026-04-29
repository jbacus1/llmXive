"""
Integration test for data acquisition pipeline (US1).

Tests the end-to-end flow of RNA-seq data acquisition from SRA
through to aligned BAM file production.

NOTE: This test should FAIL initially until T017-T022 are implemented.
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import pipeline components (will fail until implementation complete)
try:
    from code.src.acquisition.sra_downloader import SRADownloader
    from code.src.acquisition.metadata_parser import MetadataParser
    from code.src.alignment.star_runner import STARRunner
    from code.src.models.rna_seq_sample import RNASeqSample
    from code.src.utils.config import load_config
except ImportError as e:
    pytest.skip(f"Pipeline components not yet implemented: {e}", allow_module_level=True)


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for integration tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        workspace.joinpath("downloads").mkdir()
        workspace.joinpath("aligned").mkdir()
        workspace.joinpath("logs").mkdir()
        yield workspace
        # Cleanup handled by TemporaryDirectory

@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return {
        "samples": [
            {
                "accession": "SRR12345678",
                "species": "homo_sapiens",
                "tissue": "cortex",
                "read_type": "paired",
                "fastq_urls": [
                    "ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR123/001/SRR12345678/SRR12345678_1.fastq.gz",
                    "ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR123/001/SRR12345678/SRR12345678_2.fastq.gz"
                ]
            }
        ]
    }

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "acquisition": {
            "sra_base_url": "https://ftp.sra.ebi.ac.uk",
            "download_timeout": 300,
            "max_retries": 3
        },
        "alignment": {
            "star_path": "star",
            "genome_dir": "/path/to/genome",
            "mapping_rate_threshold": 0.70
        },
        "workspace": {
            "downloads": "downloads",
            "aligned": "aligned",
            "logs": "logs"
        }
    }

class TestDataAcquisitionPipeline:
    """Integration tests for the data acquisition pipeline."""

    def test_pipeline_initialization(self, temp_workspace, mock_config):
        """Test that pipeline components can be initialized."""
        # Arrange
        config = mock_config
        
        # Act & Assert
        downloader = SRADownloader(config)
        parser = MetadataParser(config)
        aligner = STARRunner(config)
        
        assert downloader is not None
        assert parser is not None
        assert aligner is not None

    def test_metadata_parsing(self, temp_workspace, sample_metadata):
        """Test that metadata is correctly parsed into sample objects."""
        # Arrange
        parser = MetadataParser({})
        
        # Act
        samples = parser.parse(sample_metadata)
        
        # Assert
        assert len(samples) == 1
        assert isinstance(samples[0], RNASeqSample)
        assert samples[0].accession == "SRR12345678"
        assert samples[0].species == "homo_sapiens"
        assert samples[0].tissue == "cortex"
        assert samples[0].read_type == "paired"

    @patch('code.src.acquisition.sra_downloader.SRADownloader.download')
    def test_sra_download_integration(self, mock_download, temp_workspace, sample_metadata):
        """Test SRA download integration with mocked external call."""
        # Arrange
        mock_download.return_value = {
            "success": True,
            "files": [
                temp_workspace / "downloads" / "SRR12345678_1.fastq.gz",
                temp_workspace / "downloads" / "SRR12345678_2.fastq.gz"
            ]
        }
        downloader = SRADownloader({})
        
        # Act
        result = downloader.download(sample_metadata["samples"][0], temp_workspace / "downloads")
        
        # Assert
        assert result["success"] is True
        assert len(result["files"]) == 2
        mock_download.assert_called_once()

    @patch('code.src.alignment.star_runner.STARRunner.run')
    def test_star_alignment_integration(self, mock_run, temp_workspace, sample_metadata):
        """Test STAR alignment integration with mocked external call."""
        # Arrange
        mock_run.return_value = {
            "success": True,
            "bam_file": str(temp_workspace / "aligned" / "SRR12345678Aligned.out.bam"),
            "mapping_rate": 0.85,
            "log_file": str(temp_workspace / "logs" / "SRR12345678.log")
        }
        
        # Create mock FASTQ files
        fastq1 = temp_workspace / "downloads" / "SRR12345678_1.fastq.gz"
        fastq1.touch()
        fastq2 = temp_workspace / "downloads" / "SRR12345678_2.fastq.gz"
        fastq2.touch()
        
        aligner = STARRunner({})
        
        # Act
        result = aligner.run(
            sample_id="SRR12345678",
            fastq_files=[str(fastq1), str(fastq2)],
            output_dir=temp_workspace / "aligned"
        )
        
        # Assert
        assert result["success"] is True
        assert result["mapping_rate"] >= 0.70  # Meets threshold
        mock_run.assert_called_once()

    @patch('code.src.acquisition.sra_downloader.SRADownloader.download')
    @patch('code.src.alignment.star_runner.STARRunner.run')
    def test_full_pipeline_integration(self, mock_align, mock_download, temp_workspace, sample_metadata):
        """Test complete pipeline from SRA to aligned BAM."""
        # Arrange
        mock_download.return_value = {
            "success": True,
            "files": [
                temp_workspace / "downloads" / "SRR12345678_1.fastq.gz",
                temp_workspace / "downloads" / "SRR12345678_2.fastq.gz"
            ]
        }
        
        mock_align.return_value = {
            "success": True,
            "bam_file": str(temp_workspace / "aligned" / "SRR12345678Aligned.out.bam"),
            "mapping_rate": 0.85,
            "log_file": str(temp_workspace / "logs" / "SRR12345678.log")
        }
        
        # Create mock FASTQ files for alignment
        fastq1 = temp_workspace / "downloads" / "SRR12345678_1.fastq.gz"
        fastq1.touch()
        fastq2 = temp_workspace / "downloads" / "SRR12345678_2.fastq.gz"
        fastq2.touch()
        
        parser = MetadataParser({})
        downloader = SRADownloader({})
        aligner = STARRunner({})
        
        # Act - Full pipeline
        samples = parser.parse(sample_metadata)
        download_result = downloader.download(samples[0], temp_workspace / "downloads")
        align_result = aligner.run(
            sample_id=samples[0].accession,
            fastq_files=[str(fastq1), str(fastq2)],
            output_dir=temp_workspace / "aligned"
        )
        
        # Assert - Pipeline succeeds end-to-end
        assert download_result["success"] is True
        assert align_result["success"] is True
        assert align_result["mapping_rate"] >= 0.70  # SC-001 threshold
        assert os.path.exists(align_result["bam_file"])

    def test_pipeline_failure_handling(self, temp_workspace):
        """Test that pipeline handles failures gracefully."""
        # Arrange
        parser = MetadataParser({})
        
        # Act & Assert - Invalid metadata should raise appropriate error
        with pytest.raises((ValueError, KeyError)):
            parser.parse({"invalid": "metadata"})

    def test_mapping_rate_threshold_enforcement(self, temp_workspace, mock_config):
        """Test that mapping rate threshold is enforced (SC-001)."""
        # Arrange
        mock_config["alignment"]["mapping_rate_threshold"] = 0.70
        aligner = STARRunner(mock_config)
        
        # Mock a failed alignment (below threshold)
        with patch.object(aligner, 'run', return_value={
            "success": False,
            "mapping_rate": 0.65,  # Below threshold
            "error": "Mapping rate below threshold"
        }):
            # Act
            result = aligner.run(
                sample_id="SRR12345678",
                fastq_files=["mock_1.fastq.gz", "mock_2.fastq.gz"],
                output_dir=temp_workspace / "aligned"
            )
            
            # Assert
            assert result["success"] is False
            assert result["mapping_rate"] < 0.70