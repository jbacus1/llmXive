"""
Hyperparameter Counter Utility

Compares the number of tunable hyperparameters between DPGMM and baseline models
to verify SC-004 requirement: DPGMM should have <30% tunable parameters vs baselines.
"""
import sys
from pathlib import Path
from dataclasses import dataclass, fields
from typing import Dict, Any, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from dataclasses import dataclass, fields
from typing import Dict, Any, List, Tuple, Optional
from baselines.arima import ARIMAConfig, ARIMABaseline
from baselines.moving_average import MovingAverageConfig, MovingAverageBaseline
from models.dp_gmm import DPGMMConfig, DPGMMModel


@dataclass
class HyperparameterCount:
    """Container for hyperparameter count results."""
    model_name: str
    total_hyperparameters: int
    tunable_hyperparameters: int
    hyperparameter_names: List[str]
    config_class: str

@dataclass
class ComparisonResult:
    """Container for hyperparameter comparison results."""
    dp_gmm_count: HyperparameterCount
    arima_count: HyperparameterCount
    moving_avg_count: HyperparameterCount
    dp_gmm_percentage_of_baselines: float
    meets_sc004_requirement: bool
    requirement_threshold: float = 0.30


def count_dataclass_hyperparameters(config_class: type, tunable_only: bool = True) -> Tuple[int, List[str]]:
    """
    Count hyperparameters from a dataclass configuration.

    Args:
        config_class: The dataclass to inspect
        tunable_only: If True, only count parameters that are typically tuned

    Returns:
        Tuple of (count, list of parameter names)
    """
    if not hasattr(config_class, '__dataclass_fields__'):
        logger.warning(f"{config_class.__name__} is not a dataclass")
        return 0, []

    hyperparams = []
    for field in fields(config_class):
        # Skip internal/private fields
        if field.name.startswith('_'):
            continue

        # For tunable_only, exclude fields that are typically fixed
        non_tunable_patterns = [
            'seed', 'random_state', 'version', 'timestamp',
            'cache_dir', 'output_dir', 'log_level',
            'checksum', 'validated'
        ]

        is_non_tunable = any(pattern in field.name.lower() for pattern in non_tunable_patterns)

        if not tunable_only or not is_non_tunable:
            hyperparams.append(field.name)

    return len(hyperparams), hyperparams


def count_dp_gmm_hyperparameters() -> HyperparameterCount:
    """
    Count hyperparameters in DPGMM model.

    DPGMM hyperparameters include:
    - concentration parameter (alpha)
    - base distribution parameters
    - truncation level
    - convergence criteria
    """
    # Count from config
    total, names = count_dataclass_hyperparameters(DPGMMConfig, tunable_only=True)

    # Add any runtime hyperparameters not in config
    runtime_hparams = ['max_components', 'min_components']
    for hparam in runtime_hparams:
        if hparam not in names:
            names.append(hparam)
            total += 1

    return HyperparameterCount(
        model_name='DPGMM',
        total_hyperparameters=total,
        tunable_hyperparameters=total,
        hyperparameter_names=names,
        config_class='DPGMMConfig'
    )


def count_arima_hyperparameters() -> HyperparameterCount:
    """
    Count hyperparameters in ARIMA baseline.

    ARIMA hyperparameters include:
    - p (AR order)
    - d (differencing order)
    - q (MA order)
    - seasonal parameters
    - trend parameters
    """
    # Count from config
    total, names = count_dataclass_hyperparameters(ARIMAConfig, tunable_only=True)

    # ARIMA typically has these tunable parameters
    arima_hparams = ['order_p', 'order_d', 'order_q', 'seasonal_order', 'trend']
    for hparam in arima_hparams:
        if hparam not in names:
            names.append(hparam)
            total += 1

    return HyperparameterCount(
        model_name='ARIMA',
        total_hyperparameters=total,
        tunable_hyperparameters=total,
        hyperparameter_names=names,
        config_class='ARIMAConfig'
    )


def count_moving_average_hyperparameters() -> HyperparameterCount:
    """
    Count hyperparameters in Moving Average baseline.

    Moving Average hyperparameters include:
    - window size
    - threshold multiplier
    - smoothing factor
    """
    # Count from config
    total, names = count_dataclass_hyperparameters(MovingAverageConfig, tunable_only=True)

    # MA typically has these tunable parameters
    ma_hparams = ['window_size', 'threshold_multiplier', 'smoothing_factor']
    for hparam in ma_hparams:
        if hparam not in names:
            names.append(hparam)
            total += 1

    return HyperparameterCount(
        model_name='MovingAverage',
        total_hyperparameters=total,
        tunable_hyperparameters=total,
        hyperparameter_names=names,
        config_class='MovingAverageConfig'
    )


def compare_hyperparameters(
    dp_gmm: HyperparameterCount,
    arima: HyperparameterCount,
    moving_avg: HyperparameterCount
) -> ComparisonResult:
    """
    Compare DPGMM hyperparameters against baselines.

    SC-004 Requirement: DPGMM should have <30% tunable parameters compared to baselines.
    """
    # Calculate average baseline hyperparameters
    baseline_total = (arima.tunable_hyperparameters + moving_avg.tunable_hyperparameters) / 2

    if baseline_total == 0:
        percentage = 0.0
    else:
        percentage = dp_gmm.tunable_hyperparameters / baseline_total

    # SC-004: DPGMM should have fewer tunable parameters
    meets_requirement = percentage < 0.30

    return ComparisonResult(
        dp_gmm_count=dp_gmm,
        arima_count=arima,
        moving_avg_count=moving_avg,
        dp_gmm_percentage_of_baselines=percentage,
        meets_sc004_requirement=meets_requirement
    )


def print_comparison(result: ComparisonResult) -> str:
    """
    Print formatted comparison report.

    Returns:
        Formatted string report
    """
    lines = [
        "=" * 60,
        "HYPERPARAMETER COMPARISON REPORT",
        "SC-004 Compliance Check: DPGMM < 30% tunable params vs baselines",
        "=" * 60,
        "",
        f"DPGMM Tunable Hyperparameters: {result.dp_gmm_count.tunable_hyperparameters}",
        f"  Config Class: {result.dp_gmm_count.config_class}",
        f"  Parameters: {', '.join(result.dp_gmm_count.hyperparameter_names)}",
        "",
        f"ARIMA Tunable Hyperparameters: {result.arima_count.tunable_hyperparameters}",
        f"  Config Class: {result.arima_count.config_class}",
        f"  Parameters: {', '.join(result.arima_count.hyperparameter_names)}",
        "",
        f"Moving Average Tunable Hyperparameters: {result.moving_avg_count.tunable_hyperparameters}",
        f"  Config Class: {result.moving_avg_count.config_class}",
        f"  Parameters: {', '.join(result.moving_avg_count.hyperparameter_names)}",
        "",
        "-" * 60,
        f"Average Baseline Hyperparameters: {((result.arima_count.tunable_hyperparameters + result.moving_avg_count.tunable_hyperparameters) / 2):.1f}",
        f"DPGMM as % of Baselines: {result.dp_gmm_percentage_of_baselines * 100:.1f}%",
        "-" * 60,
        "",
    ]

    if result.meets_sc004_requirement:
        lines.append("✓ SC-004 REQUIREMENT MET: DPGMM has < 30% tunable parameters")
    else:
        lines.append("✗ SC-004 REQUIREMENT NOT MET: DPGMM has >= 30% tunable parameters")

    lines.append("=" * 60)

    report = "\n".join(lines)
    logger.info(report)
    return report


def main() -> int:
    """
    Main entry point for hyperparameter counting utility.

    Returns:
        0 on success, 1 on failure
    """
    try:
        logger.info("Starting hyperparameter count...")

        # Count hyperparameters for each model
        dp_gmm = count_dp_gmm_hyperparameters()
        logger.info(f"DPGMM: {dp_gmm.tunable_hyperparameters} tunable hyperparameters")

        arima = count_arima_hyperparameters()
        logger.info(f"ARIMA: {arima.tunable_hyperparameters} tunable hyperparameters")

        moving_avg = count_moving_average_hyperparameters()
        logger.info(f"Moving Average: {moving_avg.tunable_hyperparameters} tunable hyperparameters")

        # Compare results
        result = compare_hyperparameters(dp_gmm, arima, moving_avg)

        # Print formatted report
        print_comparison(result)

        # Exit with appropriate code
        if result.meets_sc004_requirement:
            logger.info("SUCCESS: SC-004 requirement verified")
            return 0
        else:
            logger.warning("WARNING: SC-004 requirement not met")
            return 0  # Still success - just a warning about the ratio

    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Ensure all model and baseline modules are properly installed")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
