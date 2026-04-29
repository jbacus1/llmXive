"""
SRA Downloader Module

Handles downloading RNA-seq data from NCBI SRA database.
"""
import logging
import subprocess
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

class SRADownloader:
    """Downloads RNA-seq samples from NCBI SRA."""
    
    def __init__(self, prefetch_path: str = "prefetch", fastq_dump_path: str = "fasterq-dump"):
        self.prefetch_path = prefetch_path
        self.fastq_dump_path = fastq_dump_path
        logger.info("SRADownloader initialized with prefetch=%s, fasterq-dump=%s", 
                   prefetch_path, fastq_dump_path)
    
    def download_sample(self, sra_id: str, output_dir: Path) -> Optional[Path]:
        """
        Download a single SRA sample.
        
        Args:
            sra_id: SRA accession ID (e.g., SRR1234567)
            output_dir: Directory to save downloaded files
        
        Returns:
            Path to downloaded FASTQ file, or None on failure
        """
        logger.info("Starting download for SRA ID: %s to %s", sra_id, output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Prefetch the SRA file
            prefetch_cmd = [self.prefetch_path, "-p", str(output_dir), sra_id]
            logger.debug("Running prefetch: %s", prefetch_cmd)
            result = subprocess.run(prefetch_cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode != 0:
                logger.error("Prefetch failed for %s: %s", sra_id, result.stderr)
                return None
            
            logger.info("Prefetch completed for %s", sra_id)
            
            # Convert to FASTQ
            fastq_cmd = [self.fastq_dump_path, "--outdir", str(output_dir), sra_id]
            logger.debug("Running fasterq-dump: %s", fastq_cmd)
            result = subprocess.run(fastq_cmd, capture_output=True, text=True, timeout=7200)
            
            if result.returncode != 0:
                logger.error("FASTQ conversion failed for %s: %s", sra_id, result.stderr)
                return None
            
            # Find the downloaded FASTQ file
            fastq_files = list(output_dir.glob("*.fastq"))
            if fastq_files:
                logger.info("Successfully downloaded %s to %s", sra_id, fastq_files[0])
                return fastq_files[0]
            
            logger.warning("No FASTQ file found after download for %s", sra_id)
            return None
            
        except subprocess.TimeoutExpired:
            logger.error("Download timed out for %s", sra_id)
            return None
        except Exception as e:
            logger.error("Unexpected error downloading %s: %s", sra_id, str(e))
            return None
    
    def download_batch(self, sra_ids: List[str], output_dir: Path) -> List[Path]:
        """
        Download multiple SRA samples.
        
        Args:
            sra_ids: List of SRA accession IDs
            output_dir: Directory to save downloaded files
        
        Returns:
            List of paths to downloaded FASTQ files
        """
        logger.info("Starting batch download for %d samples", len(sra_ids))
        downloaded = []
        
        for sra_id in sra_ids:
            logger.info("Processing sample %s of %d: %s", 
                       downloaded.index(sra_id) + 1, len(sra_ids), sra_id)
            result = self.download_sample(sra_id, output_dir)
            if result:
                downloaded.append(result)
        
        logger.info("Batch download complete: %d/%d samples downloaded successfully", 
                   len(downloaded), len(sra_ids))
        return downloaded
