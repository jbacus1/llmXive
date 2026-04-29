"""
rMATS wrapper for splicing quantification.
Wraps rMATS tool for differential splicing analysis.
"""
import logging
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Optional

from utils.config import get_config
from utils.logging import get_logger

logger = get_logger(__name__)

class RMatsWrapper:
    """Wrapper for rMATS differential splicing analysis."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize rMATS wrapper with configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or get_config()
        self.rmats_path = self.config.get('rmats_path', 'rmats.py')
        logger.info(f"Initialized rMATS wrapper with path: {self.rmats_path}")
    
    def run(
        self,
        sample_groups: Dict[str, List[Path]],
        output_dir: Path,
        reference_gtf: Path,
        n_threads: int = 4,
        tmp_dir: Optional[Path] = None
    ) -> Path:
        """Run rMATS analysis on sample groups.
        
        Args:
            sample_groups: Dict mapping group names to list of BAM file paths
            output_dir: Directory for output files
            reference_gtf: Path to reference GTF file
            n_threads: Number of threads for parallel processing
            tmp_dir: Optional temporary directory for rMATS temp files
        
        Returns:
            Path to output directory
        
        Raises:
            RuntimeError: If rMATS execution fails
        """
        logger.info(f"Starting rMATS analysis with {n_threads} threads")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Reference GTF: {reference_gtf}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            self.rmats_path,
            '--b1', self._format_bam_list(sample_groups.get('group1', [])),
            '--b2', self._format_bam_list(sample_groups.get('group2', [])),
            '--gtf', str(reference_gtf),
            '--od', str(output_dir),
            '--t', str(n_threads),
            '--readLength', str(self.config.get('read_length', 150)),
            '--cstat', str(self.config.get('cstat', 0.0001))
        ]
        
        if tmp_dir:
            cmd.extend(['--tmp', str(tmp_dir)])
            logger.info(f"Using temporary directory: {tmp_dir}")
        
        logger.debug(f"rMATS command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("rMATS analysis completed successfully")
            logger.debug(f"rMATS stdout: {result.stdout[:500]}")
        except subprocess.CalledProcessError as e:
            logger.error(f"rMATS execution failed: {e.stderr}")
            raise RuntimeError(f"rMATS failed: {e.stderr}")
        
        logger.info(f"rMATS results written to: {output_dir}")
        return output_dir
    
    def _format_bam_list(self, bam_files: List[Path]) -> str:
        """Format list of BAM files for rMATS command line.
        
        Args:
            bam_files: List of BAM file paths
        
        Returns:
            Comma-separated string of BAM file paths
        """
        return ','.join(str(f) for f in bam_files)
