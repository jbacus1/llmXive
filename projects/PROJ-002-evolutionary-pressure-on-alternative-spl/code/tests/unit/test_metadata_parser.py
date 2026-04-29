"""
Unit tests for metadata parser functionality (US1).

These tests verify the metadata parser can correctly parse
sample metadata from various formats and handle edge cases.

NOTE: These tests are written FIRST (TDD approach) and will FAIL
until T018 (metadata parser implementation) is complete.
"""

import pytest
import yaml
from pathlib import Path
from typing import Dict, List, Any

# Import the module under test (will fail until T018 is implemented)
try:
    from code.src.acquisition.metadata_parser import (
        MetadataParser,
        parse_sample_metadata,
        validate_metadata_schema,
        MetadataValidationError
    )
    METADATA_PARSER_AVAILABLE = True
except ImportError:
    METADATA_PARSER_AVAILABLE = False


@pytest.fixture
def sample_metadata_dict() -> Dict[str, Any]:
    """Sample metadata structure for testing."""
    return {
        "samples": [
            {
                "sample_id": "SRR123456",
                "species": "Homo sapiens",
                "tissue": "cortex",
                "accession": "SRA:SRP123456",
                "read_type": "paired",
                "read_length": 150,
                "library_type": "stranded",
                "sequencing_center": "NCBI"
            },
            {
                "sample_id": "SRR789012",
                "species": "Pan troglodytes",
                "tissue": "cortex",
                "accession": "SRA:SRP789012",
                "read_type": "paired",
                "read_length": 150,
                "library_type": "stranded",
                "sequencing_center": "NCBI"
            }
        ]
    }


@pytest.fixture
def minimal_metadata_dict() -> Dict[str, Any]:
    """Minimal valid metadata structure."""
    return {
        "samples": [
            {
                "sample_id": "SRR000001",
                "species": "Homo sapiens",
                "tissue": "cortex",
                "accession": "SRA:SRP000001"
            }
        ]
    }


@pytest.fixture
def invalid_metadata_dict() -> Dict[str, Any]:
    """Metadata with missing required fields."""
    return {
        "samples": [
            {
                "sample_id": "SRR000001",
                # Missing: species, tissue, accession
                "read_type": "paired"
            }
        ]
    }


@pytest.fixture
def yaml_metadata_file(tmp_path: Path) -> Path:
    """Create a temporary YAML metadata file."""
    metadata = {
        "metadata_version": "1.0",
        "project": "PROJ-002-evolutionary-pressure-on-alternative-spl",
        "samples": [
            {
                "sample_id": "SRR123456",
                "species": "Homo sapiens",
                "tissue": "cortex",
                "accession": "SRA:SRP123456",
                "read_type": "paired",
                "read_length": 150
            }
        ]
    }
    yaml_file = tmp_path / "metadata.yaml"
    with open(yaml_file, 'w') as f:
        yaml.dump(metadata, f)
    return yaml_file


class TestMetadataParserInstantiation:
    """Tests for MetadataParser class instantiation."""
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_parser_initialization(self):
        """Test that MetadataParser can be instantiated."""
        parser = MetadataParser()
        assert parser is not None
        assert hasattr(parser, 'parse')
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_parser_with_custom_schema(self):
        """Test parser with custom validation schema."""
        schema = {
            "required_fields": ["sample_id", "species", "tissue"]
        }
        parser = MetadataParser(schema=schema)
        assert parser.schema == schema


class TestParseSampleMetadata:
    """Tests for parse_sample_metadata function."""
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_parse_valid_metadata(self, sample_metadata_dict):
        """Test parsing valid metadata dictionary."""
        result = parse_sample_metadata(sample_metadata_dict)
        assert len(result) == 2
        assert result[0]["sample_id"] == "SRR123456"
        assert result[1]["species"] == "Pan troglodytes"
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_parse_minimal_metadata(self, minimal_metadata_dict):
        """Test parsing minimal valid metadata."""
        result = parse_sample_metadata(minimal_metadata_dict)
        assert len(result) == 1
        assert result[0]["sample_id"] == "SRR000001"
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_parse_empty_samples(self):
        """Test parsing metadata with no samples."""
        result = parse_sample_metadata({"samples": []})
        assert len(result) == 0
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_parse_empty_metadata(self):
        """Test parsing completely empty metadata."""
        with pytest.raises(MetadataValidationError):
            parse_sample_metadata({})
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_parse_metadata_from_yaml_file(self, yaml_metadata_file):
        """Test parsing metadata from YAML file."""
        result = parse_sample_metadata(yaml_metadata_file)
        assert len(result) == 1
        assert result[0]["sample_id"] == "SRR123456"


class TestValidateMetadataSchema:
    """Tests for validate_metadata_schema function."""
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_validate_complete_metadata(self, sample_metadata_dict):
        """Test validation of complete metadata."""
        is_valid, errors = validate_metadata_schema(sample_metadata_dict)
        assert is_valid is True
        assert len(errors) == 0
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_validate_missing_required_fields(self, invalid_metadata_dict):
        """Test validation catches missing required fields."""
        is_valid, errors = validate_metadata_schema(invalid_metadata_dict)
        assert is_valid is False
        assert len(errors) > 0
        assert any("species" in str(e) or "tissue" in str(e) for e in errors)
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_validate_missing_samples_key(self):
        """Test validation catches missing samples key."""
        is_valid, errors = validate_metadata_schema({"other_key": "value"})
        assert is_valid is False
        assert any("samples" in str(e) for e in errors)


class TestSpeciesValidation:
    """Tests for species-specific validation."""
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_validate_supported_species(self):
        """Test that supported species are accepted."""
        supported_species = [
            "Homo sapiens",
            "Pan troglodytes", 
            "Macaca mulatta",
            "Callithrix jacchus"
        ]
        for species in supported_species:
            metadata = {
                "samples": [{
                    "sample_id": "SRR001",
                    "species": species,
                    "tissue": "cortex",
                    "accession": "SRA:SRP001"
                }]
            }
            is_valid, _ = validate_metadata_schema(metadata)
            assert is_valid is True
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_validate_unsupported_species(self):
        """Test that unsupported species are rejected."""
        metadata = {
            "samples": [{
                "sample_id": "SRR001",
                "species": "Mus musculus",  # Not in supported list
                "tissue": "cortex",
                "accession": "SRA:SRP001"
            }]
        }
        is_valid, errors = validate_metadata_schema(metadata)
        assert is_valid is False


class TestTissueValidation:
    """Tests for tissue-specific validation."""
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_validate_cortex_tissue(self):
        """Test that cortex tissue is accepted."""
        metadata = {
            "samples": [{
                "sample_id": "SRR001",
                "species": "Homo sapiens",
                "tissue": "cortex",
                "accession": "SRA:SRP001"
            }]
        }
        is_valid, _ = validate_metadata_schema(metadata)
        assert is_valid is True
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_validate_case_insensitive_tissue(self):
        """Test that tissue matching is case-insensitive."""
        metadata = {
            "samples": [{
                "sample_id": "SRR001",
                "species": "Homo sapiens",
                "tissue": "CORTEX",
                "accession": "SRA:SRP001"
            }]
        }
        is_valid, errors = validate_metadata_schema(metadata)
        # Should pass due to case-insensitive matching
        assert is_valid is True


class TestAccessionValidation:
    """Tests for SRA accession validation."""
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_validate_sra_accession_format(self):
        """Test SRA accession format validation."""
        valid_accessions = [
            "SRA:SRP123456",
            "SRP123456",
            "SRR123456",
            "ERR123456"
        ]
        for accession in valid_accessions:
            metadata = {
                "samples": [{
                    "sample_id": "SRR001",
                    "species": "Homo sapiens",
                    "tissue": "cortex",
                    "accession": accession
                }]
            }
            is_valid, _ = validate_metadata_schema(metadata)
            assert is_valid is True
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_validate_invalid_accession_format(self):
        """Test that invalid accession formats are rejected."""
        metadata = {
            "samples": [{
                "sample_id": "SRR001",
                "species": "Homo sapiens",
                "tissue": "cortex",
                "accession": "INVALID-ACCESSION"
            }]
        }
        is_valid, errors = validate_metadata_schema(metadata)
        assert is_valid is False


class TestReadTypeValidation:
    """Tests for read type validation."""
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_validate_paired_end(self):
        """Test paired-end read type."""
        metadata = {
            "samples": [{
                "sample_id": "SRR001",
                "species": "Homo sapiens",
                "tissue": "cortex",
                "accession": "SRA:SRP001",
                "read_type": "paired"
            }]
        }
        is_valid, _ = validate_metadata_schema(metadata)
        assert is_valid is True
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_validate_single_end(self):
        """Test single-end read type."""
        metadata = {
            "samples": [{
                "sample_id": "SRR001",
                "species": "Homo sapiens",
                "tissue": "cortex",
                "accession": "SRA:SRP001",
                "read_type": "single"
            }]
        }
        is_valid, _ = validate_metadata_schema(metadata)
        assert is_valid is True
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_validate_invalid_read_type(self):
        """Test that invalid read types are rejected."""
        metadata = {
            "samples": [{
                "sample_id": "SRR001",
                "species": "Homo sapiens",
                "tissue": "cortex",
                "accession": "SRA:SRP001",
                "read_type": "invalid_type"
            }]
        }
        is_valid, errors = validate_metadata_schema(metadata)
        assert is_valid is False


class TestMetadataParserEdgeCases:
    """Tests for edge cases and error handling."""
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_parse_duplicate_sample_ids(self):
        """Test handling of duplicate sample IDs."""
        metadata = {
            "samples": [
                {"sample_id": "SRR001", "species": "Homo sapiens", "tissue": "cortex", "accession": "SRA:SRP001"},
                {"sample_id": "SRR001", "species": "Pan troglodytes", "tissue": "cortex", "accession": "SRA:SRP002"}
            ]
        }
        with pytest.raises(MetadataValidationError):
            parse_sample_metadata(metadata)
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_parse_null_values(self):
        """Test handling of null/None values."""
        metadata = {
            "samples": [
                {"sample_id": "SRR001", "species": None, "tissue": "cortex", "accession": "SRA:SRP001"}
            ]
        }
        is_valid, errors = validate_metadata_schema(metadata)
        assert is_valid is False
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_parse_extra_fields_ignored(self, sample_metadata_dict):
        """Test that extra fields are allowed but ignored."""
        sample_metadata_dict["samples"][0]["extra_field"] = "should_be_ignored"
        result = parse_sample_metadata(sample_metadata_dict)
        assert result[0]["sample_id"] == "SRR123456"
        # Extra field should not be in parsed result
        assert "extra_field" not in result[0] or result[0].get("extra_field") is None


class TestMetadataParserIntegration:
    """Integration-style unit tests for metadata parser."""
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_parse_multiple_species(self):
        """Test parsing metadata with multiple species."""
        metadata = {
            "samples": [
                {"sample_id": "SRR001", "species": "Homo sapiens", "tissue": "cortex", "accession": "SRA:SRP001"},
                {"sample_id": "SRR002", "species": "Pan troglodytes", "tissue": "cortex", "accession": "SRA:SRP002"},
                {"sample_id": "SRR003", "species": "Macaca mulatta", "tissue": "cortex", "accession": "SRA:SRP003"},
                {"sample_id": "SRR004", "species": "Callithrix jacchus", "tissue": "cortex", "accession": "SRA:SRP004"}
            ]
        }
        result = parse_sample_metadata(metadata)
        assert len(result) == 4
        species_list = [s["species"] for s in result]
        assert "Homo sapiens" in species_list
        assert "Pan troglodytes" in species_list
        assert "Macaca mulatta" in species_list
        assert "Callithrix jacchus" in species_list
    
    @pytest.mark.skipif(not METADATA_PARSER_AVAILABLE, reason="Metadata parser not yet implemented")
    def test_parse_preserves_all_fields(self):
        """Test that all valid fields are preserved in parsed output."""
        metadata = {
            "samples": [{
                "sample_id": "SRR001",
                "species": "Homo sapiens",
                "tissue": "cortex",
                "accession": "SRA:SRP001",
                "read_type": "paired",
                "read_length": 150,
                "library_type": "stranded",
                "sequencing_center": "NCBI"
            }]
        }
        result = parse_sample_metadata(metadata)
        assert result[0]["sample_id"] == "SRR001"
        assert result[0]["species"] == "Homo sapiens"
        assert result[0]["tissue"] == "cortex"
        assert result[0]["accession"] == "SRA:SRP001"
        assert result[0]["read_type"] == "paired"
        assert result[0]["read_length"] == 150
        assert result[0]["library_type"] == "stranded"
        assert result[0]["sequencing_center"] == "NCBI"