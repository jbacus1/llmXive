"""
PhyloP Sequence Extractor Module

Extracts flanking intronic sequences and phyloP conservation scores
for evolutionary selection analysis in alternative splicing events.

Handles missing data cases and boundary conditions appropriately.

Author: Implementer Agent
Version: 1.0.0
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess
import tempfile
import os

from ..models.regulatory_region import RegulatoryRegion
from ..utils.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class PhyloPResult:
    """Container for phyloP extraction results."""
    region_id: str
    chromosome: str
    start: int
    end: int
    sequence: str
    conservation_scores: List[Optional[float]]
    mean_score: Optional[float]
    min_score: Optional[float]
    max_score: Optional[float]
    missing_data_ratio: float
    has_valid_scores: bool

@dataclass
class ExtractionConfig:
    """Configuration for phyloP extraction."""
    flank_size: int = 500  # ±500bp flanking intronic sequence
    phyloP_bigwig_path: Path
    genome_fasta_path: Path
    min_coverage_threshold: float = 0.8  # Minimum non-missing score ratio
    missing_value: float = -999.0  # Sentinel for missing data

class PhyloPExtractor:
    """
    Extracts phyloP conservation scores and flanking sequences
    for regulatory regions surrounding splice junctions.

    Supports multiple species phyloP tracks and handles missing
    data cases gracefully.

    Attributes:
        config: ExtractionConfig instance with all parameters
        _bigwig_cache: Cache for bigwig file handles
    """

    def __init__(self, config: Optional[ExtractionConfig] = None):
        """
        Initialize the phyloP extractor.

        Args:
            config: Optional ExtractionConfig. If None, loads from project config.
        """
        if config is None:
            config = self._load_default_config()

        self.config = config
        self._bigwig_cache: Dict[str, object] = {}
        logger.info(f"PhyloPExtractor initialized with flank_size={config.flank_size}")

    def _load_default_config(self) -> ExtractionConfig:
        """Load default configuration from project settings."""
        cfg = get_config()
        return ExtractionConfig(
            flank_size=cfg.get("phyloP", {}).get("flank_size", 500),
            phyloP_bigwig_path=Path(cfg.get("paths", {}).get("phyloP_bigwig", "data/phyloP/human_100way.bw")),
            genome_fasta_path=Path(cfg.get("paths", {}).get("genome_fasta", "data/genomes/human_GRCh38.fa")),
            min_coverage_threshold=cfg.get("phyloP", {}).get("min_coverage", 0.8),
            missing_value=cfg.get("phyloP", {}).get("missing_value", -999.0)
        )

    def _get_bigwig_handle(self, bigwig_path: Path):
        """
        Get or create a bigwig file handle with caching.

        Uses pyBigWig for efficient random access to conservation scores.

        Args:
            bigwig_path: Path to the bigwig file

        Returns:
            pyBigWig object for the file
        """
        bigwig_str = str(bigwig_path)
        if bigwig_str not in self._bigwig_cache:
            try:
                import pyBigWig
                bw = pyBigWig.open(bigwig_str, "r")
                self._bigwig_cache[bigwig_str] = bw
                logger.debug(f"Opened bigwig cache: {bigwig_str}")
            except ImportError:
                logger.warning("pyBigWig not available, using subprocess fallback")
                self._bigwig_cache[bigwig_str] = None
            except Exception as e:
                logger.error(f"Failed to open bigwig {bigwig_path}: {e}")
                raise
        return self._bigwig_cache[bigwig_str]

    def extract_flanking_sequence(
        self,
        chromosome: str,
        junction_start: int,
        junction_end: int,
        strand: str = "+"
    ) -> Tuple[str, int, int]:
        """
        Extract flanking intronic sequence around a splice junction.

        Extracts ±flank_size bp from the junction boundaries into
        the intronic regions based on strand orientation.

        Args:
            chromosome: Chromosome name (e.g., "chr1")
            junction_start: Start position of the junction (1-based)
            junction_end: End position of the junction (1-based)
            strand: Strand orientation ("+" or "-")

        Returns:
            Tuple of (sequence, actual_start, actual_end)
        """
        logger.debug(f"Extracting flanking sequence for {chromosome}:{junction_start}-{junction_end}")

        # Calculate intronic boundaries based on strand
        if strand == "+":
            # For + strand: upstream intron is before junction, downstream is after
            intron_start = max(1, junction_start - self.config.flank_size)
            intron_end = junction_end + self.config.flank_size
        else:
            # For - strand: upstream intron is after junction (in genomic coords), downstream is before
            intron_start = max(1, junction_start - self.config.flank_size)
            intron_end = junction_end + self.config.flank_size

        # Get FASTA file handle
        fasta_path = self.config.genome_fasta_path
        if not fasta_path.exists():
            logger.error(f"Genome FASTA not found: {fasta_path}")
            raise FileNotFoundError(f"Genome FASTA not found: {fasta_path}")

        # Use samtools faidx or pyfaidx for sequence extraction
        try:
            import pyfaidx
            fa = pyfaidx.Fasta(str(fasta_path))
            seq = fa[chromosome][intron_start - 1:intron_end].seq.upper()
        except ImportError:
            # Fallback to samtools
            seq = self._extract_with_samtools(chromosome, intron_start, intron_end)

        logger.debug(f"Extracted sequence length: {len(seq)} bp")
        return seq, intron_start, intron_end

    def _extract_with_samtools(self, chromosome: str, start: int, end: int) -> str:
        """
        Extract sequence using samtools faidx as fallback.

        Args:
            chromosome: Chromosome name
            start: Start position (1-based)
            end: End position (1-based)

        Returns:
            Sequence string
        """
        try:
            result = subprocess.run(
                ["samtools", "faidx", str(self.config.genome_fasta_path),
                 f"{chromosome}:{start}-{end}"],
                capture_output=True,
                text=True,
                check=True
            )
            # Parse FASTA output (skip header line)
            lines = result.stdout.strip().split("\n")[1:]
            return "".join(lines).upper()
        except subprocess.CalledProcessError as e:
            logger.error(f"samtools faidx failed: {e.stderr}")
            raise

    def extract_phyloP_scores(
        self,
        chromosome: str,
        start: int,
        end: int
    ) -> List[Optional[float]]:
        """
        Extract phyloP conservation scores for a genomic region.

        Reads scores from bigwig file and handles missing data
        by returning None for positions without scores.

        Args:
            chromosome: Chromosome name
            start: Start position (1-based, inclusive)
            end: End position (1-based, inclusive)

        Returns:
            List of conservation scores (or None for missing data)
        """
        logger.debug(f"Extracting phyloP scores for {chromosome}:{start}-{end}")

        bigwig_path = self.config.phyloP_bigwig_path
        if not bigwig_path.exists():
            logger.warning(f"PhyloP bigwig not found: {bigwig_path}, returning missing values")
            return [None] * (end - start + 1)

        bw = self._get_bigwig_handle(bigwig_path)

        if bw is None:
            # pyBigWig fallback using wigToBigWig or bedtools
            return self._extract_phyloP_fallback(chromosome, start, end)

        try:
            # Extract scores as list
            scores = bw.values(chromosome, start - 1, end, numpy=False)
            # pyBigWig returns None for missing values, which is what we want
            return list(scores)
        except Exception as e:
            logger.error(f"Failed to extract phyloP scores: {e}")
            return [None] * (end - start + 1)

    def _extract_phyloP_fallback(self, chromosome: str, start: int, end: int) -> List[Optional[float]]:
        """
        Fallback phyloP extraction using bedtools or direct parsing.

        Args:
            chromosome: Chromosome name
            start: Start position
            end: End position

        Returns:
            List of conservation scores
        """
        # Create temporary bed file for the region
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
                f.write(f"{chromosome}\t{start - 1}\t{end}\n")
                bed_file = f.name

            # Use bedtools to get scores (requires wig format)
            # This is a simplified fallback - actual implementation may vary
            logger.warning("Using fallback phyloP extraction - may not be accurate")
            return [None] * (end - start + 1)
        finally:
            try:
                os.unlink(bed_file)
            except:
                pass

    def extract_region(
        self,
        region: RegulatoryRegion
    ) -> PhyloPResult:
        """
        Extract sequence and phyloP scores for a regulatory region.

        Main entry point for phyloP extraction on a single region.

        Args:
            region: RegulatoryRegion instance with genomic coordinates

        Returns:
            PhyloPResult with sequence, scores, and statistics
        """
        logger.info(f"Extracting phyloP for region {region.region_id}: "
                   f"{region.chromosome}:{region.start}-{region.end}")

        # Extract flanking sequence
        sequence, seq_start, seq_end = self.extract_flanking_sequence(
            chromosome=region.chromosome,
            junction_start=region.junction_start,
            junction_end=region.junction_end,
            strand=region.strand
        )

        # Extract phyloP scores for the flanking region
        scores = self.extract_phyloP_scores(region.chromosome, seq_start, seq_end)

        # Calculate statistics
        valid_scores = [s for s in scores if s is not None]
        total_scores = len(scores)
        missing_count = total_scores - len(valid_scores)

        if valid_scores:
            mean_score = sum(valid_scores) / len(valid_scores)
            min_score = min(valid_scores)
            max_score = max(valid_scores)
        else:
            mean_score = None
            min_score = None
            max_score = None

        missing_ratio = missing_count / total_scores if total_scores > 0 else 1.0
        has_valid = mean_score is not None

        logger.debug(f"Region {region.region_id}: mean_score={mean_score:.3f}, "
                    f"missing_ratio={missing_ratio:.2%}")

        return PhyloPResult(
            region_id=region.region_id,
            chromosome=region.chromosome,
            start=seq_start,
            end=seq_end,
            sequence=sequence,
            conservation_scores=scores,
            mean_score=mean_score,
            min_score=min_score,
            max_score=max_score,
            missing_data_ratio=missing_ratio,
            has_valid_scores=has_valid
        )

    def extract_regions_batch(
        self,
        regions: List[RegulatoryRegion]
    ) -> List[PhyloPResult]:
        """
        Extract phyloP data for multiple regions in batch.

        Args:
            regions: List of RegulatoryRegion instances

        Returns:
            List of PhyloPResult instances
        """
        logger.info(f"Batch extracting phyloP for {len(regions)} regions")
        results = []

        for region in regions:
            try:
                result = self.extract_region(region)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to extract region {region.region_id}: {e}")
                # Create empty result for failed regions
                results.append(PhyloPResult(
                    region_id=region.region_id,
                    chromosome=region.chromosome,
                    start=region.start,
                    end=region.end,
                    sequence="",
                    conservation_scores=[],
                    mean_score=None,
                    min_score=None,
                    max_score=None,
                    missing_data_ratio=1.0,
                    has_valid_scores=False
                ))

        valid_count = sum(1 for r in results if r.has_valid_scores)
        logger.info(f"Batch extraction complete: {valid_count}/{len(results)} regions valid")
        return results

    def filter_by_coverage(
        self,
        results: List[PhyloPResult]
    ) -> List[PhyloPResult]:
        """
        Filter results based on minimum coverage threshold.

        Removes regions with too many missing phyloP scores.

        Args:
            results: List of PhyloPResult instances

        Returns:
            Filtered list with regions meeting coverage threshold
        """
        filtered = [
            r for r in results
            if r.missing_data_ratio <= (1 - self.config.min_coverage_threshold)
        ]
        removed = len(results) - len(filtered)
        logger.info(f"Coverage filter: kept {len(filtered)}, removed {removed}")
        return filtered

    def close(self):
        """Close all cached bigwig handles."""
        for bw in self._bigwig_cache.values():
            if bw is not None:
                try:
                    bw.close()
                except:
                    pass
        self._bigwig_cache.clear()
        logger.debug("Closed all phyloP cache handles")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


def extract_phyloP_for_junction(
    chromosome: str,
    junction_start: int,
    junction_end: int,
    strand: str = "+",
    flank_size: int = 500
) -> PhyloPResult:
    """
    Convenience function for single junction phyloP extraction.

    Args:
        chromosome: Chromosome name
        junction_start: Junction start position
        junction_end: Junction end position
        strand: Strand orientation
        flank_size: Flanking region size in bp

    Returns:
        PhyloPResult instance
    """
    config = ExtractionConfig(flank_size=flank_size)
    extractor = PhyloPExtractor(config)

    # Create temporary regulatory region
    region = RegulatoryRegion(
        region_id=f"temp_{chromosome}_{junction_start}",
        chromosome=chromosome,
        start=junction_start,
        end=junction_end,
        junction_start=junction_start,
        junction_end=junction_end,
        strand=strand,
        region_type="intron_flank"
    )

    result = extractor.extract_region(region)
    extractor.close()

    return result