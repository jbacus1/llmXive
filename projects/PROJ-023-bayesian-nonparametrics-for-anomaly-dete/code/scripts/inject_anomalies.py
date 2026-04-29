"""
T004: Inject anomalies into time series data.

Loads data/raw/series.csv, injects mean shifts and variance spikes
at known indices, saves:
- data/processed/series_with_anomalies.csv
- data/processed/ground_truth.csv

This script MUST be executed to produce the output files.
"""

import os
import numpy as np
import pandas as pd

def main():
    # Paths
    input_path = "data/raw/series.csv"
    output_series_path = "data/processed/series_with_anomalies.csv"
    output_gt_path = "data/processed/ground_truth.csv"
    
    # Ensure output directory exists
    os.makedirs("data/processed", exist_ok=True)
    
    # Load the time series data
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Handle different possible column names
    if 'value' in df.columns:
        series = df['value'].values
    elif 'Value' in df.columns:
        series = df['Value'].values
    elif 'values' in df.columns:
        series = df['values'].values
    else:
        # Assume first column is the series
        series = df.iloc[:, 0].values
    
    n = len(series)
    print(f"Loaded {n} data points.")
    
    # Compute baseline statistics for anomaly injection
    mean_val = np.mean(series)
    std_val = np.std(series)
    
    # Define anomaly injection parameters
    # Mean shifts: add/subtract multiple of std
    # Variance spikes: multiply local variance by factor
    
    # Select known indices for anomalies (spread throughout series)
    # Using deterministic indices for reproducibility
    anomaly_indices = {
        'mean_shift_pos': [int(n * 0.1), int(n * 0.4), int(n * 0.75)],
        'mean_shift_neg': [int(n * 0.2), int(n * 0.55)],
        'variance_spike': [int(n * 0.3), int(n * 0.65), int(n * 0.9)]
    }
    
    # Create anomaly ground truth (0 = normal, 1 = anomaly)
    ground_truth = np.zeros(n, dtype=int)
    
    # Create copy of series for modification
    series_anomalous = series.copy().astype(float)
    
    print(f"Injecting anomalies at {sum(len(v) for v in anomaly_indices.values())} locations...")
    
    # Inject positive mean shifts (add 4 * std)
    for idx in anomaly_indices['mean_shift_pos']:
        series_anomalous[idx] = mean_val + 4 * std_val
        ground_truth[idx] = 1
        print(f"  Mean shift (+4σ) at index {idx}")
    
    # Inject negative mean shifts (subtract 4 * std)
    for idx in anomaly_indices['mean_shift_neg']:
        series_anomalous[idx] = mean_val - 4 * std_val
        ground_truth[idx] = 1
        print(f"  Mean shift (-4σ) at index {idx}")
    
    # Inject variance spikes (replace with high-variance noise)
    for idx in anomaly_indices['variance_spike']:
        # Create a small window of variance spike
        window_size = 5
        start = max(0, idx - window_size // 2)
        end = min(n, idx + window_size // 2 + 1)
        for j in range(start, end):
            series_anomalous[j] = mean_val + np.random.randn() * 3 * std_val
            ground_truth[j] = 1
        print(f"  Variance spike at index {idx} (window {start}-{end})")
    
    # Save the anomalous series
    output_df = pd.DataFrame({'value': series_anomalous})
    output_df.to_csv(output_series_path, index=False)
    print(f"Saved anomalous series to {output_series_path}")
    
    # Save ground truth
    gt_df = pd.DataFrame({
        'index': range(n),
        'is_anomaly': ground_truth
    })
    gt_df.to_csv(output_gt_path, index=False)
    print(f"Saved ground truth to {output_gt_path}")
    
    # Summary statistics
    total_anomalies = np.sum(ground_truth)
    print(f"\nSummary:")
    print(f"  Total data points: {n}")
    print(f"  Anomaly points: {total_anomalies} ({100*total_anomalies/n:.2f}%)")
    print(f"  Mean shift (+): {len(anomaly_indices['mean_shift_pos'])} points")
    print(f"  Mean shift (-): {len(anomaly_indices['mean_shift_neg'])} points")
    print(f"  Variance spikes: {len(anomaly_indices['variance_spike'])} windows")

if __name__ == "__main__":
    main()
