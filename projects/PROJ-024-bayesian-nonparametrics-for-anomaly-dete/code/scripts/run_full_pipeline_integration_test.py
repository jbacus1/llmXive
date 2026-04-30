"""
T078: Final Integration Test - Full Pipeline from Data Download to Evaluation
Tests the complete anomaly detection pipeline on 3-5 UCI datasets
"""
import os
import sys
import json
import time
import yaml
from pathlib import Path
from datetime import datetime

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.timeseries import TimeSeries
from models.dpgmm import DPGMMModel
from models.baselines import ARIMABaseline, MovingAverageBaseline
from services.anomaly_detector import AnomalyDetector
from services.threshold_calibrator import ThresholdCalibrator
from evaluation.metrics import compute_metrics, generate_confusion_matrix
from evaluation.plots import generate_roc_curve, generate_pr_curve
from utils.logger import get_logger
from utils.memory_profiler import profile_memory
from utils.runtime_profiler import profile_runtime

logger = get_logger(__name__)


def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent.parent / 'code' / 'config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def download_datasets_if_needed(dataset_paths, raw_data_dir):
    """Download UCI datasets if not already present"""
    from data.download_datasets import download_dataset
    
    datasets = []
    for dataset_name, url in dataset_paths.items():
        local_path = raw_data_dir / f"{dataset_name}.csv"
        if not local_path.exists():
            logger.info(f"Downloading {dataset_name}...")
            download_dataset(url, str(local_path))
        datasets.append(local_path)
    return datasets


def load_timeseries(filepath):
    """Load time series data from CSV"""
    import pandas as pd
    df = pd.read_csv(filepath)
    # Assume first numeric column is the time series
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    if len(numeric_cols) == 0:
        raise ValueError(f"No numeric columns found in {filepath}")
    values = df[numeric_cols[0]].values
    return TimeSeries(values=values, name=Path(filepath).stem)


def run_dpgmm_on_timeseries(ts, config):
    """Run DPGMM model on time series"""
    model = DPGMMModel(
      concentration_prior=config['dpgmm']['concentration_prior'],
      variance_prior=config['dpgmm']['variance_prior'],
      random_seed=config['random_seed']
    )
    
    # Stream observations one at a time
    scores = []
    for i, obs in enumerate(ts.values):
        model.update(obs)
        score = model.compute_anomaly_score(obs)
        scores.append(score)
    
    return scores, model


def run_baseline_models(ts, config):
    """Run ARIMA and moving average baselines"""
    arima_scores = ARIMABaseline().compute_scores(ts.values)
    ma_scores = MovingAverageBaseline(
      window_size=config['baselines']['moving_average_window']
    ).compute_scores(ts.values)
    return arima_scores, ma_scores


def compute_ground_truth(ts, config):
    """
    Compute ground truth anomaly labels.
    For UCI datasets, use statistical outliers as proxy ground truth.
    For synthetic datasets, use known labels.
    """
    import numpy as np
    from scipy import stats
    
    # Use Z-score based ground truth for real datasets
    z_scores = np.abs(stats.zscore(ts.values, nan_policy='omit'))
    threshold = config['threshold']['z_score_threshold']
    ground_truth = (z_scores > threshold).astype(int)
    return ground_truth


def evaluate_model(scores, ground_truth, config):
    """Evaluate model performance against ground truth"""
    # Calibrate threshold
    calibrator = ThresholdCalibrator(
      percentile=config['threshold']['calibration_percentile']
    )
    threshold = calibrator.calibrate(scores)
    
    # Flag anomalies
    predictions = (np.array(scores) > threshold).astype(int)
    
    # Compute metrics
    metrics = compute_metrics(
      y_true=ground_truth,
      y_pred=predictions,
      scores=np.array(scores)
    )
    
    return metrics, threshold


def run_full_pipeline_on_dataset(filepath, config, output_dir):
    """Run complete pipeline on a single dataset"""
    start_time = time.time()
    dataset_name = Path(filepath).stem
    results = {
      'dataset': dataset_name,
      'status': 'running',
      'start_time': datetime.now().isoformat()
    }
    
    try:
        logger.info(f"Processing {dataset_name}...")
        
        # Load time series
        ts = load_timeseries(filepath)
        logger.info(f"Loaded {len(ts.values)} observations")
        
        # Run DPGMM
        logger.info("Running DPGMM model...")
        dpgmm_scores, dpgmm_model = run_dpgmm_on_timeseries(ts, config)
        results['dpgmm'] = {
          'n_clusters': dpgmm_model.n_clusters,
          'convergence': dpgmm_model.converged
        }
        
        # Run baselines
        logger.info("Running baseline models...")
        arima_scores, ma_scores = run_baseline_models(ts, config)
        
        # Compute ground truth
        logger.info("Computing ground truth...")
        ground_truth = compute_ground_truth(ts, config)
        
        # Evaluate DPGMM
        logger.info("Evaluating DPGMM...")
        dpgmm_metrics, threshold = evaluate_model(dpgmm_scores, ground_truth, config)
        results['dpgmm_metrics'] = dpgmm_metrics
        results['threshold'] = float(threshold)
        
        # Evaluate baselines
        logger.info("Evaluating baselines...")
        arima_metrics, _ = evaluate_model(arima_scores, ground_truth, config)
        ma_metrics, _ = evaluate_model(ma_scores, ground_truth, config)
        results['baseline_metrics'] = {
          'arima': arima_metrics,
          'moving_average': ma_metrics
        }
        
        # Generate plots
        logger.info("Generating plots...")
        plot_dir = output_dir / 'plots'
        plot_dir.mkdir(parents=True, exist_ok=True)
        
        generate_roc_curve(
          y_true=ground_truth,
          scores=dpgmm_scores,
          title=f'{dataset_name} - DPGMM ROC',
          output_path=str(plot_dir / f'{dataset_name}_roc.png')
        )
        
        generate_pr_curve(
          y_true=ground_truth,
          scores=dpgmm_scores,
          title=f'{dataset_name} - DPGMM PR',
          output_path=str(plot_dir / f'{dataset_name}_pr.png')
        )
        
        results['status'] = 'completed'
        results['end_time'] = datetime.now().isoformat()
        results['runtime_seconds'] = time.time() - start_time
        
    except Exception as e:
        results['status'] = 'failed'
        results['error'] = str(e)
        results['end_time'] = datetime.now().isoformat()
        logger.error(f"Failed to process {dataset_name}: {e}")
    
    return results


def main():
    """Main integration test runner"""
    config = load_config()
    project_root = Path(__file__).parent.parent.parent
    
    # Setup output directories
    output_dir = project_root / 'data' / 'results' / 'integration_test'
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_data_dir = project_root / 'data' / 'raw'
    
    # UCI dataset URLs (from T057)
    dataset_paths = config.get('datasets', {
      'nyc_taxi': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00344/traffic.csv',
      'sml2010': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00213/data.csv',
      'ecg200': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00235/ECG200.zip'
    })
    
    # Download datasets if needed
    logger.info("Checking/Downloading datasets...")
    datasets = download_datasets_if_needed(dataset_paths, raw_data_dir)
    
    # Run full pipeline on each dataset
    all_results = []
    total_start = time.time()
    
    for dataset_path in datasets[:5]:  # Limit to 5 datasets
        result = run_full_pipeline_on_dataset(dataset_path, config, output_dir)
        all_results.append(result)
        
        # Save individual result
        with open(output_dir / f"{result['dataset']}_result.json", 'w') as f:
            json.dump(result, f, indent=2)
    
    # Generate summary report
    summary = {
      'test_id': 'T078_integration_test',
      'timestamp': datetime.now().isoformat(),
      'total_datasets': len(all_results),
      'completed': sum(1 for r in all_results if r['status'] == 'completed'),
      'failed': sum(1 for r in all_results if r['status'] == 'failed'),
      'total_runtime_seconds': time.time() - total_start,
      'datasets': all_results,
      'summary_metrics': {
          'dpgmm_avg_precision': sum(r.get('dpgmm_metrics', {}).get('precision', 0) for r in all_results) / max(len(all_results), 1),
          'dpgmm_avg_recall': sum(r.get('dpgmm_metrics', {}).get('recall', 0) for r in all_results) / max(len(all_results), 1),
          'dpgmm_avg_f1': sum(r.get('dpgmm_metrics', {}).get('f1_score', 0) for r in all_results) / max(len(all_results), 1),
      }
    }
    
    # Save summary
    with open(output_dir / 'integration_test_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print("=" * 60)
    print("INTEGRATION TEST T078 SUMMARY")
    print("=" * 60)
    print(f"Total Datasets: {summary['total_datasets']}")
    print(f"Completed: {summary['completed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Total Runtime: {summary['total_runtime_seconds']:.2f} seconds")
    print(f"DPGMM Avg Precision: {summary['summary_metrics']['dpgmm_avg_precision']:.4f}")
    print(f"DPGMM Avg Recall: {summary['summary_metrics']['dpgmm_avg_recall']:.4f}")
    print(f"DPGMM Avg F1: {summary['summary_metrics']['dpgmm_avg_f1']:.4f}")
    print("=" * 60)
    
    # Return success if at least 3 datasets completed
    if summary['completed'] >= 3:
        print("✓ INTEGRATION TEST PASSED (>= 3 datasets)")
        return 0
    else:
        print("✗ INTEGRATION TEST FAILED (< 3 datasets)")
        return 1


if __name__ == '__main__':
    sys.exit(main())
