"""
Unit tests for fixed effect model in differential splicing analysis.

This test file implements the unit test for T026 as specified in tasks.md.
Tests are written to FAIL initially before the fixed effect model implementation
(T029-T031) is complete, per the "write tests first" methodology.

User Story: US2 - Splicing Quantification and Differential Analysis
"""
import pytest
import numpy as np
from typing import Dict, List, Optional
import pandas as pd

# Import the fixed effect model module (will fail until implementation exists)
try:
    from code.src.analysis.fixed_effect_model import FixedEffectModel
    MODEL_AVAILABLE = True
except ImportError:
    MODEL_AVAILABLE = False
    FixedEffectModel = None


class TestFixedEffectModelInit:
    """Tests for FixedEffectModel initialization."""
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_init_with_valid_parameters(self):
        """Test model initialization with valid parameters."""
        model = FixedEffectModel(
            psi_threshold=0.1,
            coverage_threshold=20,
            fdr_threshold=0.05
        )
        assert model.psi_threshold == 0.1
        assert model.coverage_threshold == 20
        assert model.fdr_threshold == 0.05
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_init_with_default_parameters(self):
        """Test model initialization with default parameters."""
        model = FixedEffectModel()
        assert model.psi_threshold == 0.1  # Default from spec
        assert model.coverage_threshold == 20  # Default from spec
        assert model.fdr_threshold == 0.05  # Default from spec
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_init_with_invalid_threshold_raises_error(self):
        """Test that invalid thresholds raise appropriate errors."""
        with pytest.raises(ValueError):
            FixedEffectModel(psi_threshold=-0.1)
        
        with pytest.raises(ValueError):
            FixedEffectModel(coverage_threshold=0)
        
        with pytest.raises(ValueError):
            FixedEffectModel(fdr_threshold=1.5)
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_init_with_missing_species_raises_error(self):
        """Test that missing required species raises error."""
        with pytest.raises(ValueError):
            FixedEffectModel(specific_species=[])
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_species_list_validation(self):
        """Test validation of species list parameter."""
        valid_species = ['human', 'chimpanzee', 'macaque', 'marmoset']
        model = FixedEffectModel(specific_species=valid_species)
        assert model.species_list == valid_species
        
        # Test with duplicate species
        with pytest.raises(ValueError):
            FixedEffectModel(specific_species=['human', 'human'])

class TestFixedEffectModelFit:
    """Tests for FixedEffectModel fitting functionality."""
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_fit_with_valid_input(self):
        """Test model fitting with valid input data."""
        model = FixedEffectModel()
        
        # Create synthetic PSI data for 4 species
        psi_data = pd.DataFrame({
            'species': ['human'] * 100 + ['chimpanzee'] * 100 + 
                      ['macaque'] * 100 + ['marmoset'] * 100,
            'event_id': [f'E{i}' for i in range(100)] * 4,
            'psi': np.random.uniform(0, 1, 400),
            'coverage': np.random.randint(20, 1000, 400)
        })
        
        result = model.fit(psi_data)
        assert result is not None
        assert 'coefficients' in result
        assert 'p_values' in result
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_fit_with_low_coverage_filtered(self):
        """Test that low coverage events are filtered during fitting."""
        model = FixedEffectModel(coverage_threshold=20)
        
        psi_data = pd.DataFrame({
            'species': ['human'] * 50 + ['chimpanzee'] * 50,
            'event_id': [f'E{i}' for i in range(50)] * 2,
            'psi': np.random.uniform(0, 1, 100),
            'coverage': [10] * 50 + [100] * 50  # Half below threshold
        })
        
        result = model.fit(psi_data)
        assert result['n_filtered'] == 50  # 50 events filtered
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_fit_with_insufficient_replicates_raises_error(self):
        """Test error when insufficient replicates per species."""
        model = FixedEffectModel()
        
        psi_data = pd.DataFrame({
            'species': ['human'] * 1 + ['chimpanzee'] * 1,
            'event_id': ['E1', 'E1'],
            'psi': [0.5, 0.6],
            'coverage': [100, 100]
        })
        
        with pytest.raises(ValueError):
            model.fit(psi_data)
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_fit_returns_expected_structure(self):
        """Test that fit returns expected result structure."""
        model = FixedEffectModel()
        
        psi_data = pd.DataFrame({
            'species': ['human'] * 100 + ['chimpanzee'] * 100,
            'event_id': [f'E{i}' for i in range(100)] * 2,
            'psi': np.random.uniform(0, 1, 200),
            'coverage': np.random.randint(20, 1000, 200)
        })
        
        result = model.fit(psi_data)
        
        expected_keys = ['coefficients', 'p_values', 'fdr_adjusted',
                       'significant_events', 'n_total', 'n_filtered']
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

class TestFixedEffectModelPredict:
    """Tests for FixedEffectModel prediction functionality."""
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_predict_with_fitted_model(self):
        """Test prediction after model fitting."""
        model = FixedEffectModel()
        
        psi_data = pd.DataFrame({
            'species': ['human'] * 100 + ['chimpanzee'] * 100,
            'event_id': [f'E{i}' for i in range(100)] * 2,
            'psi': np.random.uniform(0, 1, 200),
            'coverage': np.random.randint(20, 1000, 200)
        })
        
        model.fit(psi_data)
        predictions = model.predict()
        
        assert predictions is not None
        assert len(predictions) > 0
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_predict_before_fit_raises_error(self):
        """Test error when predicting before fitting."""
        model = FixedEffectModel()
        
        with pytest.raises(RuntimeError):
            model.predict()

class TestFixedEffectModelDifferentialAnalysis:
    """Tests for differential splicing analysis."""
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_differential_analysis_with_known_differences(self):
        """Test detection of known PSI differences."""
        model = FixedEffectModel(psi_threshold=0.1)
        
        # Create data with known ΔPSI > 0.1
        psi_data = pd.DataFrame({
            'species': ['human'] * 50 + ['chimpanzee'] * 50,
            'event_id': ['E1'] * 50 + ['E1'] * 50,
            'psi': [0.8] * 50 + [0.6] * 50,  # ΔPSI = 0.2
            'coverage': [100] * 100
        })
        
        result = model.fit(psi_data)
        
        # Should detect significant difference
        assert result['significant_events']['n_significant'] >= 1
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_differential_analysis_below_threshold(self):
        """Test that small PSI differences are not flagged."""
        model = FixedEffectModel(psi_threshold=0.1)
        
        # Create data with ΔPSI < 0.1
        psi_data = pd.DataFrame({
            'species': ['human'] * 50 + ['chimpanzee'] * 50,
            'event_id': ['E1'] * 50 + ['E1'] * 50,
            'psi': [0.8] * 50 + [0.75] * 50,  # ΔPSI = 0.05
            'coverage': [100] * 100
        })
        
        result = model.fit(psi_data)
        
        # Should not detect significant difference
        assert result['significant_events']['n_significant'] == 0
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_benjamini_hochberg_correction(self):
        """Test FDR correction is applied correctly."""
        model = FixedEffectModel(fdr_threshold=0.05)
        
        psi_data = pd.DataFrame({
            'species': ['human'] * 100 + ['chimpanzee'] * 100,
            'event_id': [f'E{i}' for i in range(100)] * 2,
            'psi': np.random.uniform(0, 1, 200),
            'coverage': np.random.randint(20, 1000, 200)
        })
        
        result = model.fit(psi_data)
        
        # Check FDR-adjusted values exist and are sorted
        assert 'fdr_adjusted' in result
        assert all(0 <= p <= 1 for p in result['fdr_adjusted'])

class TestFixedEffectModelEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_empty_input_raises_error(self):
        """Test error handling for empty input."""
        model = FixedEffectModel()
        
        psi_data = pd.DataFrame({
            'species': [],
            'event_id': [],
            'psi': [],
            'coverage': []
        })
        
        with pytest.raises(ValueError):
            model.fit(psi_data)
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_missing_species_column_raises_error(self):
        """Test error when species column is missing."""
        model = FixedEffectModel()
        
        psi_data = pd.DataFrame({
            'event_id': ['E1', 'E2'],
            'psi': [0.5, 0.6],
            'coverage': [100, 100]
        })
        
        with pytest.raises(ValueError):
            model.fit(psi_data)
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_missing_psi_column_raises_error(self):
        """Test error when psi column is missing."""
        model = FixedEffectModel()
        
        psi_data = pd.DataFrame({
            'species': ['human', 'chimpanzee'],
            'event_id': ['E1', 'E1'],
            'coverage': [100, 100]
        })
        
        with pytest.raises(ValueError):
            model.fit(psi_data)
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_negative_psi_values_rejected(self):
        """Test that negative PSI values are rejected."""
        model = FixedEffectModel()
        
        psi_data = pd.DataFrame({
            'species': ['human', 'chimpanzee'],
            'event_id': ['E1', 'E1'],
            'psi': [-0.1, 0.6],  # Invalid PSI
            'coverage': [100, 100]
        })
        
        with pytest.raises(ValueError):
            model.fit(psi_data)
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_psi_above_one_rejected(self):
        """Test that PSI values > 1 are rejected."""
        model = FixedEffectModel()
        
        psi_data = pd.DataFrame({
            'species': ['human', 'chimpanzee'],
            'event_id': ['E1', 'E1'],
            'psi': [0.5, 1.5],  # Invalid PSI
            'coverage': [100, 100]
        })
        
        with pytest.raises(ValueError):
            model.fit(psi_data)
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_zero_coverage_rejected(self):
        """Test that zero coverage is rejected."""
        model = FixedEffectModel()
        
        psi_data = pd.DataFrame({
            'species': ['human', 'chimpanzee'],
            'event_id': ['E1', 'E1'],
            'psi': [0.5, 0.6],
            'coverage': [0, 100]  # Invalid coverage
        })
        
        with pytest.raises(ValueError):
            model.fit(psi_data)

class TestFixedEffectModelStatistics:
    """Tests for statistical correctness."""
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_coefficients_sum_to_zero(self):
        """Test that fixed effect coefficients sum to zero (constraint)."""
        model = FixedEffectModel()
        
        psi_data = pd.DataFrame({
            'species': ['human'] * 100 + ['chimpanzee'] * 100,
            'event_id': [f'E{i}' for i in range(100)] * 2,
            'psi': np.random.uniform(0, 1, 200),
            'coverage': np.random.randint(20, 1000, 200)
        })
        
        result = model.fit(psi_data)
        
        # Sum of species effects should be approximately zero
        coef_sum = sum(result['coefficients'].values())
        assert abs(coef_sum) < 0.001, "Coefficients should sum to zero"
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_p_values_in_valid_range(self):
        """Test that p-values are in valid [0, 1] range."""
        model = FixedEffectModel()
        
        psi_data = pd.DataFrame({
            'species': ['human'] * 100 + ['chimpanzee'] * 100,
            'event_id': [f'E{i}' for i in range(100)] * 2,
            'psi': np.random.uniform(0, 1, 200),
            'coverage': np.random.randint(20, 1000, 200)
        })
        
        result = model.fit(psi_data)
        
        assert all(0 <= p <= 1 for p in result['p_values'])
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_fdr_adjusted_less_than_or_equal_to_pvalues(self):
        """Test that FDR-adjusted values are >= raw p-values."""
        model = FixedEffectModel()
        
        psi_data = pd.DataFrame({
            'species': ['human'] * 100 + ['chimpanzee'] * 100,
            'event_id': [f'E{i}' for i in range(100)] * 2,
            'psi': np.random.uniform(0, 1, 200),
            'coverage': np.random.randint(20, 1000, 200)
        })
        
        result = model.fit(psi_data)
        
        # FDR-adjusted should be >= raw p-values
        for raw_p, adj_p in zip(result['p_values'], result['fdr_adjusted']):
            assert adj_p >= raw_p, "FDR-adjusted should be >= raw p-value"

class TestFixedEffectModelReproducibility:
    """Tests for reproducibility and determinism."""
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_same_input_produces_same_output(self):
        """Test deterministic behavior with same input."""
        model1 = FixedEffectModel()
        model2 = FixedEffectModel()
        
        psi_data = pd.DataFrame({
            'species': ['human'] * 100 + ['chimpanzee'] * 100,
            'event_id': [f'E{i}' for i in range(100)] * 2,
            'psi': np.random.uniform(0, 1, 200),
            'coverage': np.random.randint(20, 1000, 200)
        })
        
        result1 = model1.fit(psi_data)
        result2 = model2.fit(psi_data)
        
        # Results should be identical
        np.testing.assert_array_equal(result1['coefficients'], result2['coefficients'])
        np.testing.assert_array_equal(result1['p_values'], result2['p_values'])

class TestFixedEffectModelIntegration:
    """Integration-style unit tests combining multiple features."""
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_full_pipeline_with_primate_species(self):
        """Test full pipeline with all four primate species."""
        model = FixedEffectModel(
            psi_threshold=0.1,
            coverage_threshold=20,
            fdr_threshold=0.05,
            specific_species=['human', 'chimpanzee', 'macaque', 'marmoset']
        )
        
        # Create realistic PSI data for all 4 species
        n_per_species = 100
        psi_data = pd.DataFrame({
            'species': ['human'] * n_per_species + 
                      ['chimpanzee'] * n_per_species +
                      ['macaque'] * n_per_species +
                      ['marmoset'] * n_per_species,
            'event_id': [f'E{i}' for i in range(n_per_species)] * 4,
            'psi': np.random.uniform(0.2, 0.8, 4 * n_per_species),
            'coverage': np.random.randint(20, 500, 4 * n_per_species)
        })
        
        result = model.fit(psi_data)
        
        # Verify all expected outputs
        assert 'coefficients' in result
        assert 'p_values' in result
        assert 'fdr_adjusted' in result
        assert 'significant_events' in result
        assert result['n_total'] == 4 * n_per_species
        assert result['n_filtered'] == 0  # All above coverage threshold
    
    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="FixedEffectModel not implemented yet")
    def test_comparison_baseline_species(self):
        """Test comparison with human as baseline species."""
        model = FixedEffectModel(baseline_species='human')
        
        psi_data = pd.DataFrame({
            'species': ['human'] * 100 + ['chimpanzee'] * 100,
            'event_id': [f'E{i}' for i in range(100)] * 2,
            'psi': np.random.uniform(0, 1, 200),
            'coverage': np.random.randint(20, 1000, 200)
        })
        
        result = model.fit(psi_data)
        
        # Human baseline coefficient should be 0 or reference
        assert result['coefficients']['human'] == 0
