"""
Shewhart Control Chart for Time Series Anomaly Detection

Implements a classical statistical process control method that flags
observations outside mean ± k*standard_deviation as anomalies.

Input:  data/processed/series_with_anomalies.csv
Output: data/results/shewhart_predictions.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Configuration
DATA_PATH = Path("data/processed/series_with_anomalies.csv")
OUTPUT_PATH = Path("data/results/shewhart_predictions.csv")
SIGMA_THRESHOLD = 3.0  # Standard control chart limit (99.7% coverage)

def main():
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = pd.read_csv(DATA_PATH)
    
    # Handle both single-column and multi-column formats
    if 'value' in df.columns:
        series = df['value'].values
        indices = df.index.values if 'index' not in df.columns else df['index'].values
    elif len(df.columns) == 1:
        series = df.iloc[:, 0].values
        indices = np.arange(len(series))
    else:
        # Use first numeric column
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        series = df[numeric_cols[0]].values
        indices = df.index.values
    
    # Calculate baseline statistics (using robust estimation)
    # For control charts, we typically use the first portion of data
    # or all data assuming anomalies are sparse
    n_normal_estimate = int(len(series) * 0.8)  # Assume first 80% is mostly normal
    baseline_data = series[:n_normal_estimate]
    
    mean = np.mean(baseline_data)
    std = np.std(baseline_data)
    
    # Handle edge case where std is zero or very small
    if std < 1e-10:
        std = 1.0
    
    # Set control limits
    upper_limit = mean + SIGMA_THRESHOLD * std
    lower_limit = mean - SIGMA_THRESHOLD * std
    
    # Detect anomalies
    anomaly_flags = ((series > upper_limit) | (series < lower_limit)).astype(int)
    
    # Calculate z-scores for each point (deviation from mean in std units)
    z_scores = (series - mean) / std
    
    # Create predictions dataframe
    predictions = pd.DataFrame({
        'index': indices,
        'value': series,
        'mean': mean,
        'std': std,
        'upper_limit': upper_limit,
        'lower_limit': lower_limit,
        'z_score': z_scores,
        'anomaly': anomaly_flags
    })
    
    # Save predictions
    predictions.to_csv(OUTPUT_PATH, index=False)
    
    # Print summary statistics
    n_anomalies = anomaly_flags.sum()
    anomaly_rate = n_anomalies / len(series) * 100
    
    print(f"Shewhart Control Chart Results:")
    print(f"  Baseline mean: {mean:.4f}")
    print(f"  Baseline std: {std:.4f}")
    print(f"  Upper control limit: {upper_limit:.4f}")
    print(f"  Lower control limit: {lower_limit:.4f}")
    print(f"  Total points analyzed: {len(series)}")
    print(f"  Anomalies detected: {n_anomalies}")
    print(f"  Anomaly rate: {anomaly_rate:.2f}%")
    print(f"  Predictions saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
