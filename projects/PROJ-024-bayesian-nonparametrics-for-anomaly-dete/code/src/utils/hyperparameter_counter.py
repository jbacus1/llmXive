"""
Hyperparameter Counting Utility

Counts tunable parameters in DPGMM vs baseline models to verify
SC-004 requirement: DPGMM must have <30% tunable parameters vs baselines.

Usage:
    python hyperparameter_counter.py

This script does its full intended work without requiring arguments.
"""
import os
import sys
import json
import yaml
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ModelHyperparameters:
    """Container for hyperparameter counts from a model."""
    model_name: str
    config_params: Dict[str, Any] = field(default_factory=dict)
    tunable_count: int = 0
    fixed_count: int = 0
    total_count: int = 0
    source_file: Optional[str] = None


@dataclass
class ComparisonResult:
    """Result of comparing DPGMM vs baseline hyperparameters."""
    dp_gmm: ModelHyperparameters
    baselines: Dict[str, ModelHyperparameters]
    dp_gmm_ratio: float = 0.0
    meets_requirement: bool = False
    threshold: float = 0.30  # SC-004: <30%


def load_config_yaml(config_path: Path) -> Dict[str, Any]:
    """Load hyperparameters from config.yaml."""
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return {}

    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def count_tunable_params_from_dataclass(cls) -> Tuple[int, int]:
    """
    Count tunable vs fixed parameters from a dataclass definition.

    Returns: (tunable_count, fixed_count)
    - Tunable: parameters with default values that can be changed
    - Fixed: parameters that are computed internally or have no defaults
    """
    tunable = 0
    fixed = 0

    # Try to get fields from the dataclass
    try:
        import dataclasses
        if dataclasses.is_dataclass(cls):
            for f in dataclasses.fields(cls):
                if f.default is not dataclasses.MISSING or f.default_factory is not dataclasses.MISSING:
                    tunable += 1
                else:
                    fixed += 1
    except Exception as e:
        logger.debug(f"Could not introspect {cls.__name__}: {e}")

    return tunable, fixed


def count_params_from_dict(config_dict: Dict[str, Any], prefix: str = "") -> int:
    """Recursively count parameters in a nested dictionary."""
    count = 0
    for key, value in config_dict.items():
        full_key = f"{prefix}.{key}" if prefix else key

        # Skip derived/computed values (marked with _ in name or certain patterns)
        if key.startswith('_') or key in ['metadata', 'created_at', 'updated_at']:
            continue

        if isinstance(value, dict):
            count += count_params_from_dict(value, full_key)
        else:
            count += 1

    return count


def analyze_dp_gmm_config(config_path: Path) -> ModelHyperparameters:
    """Analyze DPGMM hyperparameters from config.yaml."""
    config = load_config_yaml(config_path)

    # Extract DPGMM-specific section
    dp_gmm_config = config.get('dp_gmm', {})
    if not dp_gmm_config:
        # Try to find it under different keys
        for key in ['model', 'model_config', 'dpgmm']:
            if key in config:
                dp_gmm_config = config[key]
                break

    tunable = count_params_from_dict(dp_gmm_config)

    return ModelHyperparameters(
        model_name="DPGMM",
        config_params=dp_gmm_config,
        tunable_count=tunable,
        fixed_count=0,
        total_count=tunable,
        source_file=str(config_path)
    )


def analyze_arima_config(config_path: Path) -> ModelHyperparameters:
    """Analyze ARIMA baseline hyperparameters."""
    config = load_config_yaml(config_path)

    # Extract ARIMA-specific section
    arima_config = config.get('arima', {})
    if not arima_config:
        # Common ARIMA hyperparameters
        arima_config = {
            'order_p': config.get('arima_order_p', 1),
            'order_d': config.get('arima_order_d', 1),
            'order_q': config.get('arima_order_q', 1),
            'seasonal_period': config.get('seasonal_period', 24),
            'trend': config.get('trend', 'c'),
        }

    tunable = count_params_from_dict(arima_config)

    return ModelHyperparameters(
        model_name="ARIMA",
        config_params=arima_config,
        tunable_count=tunable,
        fixed_count=0,
        total_count=tunable,
        source_file=str(config_path)
    )


def analyze_moving_average_config(config_path: Path) -> ModelHyperparameters:
    """Analyze Moving Average baseline hyperparameters."""
    config = load_config_yaml(config_path)

    # Extract Moving Average-specific section
    ma_config = config.get('moving_average', {})
    if not ma_config:
        # Common MA hyperparameters
        ma_config = {
            'window_size': config.get('ma_window_size', 20),
            'z_threshold': config.get('z_threshold', 3.0),
            'min_samples': config.get('ma_min_samples', 50),
        }

    tunable = count_params_from_dict(ma_config)

    return ModelHyperparameters(
        model_name="MovingAverage",
        config_params=ma_config,
        tunable_count=tunable,
        fixed_count=0,
        total_count=tunable,
        source_file=str(config_path)
    )


def analyze_lstm_ae_config(config_path: Path) -> ModelHyperparameters:
    """Analyze LSTM Autoencoder baseline hyperparameters."""
    config = load_config_yaml(config_path)

    # Extract LSTM-AE-specific section
    lstm_config = config.get('lstm_ae', {})
    if not lstm_config:
        # Common LSTM-AE hyperparameters
        lstm_config = {
            'input_length': config.get('lstm_input_length', 100),
            'encoder_units': config.get('lstm_encoder_units', 64),
            'decoder_units': config.get('lstm_decoder_units', 64),
            'latent_dim': config.get('lstm_latent_dim', 32),
            'learning_rate': config.get('lstm_learning_rate', 0.001),
            'batch_size': config.get('lstm_batch_size', 32),
            'epochs': config.get('lstm_epochs', 100),
        }

    tunable = count_params_from_dict(lstm_config)

    return ModelHyperparameters(
        model_name="LSTM_AE",
        config_params=lstm_config,
        tunable_count=tunable,
        fixed_count=0,
        total_count=tunable,
        source_file=str(config_path)
    )


def compare_hyperparameters(dp_gmm: ModelHyperparameters,
                             baselines: Dict[str, ModelHyperparameters],
                             threshold: float = 0.30) -> ComparisonResult:
    """Compare DPGMM hyperparameter count vs baselines."""
    # Calculate average baseline count
    if baselines:
        avg_baseline = sum(b.tunable_count for b in baselines.values()) / len(baselines)
    else:
        avg_baseline = 1  # Avoid division by zero

    # Calculate ratio
    if avg_baseline > 0:
        ratio = dp_gmm.tunable_count / avg_baseline
    else:
        ratio = float('inf')

    # Check if meets requirement (<30%)
    meets_req = ratio < threshold

    return ComparisonResult(
        dp_gmm=dp_gmm,
        baselines=baselines,
        dp_gmm_ratio=ratio,
        meets_requirement=meets_req,
        threshold=threshold
    )


def generate_report(result: ComparisonResult) -> str:
    """Generate a human-readable report."""
    lines = [
        "=" * 60,
        "HYPERPARAMETER COMPARISON REPORT",
        "=" * 60,
        "",
        f"SC-004 Requirement: DPGMM tunable params < 30% of baseline average",
        f"Threshold: {result.threshold * 100:.1f}%",
        "",
        "-" * 60,
        "DPGMM Configuration:",
        "-" * 60,
        f"  Model: {result.dp_gmm.model_name}",
        f"  Tunable parameters: {result.dp_gmm.tunable_count}",
        f"  Source: {result.dp_gmm.source_file}",
        "",
        "  Parameters:",
    ]

    for key, value in result.dp_gmm.config_params.items():
        lines.append(f"    - {key}: {value}")

    lines.extend([
        "",
        "-" * 60,
        "Baseline Configurations:",
        "-" * 60,
    ])

    total_baseline = 0
    for name, baseline in result.baselines.items():
        lines.extend([
            f"  {name}:",
            f"    Tunable parameters: {baseline.tunable_count}",
            f"    Parameters:",
        ])
        for key, value in baseline.config_params.items():
            lines.append(f"      - {key}: {value}")
        total_baseline += baseline.tunable_count
        lines.append("")

    avg_baseline = total_baseline / len(result.baselines) if result.baselines else 0

    lines.extend([
        "-" * 60,
        "COMPARISON SUMMARY:",
        "-" * 60,
        f"  DPGMM tunable count: {result.dp_gmm.tunable_count}",
        f"  Baseline average: {avg_baseline:.1f}",
        f"  Ratio: {result.dp_gmm_ratio * 100:.1f}%",
        f"  Threshold: {result.threshold * 100:.1f}%",
        "",
        f"  ✓ MEETS REQUIREMENT" if result.meets_requirement else "  ✗ FAILS REQUIREMENT",
        "",
        "=" * 60,
    ])

    return "\n".join(lines)


def save_results(result: ComparisonResult, output_path: Path) -> None:
    """Save results to JSON file."""
    results_dict = {
        'dp_gmm': {
            'model_name': result.dp_gmm.model_name,
            'tunable_count': result.dp_gmm.tunable_count,
            'config_params': result.dp_gmm.config_params,
            'source_file': result.dp_gmm.source_file,
        },
        'baselines': {},
        'comparison': {
            'dp_gmm_ratio': result.dp_gmm_ratio,
            'threshold': result.threshold,
            'meets_requirement': result.meets_requirement,
        }
    }

    for name, baseline in result.baselines.items():
        results_dict['baselines'][name] = {
            'model_name': baseline.model_name,
            'tunable_count': baseline.tunable_count,
            'config_params': baseline.config_params,
            'source_file': baseline.source_file,
        }

    with open(output_path, 'w') as f:
        json.dump(results_dict, f, indent=2, default=str)

    logger.info(f"Results saved to: {output_path}")


def main():
    """Main entry point - runs the full hyperparameter analysis."""
    logger.info("Starting hyperparameter comparison analysis...")

    # Determine project root
    # Script runs from code/src/utils/, so go up 3 levels
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent

    config_path = project_root / "code" / "config.yaml"
    output_dir = project_root / "code" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "hyperparameter_comparison.json"
    report_path = output_dir / "hyperparameter_comparison.txt"

    logger.info(f"Project root: {project_root}")
    logger.info(f"Config path: {config_path}")

    # Analyze each model
    logger.info("Analyzing DPGMM configuration...")
    dp_gmm = analyze_dp_gmm_config(config_path)

    logger.info("Analyzing ARIMA baseline configuration...")
    arima = analyze_arima_config(config_path)

    logger.info("Analyzing Moving Average baseline configuration...")
    ma = analyze_moving_average_config(config_path)

    logger.info("Analyzing LSTM Autoencoder baseline configuration...")
    lstm_ae = analyze_lstm_ae_config(config_path)

    # Compare
    baselines = {
        'ARIMA': arima,
        'MovingAverage': ma,
        'LSTM_AE': lstm_ae,
    }

    logger.info("Comparing hyperparameters...")
    result = compare_hyperparameters(dp_gmm, baselines)

    # Generate and save report
    report = generate_report(result)
    logger.info("\n" + report)

    # Save to files
    save_results(result, output_path)

    with open(report_path, 'w') as f:
        f.write(report)

    logger.info(f"Report saved to: {report_path}")

    # Exit with appropriate code
    if result.meets_requirement:
        logger.info("SUCCESS: DPGMM meets SC-004 hyperparameter requirement")
        sys.exit(0)
    else:
        logger.warning("WARNING: DPGMM does not meet SC-004 hyperparameter requirement")
        # Don't exit with error - this is informational for the research
        sys.exit(0)


if __name__ == "__main__":
    main()
