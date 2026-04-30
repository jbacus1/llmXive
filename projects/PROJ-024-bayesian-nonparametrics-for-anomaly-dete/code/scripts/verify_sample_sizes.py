#!/usr/bin/env python3
"""
Verify sample size adequacy for all datasets.
Ensures all datasets have 1000+ observations and documents counts in data dictionary.

Usage: python verify_sample_sizes.py
"""
import os
import sys
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DatasetStats:
    """Statistics for a single dataset."""
    name: str
    path: str
    observations: int
    features: int
    has_anomalies: bool
    anomaly_count: int = 0
    observation_count_valid: bool = True
    file_size_mb: float = 0.0
    file_type: str = "unknown"

def find_dataset_files(data_dir: Path) -> List[Dict[str, Any]]:
    """Find all dataset files in the data directory."""
    dataset_files = []
    
    if not data_dir.exists():
        logger.warning(f"Data directory not found: {data_dir}")
        return dataset_files
    
    # Search in raw and processed subdirectories
    search_paths = [
        data_dir / "raw",
        data_dir / "processed",
        data_dir
    ]
    
    for search_path in search_paths:
        if not search_path.exists():
            continue
        
        # Find CSV and parquet files
        for ext in ["*.csv", "*.parquet", "*.csv.gz", "*.tsv"]:
            for file_path in search_path.glob(ext):
                # Skip small files that are likely metadata
                if file_path.stat().st_size > 1000:  # >1KB
                    dataset_files.append({
                        "name": file_path.stem,
                        "path": str(file_path),
                        "extension": file_path.suffix,
                        "type": "raw" if "raw" in str(file_path) else "processed"
                    })
    
    return dataset_files

def count_observations(file_path: Path) -> Optional[DatasetStats]:
    """Count observations and features in a dataset file."""
    try:
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        
        # Determine file type
        if file_path.suffix == ".csv" or file_path.suffix == ".tsv":
            df = pd.read_csv(file_path)
            file_type = "csv"
        elif file_path.suffix == ".parquet":
            df = pd.read_parquet(file_path)
            file_type = "parquet"
        elif file_path.suffix == ".gz" and file_path.stem.endswith(".csv"):
            df = pd.read_csv(file_path, compression="gzip")
            file_type = "csv.gz"
        else:
            logger.warning(f"Unsupported file format: {file_path.suffix}")
            return None
        
        observations = len(df)
        features = len(df.columns)
        
        # Check for anomaly columns
        anomaly_columns = ["anomaly", "label", "target", "is_anomaly", "anomaly_score"]
        has_anomalies = any(col in df.columns for col in anomaly_columns)
        
        anomaly_count = 0
        if has_anomalies:
            # Try to count anomalies
            for col in anomaly_columns:
                if col in df.columns:
                    anomaly_count = int(df[col].sum()) if df[col].dtype in ["int64", "float64"] else 0
                    break
        
        stats = DatasetStats(
            name=file_path.stem,
            path=str(file_path),
            observations=observations,
            features=features,
            has_anomalies=has_anomalies,
            anomaly_count=anomaly_count,
            observation_count_valid=observations >= 1000,
            file_size_mb=round(file_size_mb, 2),
            file_type=file_type
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return None

def analyze_datasets(project_root: Path) -> List[DatasetStats]:
    """Analyze all datasets in the project."""
    data_dir = project_root / "data"
    dataset_files = find_dataset_files(data_dir)
    
    if not dataset_files:
        logger.warning("No dataset files found")
        return []
    
    logger.info(f"Found {len(dataset_files)} dataset files to analyze")
    
    all_stats = []
    for file_info in dataset_files:
        file_path = Path(file_info["path"])
        logger.info(f"Processing: {file_info['name']}")
        
        stats = count_observations(file_path)
        if stats:
            all_stats.append(stats)
            logger.info(f"  - {stats.observations} observations, {stats.features} features")
        else:
            logger.warning(f"  - Could not process file")
    
    return all_stats

def generate_report(stats: List[DatasetStats]) -> str:
    """Generate a markdown report of dataset statistics."""
    report_lines = [
        "# Dataset Sample Size Verification Report",
        f"\nGenerated: {datetime.now().isoformat()}",
        "\n## Summary",
        "",
        f"- **Total Datasets Analyzed**: {len(stats)}",
        f"- **Datasets with 1000+ Observations**: {sum(1 for s in stats if s.observation_count_valid)}",
        f"- **Datasets Below 1000 Observations**: {sum(1 for s in stats if not s.observation_count_valid)}",
        ""
    ]
    
    if not stats:
        report_lines.extend([
            "No datasets were found or processed.",
            ""
        ])
        return "\n".join(report_lines)
    
    # Table of all datasets
    report_lines.extend([
        "## Dataset Details",
        "",
        "| Dataset Name | File Path | Observations | Features | Has Anomalies | Anomaly Count | File Size (MB) | Valid (>1000) |",
        "|--------------|-----------|--------------|----------|---------------|---------------|----------------|---------------|"
    ])
    
    for s in stats:
        valid_marker = "✓" if s.observation_count_valid else "✗"
        report_lines.append(
            f"| {s.name} | {s.path} | {s.observations} | {s.features} | "
            f"{'Yes' if s.has_anomalies else 'No'} | {s.anomaly_count} | {s.file_size_mb} | {valid_marker} |"
        )
    
    report_lines.extend([
        "",
        "## Requirements",
        "",
        "- **Minimum Observations**: 1000 per dataset (per SC-001)",
        "- **Datasets Analyzed**: Electricity, Traffic, Synthetic Control Chart",
        "",
        "## Datasets Below Requirement",
        ""
    ])
    
    failed_datasets = [s for s in stats if not s.observation_count_valid]
    if failed_datasets:
        for s in failed_datasets:
            report_lines.append(f"- **{s.name}**: {s.observations} observations (needs {1000 - s.observations} more)")
        report_lines.append("")
    else:
        report_lines.append("All datasets meet the 1000+ observation requirement.")
        report_lines.append("")
    
    return "\n".join(report_lines)

def update_data_dictionary(project_root: Path, stats: List[DatasetStats]) -> bool:
    """Update the data dictionary with observation counts."""
    # Find data dictionary file
    data_dict_paths = [
        project_root / "specs" / "001-bayesian-nonparametrics-anomaly-detection" / "data-dictionary.md",
        project_root / "specs" / "data-dictionary.md",
        project_root / "data" / "README.md"
    ]
    
    data_dict_path = None
    for path in data_dict_paths:
        if path.exists():
            data_dict_path = path
            break
    
    if not data_dict_path:
        logger.warning("Data dictionary not found - creating new one")
        data_dict_path = project_root / "specs" / "001-bayesian-nonparametrics-anomaly-detection" / "data-dictionary.md"
        data_dict_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing content
    existing_content = ""
    if data_dict_path.exists():
        existing_content = data_dict_path.read_text()
    
    # Build dataset section
    dataset_section = [
        "## Dataset Observation Counts",
        "",
        f"*Last Updated: {datetime.now().isoformat()}*",
        "",
        "| Dataset | Observations | Features | Has Anomalies | Source |",
        "|---------|--------------|----------|---------------|--------|"
    ]
    
    for s in stats:
        source = "UCI" if "uci" in s.path.lower() or "electricity" in s.path.lower() or "traffic" in s.path.lower() else "Synthetic/NAB"
        dataset_section.append(
            f"| {s.name} | {s.observations} | {s.features} | {'Yes' if s.has_anomalies else 'No'} | {source} |"
        )
    
    dataset_section.append("")
    
    # Check all datasets meet requirement
    all_valid = all(s.observation_count_valid for s in stats)
    if all_valid and stats:
        dataset_section.extend([
          "### Sample Size Adequacy ✓",
          "",
          "All datasets meet the minimum requirement of **1000+ observations**.",
          ""
        ])
    else:
        dataset_section.extend([
            "### Sample Size Adequacy",
            "",
            "Some datasets do not meet the 1000+ observation requirement.",
            ""
        ])
    
    # Insert or append the section
    if "## Dataset Observation Counts" in existing_content:
        # Replace existing section
        lines = existing_content.split("\n")
        new_lines = []
        in_section = False
        section_added = False
        
        for i, line in enumerate(lines):
            if "## Dataset Observation Counts" in line:
                in_section = True
                new_lines.append(line)
                new_lines.append("")
                # Add the new content
                new_lines.extend(dataset_section[1:])  # Skip first line which is already added
                section_added = True
                continue
            
            # Skip lines until we hit the next section
            if in_section and line.startswith("## "):
                in_section = False
                new_lines.append(line)
                continue
            
            if not in_section:
                new_lines.append(line)
        
        if not section_added:
            new_lines.extend(dataset_section)
        
        data_dict_path.write_text("\n".join(new_lines))
    else:
        # Append new section
        if existing_content and not existing_content.endswith("\n"):
            existing_content += "\n\n"
        data_dict_path.write_text(existing_content + "\n".join(dataset_section))
    
    logger.info(f"Updated data dictionary at: {data_dict_path}")
    return True

def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Dataset Sample Size Verification")
    logger.info("=" * 60)
    
    project_root = Path(__file__).parent.parent.parent
    
    # Analyze all datasets
    stats = analyze_datasets(project_root)
    
    if not stats:
        logger.warning("No datasets found to analyze")
        print("No datasets found. Ensure data files exist in data/raw/ or data/processed/")
        sys.exit(0)
    
    # Generate report
    report = generate_report(stats)
    report_path = project_root / "data" / "sample_size_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    logger.info(f"Report saved to: {report_path}")
    
    # Update data dictionary
    update_data_dictionary(project_root, stats)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total datasets analyzed: {len(stats)}")
    print(f"Datasets with 1000+ observations: {sum(1 for s in stats if s.observation_count_valid)}")
    print(f"Datasets below 1000 observations: {sum(1 for s in stats if not s.observation_count_valid)}")
    
    all_valid = all(s.observation_count_valid for s in stats)
    if all_valid:
        print("\n✓ All datasets meet the 1000+ observation requirement.")
    else:
        print("\n✗ Some datasets do not meet the requirement:")
        for s in stats:
            if not s.observation_count_valid:
                print(f"  - {s.name}: {s.observations} observations")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
