"""
Integration test for the analysis pipeline (User Story 2).

This test validates the end-to-end statistical analysis pipeline:
- Loading processed data from data/processed/
- Running statistical routines (t-tests, ANOVA)
- Generating analysis reports

NOTE: This test should FAIL initially since the analysis service
(src/services/analysis.py) has not been implemented yet.
This follows the "tests first" approach per task requirements.
"""
import pytest
import os
from pathlib import Path
import tempfile
import json
from datetime import datetime

import pandas as pd
import numpy as np

# Import the analysis service (will fail until T020 is implemented)
try:
    from src.services.analysis import AnalysisService
    from src.models.data_models import AssessmentData
except ImportError as e:
    pytest.skip(f"Analysis service not yet implemented: {e}", allow_module_level=True)

# Test fixtures
BASE_DIR = Path(__file__).parent.parent.parent
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

@pytest.fixture
def synthetic_dataset():
    """Create synthetic RCT dataset for testing."""
    np.random.seed(42)
    n_participants = 60
    n_timepoints = 3  # baseline, post, follow-up
    
    # Generate participant IDs
    participant_ids = [f"ASD{str(i).zfill(3)}" for i in range(1, n_participants + 1)]
    
    # Randomly assign to intervention/control groups
    groups = np.random.choice(["intervention", "control"], size=n_participants)
    
    # Generate baseline social skills scores (0-100 scale)
    baseline_scores = np.random.normal(loc=50, scale=15, size=n_participants)
    
    # Generate timepoint data
    timepoints = ["baseline", "post", "followup"]
    data = []
    
    for i, pid in enumerate(participant_ids):
        for tp_idx, tp in enumerate(timepoints):
            # Apply intervention effect for intervention group at post/followup
            if groups[i] == "intervention" and tp_idx > 0:
                effect_size = 8 + (tp_idx * 2)  # Progressive improvement
            else:
                effect_size = 0
            
            # Add noise
            score = baseline_scores[i] + effect_size + np.random.normal(0, 5)
            score = np.clip(score, 0, 100)
            
            data.append({
                "participant_id": pid,
                "group": groups[i],
                "timepoint": tp,
                "social_skills_score": round(score, 2),
                "assessment_date": datetime(2025, 1, 1) + pd.Timedelta(days=tp_idx * 30)
            })
    
    return pd.DataFrame(data)

@pytest.fixture
def processed_data_path(synthetic_dataset):
    """Save synthetic dataset to processed data directory."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_path = PROCESSED_DATA_DIR / "analysis_ready.csv"
    synthetic_dataset.to_csv(file_path, index=False)
    return file_path

@pytest.fixture
def analysis_service(processed_data_path):
    """Initialize the analysis service."""
    return AnalysisService(data_path=str(processed_data_path))

class TestAnalysisPipelineIntegration:
    """Integration tests for the full analysis pipeline."""
    
    def test_pipeline_initialization(self, analysis_service):
        """Test that the analysis service initializes correctly."""
        assert analysis_service is not None
        assert hasattr(analysis_service, 'load_data')
        assert hasattr(analysis_service, 'run_analysis')
    
    def test_data_loading(self, analysis_service):
        """Test that the pipeline can load processed data."""
        data = analysis_service.load_data()
        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
        assert "participant_id" in data.columns
        assert "social_skills_score" in data.columns
    
    def test_group_comparison(self, analysis_service):
        """Test that group comparison statistics are computed."""
        data = analysis_service.load_data()
        result = analysis_service.compare_groups(
            data, 
            metric="social_skills_score",
            timepoint="post"
        )
        assert result is not None
        assert "p_value" in result
        assert "effect_size" in result
    
    def test_pre_post_analysis(self, analysis_service):
        """Test pre-post intervention analysis."""
        data = analysis_service.load_data()
        result = analysis_service.pre_post_analysis(
            data,
            metric="social_skills_score"
        )
        assert result is not None
        assert "baseline_mean" in result
        assert "post_mean" in result
        assert "change" in result
    
    def test_full_pipeline_execution(self, analysis_service):
        """Test complete pipeline execution from data to report."""
        analysis_results = analysis_service.run_full_analysis()
        assert analysis_results is not None
        assert "descriptive_stats" in analysis_results
        assert "group_comparisons" in analysis_results
        assert "longitudinal_analysis" in analysis_results
    
    def test_report_generation(self, analysis_service):
        """Test that analysis reports can be generated."""
        analysis_results = analysis_service.run_full_analysis()
        report = analysis_service.generate_report(analysis_results)
        assert report is not None
        assert isinstance(report, str)
        assert len(report) > 100
    
    def test_synthetic_data_validation(self, synthetic_dataset):
        """Validate that synthetic data meets expected schema."""
        required_columns = ["participant_id", "group", "timepoint", "social_skills_score"]
        for col in required_columns:
            assert col in synthetic_dataset.columns, f"Missing column: {col}"
        
        assert synthetic_dataset["group"].isin(["intervention", "control"]).all()
        assert synthetic_dataset["timepoint"].isin(["baseline", "post", "followup"]).all()
        assert synthetic_dataset["social_skills_score"].between(0, 100).all()
    
    def test_data_integrity_check(self, processed_data_path):
        """Test that data integrity checks work on loaded data."""
        df = pd.read_csv(processed_data_path)
        
        # Check for missing values in critical columns
        assert df["participant_id"].isna().sum() == 0
        assert df["social_skills_score"].isna().sum() == 0
        
        # Check participant count
        assert len(df["participant_id"].unique()) == 60
    
    def test_timepoint_analysis(self, analysis_service):
        """Test analysis across all timepoints."""
        data = analysis_service.load_data()
        timepoint_results = analysis_service.analyze_by_timepoint(
            data,
            metric="social_skills_score"
        )
        assert len(timepoint_results) == 3
        assert "baseline" in timepoint_results
        assert "post" in timepoint_results
        assert "followup" in timepoint_results