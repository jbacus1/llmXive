"""
rMATS Wrapper Module

Provides a Python interface for running rMATS (replicate Multivariate
Analysis of Transcript Splicing) for detecting differential splicing
events from RNA-seq data.

This wrapper handles:
- Input preparation (BAM files, junction files, sample groups)
- rMATS execution with configurable parameters
- Output parsing and result extraction
- Error handling and logging

Dependencies:
- rMATS (v4.1.0+ recommended)
- Python 3.11+
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from src.utils.config import get_config
from src.utils.checksum import calculate_file_checksum
from src.models.splice_junction import SpliceJunction
from src.models.differential_splicing_event import DifferentialSplicingEvent


class EventType(Enum):
    """Types of splicing events supported by rMATS."""
    SE = "SE"  # Skipped Exon
    A5SS = "A5SS"  # Alternative 5' Splice Site
    A3SS = "A3SS"  # Alternative 3' Splice Site
    MXE = "MXE"  # Mutually Exclusive Exons
    RI = "RI"  # Retained Intron


@dataclass
class RMatsConfig:
    """Configuration parameters for rMATS execution."""
    # Required paths
    b1: List[str]  # List of BAM file paths for group 1
    b2: List[str]  # List of BAM file paths for group 2
    t: str  # Reference transcriptome FASTA file
    gtf: str  # GTF annotation file
    output_dir: str  # Output directory for results

    # Optional parameters with defaults
    read_length: Optional[int] = None  # Read length for single-end data
    read_length1: Optional[int] = None  # Read length for group 1 (paired-end)
    read_length2: Optional[int] = None  # Read length for group 2 (paired-end)
    lib_type: str = "unstranded"  # Library type: unstranded, fr-firststrand, fr-secondstrand
    nthread: int = 4  # Number of threads
    tmp_dir: Optional[str] = None  # Temporary directory
    stat: Optional[float] = None  # Statistical threshold (default: FDR < 0.05)
    fdr: Optional[float] = None  # FDR threshold
    pval: Optional[float] = None  # P-value threshold
    delta_psi: Optional[float] = None  # Minimum |ΔPSI| threshold (default: 0.1)
    min_junction_reads: int = 20  # Minimum junction reads (per SC-002)
    min_read_coverage: int = 20  # Minimum read coverage per junction (per SC-002)
    event_type: Optional[EventType] = None  # Specific event type to analyze
    paired: bool = False  # Whether data is paired-end
    variance_method: str = "fixed"  # Variance method: fixed or random

    def to_args(self) -> List[str]:
        """Convert configuration to rMATS command-line arguments."""
        args = [
            "--b1", ",".join(self.b1),
            "--b2", ",".join(self.b2),
            "--t", self.t,
            "--gtf", self.gtf,
            "--output", self.output_dir,
            "--libType", self.lib_type,
            "--nthread", str(self.nthread),
        ]

        if self.read_length:
            args.extend(["--readLength", str(self.read_length)])
        if self.read_length1:
            args.extend(["--readLength1", str(self.read_length1)])
        if self.read_length2:
            args.extend(["--readLength2", str(self.read_length2)])
        if self.tmp_dir:
            args.extend(["--tmp", self.tmp_dir])
        if self.stat:
            args.extend(["--stat", str(self.stat)])
        if self.fdr:
            args.extend(["--fdr", str(self.fdr)])
        if self.pval:
            args.extend(["--pval", str(self.pval)])
        if self.delta_psi is not None:
            args.extend(["--deltaPSI", str(self.delta_psi)])
        if self.min_junction_reads:
            args.extend(["--minJunctionReads", str(self.min_junction_reads)])
        if self.min_read_coverage:
            args.extend(["--minReadCoverage", str(self.min_read_coverage)])
        if self.event_type:
            args.extend(["--event", self.event_type.value])
        if self.paired:
            args.append("--paired")
        if self.variance_method:
            args.extend(["--varianceMethod", self.variance_method])

        return args


class RMatsWrapper:
    """
    Wrapper class for executing rMATS differential splicing analysis.

    This class provides a high-level interface for running rMATS with
    proper error handling, logging, and result parsing.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the rMATS wrapper.

        Args:
            logger: Optional logger instance. If None, creates a new logger.
        """
        self.logger = logger or logging.getLogger(__name__)
        self.config = get_config()
        self._rmats_executable = self._find_rmats_executable()
        self._last_output: Optional[Dict[str, Any]] = None

    def _find_rmats_executable(self) -> str:
        """
        Locate the rMATS executable or entry point.

        Returns:
            Path to rMATS executable or 'rmats' if in PATH.

        Raises:
            FileNotFoundError: If rMATS is not found.
        """
        # Check common locations
        candidates = [
            "rmats",
            "rmats.py",
            "/usr/local/bin/rmats",
            "/usr/bin/rmats",
            Path.home() / ".local" / "bin" / "rmats",
        ]

        for candidate in candidates:
            if os.path.isfile(candidate) or shutil.which(candidate):
                return str(candidate)

        # Check if installed via pip
        try:
            import rmats
            return "rmats"
        except ImportError:
            pass

        raise FileNotFoundError(
            "rMATS executable not found. Please install rMATS and ensure "
            "it is in your PATH or set RMATS_PATH environment variable."
        )

    def validate_inputs(self, config: RMatsConfig) -> Tuple[bool, List[str]]:
        """
        Validate all input files and directories.

        Args:
            config: RMatsConfig instance with input paths.

        Returns:
            Tuple of (is_valid, list_of_error_messages).
        """
        errors = []

        # Validate BAM files
        for i, bam_path in enumerate(config.b1 + config.b2):
            if not os.path.isfile(bam_path):
                errors.append(f"BAM file not found: {bam_path}")
            elif not bam_path.endswith((".bam", ".bam.bai")):
                errors.append(f"BAM file has invalid extension: {bam_path}")
            else:
                # Check for index file
                index_path = bam_path + ".bai"
                if not os.path.isfile(index_path):
                    errors.append(f"BAM index not found: {index_path}")

        # Validate transcriptome file
        if not os.path.isfile(config.t):
            errors.append(f"Transcriptome FASTA not found: {config.t}")

        # Validate GTF file
        if not os.path.isfile(config.gtf):
            errors.append(f"GTF annotation file not found: {config.gtf}")

        # Validate output directory
        output_dir = Path(config.output_dir)
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                errors.append(f"Cannot create output directory: {e}")
        elif not output_dir.is_dir():
            errors.append(f"Output path exists but is not a directory: {config.output_dir}")

        # Validate thread count
        if config.nthread < 1:
            errors.append(f"Thread count must be positive: {config.nthread}")

        # Validate thresholds per spec requirements
        if config.delta_psi is not None and config.delta_psi < 0.1:
            errors.append(f"deltaPSI threshold must be >= 0.1 per spec: {config.delta_psi}")
        if config.min_junction_reads < 20:
            errors.append(f"minJunctionReads must be >= 20 per SC-002: {config.min_junction_reads}")
        if config.min_read_coverage < 20:
            errors.append(f"minReadCoverage must be >= 20 per SC-002: {config.min_read_coverage}")

        return len(errors) == 0, errors

    def run(self, config: RMatsConfig) -> Dict[str, Any]:
        """
        Execute rMATS analysis with the given configuration.

        Args:
            config: RMatsConfig instance with all parameters.

        Returns:
            Dictionary containing execution results and output paths.

        Raises:
            ValueError: If input validation fails.
            RuntimeError: If rMATS execution fails.
        """
        # Validate inputs
        is_valid, errors = self.validate_inputs(config)
        if not is_valid:
          raise ValueError(f"Input validation failed: {'; '.join(errors)}")

        self.logger.info(f"Starting rMATS analysis with {len(config.b1) + len(config.b2)} samples")
        self.logger.info(f"Output directory: {config.output_dir}")

        # Build command
        cmd = [self._rmats_executable] + config.to_args()

        self.logger.debug(f"rMATS command: {' '.join(cmd)}")

        # Execute rMATS
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
                check=False,
            )

            if result.returncode != 0:
                self.logger.error(f"rMATS failed with code {result.returncode}")
                self.logger.error(f"stdout: {result.stdout}")
                self.logger.error(f"stderr: {result.stderr}")
                raise RuntimeError(f"rMATS execution failed: {result.stderr}")

            self.logger.info("rMATS completed successfully")
            self.logger.debug(f"stdout: {result.stdout}")

        except subprocess.TimeoutExpired:
            self.logger.error("rMATS execution timed out after 1 hour")
            raise RuntimeError("rMATS execution timed out")
        except FileNotFoundError as e:
            self.logger.error(f"rMATS executable not found: {e}")
            raise

        # Parse outputs
        outputs = self._parse_outputs(config.output_dir)
        self._last_output = outputs

        return {
            "success": True,
            "output_dir": config.output_dir,
            "outputs": outputs,
            "event_counts": self._count_events(outputs),
        }

    def _parse_outputs(self, output_dir: str) -> Dict[str, Any]:
        """
        Parse rMATS output files.

        Args:
            output_dir: Path to rMATS output directory.

        Returns:
            Dictionary mapping event types to their result DataFrames.
        """
        outputs = {}
        output_path = Path(output_dir)

        # Expected output files per event type
        file_patterns = {
            EventType.SE: "ASEC.txt",
            EventType.A5SS: "AA5SS.txt",
            EventType.A3SS: "AA3SS.txt",
            EventType.MXE: "AMXE.txt",
            EventType.RI: "ARI.txt",
        }

        for event_type, filename in file_patterns.items():
            file_path = output_path / filename
            if file_path.exists():
                outputs[event_type.value] = self._parse_rmats_result(file_path)
            else:
                self.logger.warning(f"Output file not found: {file_path}")

        # Also check for IJC/SJC files
        for event_type in EventType:
            ijc_file = output_path / f"IJC.{event_type.value}.txt"
            sjc_file = output_path / f"SJC.{event_type.value}.txt"
            if ijc_file.exists() and sjc_file.exists():
                outputs[f"{event_type.value}_junctions"] = {
                    "included": ijc_file,
                    "skipped": sjc_file,
                }

        return outputs

    def _parse_rmats_result(self, file_path: Path) -> List[DifferentialSplicingEvent]:
        """
        Parse a single rMATS result file into DifferentialSplicingEvent objects.

        Args:
            file_path: Path to the rMATS result file (e.g., ASEC.txt).

        Returns:
            List of DifferentialSplicingEvent objects.
        """
        events = []

        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()

            if len(lines) < 2:
                self.logger.warning(f"Empty result file: {file_path}")
                return events

            # Parse header
            header = lines[0].strip().split('\t')

            for line in lines[1:]:
                if not line.strip():
                    continue

                values = line.strip().split('\t')
                if len(values) != len(header):
                    self.logger.warning(f"Malformed line in {file_path}: {line[:50]}...")
                    continue

                row = dict(zip(header, values))

                # Convert to DifferentialSplicingEvent
                try:
                    event = self._row_to_event(row, file_path.stem)
                    if event:
                        events.append(event)
                except (ValueError, KeyError) as e:
                    self.logger.warning(f"Failed to parse row: {e}")
                    continue

        except IOError as e:
            self.logger.error(f"Failed to read result file {file_path}: {e}")

        return events

    def _row_to_event(self, row: Dict[str, str], event_type: str) -> Optional[DifferentialSplicingEvent]:
        """
        Convert a parsed row dictionary to a DifferentialSplicingEvent.

        Args:
            row: Dictionary of parsed column values.
            event_type: Type of splicing event (SE, A5SS, etc.).

        Returns:
            DifferentialSplicingEvent object or None if invalid.
        """
        # Required fields
        required_fields = ["ID", "IJC1", "SJC1", "IJC2", "SJC2", "PValue", "FDR", "IncLevel1", "IncLevel2"]

        for field in required_fields:
            if field not in row:
              self.logger.warning(f"Missing required field {field} in row")
              return None

        # Parse numeric fields
        try:
            p_value = float(row["PValue"])
            fdr = float(row["FDR"])
            inc_level1 = float(row["IncLevel1"])
            inc_level2 = float(row["IncLevel2"])
            delta_psi = abs(inc_level1 - inc_level2)
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to parse numeric fields: {e}")
            return None

        # Apply thresholds
        if fdr >= 0.05:  # FDR threshold per spec
            return None
        if delta_psi < 0.1:  # Delta PSI threshold per spec
            return None

        # Extract junction counts
        try:
            ijc1 = int(row["IJC1"])
            sjc1 = int(row["SJC1"])
            ijc2 = int(row["IJC2"])
            sjc2 = int(row["SJC2"])

            # Apply minimum junction read threshold
            if min(ijc1, sjc1, ijc2, sjc2) < 20:
                return None
        except (ValueError, TypeError):
            return None

        return DifferentialSplicingEvent(
            event_id=row["ID"],
            event_type=event_type,
            p_value=p_value,
            fdr=fdr,
            psi_group1=inc_level1,
            psi_group2=inc_level2,
            delta_psi=delta_psi,
            junction_counts_group1={"included": ijc1, "skipped": sjc1},
            junction_counts_group2={"included": ijc2, "skipped": sjc2},
            significant=True,
        )

    def _count_events(self, outputs: Dict[str, Any]) -> Dict[str, int]:
        """
        Count significant events by type.

        Args:
            outputs: Parsed rMATS output dictionary.

        Returns:
            Dictionary mapping event types to counts.
        """
        counts = {}
        for event_type, events in outputs.items():
            if isinstance(events, list):
                counts[event_type] = len(events)
        return counts

    def get_last_output(self) -> Optional[Dict[str, Any]]:
        """
        Get the output from the last rMATS execution.

        Returns:
            Output dictionary from last run, or None if no run yet.
        """
        return self._last_output

    def batch_run(
        self,
        sample_groups: List[Dict[str, List[str]]],
        common_config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Run rMATS on multiple sample group comparisons.

        Args:
            sample_groups: List of dicts with 'group1_bams' and 'group2_bams' keys.
            common_config: Shared configuration (transcriptome, GTF, etc.).

        Returns:
            List of results dictionaries for each comparison.
        """
        results = []

        for i, groups in enumerate(sample_groups):
            self.logger.info(f"Running comparison {i+1}/{len(sample_groups)}")

            config = RMatsConfig(
                b1=groups["group1_bams"],
                b2=groups["group2_bams"],
                t=common_config["transcriptome"],
                gtf=common_config["gtf"],
                output_dir=os.path.join(common_config["output_dir"], f"comparison_{i}"),
                **{k: v for k, v in common_config.items() if k not in ["transcriptome", "gtf", "output_dir"]}
            )

            try:
                result = self.run(config)
                results.append(result)
            except (ValueError, RuntimeError) as e:
                self.logger.error(f"Comparison {i+1} failed: {e}")
                results.append({"success": False, "error": str(e)})

        return results


# Convenience functions for common use cases

def run_rmats_simple(
    group1_bams: List[str],
    group2_bams: List[str],
    transcriptome: str,
    gtf: str,
    output_dir: str,
    **kwargs,
) -> Dict[str, Any]:
    """
    Simple interface for running rMATS with minimal configuration.

    Args:
        group1_bams: List of BAM files for group 1.
        group2_bams: List of BAM files for group 2.
        transcriptome: Path to reference transcriptome FASTA.
        gtf: Path to GTF annotation file.
        output_dir: Output directory for results.
        **kwargs: Additional RMatsConfig parameters.

    Returns:
        Dictionary containing execution results.
    """
    wrapper = RMatsWrapper()
    config = RMatsConfig(
        b1=group1_bams,
        b2=group2_bams,
        t=transcriptome,
        gtf=gtf,
        output_dir=output_dir,
        **kwargs
    )
    return wrapper.run(config)


def filter_significant_events(
    events: List[DifferentialSplicingEvent],
    fdr_threshold: float = 0.05,
    delta_psi_threshold: float = 0.1,
    min_junction_reads: int = 20,
) -> List[DifferentialSplicingEvent]:
    """
    Filter differential splicing events by significance thresholds.

    Args:
        events: List of DifferentialSplicingEvent objects.
        fdr_threshold: Maximum FDR for significance (default: 0.05).
        delta_psi_threshold: Minimum |ΔPSI| for significance (default: 0.1).
        min_junction_reads: Minimum junction reads per condition (default: 20).

    Returns:
        Filtered list of significant events.
    """
    filtered = []
    for event in events:
        if event.fdr < fdr_threshold and event.delta_psi >= delta_psi_threshold:
            # Check junction counts
            if (min(event.junction_counts_group1["included"],
                    event.junction_counts_group1["skipped"],
                    event.junction_counts_group2["included"],
                    event.junction_counts_group2["skipped"]) >= min_junction_reads):
                filtered.append(event)
    return filtered