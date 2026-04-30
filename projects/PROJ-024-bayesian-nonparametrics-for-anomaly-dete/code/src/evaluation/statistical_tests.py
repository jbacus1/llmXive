"""
Statistical tests for model comparison with Bonferroni correction.

Implements paired t-tests across datasets with multiple comparison
correction per US2 acceptance scenario 2.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats
from pathlib import Path
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class StatisticalTestResult:
    """Result of a single statistical test comparison."""
    test_name: str
    model_a: str
    model_b: str
    statistic: float
    p_value: float
    significant: bool
    corrected_p_value: float
    alpha: float
    n_datasets: int
    description: str = ""


@dataclass
class ComparisonSummary:
    """Summary of all model comparisons across datasets."""
    timestamp: str
    models_compared: List[str]
    datasets_used: List[str]
    test_results: List[StatisticalTestResult]
    best_model: str
    best_model_wins: int
    total_comparisons: int
    summary_dict: Dict[str, Any] = field(default_factory=dict)


def apply_bonferroni_correction(
    p_values: List[float],
    num_comparisons: int,
    alpha: float = 0.05
) -> List[float]:
    """
    Apply Bonferroni correction to multiple p-values.

    Args:
        p_values: List of raw p-values from statistical tests
        num_comparisons: Total number of comparisons being made
        alpha: Significance threshold (default 0.05)

    Returns:
        List of corrected p-values (capped at 1.0)
    """
    corrected = []
    for p in p_values:
        corrected_p = min(p * num_comparisons, 1.0)
        corrected.append(corrected_p)
    return corrected


def paired_ttest_with_bonferroni(
    scores_a: List[float],
    scores_b: List[float],
    test_name: str,
    model_a: str,
    model_b: str,
    alpha: float = 0.05
) -> StatisticalTestResult:
    """
    Perform paired t-test between two models with Bonferroni correction.

    Args:
        scores_a: Performance scores for model A across datasets
        scores_b: Performance scores for model B across datasets
        test_name: Name/identifier for this test
        model_a: Name of model A
        model_b: Name of model B
        alpha: Significance threshold (default 0.05)

    Returns:
        StatisticalTestResult with test statistics and significance
    """
    if len(scores_a) != len(scores_b):
        raise ValueError(
            f"Score lists must have equal length: "
            f"len(scores_a)={len(scores_a)}, len(scores_b)={len(scores_b)}"
        )

    if len(scores_a) < 2:
        raise ValueError(
            f"Need at least 2 datasets for paired t-test, "
            f"got {len(scores_a)}"
        )

    # Perform paired t-test
    statistic, p_value = stats.ttest_rel(scores_a, scores_b)

    # Bonferroni correction (single comparison, but apply for consistency)
    corrected_p_value = min(p_value * 1, 1.0)
    significant = corrected_p_value < alpha

    return StatisticalTestResult(
        test_name=test_name,
        model_a=model_a,
        model_b=model_b,
        statistic=float(statistic),
        p_value=float(p_value),
        significant=significant,
        corrected_p_value=float(corrected_p_value),
        alpha=alpha,
        n_datasets=len(scores_a),
        description=f"Paired t-test comparing {model_a} vs {model_b}"
    )


def compare_all_models(
    model_scores: Dict[str, Dict[str, List[float]]],
    metric: str = "f1_score",
    alpha: float = 0.05
) -> ComparisonSummary:
    """
    Compare all models pairwise across datasets using paired t-tests.

    Args:
        model_scores: Dict mapping model_name -> dataset_name -> scores
        metric: Metric to compare (e.g., 'f1_score', 'auc')
        alpha: Significance threshold (default 0.05)

    Returns:
        ComparisonSummary with all test results
    """
    models = list(model_scores.keys())
    datasets = list(model_scores[models[0]].keys())

    # Calculate number of pairwise comparisons
    num_comparisons = len(models) * (len(models) - 1) // 2

    test_results = []
    win_counts = {model: 0 for model in models}

    # Perform pairwise comparisons
    for i, model_a in enumerate(models):
        for model_b in models[i + 1:]:
            # Extract scores for both models across all datasets
            scores_a = [
                model_scores[model_a][ds][metric]
                for ds in datasets
                if ds in model_scores[model_a] and metric in model_scores[model_a][ds]
            ]
            scores_b = [
                model_scores[model_b][ds][metric]
                for ds in datasets
                if ds in model_scores[model_b] and metric in model_scores[model_b][ds]
            ]

            if len(scores_a) < 2 or len(scores_b) < 2:
                logger.warning(
                    f"Skipping comparison {model_a} vs {model_b}: "
                    f"insufficient data ({len(scores_a)} vs {len(scores_b)} datasets)"
                )
                continue

            # Ensure equal length by intersecting datasets
            common_datasets = [
                ds for ds in datasets
                if ds in model_scores[model_a] and ds in model_scores[model_b]
            ]
            scores_a = [
                model_scores[model_a][ds][metric] for ds in common_datasets
            ]
            scores_b = [
                model_scores[model_b][ds][metric] for ds in common_datasets
            ]

            if len(scores_a) < 2:
                continue

            test_name = f"{metric}_{model_a}_vs_{model_b}"
            result = paired_ttest_with_bonferroni(
                scores_a=scores_a,
                scores_b=scores_b,
                test_name=test_name,
                model_a=model_a,
                model_b=model_b,
                alpha=alpha
            )

            test_results.append(result)

            # Track wins (model_a wins if t-statistic > 0 and significant)
            if result.significant and result.statistic > 0:
                win_counts[model_a] += 1
            elif result.significant and result.statistic < 0:
                win_counts[model_b] += 1

    # Apply Bonferroni correction to all p-values
    if test_results:
        raw_p_values = [r.p_value for r in test_results]
        corrected_p_values = apply_bonferroni_correction(
            raw_p_values, num_comparisons, alpha
        )
        for result, corrected_p in zip(test_results, corrected_p_values):
            result.corrected_p_value = corrected_p
            result.significant = corrected_p < alpha

    # Determine best model
    best_model = max(win_counts, key=win_counts.get)
    best_wins = win_counts[best_model]

    # Build summary
    summary_dict = {
        "metric": metric,
        "num_datasets": len(datasets),
        "num_comparisons": len(test_results),
        "win_counts": win_counts,
        "significant_comparisons": sum(1 for r in test_results if r.significant)
    }

    return ComparisonSummary(
        timestamp=datetime.now().isoformat(),
        models_compared=models,
        datasets_used=datasets,
        test_results=test_results,
        best_model=best_model,
        best_model_wins=best_wins,
        total_comparisons=len(test_results),
        summary_dict=summary_dict
    )


def format_comparison_summary(
    summary: ComparisonSummary,
    include_details: bool = True
) -> str:
    """
    Format comparison summary as human-readable string.

    Args:
        summary: ComparisonSummary to format
        include_details: Include individual test results (default True)

    Returns:
        Formatted string representation
    """
    lines = [
        "=" * 60,
        "STATISTICAL COMPARISON SUMMARY",
        "=" * 60,
        f"Timestamp: {summary.timestamp}",
        f"Metric: {summary.summary_dict.get('metric', 'N/A')}",
        f"Models: {', '.join(summary.models_compared)}",
        f"Datasets: {len(summary.datasets_used)}",
        f"Total Comparisons: {summary.total_comparisons}",
        f"Significant Comparisons: {summary.summary_dict.get('significant_comparisons', 0)}",
        "",
        "WIN COUNTS:",
        "-" * 40,
    ]

    for model, wins in summary.summary_dict.get("win_counts", {}).items():
        lines.append(f"  {model}: {wins} wins")

    lines.extend([
        "",
        f"Best Model: {summary.best_model} ({summary.best_model_wins} wins)",
        "",
    ])

    if include_details and summary.test_results:
        lines.extend([
            "DETAILED RESULTS:",
            "-" * 40,
        ])

        for result in summary.test_results:
            sig_marker = "***" if result.significant else ""
            lines.extend([
                f"Test: {result.test_name}",
                f"  {result.model_a} vs {result.model_b}",
                f"  Statistic: {result.statistic:.4f}",
                f"  P-value: {result.p_value:.4f}",
                f"  Corrected P-value: {result.corrected_p_value:.4f}",
                f"  Significant: {result.significant} {sig_marker}",
                f"  Datasets: {result.n_datasets}",
                "",
            ])

    lines.append("=" * 60)
    return "\n".join(lines)


def save_comparison_results(
    summary: ComparisonSummary,
    output_path: Path,
    format: str = "json"
) -> Path:
    """
    Save comparison results to file.

    Args:
        summary: ComparisonSummary to save
        output_path: Path to output file
        format: Output format ('json' or 'txt')

    Returns:
        Path to saved file
    """
  output_path = Path(output_path)
  output_path.parent.mkdir(parents=True, exist_ok=True)

  if format == "json":
      data = {
          "timestamp": summary.timestamp,
          "models_compared": summary.models_compared,
          "datasets_used": summary.datasets_used,
          "test_results": [
              {
                  "test_name": r.test_name,
                  "model_a": r.model_a,
                  "model_b": r.model_b,
                  "statistic": r.statistic,
                  "p_value": r.p_value,
                  "significant": r.significant,
                  "corrected_p_value": r.corrected_p_value,
                  "alpha": r.alpha,
                  "n_datasets": r.n_datasets,
                  "description": r.description
              }
              for r in summary.test_results
          ],
          "best_model": summary.best_model,
          "best_model_wins": summary.best_model_wins,
          "total_comparisons": summary.total_comparisons,
          "summary_dict": summary.summary_dict
      }

      with open(output_path, "w") as f:
          json.dump(data, f, indent=2)
      logger.info(f"Saved JSON results to {output_path}")

  elif format == "txt":
      formatted = format_comparison_summary(summary)
      with open(output_path, "w") as f:
          f.write(formatted)
      logger.info(f"Saved text results to {output_path}")

  else:
      raise ValueError(f"Unknown format: {format}")

  return output_path


def main():
    """
    CLI entry point for statistical comparison.

    Generates synthetic test data and runs comparisons if no input provided.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Statistical comparison of anomaly detection models"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to JSON file with model scores"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="code/evaluation/results/comparison_results.json",
        help="Output path for results"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "txt"],
        default="json",
        help="Output format"
    )
    parser.add_argument(
        "--metric",
        type=str,
        default="f1_score",
        help="Metric to compare"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance threshold"
    )

    args = parser.parse_args()

    # Generate synthetic test data if no input provided
    if args.input is None:
        logger.info("No input file provided, generating synthetic test data...")

        # Create synthetic model scores across 3 datasets
        model_scores = {
            "DPGMM": {
                "electricity": {"f1_score": 0.85, "auc": 0.92},
                "traffic": {"f1_score": 0.78, "auc": 0.88},
                "synthetic_control": {"f1_score": 0.91, "auc": 0.95}
            },
            "ARIMA": {
                "electricity": {"f1_score": 0.72, "auc": 0.81},
                "traffic": {"f1_score": 0.69, "auc": 0.77},
                "synthetic_control": {"f1_score": 0.75, "auc": 0.83}
            },
            "MovingAverage": {
                "electricity": {"f1_score": 0.65, "auc": 0.74},
                "traffic": {"f1_score": 0.62, "auc": 0.71},
                "synthetic_control": {"f1_score": 0.68, "auc": 0.76}
            },
            "LSTM-AE": {
                "electricity": {"f1_score": 0.82, "auc": 0.90},
                "traffic": {"f1_score": 0.76, "auc": 0.86},
                "synthetic_control": {"f1_score": 0.88, "auc": 0.93}
            }
        }

        # Run comparison
        summary = compare_all_models(
            model_scores=model_scores,
            metric=args.metric,
            alpha=args.alpha
        )

        # Print summary
        print(format_comparison_summary(summary))

        # Save results
        output_path = save_comparison_results(
            summary,
            Path(args.output),
            format=args.format
        )
        print(f"\nResults saved to: {output_path}")

    else:
        # Load from input file
        input_path = Path(args.input)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        with open(input_path, "r") as f:
            model_scores = json.load(f)

        # Run comparison
        summary = compare_all_models(
            model_scores=model_scores,
            metric=args.metric,
            alpha=args.alpha
        )

        # Print summary
        print(format_comparison_summary(summary))

        # Save results
        output_path = save_comparison_results(
            summary,
            Path(args.output),
            format=args.format
        )
        print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
