"""
Metadata Parser Module

Parses sample metadata from YAML configuration files.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional
import yaml

logger = logging.getLogger(__name__)

class MetadataParser:
    """Parses and validates sample metadata from YAML files."""
    
    def __init__(self, metadata_path: Path):
        self.metadata_path = metadata_path
        logger.info("MetadataParser initialized with path: %s", metadata_path)
    
    def load_metadata(self) -> Optional[Dict]:
        """
        Load metadata from YAML file.
        
        Returns:
            Parsed metadata dictionary, or None on failure
        """
        logger.info("Loading metadata from %s", self.metadata_path)
        
        if not self.metadata_path.exists():
            logger.error("Metadata file not found: %s", self.metadata_path)
            return None
        
        try:
            with open(self.metadata_path, 'r') as f:
                metadata = yaml.safe_load(f)
            logger.info("Successfully loaded metadata with %d entries", 
                       len(metadata.get('samples', [])))
            return metadata
        except yaml.YAMLError as e:
            logger.error("YAML parsing error: %s", str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error loading metadata: %s", str(e))
            return None
    
    def get_samples_by_species(self, metadata: Dict, species: str) -> List[Dict]:
        """
        Filter samples by species.
        
        Args:
            metadata: Parsed metadata dictionary
            species: Species name to filter by
        
        Returns:
            List of sample dictionaries for the specified species
        """
        logger.info("Filtering samples by species: %s", species)
        samples = metadata.get('samples', [])
        filtered = [s for s in samples if s.get('species', '').lower() == species.lower()]
        logger.info("Found %d samples for species %s", len(filtered), species)
        return filtered
    
    def validate_sample(self, sample: Dict) -> bool:
        """
        Validate a single sample entry.
        
        Args:
            sample: Sample dictionary to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['sra_id', 'species', 'tissue', 'fastq_path']
        missing = [f for f in required_fields if f not in sample]
        
        if missing:
            logger.warning("Sample missing required fields: %s. Sample: %s", 
                          missing, sample.get('sra_id', 'unknown'))
            return False
        
        logger.debug("Sample %s validation passed", sample.get('sra_id'))
        return True
    
    def get_valid_samples(self, metadata: Dict) -> List[Dict]:
        """
        Get all valid samples from metadata.
        
        Args:
            metadata: Parsed metadata dictionary
        
        Returns:
            List of valid sample dictionaries
        """
        logger.info("Validating all samples in metadata")
        samples = metadata.get('samples', [])
        valid = [s for s in samples if self.validate_sample(s)]
        logger.info("Validated %d/%d samples", len(valid), len(samples))
        return valid
