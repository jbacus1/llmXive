"""
PhyloP Conservation Score Handler

Handles phyloP conservation score processing including:
- Reading score files from various sources
- Handling missing/NA/null values appropriately
- Providing sensible defaults for missing data
- Filtering and validation utilities
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Constants for missing data handling
MISSING_VALUES = {'NA', 'na', 'NaN', 'nan', 'NULL', 'null', 'None', 'none', '-999', ''}
DEFAULT_MISSING_SCORE = 0.0  # Neutral conservation score for missing data
MIN_VALID_SCORE = -10.0      # Minimum valid phyloP score (highly accelerated)
MAX_VALID_SCORE = 10.0       # Maximum valid phyloP score (highly conserved)

class PhyloPScoreHandler:
    """
    Handler for phyloP conservation scores with robust missing data support.
    
    PhyloP scores measure evolutionary conservation at individual nucleotides:
    - Positive values: conserved (slower evolution than neutral)
    - Negative values: accelerated (faster evolution than neutral)
    - Zero: neutral evolution
    """
    
    def __init__(
        self,
        default_score: float = DEFAULT_MISSING_SCORE,
        min_score: float = MIN_VALID_SCORE,
        max_score: float = MAX_VALID_SCORE,
        treat_missing_as_neutral: bool = True
    ):
        """
        Initialize the phyloP score handler.
        
        Args:
            default_score: Score to use when data is missing
            min_score: Minimum valid score threshold
            max_score: Maximum valid score threshold
            treat_missing_as_neutral: If True, missing values get neutral score (0)
        """
        self.default_score = default_score if not treat_missing_as_neutral else 0.0
        self.min_score = min_score
        self.max_score = max_score
        self.treat_missing_as_neutral = treat_missing_as_neutral
        self._missing_count = 0
        self._total_count = 0
    
    def parse_score(self, value: Union[str, float, int, None]) -> Tuple[Optional[float], bool]:
        """
        Parse a single phyloP score value, handling missing data cases.
        
        Args:
            value: Raw score value (string, float, int, or None)
        
        Returns:
            Tuple of (parsed_score, is_missing)
        """
        self._total_count += 1
        
        # Handle None explicitly
        if value is None:
            self._missing_count += 1
            return (self.default_score, True)
        
        # Handle string values
        if isinstance(value, str):
            stripped = value.strip()
            if stripped in MISSING_VALUES or stripped == '':
                self._missing_count += 1
                return (self.default_score, True)
            try:
                parsed = float(stripped)
                return self._validate_score(parsed)
            except ValueError:
                logger.warning(f"Invalid phyloP score value: {value}")
                self._missing_count += 1
                return (self.default_score, True)
        
        # Handle numeric values
        if isinstance(value, (int, float)):
            # Check for NaN and Inf
            if isinstance(value, float):
                if np.isnan(value) or np.isinf(value):
                    self._missing_count += 1
                    return (self.default_score, True)
            return self._validate_score(value)
        
        # Unknown type
        logger.warning(f"Unknown score type: {type(value)}")
        self._missing_count += 1
        return (self.default_score, True)
    
    def _validate_score(self, score: float) -> Tuple[Optional[float], bool]:
        """
        Validate and clip score to acceptable range.
        
        Args:
            score: Numeric score value
        
        Returns:
            Tuple of (clipped_score, was_clipped)
        """
        was_clipped = False
        
        if score < self.min_score:
            logger.warning(f"Score {score} below minimum {self.min_score}, clipping")
            score = self.min_score
            was_clipped = True
        elif score > self.max_score:
            logger.warning(f"Score {score} above maximum {self.max_score}, clipping")
            score = self.max_score
            was_clipped = True
        
        return (score, was_clipped)
    
    def parse_score_list(
        self,
        values: List[Union[str, float, int, None]]
    ) -> List[float]:
        """
        Parse a list of phyloP score values with missing data handling.
        
        Args:
            values: List of raw score values
        
        Returns:
            List of parsed and validated scores
        """
        parsed_scores = []
        for value in values:
            score, is_missing = self.parse_score(value)
            parsed_scores.append(score)
        return parsed_scores
    
    def get_missing_rate(self) -> float:
        """
        Calculate the rate of missing data encountered.
        
        Returns:
            Fraction of values that were missing (0.0 to 1.0)
        """
        if self._total_count == 0:
            return 0.0
        return self._missing_count / self._total_count
    
    def reset_statistics(self):
        """Reset missing data statistics."""
        self._missing_count = 0
        self._total_count = 0
    
    def filter_scores(
        self,
        scores: List[float],
        min_score: Optional[float] = None,
        max_score: Optional[float] = None
    ) -> List[float]:
        """
        Filter scores based on threshold values.
        
        Args:
            scores: List of phyloP scores
            min_score: Minimum score to include (default: class min_score)
            max_score: Maximum score to include (default: class max_score)
        
        Returns:
            Filtered list of scores
        """
        min_threshold = min_score if min_score is not None else self.min_score
        max_threshold = max_score if max_score is not None else self.max_score
        
        return [
            score for score in scores
            if min_threshold <= score <= max_threshold
        ]
    
    def get_conservation_category(self, score: float) -> str:
        """
        Categorize a conservation score.
        
        Args:
            score: phyloP score value
        
        Returns:
            Category string: 'accelerated', 'neutral', or 'conserved'
        """
        if score < -0.5:
            return 'accelerated'
        elif score > 0.5:
            return 'conserved'
        else:
            return 'neutral'
    
    def get_statistics(self, scores: List[float]) -> Dict[str, float]:
        """
        Calculate summary statistics for a list of scores.
        
        Args:
            scores: List of phyloP scores
        
        Returns:
            Dictionary with mean, median, std, min, max
        """
        if not scores:
            return {
                'mean': 0.0,
                'median': 0.0,
                'std': 0.0,
                'min': 0.0,
                'max': 0.0,
                'count': 0
            }
        
        return {
            'mean': float(np.mean(scores)),
            'median': float(np.median(scores)),
            'std': float(np.std(scores)),
            'min': float(np.min(scores)),
            'max': float(np.max(scores)),
            'count': len(scores)
        }

def handle_missing_phyloP_scores(
    score_file: str,
    output_file: str,
    fill_value: float = 0.0
) -> Dict[str, int]:
    """
    Convenience function to process a phyloP score file with missing data handling.
    
    Args:
        score_file: Path to input phyloP score file
        output_file: Path to output processed file
        fill_value: Value to use for missing data
    
    Returns:
        Dictionary with processing statistics
    """
    handler = PhyloPScoreHandler(default_score=fill_value)
    processed_count = 0
    missing_count = 0
    
    with open(score_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            
            # Assume format: chr pos score [other columns...]
            score_value = parts[2] if len(parts) > 2 else None
            parsed_score, is_missing = handler.parse_score(score_value)
            
            if is_missing:
                missing_count += 1
            
            # Reconstruct line with processed score
            parts[2] = str(parsed_score)
            outfile.write('\t'.join(parts) + '\n')
            processed_count += 1
    
    return {
        'processed': processed_count,
        'missing': missing_count,
        'missing_rate': handler.get_missing_rate()
    }

# Module-level handler instance for convenience
_default_handler = PhyloPScoreHandler()

def get_default_handler() -> PhyloPScoreHandler:
    """Get the default phyloP score handler instance."""
    return _default_handler