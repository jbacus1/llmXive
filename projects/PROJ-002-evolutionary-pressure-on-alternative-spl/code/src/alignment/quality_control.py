"""
Quality Control Module for Alignment

Performs quality control checks on aligned RNA-seq data.
"""
import logging
from pathlib import Path
from typing import Optional, Dict
import subprocess

logger = logging.getLogger(__name__)

class QualityControl:
    """Performs quality control on aligned BAM files."""
    
    def __init__(self, min_mapping_rate: float = 0.70):
        self.min_mapping_rate = min_mapping_rate
        logger.info("QualityControl initialized with min_mapping_rate=%.2f", 
                   min_mapping_rate)
    
    def check_mapping_rate(self, bam_path: Path) -> Optional[Dict]:
        """
        Check the mapping rate of a BAM file.
        
        Args:
            bam_path: Path to BAM file
        
        Returns:
            Dictionary with mapping statistics, or None on failure
        """
        logger.info("Checking mapping rate for %s", bam_path)
        
        try:
            # Use samtools flagstat
            cmd = ["samtools", "flagstat", str(bam_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.error("samtools flagstat failed: %s", result.stderr)
                return None
            
            # Parse output
            total_reads = 0
            mapped_reads = 0
            
            for line in result.stdout.split('\n'):
                if 'mapped' in line.lower() and '+' not in line:
                    try:
                        count = int(line.split()[0])
                        if 'primary' in line.lower():
                            mapped_reads = count
                        else:
                            total_reads = count
                    except (ValueError, IndexError):
                        continue
            
            if total_reads == 0:
                logger.warning("No total reads found in BAM file: %s", bam_path)
                return None
            
            mapping_rate = mapped_reads / total_reads
            logger.info("Mapping rate for %s: %.2f%% (%d/%d reads)", 
                       bam_path.name, mapping_rate * 100, mapped_reads, total_reads)
            
            return {
                'total_reads': total_reads,
                'mapped_reads': mapped_reads,
                'mapping_rate': mapping_rate,
                'passed': mapping_rate >= self.min_mapping_rate
            }
            
        except Exception as e:
            logger.error("Error checking mapping rate: %s", str(e))
            return None
    
    def validate_alignment(self, bam_path: Path) -> bool:
        """
        Validate that a BAM file meets quality thresholds.
        
        Args:
            bam_path: Path to BAM file
        
        Returns:
            True if validation passes, False otherwise
        """
        logger.info("Validating alignment quality for %s", bam_path)
        
        stats = self.check_mapping_rate(bam_path)
        
        if stats is None:
            logger.error("Could not compute mapping statistics for %s", bam_path)
            return False
        
        if not stats['passed']:
            logger.warning("Mapping rate %.2f%% below threshold %.2f%% for %s", 
                          stats['mapping_rate'] * 100, 
                          self.min_mapping_rate * 100,
                          bam_path.name)
            return False
        
        logger.info("Alignment validation passed for %s", bam_path.name)
        return True
    
    def run_multiqc(self, output_dir: Path, bam_files: list = None) -> Optional[Path]:
        """
        Run MultiQC to generate quality reports.
        
        Args:
            output_dir: Directory containing alignment files
            bam_files: Optional list of specific BAM files to include
        
        Returns:
            Path to MultiQC report, or None on failure
        """
        logger.info("Running MultiQC on %s", output_dir)
        
        try:
            cmd = ["multiqc", str(output_dir), "-o", str(output_dir)]
            if bam_files:
                cmd.extend([str(f) for f in bam_files])
            
            logger.debug("MultiQC command: %s", cmd)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.warning("MultiQC returned non-zero: %s", result.stderr)
                # MultiQC often returns non-zero but still generates reports
            
            report_path = output_dir / "multiqc_report.html"
            if report_path.exists():
                logger.info("MultiQC report generated: %s", report_path)
                return report_path
            
            logger.warning("MultiQC report not found at expected location")
            return None
            
        except Exception as e:
            logger.error("Error running MultiQC: %s", str(e))
            return None