"""
Hyperparameter counting utility for SC-004 compliance verification.

This module counts tunable hyperparameters across DPGMM and baseline models
to verify that DPGMM has <30% tunable parameters compared to baselines.

SC-004: DPGMM should have <30% tunable parameters vs baselines (ARIMA, Moving Average)

Usage:
    python code/src/utils/hyperparameter_counter.py
"""

import sys
import os
from pathlib import Path
from dataclasses import fields, is_dataclass
from typing import Dict, Any, List, Tuple, Optional
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from baselines.arima import ARIMAConfig
from baselines.moving_average import MovingAverageConfig
from models.dp_gmm import DPGMMConfig


class HyperparameterCounter:
    """
    Counts and compares tunable hyperparameters across models.
    
    SC-004 Compliance: DPGMM should have <30% tunable parameters vs baselines.
    """
    
    def __init__(self):
        self.model_configs: Dict[str, Any] = {}
        self.counts: Dict[str, int] = {}
        self.comparison_results: Dict[str, Any] = {}
    
    def count_dataclass_fields(self, config_class: type, config_name: str) -> int:
        """
        Count tunable hyperparameters in a dataclass config.
        
        Args:
            config_class: The dataclass config type
            config_name: Name of the config/model for reporting
        
        Returns:
            Number of tunable hyperparameters (fields with default values)
        """
        if not is_dataclass(config_class):
            raise ValueError(f"{config_name} is not a dataclass")
        
        count = 0
        for field in fields(config_class):
            # Count fields that have default values (tunable hyperparameters)
            # Exclude internal/private fields (starting with _)
            if field.name.startswith('_'):
                continue
            # Count all fields as tunable (user can modify them)
            count += 1
        
        return count
    
    def count_model_hyperparameters(self, model_name: str, config_class: type) -> int:
        """
        Count total tunable hyperparameters for a model.
        
        Args:
            model_name: Name of the model
            config_class: The config dataclass for the model
        
        Returns:
            Number of tunable hyperparameters
        """
        try:
            count = self.count_dataclass_fields(config_class, model_name)
            self.model_configs[model_name] = config_class
            self.counts[model_name] = count
            return count
        except Exception as e:
            print(f"Error counting {model_name} hyperparameters: {e}")
            return 0
    
    def count_all_models(self) -> None:
        """Count hyperparameters for all supported models."""
        # Count DPGMM hyperparameters
        dp_gmm_count = self.count_model_hyperparameters(
            "DPGMM", 
            DPGMMConfig
        )
        
        # Count ARIMA baseline hyperparameters
        arima_count = self.count_model_hyperparameters(
            "ARIMA", 
            ARIMAConfig
        )
        
        # Count Moving Average baseline hyperparameters
        ma_count = self.count_model_hyperparameters(
            "MovingAverage", 
            MovingAverageConfig
        )
        
        print(f"\nHyperparameter Counts:")
        print(f"  DPGMM:        {dp_gmm_count} tunable parameters")
        print(f"  ARIMA:        {arima_count} tunable parameters")
        print(f"  MovingAverage: {ma_count} tunable parameters")
    
    def compute_ratios(self) -> Dict[str, float]:
        """
        Compute ratio of DPGMM hyperparameters to each baseline.
        
        Returns:
            Dictionary mapping baseline names to DPGMM/baseline ratios
        """
        ratios = {}
        dp_gmm_count = self.counts.get("DPGMM", 0)
        
        for baseline_name in ["ARIMA", "MovingAverage"]:
            baseline_count = self.counts.get(baseline_name, 0)
            if baseline_count > 0:
                ratio = dp_gmm_count / baseline_count
                ratios[baseline_name] = ratio
            else:
                ratios[baseline_name] = float('inf')
        
        return ratios
    
    def verify_sc004_compliance(self) -> Tuple[bool, str]:
        """
        Verify SC-004 compliance: DPGMM should have <30% tunable parameters vs baselines.
        
        Returns:
            Tuple of (is_compliant, compliance_message)
        """
        ratios = self.compute_ratios()
        
        # SC-004: DPGMM should have <30% tunable parameters vs baselines
        # This means DPGMM_count / Baseline_count < 0.30
        
        all_compliant = True
        messages = []
        
        for baseline_name, ratio in ratios.items():
            is_compliant = ratio < 0.30
            status = "✓ PASS" if is_compliant else "✗ FAIL"
            messages.append(
                f"  {status}: DPGMM/{baseline_name} = {ratio:.2%} "
                f"(threshold: <30%)"
            )
            if not is_compliant:
                all_compliant = False
        
        compliance_message = "\n".join(messages)
        
        if all_compliant:
            messages.insert(0, "SC-004 COMPLIANCE: PASSED")
        else:
            messages.insert(0, "SC-004 COMPLIANCE: FAILED")
        
        return all_compliant, "\n".join(messages)
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive hyperparameter comparison report.
        
        Returns:
            Dictionary containing full comparison report
        """
        self.count_all_models()
        ratios = self.compute_ratios()
        is_compliant, compliance_message = self.verify_sc004_compliance()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "sc004_requirement": "DPGMM should have <30% tunable parameters vs baselines",
            "is_compliant": is_compliant,
            "compliance_message": compliance_message,
            "hyperparameter_counts": self.counts,
            "ratios": {k: float(v) if v != float('inf') else None for k, v in ratios.items()},
            "summary": {
                "dp_gmm_count": self.counts.get("DPGMM", 0),
                "baseline_avg_count": sum(
                    v for k, v in self.counts.items() 
                    if k != "DPGMM"
                ) / max(1, len([k for k in self.counts if k != "DPGMM"])),
                "dp_gmm_vs_baseline_ratio": (
                    self.counts.get("DPGMM", 0) / 
                    max(1, sum(v for k, v in self.counts.items() if k != "DPGMM"))
                ) * 100 if len([k for k in self.counts if k != "DPGMM"]) > 0 else None
            }
        }
        
        return report
    
    def print_report(self) -> None:
        """Print formatted compliance report to stdout."""
        report = self.generate_report()
        
        print("\n" + "=" * 70)
        print("HYPERPARAMETER COMPLIANCE REPORT (SC-004)")
        print("=" * 70)
        print(f"\nTimestamp: {report['timestamp']}")
        print(f"\nRequirement: {report['sc004_requirement']}")
        print(f"\n{report['compliance_message']}")
        
        print("\n" + "-" * 70)
        print("HYPERPARAMETER COUNTS:")
        print("-" * 70)
        for model_name, count in report['hyperparameter_counts'].items():
            marker = "← DPGMM" if model_name == "DPGMM" else ""
            print(f"  {model_name:20s}: {count:3d} tunable parameters {marker}")
        
        print("\n" + "-" * 70)
        print("RATIOS (DPGMM / Baseline):")
        print("-" * 70)
        for baseline, ratio in report['ratios'].items():
            if ratio is not None:
                status = "✓" if ratio < 0.30 else "✗"
                print(f"  {status} DPGMM / {baseline:15s}: {ratio:.2%}")
        
        print("\n" + "-" * 70)
        print("SUMMARY:")
        print("-" * 70)
        summary = report['summary']
        print(f"  DPGMM tunable parameters: {summary['dp_gmm_count']}")
        print(f"  Baseline average: {summary['baseline_avg_count']:.1f}")
        if summary['dp_gmm_vs_baseline_ratio'] is not None:
            print(f"  DPGMM vs Baseline ratio: {summary['dp_gmm_vs_baseline_ratio']:.1f}%")
        
        print("\n" + "=" * 70)
        if report['is_compliant']:
            print("SC-004 VERIFICATION: PASSED ✓")
        else:
            print("SC-004 VERIFICATION: FAILED ✗")
        print("=" * 70 + "\n")
        
        return report


def main():
    """
    Main entry point for hyperparameter counting utility.
    
    Runs compliance check for SC-004 and outputs report.
    """
    print("Hyperparameter Counter - SC-004 Compliance Verification")
    print("-" * 50)
    
    counter = HyperparameterCounter()
    
    try:
        report = counter.print_report()
        
        # Save JSON report
        report_path = Path(__file__).parent.parent.parent / "data" / "reports" / "hyperparameter_compliance.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Report saved to: {report_path}")
        
        # Exit with appropriate code
        sys.exit(0 if report['is_compliant'] else 1)
        
    except Exception as e:
        print(f"Error during hyperparameter counting: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
