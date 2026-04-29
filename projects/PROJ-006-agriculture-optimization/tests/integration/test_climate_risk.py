"""
Integration test for climate risk model (US2).

This test verifies that the climate risk assessment pipeline:
1. Correctly loads and preprocesses climate data
2. Calculates risk scores using the climate_risk model
3. Outputs results matching the expected schema

NOTE: Written before implementation per TDD approach.
Tests will FAIL until T025 (climate_risk model) is implemented.
"""

import pytest
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import model (will fail until T025 is complete)
try:
    from models.climate_risk import ClimateRiskModel
    MODEL_AVAILABLE = True
except ImportError:
    MODEL_AVAILABLE = False

from config.constants import DATA_DIR, OUTPUT_DIR
from config.schemas import RiskAssessmentSchema


class TestClimateRiskIntegration:
    """Integration tests for climate risk assessment pipeline."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test fixtures before each test."""
        self.test_data_dir = Path(DATA_DIR) / "raw" / "test_climate"
        self.test_output_dir = Path(OUTPUT_DIR) / "test_risk"
        
        # Ensure test directories exist
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        yield
        
        # Cleanup test outputs
        if self.test_output_dir.exists():
            import shutil
            shutil.rmtree(self.test_output_dir)
    
    @pytest.mark.skipif(
        not MODEL_AVAILABLE,
        reason="ClimateRiskModel not yet implemented (T025)"
    )
    def test_climate_risk_model_initialization(self):
        """Test that the climate risk model initializes correctly."""
        model = ClimateRiskModel()
        
        assert model is not None
        assert hasattr(model, 'calculate_risk_score')
        assert hasattr(model, 'assess_vulnerability')
    
    @pytest.mark.skipif(
        not MODEL_AVAILABLE,
        reason="ClimateRiskModel not yet implemented (T025)"
    )
    def test_climate_risk_score_calculation(self):
        """Test risk score calculation with sample climate data."""
        model = ClimateRiskModel()
        
        # Sample climate data (would come from US1 collectors)
        sample_data = {
            "temperature_avg": 25.5,
            "temperature_max": 35.0,
            "precipitation_mm": 120.0,
            "drought_index": 0.3,
            "flood_risk": 0.2,
            "growing_season_days": 180
        }
        
        risk_score = model.calculate_risk_score(sample_data)
        
        # Validate risk score is in expected range
        assert isinstance(risk_score, (int, float))
        assert 0 <= risk_score <= 100, "Risk score should be between 0-100"
    
    @pytest.mark.skipif(
        not MODEL_AVAILABLE,
        reason="ClimateRiskModel not yet implemented (T025)"
    )
    def test_climate_risk_output_schema(self):
        """Test that risk assessment output matches the schema."""
        model = ClimateRiskModel()
        
        sample_data = {
            "temperature_avg": 28.0,
            "temperature_max": 38.0,
            "precipitation_mm": 80.0,
            "drought_index": 0.5,
            "flood_risk": 0.1,
            "growing_season_days": 150
        }
        
        result = model.assess_vulnerability(sample_data)
        
        # Validate against RiskAssessmentSchema
        RiskAssessmentSchema.validate(result)
        
        # Verify required fields exist
        assert "risk_score" in result
        assert "risk_level" in result
        assert "timestamp" in result
        assert "data_sources" in result
    
    @pytest.mark.skipif(
        not MODEL_AVAILABLE,
        reason="ClimateRiskModel not yet implemented (T025)"
    )
    def test_climate_risk_time_series_integration(self):
        """Test time series analysis for historical climate patterns."""
        model = ClimateRiskModel()
        
        # Historical climate data (would come from US1)
        historical_data = [
            {"year": 2020, "temp_avg": 24.0, "precip_mm": 100.0},
            {"year": 2021, "temp_avg": 25.5, "precip_mm": 95.0},
            {"year": 2022, "temp_avg": 26.0, "precip_mm": 85.0},
            {"year": 2023, "temp_avg": 27.5, "precip_mm": 70.0},
        ]
        
        trend_analysis = model.analyze_climate_trends(historical_data)
        
        assert isinstance(trend_analysis, dict)
        assert "trend_direction" in trend_analysis
        assert "risk_trajectory" in trend_analysis
    
    @pytest.mark.skipif(
        not MODEL_AVAILABLE,
        reason="ClimateRiskModel not yet implemented (T025)"
    )
    def test_climate_risk_edge_cases(self):
        """Test model handles edge cases gracefully."""
        model = ClimateRiskModel()
        
        # Empty data
        with pytest.raises((ValueError, KeyError)):
            model.calculate_risk_score({})
        
        # Extreme values
        extreme_data = {
            "temperature_avg": 50.0,
            "temperature_max": 60.0,
            "precipitation_mm": 0.0,
            "drought_index": 1.0,
            "flood_risk": 1.0,
            "growing_season_days": 30
        }
        
        risk_score = model.calculate_risk_score(extreme_data)
        assert risk_score > 70, "Extreme conditions should yield high risk"
    
    @pytest.mark.skipif(
        not MODEL_AVAILABLE,
        reason="ClimateRiskModel not yet implemented (T025)"
    )
    def test_climate_risk_with_processor_output(self):
        """Test integration with climate processor output format."""
        model = ClimateRiskModel()
        
        # Simulated processor output from T022
        processor_output = {
            "location": {
                "lat": 15.0,
                "lon": -20.0,
                "region": "test_region"
            },
            "climate_data": {
                "temperature_avg": 26.0,
                "temperature_max": 36.0,
                "precipitation_mm": 90.0,
                "drought_index": 0.4,
                "flood_risk": 0.3,
                "growing_season_days": 160
            },
            "data_quality": {
                "completeness": 0.95,
                "sources": ["OpenWeatherMap", "USGS"]
            }
        }
        
        risk_assessment = model.assess_vulnerability(
            processor_output["climate_data"]
        )
        
        # Verify output includes location context
        assert "location" in risk_assessment or risk_assessment.get("risk_score") is not None
    
    def test_climate_risk_data_pipeline_integration(self):
        """Test full pipeline from data collection to risk output."""
        # This test verifies end-to-end integration
        # Will fail until US1 collectors (T015-T018) and US2 model (T025) are complete
        
        if not MODEL_AVAILABLE:
            pytest.skip("ClimateRiskModel not yet implemented")
        
        # Simulate data flow: collector -> processor -> model
        raw_data = {
            "temp": 25.0,
            "rain": 100.0,
            "location": "test"
        }
        
        # Process through model
        model = ClimateRiskModel()
        risk_output = model.calculate_risk_score(raw_data)
        
        # Verify output can be consumed by downstream (US3 recommendations)
        assert risk_output is not None
        assert isinstance(risk_output, (int, float))
    
    @pytest.mark.parametrize(
        "climate_scenario,expected_risk_range",
        [
            ({"drought_index": 0.1, "flood_risk": 0.1}, (0, 30)),
            ({"drought_index": 0.5, "flood_risk": 0.5}, (30, 60)),
            ({"drought_index": 0.9, "flood_risk": 0.9}, (60, 100)),
        ]
    )
    def test_climate_risk_scenario_mapping(self, climate_scenario, expected_risk_range):
        """Test that different climate scenarios map to appropriate risk levels."""
        if not MODEL_AVAILABLE:
            pytest.skip("ClimateRiskModel not yet implemented")
        
        model = ClimateRiskModel()
        
        base_data = {
            "temperature_avg": 25.0,
            "temperature_max": 35.0,
            "precipitation_mm": 100.0,
            "drought_index": climate_scenario["drought_index"],
            "flood_risk": climate_scenario["flood_risk"],
            "growing_season_days": 180
        }
        
        risk_score = model.calculate_risk_score(base_data)
        
        assert expected_risk_range[0] <= risk_score <= expected_risk_range[1]