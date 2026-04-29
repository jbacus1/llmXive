"""
Task T059: Compute basic descriptive statistics on PSI values.

Reads the downloaded cortex PSI sample data from data/raw/cortex_psi_sample.csv,
computes mean, standard deviation, and sample count (n), and saves results
to data/results/psi_stats.json.

This script MUST execute to produce the JSON artifact.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

def compute_descriptive_stats(psi_values):
    """
    Compute mean, standard deviation, and count for PSI values.
    
    Args:
        psi_values: Array-like of PSI values (0.0 to 1.0 range)
        
    Returns:
        dict with keys: mean, std, n, min, max
    """
    psi_array = np.array(psi_values, dtype=float)
    valid_mask = ~np.isnan(psi_array)
    valid_psi = psi_array[valid_mask]
    
    if len(valid_psi) == 0:
        return {
            "mean": None,
            "std": None,
            "n": 0,
            "min": None,
            "max": None,
            "warning": "No valid PSI values found"
        }
    
    return {
        "mean": float(np.mean(valid_psi)),
        "std": float(np.std(valid_psi, ddof=1)),  # Sample std
        "n": int(len(valid_psi)),
        "min": float(np.min(valid_psi)),
        "max": float(np.max(valid_psi)),
        "warning": None
    }

def main():
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / "data" / "raw" / "cortex_psi_sample.csv"
    output_path = project_root / "data" / "results" / "psi_stats.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading PSI data from: {input_path}")
    
    # Load the CSV
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        print("Please ensure T058 has been executed to download the data first.")
        sys.exit(1)
    
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} rows from {input_path}")
    
    # Identify PSI column(s)
    # Common column names: PSI, percent_spliced_in, psi, Percent_Spliced_In
    psi_column = None
    for col in df.columns:
        col_lower = col.lower()
        if "psi" in col_lower and "percent" not in col_lower:
            psi_column = col
            break
        elif col_lower in ["psi", "percent_spliced_in", "percent_included"]:
            psi_column = col
            break
    
    if psi_column is None:
        # Fall back to first numeric column that looks like PSI (0-1 range)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].min() >= 0 and df[col].max() <= 1:
                psi_column = col
                break
    
    if psi_column is None:
        print("ERROR: Could not identify PSI column in the dataset")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)
    
    print(f"Using PSI column: {psi_column}")
    psi_values = df[psi_column].dropna()
    
    # Compute statistics
    stats = compute_descriptive_stats(psi_values)
    stats["psicolumn"] = psi_column
    stats["input_file"] = str(input_path.relative_to(project_root))
    stats["description"] = "Descriptive statistics for cortex PSI values from GTEx v8 sample"
    
    # Save to JSON
    with open(output_path, "w") as f:
        json.dump(stats, f, indent=2)
    
    print(f"\n=== Descriptive Statistics ===")
    print(f"PSI Column: {psi_column}")
    print(f"Sample Size (n): {stats['n']}")
    print(f"Mean PSI: {stats['mean']:.4f}")
    print(f"Std Dev: {stats['std']:.4f}")
    print(f"Min PSI: {stats['min']:.4f}")
    print(f"Max PSI: {stats['max']:.4f}")
    print(f"\nResults saved to: {output_path.relative_to(project_root)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
