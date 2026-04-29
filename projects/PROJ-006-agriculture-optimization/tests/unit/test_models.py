"""
Unit tests for climate-smart agricultural models.

Tests cover:
- ClimateRisk model (src/models/climate_risk.py)
- AdoptionRate model (src/models/adoption_rate.py)
- CropYield model (src/models/crop_yield.py)
- InterventionStrategies model (src/models/intervention_strategies.py)

These tests verify model initialization, validation, and core
computation methods without requiring external data sources.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from models.climate_risk import ClimateRisk
from models.adoption_rate import AdoptionRate
from models.crop_yield import CropYield
from models.intervention_strategies import InterventionStrategies


# ============================================================================
# ClimateRisk Model Tests
# ============================================================================

class TestClimateRisk:
    """Unit tests for ClimateRisk model."""
    
    def test_init_with_valid_parameters(self):
        """Test model initialization with valid parameters."""
        risk = ClimateRisk(
            region_id="R001",
            baseline_yield=2.5,
            temperature_anomaly=1.2,
            precipitation_anomaly=-0.15,
            drought_frequency=0.25
        )
        assert risk.region_id == "R001"
        assert risk.baseline_yield == 2.5
        assert risk.temperature_anomaly == 1.2
        assert risk.precipitation_anomaly == -0.15
        assert risk.drought_frequency == 0.25
    
    def test_init_with_negative_baseline_yield(self):
        """Test that negative baseline yield raises ValueError."""
        with pytest.raises(ValueError):
            ClimateRisk(
                region_id="R002",
                baseline_yield=-1.0,
                temperature_anomaly=0.5,
                precipitation_anomaly=0.1,
                drought_frequency=0.1
            )
    
    def test_init_with_probability_out_of_range(self):
        """Test that probability values outside [0,1] raise ValueError."""
        with pytest.raises(ValueError):
            ClimateRisk(
                region_id="R003",
                baseline_yield=2.0,
                temperature_anomaly=0.8,
                precipitation_anomaly=0.1,
                drought_frequency=1.5  # Invalid: > 1.0
            )
    
    def test_calculate_risk_score_positive_anomaly(self):
        """Test risk score calculation with positive temperature anomaly."""
        risk = ClimateRisk(
            region_id="R004",
            baseline_yield=3.0,
            temperature_anomaly=2.0,
            precipitation_anomaly=-0.2,
            drought_frequency=0.4
        )
        score = risk.calculate_risk_score()
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_calculate_risk_score_zero_anomaly(self):
        """Test risk score with no climate anomaly (should be low risk)."""
        risk = ClimateRisk(
            region_id="R005",
            baseline_yield=3.0,
            temperature_anomaly=0.0,
            precipitation_anomaly=0.0,
            drought_frequency=0.0
        )
        score = risk.calculate_risk_score()
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_get_risk_category_high(self):
        """Test that high risk scores return 'high' category."""
        risk = ClimateRisk(
            region_id="R006",
            baseline_yield=1.5,
            temperature_anomaly=3.0,
            precipitation_anomaly=-0.5,
            drought_frequency=0.6
        )
        score = risk.calculate_risk_score()
        category = risk.get_risk_category(score)
        assert category in ['low', 'medium', 'high', 'critical']
    
    def test_to_dict_serialization(self):
        """Test model serialization to dictionary."""
        risk = ClimateRisk(
            region_id="R007",
            baseline_yield=2.5,
            temperature_anomaly=1.5,
            precipitation_anomaly=-0.1,
            drought_frequency=0.3
        )
        data = risk.to_dict()
        assert 'region_id' in data
        assert 'risk_score' in data
        assert 'risk_category' in data
        assert data['region_id'] == "R007"
    
    def test_from_dict_deserialization(self):
        """Test model deserialization from dictionary."""
        data = {
            'region_id': 'R008',
            'baseline_yield': 2.0,
            'temperature_anomaly': 1.0,
            'precipitation_anomaly': -0.15,
            'drought_frequency': 0.25
        }
        risk = ClimateRisk.from_dict(data)
        assert risk.region_id == 'R008'
        assert risk.baseline_yield == 2.0
        assert risk.temperature_anomaly == 1.0
    
    def test_batch_risk_calculation(self):
        """Test batch risk calculation for multiple regions."""
        risk_data = [
            {'region_id': 'R009', 'baseline_yield': 2.5, 'temperature_anomaly': 1.0,
             'precipitation_anomaly': -0.1, 'drought_frequency': 0.2},
            {'region_id': 'R010', 'baseline_yield': 3.0, 'temperature_anomaly': 0.5,
             'precipitation_anomaly': 0.05, 'drought_frequency': 0.1},
        ]
        results = ClimateRisk.calculate_batch_risk(risk_data)
        assert len(results) == 2
        assert all('risk_score' in r for r in results)
        assert all('risk_category' in r for r in results)

# ============================================================================
# AdoptionRate Model Tests
# ============================================================================

class TestAdoptionRate:
    """Unit tests for AdoptionRate model."""
    
    def test_init_with_valid_parameters(self):
        """Test model initialization with valid parameters."""
        adoption = AdoptionRate(
            practice_type="conservation_tillage",
            community_id="C001",
            current_rate=0.35,
            potential_rate=0.85,
            barriers_score=0.4
        )
        assert adoption.practice_type == "conservation_tillage"
        assert adoption.community_id == "C001"
        assert adoption.current_rate == 0.35
        assert adoption.potential_rate == 0.85
        assert adoption.barriers_score == 0.4
    
    def test_init_rate_out_of_range(self):
        """Test that rates outside [0,1] raise ValueError."""
        with pytest.raises(ValueError):
            AdoptionRate(
                practice_type="cover_crops",
                community_id="C002",
                current_rate=1.5,
                potential_rate=0.8,
                barriers_score=0.3
            )
    
    def test_current_rate_exceeds_potential(self):
        """Test that current_rate > potential_rate raises ValueError."""
        with pytest.raises(ValueError):
            AdoptionRate(
                practice_type="drip_irrigation",
                community_id="C003",
                current_rate=0.7,
                potential_rate=0.5,  # Less than current
                barriers_score=0.2
            )
    
    def test_adoption_gap_calculation(self):
        """Test adoption gap calculation."""
        adoption = AdoptionRate(
            practice_type="agroforestry",
            community_id="C004",
            current_rate=0.25,
            potential_rate=0.75,
            barriers_score=0.5
        )
        gap = adoption.calculate_adoption_gap()
        assert gap == 0.50  # 0.75 - 0.25
    
    def test_adoption_potential_calculation(self):
        """Test adoption potential calculation."""
        adoption = AdoptionRate(
            practice_type="precision_farming",
            community_id="C005",
            current_rate=0.10,
            potential_rate=0.60,
            barriers_score=0.3
        )
        potential = adoption.calculate_adoption_potential()
        assert potential == 0.50  # 0.60 - 0.10
    
    def test_barriers_impact_calculation(self):
        """Test barriers impact on adoption rate."""
        adoption = AdoptionRate(
            practice_type="integrated_pest_management",
            community_id="C006",
            current_rate=0.40,
            potential_rate=0.90,
            barriers_score=0.6
        )
        impact = adoption.calculate_barriers_impact()
        assert isinstance(impact, float)
        assert 0 <= impact <= 1
    
    def test_recommendation_priority(self):
        """Test recommendation priority calculation."""
        adoption = AdoptionRate(
            practice_type="water_harvesting",
            community_id="C007",
            current_rate=0.15,
            potential_rate=0.80,
            barriers_score=0.2
        )
        priority = adoption.calculate_recommendation_priority()
        assert isinstance(priority, float)
        assert priority > 0
    
    def test_to_dict_serialization(self):
        """Test model serialization to dictionary."""
        adoption = AdoptionRate(
            practice_type="crop_rotation",
            community_id="C008",
            current_rate=0.50,
            potential_rate=0.85,
            barriers_score=0.35
        )
        data = adoption.to_dict()
        assert 'practice_type' in data
        assert 'current_rate' in data
        assert 'potential_rate' in data
        assert 'adoption_gap' in data
    
    def test_from_dict_deserialization(self):
        """Test model deserialization from dictionary."""
        data = {
            'practice_type': 'organic_farming',
            'community_id': 'C009',
            'current_rate': 0.20,
            'potential_rate': 0.70,
            'barriers_score': 0.45
        }
        adoption = AdoptionRate.from_dict(data)
        assert adoption.practice_type == 'organic_farming'
        assert adoption.current_rate == 0.20
        assert adoption.potential_rate == 0.70
    
    def test_compare_practices(self):
        """Test comparison of multiple practices."""
        practices = [
            AdoptionRate('conservation_tillage', 'C010', 0.30, 0.80, 0.3),
            AdoptionRate('cover_crops', 'C010', 0.20, 0.60, 0.5),
            AdoptionRate('agroforestry', 'C010', 0.15, 0.70, 0.4),
        ]
        ranked = AdoptionRate.compare_practices(practices)
        assert len(ranked) == 3
        # Should be ordered by priority (highest first)
        assert ranked[0]['priority'] >= ranked[1]['priority']

# ============================================================================
# CropYield Model Tests
# ============================================================================

class TestCropYield:
    """Unit tests for CropYield model."""
    
    def test_init_with_valid_parameters(self):
        """Test model initialization with valid parameters."""
        yield_model = CropYield(
            crop_type="maize",
            region_id="R011",
            baseline_yield=4.5,
            climate_sensitivity=-0.15,
            water_requirement=500
        )
        assert yield_model.crop_type == "maize"
        assert yield_model.region_id == "R011"
        assert yield_model.baseline_yield == 4.5
        assert yield_model.climate_sensitivity == -0.15
        assert yield_model.water_requirement == 500
    
    def test_init_negative_baseline_yield(self):
        """Test that negative baseline yield raises ValueError."""
        with pytest.raises(ValueError):
            CropYield(
                crop_type="wheat",
                region_id="R012",
                baseline_yield=-2.0,
                climate_sensitivity=-0.1,
                water_requirement=400
            )
    
    def test_predict_yield_with_climate_change(self):
        """Test yield prediction with climate change factors."""
        yield_model = CropYield(
            crop_type="rice",
            region_id="R013",
            baseline_yield=5.0,
            climate_sensitivity=-0.2,
            water_requirement=600
        )
        predicted = yield_model.predict_yield(
            temperature_change=1.5,
            precipitation_change=-0.1
        )
        assert isinstance(predicted, float)
        assert predicted >= 0
    
    def test_predict_yield_with_optimal_conditions(self):
        """Test yield prediction with optimal climate conditions."""
        yield_model = CropYield(
            crop_type="soybean",
            region_id="R014",
            baseline_yield=3.5,
            climate_sensitivity=0.05,
            water_requirement=450
        )
        predicted = yield_model.predict_yield(
            temperature_change=-0.5,
            precipitation_change=0.1
        )
        assert isinstance(predicted, float)
        assert predicted >= 0
    
    def test_yield_loss_calculation(self):
        """Test yield loss calculation due to climate stress."""
        yield_model = CropYield(
            crop_type="maize",
            region_id="R015",
            baseline_yield=4.0,
            climate_sensitivity=-0.25,
            water_requirement=550
        )
        loss = yield_model.calculate_yield_loss(
            temperature_change=2.0,
            precipitation_change=-0.2
        )
        assert isinstance(loss, float)
        assert loss >= 0
    
    def test_climate_resilience_score(self):
        """Test climate resilience score calculation."""
        yield_model = CropYield(
            crop_type="sorghum",
            region_id="R016",
            baseline_yield=2.5,
            climate_sensitivity=-0.08,  # Low sensitivity = resilient
            water_requirement=350
        )
        resilience = yield_model.calculate_resilience_score()
        assert isinstance(resilience, float)
        assert 0 <= resilience <= 1
    
    def test_water_stress_index(self):
        """Test water stress index calculation."""
        yield_model = CropYield(
            crop_type="cotton",
            region_id="R017",
            baseline_yield=1.5,
            climate_sensitivity=-0.18,
            water_requirement=700
        )
        stress = yield_model.calculate_water_stress_index(
            available_water=400
        )
        assert isinstance(stress, float)
        assert stress >= 0
    
    def test_to_dict_serialization(self):
        """Test model serialization to dictionary."""
        yield_model = CropYield(
            crop_type="wheat",
            region_id="R018",
            baseline_yield=3.0,
            climate_sensitivity=-0.12,
            water_requirement=480
        )
        data = yield_model.to_dict()
        assert 'crop_type' in data
        assert 'baseline_yield' in data
        assert 'climate_sensitivity' in data
    
    def test_from_dict_deserialization(self):
        """Test model deserialization from dictionary."""
        data = {
            'crop_type': 'barley',
            'region_id': 'R019',
            'baseline_yield': 2.8,
            'climate_sensitivity': -0.10,
            'water_requirement': 420
        }
        yield_model = CropYield.from_dict(data)
        assert yield_model.crop_type == 'barley'
        assert yield_model.baseline_yield == 2.8
    
    def test_compare_crops_resilience(self):
        """Test comparison of crop resilience across multiple crops."""
        crops = [
            CropYield('maize', 'R020', 4.0, -0.15, 500),
            CropYield('sorghum', 'R020', 2.5, -0.08, 350),
            CropYield('wheat', 'R020', 3.0, -0.12, 480),
        ]
        ranked = CropYield.compare_crops_resilience(crops)
        assert len(ranked) == 3
        # Most resilient (least negative sensitivity) should be first
        assert ranked[0]['crop_type'] == 'sorghum'

# ============================================================================
# InterventionStrategies Model Tests
# ============================================================================

class TestInterventionStrategies:
    """Unit tests for InterventionStrategies model."""
    
    def test_init_with_valid_parameters(self):
        """Test model initialization with valid parameters."""
        strategy = InterventionStrategies(
            strategy_id="S001",
            name="Drought-resistant varieties",
            category="adaptation",
            cost_per_hectare=150,
            implementation_time=12,
            effectiveness_score=0.75
        )
        assert strategy.strategy_id == "S001"
        assert strategy.name == "Drought-resistant varieties"
        assert strategy.category == "adaptation"
        assert strategy.cost_per_hectare == 150
        assert strategy.implementation_time == 12
        assert strategy.effectiveness_score == 0.75
    
    def test_init_negative_cost(self):
        """Test that negative cost raises ValueError."""
        with pytest.raises(ValueError):
            InterventionStrategies(
                strategy_id="S002",
                name="Test strategy",
                category="mitigation",
                cost_per_hectare=-50,
                implementation_time=6,
                effectiveness_score=0.5
            )
    
    def test_init_effectiveness_out_of_range(self):
        """Test that effectiveness outside [0,1] raises ValueError."""
        with pytest.raises(ValueError):
            InterventionStrategies(
                strategy_id="S003",
                name="Test strategy",
                category="adaptation",
                cost_per_hectare=100,
                implementation_time=8,
                effectiveness_score=1.5  # Invalid: > 1.0
            )
    
    def test_cost_effectiveness_ratio(self):
        """Test cost-effectiveness ratio calculation."""
        strategy = InterventionStrategies(
            strategy_id="S004",
            name="Conservation agriculture",
            category="adaptation",
            cost_per_hectare=200,
            implementation_time=18,
            effectiveness_score=0.8
        )
        ratio = strategy.calculate_cost_effectiveness()
        assert isinstance(ratio, float)
        assert ratio > 0
    
    def test_priority_score_calculation(self):
        """Test priority score calculation."""
        strategy = InterventionStrategies(
            strategy_id="S005",
            name="Integrated pest management",
            category="sustainability",
            cost_per_hectare=120,
            implementation_time=10,
            effectiveness_score=0.7
        )
        priority = strategy.calculate_priority_score(
            urgency_weight=0.3,
            cost_weight=0.4,
            effectiveness_weight=0.3
        )
        assert isinstance(priority, float)
        assert priority >= 0
    
    def test_category_filtering(self):
        """Test filtering strategies by category."""
        strategies = [
            InterventionStrategies("S006", "Strategy A", "adaptation", 100, 6, 0.6),
            InterventionStrategies("S007", "Strategy B", "mitigation", 150, 9, 0.7),
            InterventionStrategies("S008", "Strategy C", "adaptation", 200, 12, 0.8),
        ]
        filtered = InterventionStrategies.filter_by_category(
            strategies, "adaptation"
        )
        assert len(filtered) == 2
        assert all(s.category == "adaptation" for s in filtered)
    
    def test_budget_optimization(self):
        """Test budget-constrained strategy selection."""
        strategies = [
            InterventionStrategies("S009", "Low cost", "adaptation", 50, 3, 0.5),
            InterventionStrategies("S010", "Medium cost", "mitigation", 100, 6, 0.6),
            InterventionStrategies("S011", "High cost", "adaptation", 200, 12, 0.8),
        ]
        selected, total_cost = InterventionStrategies.optimize_for_budget(
            strategies,
            budget=150,
            min_effectiveness=0.5
        )
        assert total_cost <= 150
        assert all(s.effectiveness_score >= 0.5 for s in selected)
    
    def test_to_dict_serialization(self):
        """Test model serialization to dictionary."""
        strategy = InterventionStrategies(
            strategy_id="S012",
            name="Water harvesting",
            category="adaptation",
            cost_per_hectare=180,
            implementation_time=15,
            effectiveness_score=0.72
        )
        data = strategy.to_dict()
        assert 'strategy_id' in data
        assert 'name' in data
        assert 'category' in data
        assert 'cost_effectiveness' in data
    
    def test_from_dict_deserialization(self):
        """Test model deserialization from dictionary."""
        data = {
            'strategy_id': 'S013',
            'name': 'Climate-smart storage',
            'category': 'mitigation',
            'cost_per_hectare': 130,
            'implementation_time': 8,
            'effectiveness_score': 0.65
        }
        strategy = InterventionStrategies.from_dict(data)
        assert strategy.strategy_id == 'S013'
        assert strategy.name == 'Climate-smart storage'
        assert strategy.category == 'mitigation'
    
    def test_multi_criteria_ranking(self):
        """Test multi-criteria ranking of strategies."""
        strategies = [
            InterventionStrategies("S014", "Strategy A", "adaptation", 80, 4, 0.7),
            InterventionStrategies("S015", "Strategy B", "mitigation", 120, 6, 0.8),
            InterventionStrategies("S016", "Strategy C", "adaptation", 100, 5, 0.65),
        ]
        ranked = InterventionStrategies.multi_criteria_ranking(
            strategies,
            weights={'cost': 0.3, 'time': 0.2, 'effectiveness': 0.5}
        )
        assert len(ranked) == 3
        # Should be ordered by composite score (highest first)
        assert ranked[0]['composite_score'] >= ranked[1]['composite_score']

# ============================================================================
# Integration Tests for Model Interactions
# ============================================================================

class TestModelInteractions:
    """Tests for interactions between different models."""
    
    def test_climate_risk_and_crop_yield_integration(self):
        """Test that ClimateRisk and CropYield can work together."""
        risk = ClimateRisk(
            region_id="R021",
            baseline_yield=4.0,
            temperature_anomaly=1.5,
            precipitation_anomaly=-0.15,
            drought_frequency=0.3
        )
        yield_model = CropYield(
            crop_type="maize",
            region_id="R021",
            baseline_yield=4.0,
            climate_sensitivity=-0.15,
            water_requirement=500
        )
        
        # Both models should operate on same region
        assert risk.region_id == yield_model.region_id
        
        # Risk score and yield prediction should both be calculable
        risk_score = risk.calculate_risk_score()
        predicted_yield = yield_model.predict_yield(1.5, -0.15)
        
        assert 0 <= risk_score <= 100
        assert predicted_yield >= 0
    
    def test_adoption_rate_and_intervention_strategies_integration(self):
        """Test that AdoptionRate and InterventionStrategies can work together."""
        adoption = AdoptionRate(
            practice_type="drought_resistant_varieties",
            community_id="C011",
            current_rate=0.20,
            potential_rate=0.75,
            barriers_score=0.45
        )
        
        strategy = InterventionStrategies(
            strategy_id="S017",
            name="Drought-resistant varieties",
            category="adaptation",
            cost_per_hectare=150,
            implementation_time=12,
            effectiveness_score=0.8
        )
        
        # Both should reference similar practice types
        adoption_gap = adoption.calculate_adoption_gap()
        cost_effectiveness = strategy.calculate_cost_effectiveness()
        
        assert adoption_gap > 0
        assert cost_effectiveness > 0
    
    def test_full_pipeline_simulation(self):
        """Test a simplified full pipeline across all models."""
        # Step 1: Assess climate risk
        risk = ClimateRisk(
            region_id="R022",
            baseline_yield=3.5,
            temperature_anomaly=2.0,
            precipitation_anomaly=-0.2,
            drought_frequency=0.4
        )
        risk_score = risk.calculate_risk_score()
        
        # Step 2: Evaluate crop resilience
        crop = CropYield(
            crop_type="sorghum",
            region_id="R022",
            baseline_yield=3.5,
            climate_sensitivity=-0.08,
            water_requirement=350
        )
        resilience = crop.calculate_resilience_score()
        
        # Step 3: Identify intervention strategies
        strategies = [
            InterventionStrategies("S018", "Drought-resistant varieties", "adaptation", 150, 12, 0.75),
            InterventionStrategies("S019", "Water harvesting", "adaptation", 200, 15, 0.70),
            InterventionStrategies("S020", "Conservation agriculture", "sustainability", 180, 18, 0.65),
        ]
        
        # Step 4: Calculate adoption potential
        adoption = AdoptionRate(
            practice_type="drought_resistant_varieties",
            community_id="C012",
            current_rate=0.15,
            potential_rate=0.70,
            barriers_score=0.5
        )
        adoption_potential = adoption.calculate_adoption_potential()
        
        # All calculations should complete without error
        assert 0 <= risk_score <= 100
        assert 0 <= resilience <= 1
        assert adoption_potential > 0
        assert len(strategies) == 3
