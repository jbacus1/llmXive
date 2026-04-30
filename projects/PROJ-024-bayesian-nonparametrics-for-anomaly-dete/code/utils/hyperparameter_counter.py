#!/usr/bin/env python3
"""
Hyperparameter Counter Utility

Counts tunable hyperparameters across DPGMM and baseline models to verify
that DPGMM has <30% tunable parameters compared to baselines (SC-004).

This utility provides a quantitative comparison of model complexity
between the nonparametric DPGMM approach and traditional baselines.
"""

import sys
from pathlib import Path
from dataclasses import dataclass, fields
from typing import Dict, Any, List, Tuple, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from baselines.arima import ARIMAConfig, ARIMABaseline
from baselines.moving_average import MovingAverageConfig, MovingAverageBaseline

@dataclass
class HyperparameterCount:
    """Container for hyperparameter count results."""
    model_name: str
    count: int
    parameters: List[str]
    is_nonparametric: bool = False
    description: str = ""

@dataclass
class ComparisonResult:
    """Container for hyperparameter comparison results."""
    dp_gmm_count: int
    arima_count: int
    moving_avg_count: int
    dp_gmm_ratio_arima: float
    dp_gmm_ratio_moving_avg: float
    passes_requirement: bool
    threshold: float = 0.30
    summary: str = ""

def count_dp_gmm_hyperparameters() -> HyperparameterCount:
    """
    Count DPGMM hyperparameters.

    DPGMM uses a nonparametric Bayesian approach with the Dirichlet Process
    prior. The key hyperparameters are:
    - concentration parameter (alpha): controls number of clusters
    - base distribution parameters: prior for cluster centers
    - inference parameters: ADVI iterations, learning rate

    The model automatically adapts the number of mixture components,
    eliminating the need to specify K (number of clusters) as a hyperparameter.
    """
    params = [
        'concentration_parameter',      # Alpha - controls number of clusters
        'base_distribution_mean',       # Prior mean for cluster centers (Gaussian)
        'base_distribution_covariance', # Prior covariance (Wishart)
        'inference_iterations',         # ADVI iterations
        'learning_rate',                # Variational inference step size
        'min_components',               # Minimum active components
        'max_components',               # Maximum active components (soft cap)
        'convergence_tolerance',        # ELBO convergence threshold
    ]
    return HyperparameterCount(
        model_name="DPGMM",
        count=len(params),
        parameters=params,
        is_nonparametric=True,
        description="Nonparametric Bayesian model - number of clusters inferred from data"
    )

def count_arima_hyperparameters() -> HyperparameterCount:
    """
    Count ARIMA baseline hyperparameters.

    ARIMA requires explicit specification of multiple order parameters
    and has many configuration options for optimization and constraints.
    """
    params = [
        'order_p',                      # AR order (p)
        'order_d',                      # Integration order (d)
        'order_q',                      # MA order (q)
        'seasonal_p',                   # Seasonal AR order
        'seasonal_d',                   # Seasonal integration
        'seasonal_q',                   # Seasonal MA order
        'seasonal_period',              # Seasonal period (m)
        'trend',                        # Trend specification ('n', 'c', 't', 'ct')
        'enforce_stationarity',         # Constraint flag
        'enforce_invertibility',        # Constraint flag
        'start_params',                 # Initial parameter values
        'optim_method',                 # Optimization method (e.g., 'bfgs')
        'optim_maxiter',                # Optimization iterations
        'disp',                         # Convergence printing
        'random_state',                 # Random seed for initialization
    ]
    return HyperparameterCount(
        model_name="ARIMA",
        count=len(params),
        parameters=params,
        is_nonparametric=False,
        description="Parametric time series model - requires explicit order specification"
    )

def count_moving_average_hyperparameters() -> HyperparameterCount:
    """
    Count Moving Average baseline hyperparameters.

    Simple moving average with z-score threshold for anomaly detection.
    """
    params = [
        'window_size',                  # Smoothing window size
        'threshold_multiplier',         # Z-score threshold (e.g., 3.0 for 99.7%)
        'min_samples',                  # Minimum samples for statistics
        'warmup_period',                # Initial learning period
    ]
    return HyperparameterCount(
        model_name="MovingAverage",
        count=len(params),
        parameters=params,
        is_nonparametric=False,
        description="Simple statistical baseline - minimal hyperparameters"
    )

def compare_hyperparameters() -> ComparisonResult:
    """
    Compare hyperparameter counts across models.

    SC-004 Requirement: DPGMM should have <30% tunable parameters
    compared to traditional baselines.
    """
    dp_gmm = count_dp_gmm_hyperparameters()
    arima = count_arima_hyperparameters()
    moving_avg = count_moving_average_hyperparameters()

    # Calculate ratios (DPGMM count / baseline count)
    ratio_arima = dp_gmm.count / arima.count if arima.count > 0 else float('inf')
    ratio_moving_avg = dp_gmm.count / moving_avg.count if moving_avg.count > 0 else float('inf')

    # Check if DPGMM has <30% of baseline parameters (comparing to ARIMA as primary baseline)
    passes = ratio_arima < 0.30

    # Generate summary
    if passes:
        summary = (
            f"PASS: DPGMM has {dp_gmm.count} hyperparameters vs ARIMA's {arima.count} "
            f"({ratio_arima:.1%} ratio). Requirement (<30%) satisfied."
        )
    else:
        summary = (
            f"FAIL: DPGMM has {dp_gmm.count} hyperparameters vs ARIMA's {arima.count} "
            f"({ratio_arima:.1%} ratio). Requirement (<30%) not satisfied."
        )

    return ComparisonResult(
        dp_gmm_count=dp_gmm.count,
        arima_count=arima.count,
        moving_avg_count=moving_avg.count,
        dp_gmm_ratio_arima=ratio_arima,
        dp_gmm_ratio_moving_avg=ratio_moving_avg,
        passes_requirement=passes,
        threshold=0.30,
        summary=summary
    )

def print_comparison(result: ComparisonResult) -> None:
    """Print formatted comparison results."""
    print("=" * 70)
    print("Hyperparameter Counting Utility")
    print("Verification of SC-004: DPGMM <30% tunable parameters vs baselines")
    print("=" * 70)

    dp_gmm = count_dp_gmm_hyperparameters()
    arima = count_arima_hyperparameters()
    moving_avg = count_moving_average_hyperparameters()

    print(f"\n[DPGMM - Nonparametric Bayesian Model]")
    print(f"  Hyperparameters: {dp_gmm.count}")
    print(f"  Description: {dp_gmm.description}")
    print(f"  Parameters:")
    for param in dp_gmm.parameters:
        print(f"    - {param}")

    print(f"\n[ARIMA Baseline - Parametric Time Series]")
    print(f"  Hyperparameters: {arima.count}")
    print(f"  Description: {arima.description}")
    print(f"  Parameters:")
    for param in arima.parameters:
        print(f"    - {param}")

    print(f"\n[Moving Average Baseline - Statistical]")
    print(f"  Hyperparameters: {moving_avg.count}")
    print(f"  Description: {moving_avg.description}")
    print(f"  Parameters:")
    for param in moving_avg.parameters:
        print(f"    - {param}")

    print(f"\n{'=' * 70}")
    print("COMPARISON RESULTS")
    print(f"{'=' * 70}")
    print(f"  DPGMM vs ARIMA:     {result.dp_gmm_ratio_arima:.1%} ({result.dp_gmm_count}/{arima.count})")
    print(f"  DPGMM vs MovingAvg: {result.dp_gmm_ratio_moving_avg:.1%} ({result.dp_gmm_count}/{moving_avg.count})")
    print(f"  Threshold:          <30%")
    print(f"  Requirement:        {'PASS ✓' if result.passes_requirement else 'FAIL ✗'}")
    print(f"\n  Summary: {result.summary}")
    print(f"{'=' * 70}")

def main() -> ComparisonResult:
    """Main entry point for hyperparameter counting."""
    result = compare_hyperparameters()
    print_comparison(result)
    return result

if __name__ == "__main__":
    main()
