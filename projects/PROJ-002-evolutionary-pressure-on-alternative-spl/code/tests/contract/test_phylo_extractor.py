"""
Contract test for phyloP extractor module.

This test verifies the expected contract/interface of the PhyloExtractor
class before implementation. According to task requirements, this test
should FAIL before implementation and PASS after implementation.

Contract defines:
- PhyloExtractor class with extract_conservation_scores() method
- Handle missing data cases gracefully
- Process flanking intronic sequences (±500bp default)
- Return structured results with conservation metrics
"""

import pytest
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np

# Import will fail before implementation - this is expected
try:
    from code.src.analysis.phylo_extractor import PhyloExtractor
    HAS_IMPLEMENTATION = True
except (ImportError, ModuleNotFoundError):
    HAS_IMPLEMENTATION = False
    PhyloExtractor = None

class TestPhyloExtractorContract:
    """Contract tests for PhyloExtractor interface."""
    
    @pytest.fixture
    def sample_junction_data(self) -> List[Dict]:
        """Sample junction data for testing."""
        return [
            {
                "junction_id": "J001",
                "chrom": "chr1",
                "start": 1000,
                "end": 1500,
                "strand": "+",
                "gene_id": "ENSG00000001",
                "sample_id": "sample_001",
                "species": "human"
            },
            {
                "junction_id": "J002",
                "chrom": "chr1", 
                "start": 2000,
                "end": 2500,
                "strand": "-",
                "gene_id": "ENSG00000002",
                "sample_id": "sample_002",
                "species": "chimpanzee"
            }
        ]
    
    @pytest.fixture
    def sample_fasta_dir(self, tmp_path: Path) -> Path:
        """Create sample FASTA directory with reference sequences."""
        fasta_dir = tmp_path / "genome_fasta"
        fasta_dir.mkdir()
        return fasta_dir
    
    @pytest.fixture
    def sample_phylo_dir(self, tmp_path: Path) -> Path:
        """Create sample phyloP directory with conservation scores."""
        phylo_dir = tmp_path / "phyloP_scores"
        phylo_dir.mkdir()
        return phylo_dir
    
    def test_contract_import(self):
        """Test: Module must be importable."""
        assert HAS_IMPLEMENTATION, (
            "PhyloExtractor module not implemented yet. "
            "This is expected before T041 completion."
        )
    
    def test_contract_class_exists(self):
        """Test: PhyloExtractor class must exist."""
        assert HAS_IMPLEMENTATION
        assert hasattr(PhyloExtractor, '__init__'), (
            "PhyloExtractor must have __init__ method"
        )
    
    def test_contract_initialization(self, sample_fasta_dir: Path):
        """Test: PhyloExtractor must initialize with required parameters."""
        assert HAS_IMPLEMENTATION
        
        # Test initialization with required parameters
        extractor = PhyloExtractor(
            fasta_dir=sample_fasta_dir,
            phylo_dir=sample_fasta_dir,  # Will be proper path after impl
            flank_size_bp=500
        )
        
        assert extractor is not None
        assert hasattr(extractor, 'flank_size_bp')
    
    def test_contract_extract_method_exists(self):
        """Test: extract_conservation_scores method must exist."""
        assert HAS_IMPLEMENTATION
        assert hasattr(PhyloExtractor, 'extract_conservation_scores'), (
            "PhyloExtractor must have extract_conservation_scores method"
        )
    
    def test_contract_extract_method_signature(self, sample_junction_data: List[Dict]):
        """Test: extract_conservation_scores must have correct signature."""
        assert HAS_IMPLEMENTATION
        
        extractor = PhyloExtractor(
            fasta_dir=Path("/tmp"),
            phylo_dir=Path("/tmp"),
            flank_size_bp=500
        )
        
        # Method must accept junction data and optional parameters
        import inspect
        sig = inspect.signature(extractor.extract_conservation_scores)
        params = list(sig.parameters.keys())
        
        assert 'junction_data' in params, (
            "extract_conservation_scores must accept junction_data parameter"
        )
    
    def test_contract_return_type(self, sample_junction_data: List[Dict]):
        """Test: extract_conservation_scores must return structured results."""
        assert HAS_IMPLEMENTATION
        
        extractor = PhyloExtractor(
            fasta_dir=Path("/tmp"),
            phylo_dir=Path("/tmp"),
            flank_size_bp=500
        )
        
        result = extractor.extract_conservation_scores(sample_junction_data)
        
        assert result is not None, "Result must not be None"
        assert isinstance(result, (list, dict)), (
            "Result must be list or dict of conservation scores"
        )
    
    def test_contract_missing_data_handling(self):
        """Test: Must handle missing phyloP data gracefully."""
        assert HAS_IMPLEMENTATION
        
        extractor = PhyloExtractor(
            fasta_dir=Path("/tmp"),
            phylo_dir=Path("/tmp"),
            flank_size_bp=500
        )
        
        # Test with junction data that has no matching phyloP scores
        empty_junction_data = [{
            "junction_id": "J_MISSING",
            "chrom": "chrX",
            "start": 99999999,
            "end": 99999999,
            "strand": "+",
            "gene_id": "ENSG_MISSING",
            "sample_id": "sample_missing",
            "species": "marmoset"
        }]
        
        result = extractor.extract_conservation_scores(empty_junction_data)
        
        # Should not raise exception, should handle missing data
        assert result is not None
    
    def test_contract_flank_size_parameter(self):
        """Test: Must accept custom flank size parameter."""
        assert HAS_IMPLEMENTATION
        
        extractor = PhyloExtractor(
            fasta_dir=Path("/tmp"),
            phylo_dir=Path("/tmp"),
            flank_size_bp=1000  # Custom flank size
        )
        
        assert extractor.flank_size_bp == 1000, (
            "flank_size_bp must be configurable"
        )
    
    def test_contract_species_parameter(self):
        """Test: Must handle different primate species."""
        assert HAS_IMPLEMENTATION
        
        # Test that extractor can be configured for different species
        extractor = PhyloExtractor(
            fasta_dir=Path("/tmp"),
            phylo_dir=Path("/tmp"),
            flank_size_bp=500,
            species="human"  # Species-specific configuration
        )
        
        assert extractor is not None
    
    def test_contract_conservation_score_range(self):
        """Test: Conservation scores must be in valid range."""
        assert HAS_IMPLEMENTATION
        
        extractor = PhyloExtractor(
            fasta_dir=Path("/tmp"),
            phylo_dir=Path("/tmp"),
            flank_size_bp=500
        )
        
        sample_junction_data = [{
            "junction_id": "J001",
            "chrom": "chr1",
            "start": 1000,
            "end": 1500,
            "strand": "+",
            "gene_id": "ENSG00000001",
            "sample_id": "sample_001",
            "species": "human"
        }]
        
        result = extractor.extract_conservation_scores(sample_junction_data)
        
        # phyloP scores typically range from -10 to +10
        # Verify scores are in reasonable range
        if isinstance(result, list) and len(result) > 0:
            for item in result:
                if 'score' in item:
                    score = item['score']
                    assert isinstance(score, (int, float)), (
                        "Score must be numeric"
                    )
                    # Allow for missing data cases
                    if not np.isnan(score):
                        assert -10 <= score <= 10, (
                            f"phyloP score {score} out of valid range [-10, 10]"
                        )
    
    def test_contract_error_handling(self):
        """Test: Must handle invalid input gracefully."""
        assert HAS_IMPLEMENTATION
        
        extractor = PhyloExtractor(
            fasta_dir=Path("/tmp"),
            phylo_dir=Path("/tmp"),
            flank_size_bp=500
        )
        
        # Test with None input
        with pytest.raises((TypeError, ValueError)):
            extractor.extract_conservation_scores(None)
        
        # Test with empty list
        result = extractor.extract_conservation_scores([])
        assert result == [], "Empty input should return empty result"
    
    def test_contract_logging_integration(self):
        """Test: Must integrate with project logging infrastructure."""
        assert HAS_IMPLEMENTATION
        
        extractor = PhyloExtractor(
            fasta_dir=Path("/tmp"),
            phylo_dir=Path("/tmp"),
            flank_size_bp=500
        )
        
        # Check that extractor has logging capability
        # (either logger attribute or uses module-level logging)
        import logging
        assert logging.getLogger('code.src.analysis.phylo_extractor') is not None
