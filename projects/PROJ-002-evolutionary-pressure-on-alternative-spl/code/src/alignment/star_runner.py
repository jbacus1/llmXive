"""
STAR Alignment Runner Module

Handles alignment of RNA-seq reads using STAR aligner.
"""
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class STARRunner:
    """Runs STAR alignment for RNA-seq data."""
    
    def __init__(self, star_path: str = "STAR", genome_dir: str = None):
        self.star_path = star_path
        self.genome_dir = genome_dir
        logger.info("STARRunner initialized with star=%s, genome_dir=%s", 
                   star_path, genome_dir)
    
    def align_sample(self, fastq_path: Path, output_dir: Path, 
                    genome_dir: Path, threads: int = 8) -> Optional[Path]:
        """
        Align a single sample using STAR.
        
        Args:
            fastq_path: Path to input FASTQ file
            output_dir: Directory for alignment output
            genome_dir: Path to STAR genome index
            threads: Number of threads to use
        
        Returns:
            Path to output BAM file, or None on failure
        """
        logger.info("Starting STAR alignment for %s using %d threads", 
                   fastq_path.name, threads)
        logger.debug("Genome directory: %s, Output directory: %s", 
                    genome_dir, output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        start_time = datetime.now()
        
        try:
            # Build STAR command
            cmd = [
                self.star_path,
                "--runThreadN", str(threads),
                "--genomeDir", str(genome_dir),
                "--readFilesIn", str(fastq_path),
                "--outFileNamePrefix", str(output_dir / "Aligned."),
                "--outSAMtype", "BAM", "SortedByCoordinate",
                "--outSAMunmapped", "Within",
                "--outFilterMultimapNmax", "20",
                "--outFilterMismatchNmax", "999",
                "--outFilterMismatchNoverLmax", "0.04",
                "--alignIntronMin", "20",
                "--alignIntronMax", "1000000",
                "--alignMatesGapMax", "1000000",
            ]
            
            logger.debug("Running STAR command: %s", cmd)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=36000)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if result.returncode != 0:
                logger.error("STAR alignment failed for %s: %s", 
                            fastq_path.name, result.stderr)
                return None
            
            bam_path = output_dir / "Aligned.sortedByCoord.out.bam"
            
            if not bam_path.exists():
                logger.error("Expected BAM file not created: %s", bam_path)
                return None
            
            logger.info("STAR alignment completed for %s in %.2f seconds", 
                       fastq_path.name, elapsed)
            logger.info("Output BAM: %s (size: %d bytes)", 
                       bam_path, bam_path.stat().st_size)
            return bam_path
            
        except subprocess.TimeoutExpired:
            logger.error("STAR alignment timed out for %s", fastq_path.name)
            return None
        except Exception as e:
            logger.error("Unexpected error during STAR alignment: %s", str(e))
            return None
    
    def get_alignment_stats(self, bam_path: Path) -> Optional[Dict]:
        """
        Extract basic alignment statistics from BAM file.
        
        Args:
            bam_path: Path to BAM file
        
        Returns:
            Dictionary with alignment statistics
        """
        logger.info("Extracting alignment stats from %s", bam_path)
        
        try:
            # Use samtools flagstat for basic stats
            cmd = ["samtools", "flagstat", str(bam_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.error("samtools flagstat failed: %s", result.stderr)
                return None
            
            # Parse flagstat output
            stats = {}
            for line in result.stdout.split('\n'):
                if '+' in line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        count = int(parts[0])
                        desc = ' '.join(parts[2:])
                        stats[desc] = count
                    except ValueError:
                        continue
            
            logger.debug("Alignment stats: %s", stats)
            return stats
            
        except Exception as e:
            logger.error("Error extracting alignment stats: %s", str(e))
            return None
