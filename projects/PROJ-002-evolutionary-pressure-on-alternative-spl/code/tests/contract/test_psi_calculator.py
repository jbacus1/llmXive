"""
Contract tests for PSI (Percent Spliced In) calculator.

These tests define the expected interface and behavior of the PSI calculator
module before implementation. Tests will FAIL until T030 is implemented.

Contract Requirements (from spec.md):
- PSI values must be between 0.0 and 1.0
- Input requires junction read counts for included and excluded isoforms
- Output includes PSI value, standard error, and confidence interval
- Minimum read coverage threshold: ≥20 reads per junction
"""
import pytest
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

# Expected interface - will fail until implementation exists
try:
    from quantification.psi_calculator import PSIResult, PSICalculator
    PSI_CALCULATOR_EXISTS = True
except ImportError:
    PSI_CALCULATOR_EXISTS = False


@dataclass
class MockJunctionCounts:
    """Mock junction counts for testing PSI calculation."""
    included_reads: int
    excluded_reads: int
    junction_id: str
    sample_id: str
    
    @property
    def total_reads(self) -> int:
        return self.included_reads + self.excluded_reads


class TestPSICalculatorContract:
    """Contract tests for PSI calculator interface and behavior."""
    
    @pytest.fixture
    def sample_junctions(self) -> List[MockJunctionCounts]:
        """Sample junction data for PSI calculation."""
        return [
            MockJunctionCounts(50, 30, "J001", "SAMPLE_001"),
            MockJunctionCounts(100, 20, "J002", "SAMPLE_001"),
            MockJunctionCounts(80, 40, "J003", "SAMPLE_001"),
        ]
    
    @pytest.fixture
    def low_coverage_junctions(self) -> List[MockJunctionCounts]:
        """Junctions with insufficient read coverage."""
        return [
            MockJunctionCounts(5, 3, "J004", "SAMPLE_001"),
            MockJunctionCounts(10, 2, "J005", "SAMPLE_001"),
        ]
    
    @pytest.fixture
    def edge_case_junctions(self) -> List[MockJunctionCounts]:
        """Edge cases for PSI calculation."""
        return [
            MockJunctionCounts(100, 0, "J006", "SAMPLE_001"),  # PSI = 1.0
            MockJunctionCounts(0, 100, "J007", "SAMPLE_001"),  # PSI = 0.0
            MockJunctionCounts(50, 50, "J008", "SAMPLE_001"),  # PSI = 0.5
        ]
    
    # =========================================================================
    # CONTRACT TEST: Interface Existence
    # =========================================================================
    
    def test_psi_calculator_class_exists(self):
        """Contract: PSICalculator class must exist in module."""
        assert PSI_CALCULATOR_EXISTS, \
            "PSICalculator class not found - implementation required in T030"
        
    def test_psi_result_dataclass_exists(self):
        """Contract: PSIResult dataclass must exist for return values."""
        assert PSI_CALCULATOR_EXISTS, \
            "PSIResult class not found - implementation required in T030"
    
    # =========================================================================
    # CONTRACT TEST: Basic Calculation Interface
    # =========================================================================
    
    @pytest.mark.skipif(not PSI_CALCULATOR_EXISTS, 
                       reason="PSI calculator not yet implemented")
    def test_calculate_psi_returns_valid_range(self, sample_junctions):
        """Contract: PSI values must be between 0.0 and 1.0 inclusive."""
        calculator = PSICalculator()
        results = calculator.calculate_psi(sample_junctions)
        
        assert len(results) == len(sample_junctions), \
            "Output count must match input count"
        
        for result in results:
            assert 0.0 <= result.psi <= 1.0, \
                f"PSI value {result.psi} outside valid range [0.0, 1.0]"
    
    @pytest.mark.skipif(not PSI_CALCULATOR_EXISTS,
                       reason="PSI calculator not yet implemented")
    def test_calculate_psi_with_min_coverage_threshold(self, low_coverage_junctions):
        """Contract: Junctions with <20 reads should be flagged or excluded."""
        calculator = PSICalculator()
        results = calculator.calculate_psi(
            low_coverage_junctions,
            min_coverage=20  # SC-002 requirement
        )
        
        # All low-coverage junctions should be marked as below threshold
        for result in results:
            assert result.meets_coverage_threshold is False, \
                f"Junction {result.junction_id} should fail coverage check"
    
    @pytest.mark.skipif(not PSI_CALCULATOR_EXISTS,
                       reason="PSI calculator not yet implemented")
    def test_calculate_psi_edge_cases(self, edge_case_junctions):
        """Contract: Edge cases must produce expected PSI values."""
        calculator = PSICalculator()
        results = calculator.calculate_psi(edge_case_junctions)
        
        psi_values = {r.junction_id: r.psi for r in results}
        
        assert abs(psi_values["J006"] - 1.0) < 0.01, \
            "All included reads should give PSI ≈ 1.0"
        assert abs(psi_values["J007"] - 0.0) < 0.01, \
            "All excluded reads should give PSI ≈ 0.0"
        assert abs(psi_values["J008"] - 0.5) < 0.01, \
            "Equal reads should give PSI ≈ 0.5"
    
    # =========================================================================
    # CONTRACT TEST: Output Structure
    # =========================================================================
    
    @pytest.mark.skipif(not PSI_CALCULATOR_EXISTS,
                       reason="PSI calculator not yet implemented")
    def test_psi_result_has_required_fields(self, sample_junctions):
        """Contract: PSIResult must have all required fields per spec."""
        calculator = PSICalculator()
        results = calculator.calculate_psi(sample_junctions)
        
        required_fields = [
            "junction_id",
            "sample_id",
            "psi",
            "standard_error",
            "confidence_interval",
            "meets_coverage_threshold",
            "included_reads",
            "excluded_reads"
        ]
        
        for result in results:
            for field in required_fields:
                assert hasattr(result, field), \
                    f"PSIResult missing required field: {field}"
    
    @pytest.mark.skipif(not PSI_CALCULATOR_EXISTS,
                       reason="PSI calculator not yet implemented")
    def test_psi_result_confidence_interval_format(self, sample_junctions):
        """Contract: Confidence interval must be a 2-tuple (lower, upper)."""
        calculator = PSICalculator()
        results = calculator.calculate_psi(sample_junctions)
        
        for result in results:
            ci = result.confidence_interval
            assert isinstance(ci, tuple) and len(ci) == 2, \
                "Confidence interval must be a 2-tuple"
            assert ci[0] <= ci[1], \
                "CI lower bound must be ≤ upper bound"
    
    # =========================================================================
    # CONTRACT TEST: Error Handling
    # =========================================================================
    
    @pytest.mark.skipif(not PSI_CALCULATOR_EXISTS,
                       reason="PSI calculator not yet implemented")
    def test_calculate_psi_empty_input(self):
        """Contract: Empty input should return empty output, not raise."""
        calculator = PSICalculator()
        results = calculator.calculate_psi([])
        
        assert results == [], "Empty input should return empty list"
    
    @pytest.mark.skipif(not PSI_CALCULATOR_EXISTS,
                       reason="PSI calculator not yet implemented")
    def test_calculate_psi_invalid_counts(self):
        """Contract: Negative read counts should raise ValueError."""
        from quantification.psi_calculator import InvalidJunctionDataError
        
        calculator = PSICalculator()
        invalid_junctions = [
            MockJunctionCounts(-10, 30, "BAD", "SAMPLE_001"),
        ]
        
        with pytest.raises((ValueError, InvalidJunctionDataError)):
            calculator.calculate_psi(invalid_junctions)
    
    # =========================================================================
    # CONTRACT TEST: Multi-Sample Support
    # =========================================================================
    
    @pytest.mark.skipif(not PSI_CALCULATOR_EXISTS,
                       reason="PSI calculator not yet implemented")
    def test_calculate_psi_multiple_samples(self):
        """Contract: Calculator must handle junctions from multiple samples."""
        junctions = [
            MockJunctionCounts(50, 30, "J001", "SAMPLE_A"),
            MockJunctionCounts(60, 40, "J001", "SAMPLE_B"),  # Same junction, diff sample
        ]
        
        calculator = PSICalculator()
        results = calculator.calculate_psi(junctions)
        
        assert len(results) == 2, "Must process all junctions"
        samples = {r.sample_id for r in results}
        assert "SAMPLE_A" in samples and "SAMPLE_B" in samples, \
            "Must preserve sample identity"
    
    # =========================================================================
    # CONTRACT TEST: Integration with Delta PSI Threshold
    # =========================================================================
    
    @pytest.mark.skipif(not PSI_CALCULATOR_EXISTS,
                       reason="PSI calculator not yet implemented")
    def test_psi_calculation_for_delta_psi_threshold(self):
        """Contract: PSI precision must support ΔPSI ≥ 0.1 threshold (SC-002)."""
        junctions = [
            MockJunctionCounts(100, 100, "J001", "SAMPLE_A"),  # PSI = 0.5
            MockJunctionCounts(120, 80, "J001", "SAMPLE_B"),  # PSI = 0.6
        ]
        
        calculator = PSICalculator()
        results = calculator.calculate_psi(junctions)
        
        psi_values = {r.sample_id: r.psi for r in results}
        delta_psi = abs(psi_values["SAMPLE_B"] - psi_values["SAMPLE_A"])
        
        assert delta_psi >= 0.1, \
            "PSI precision must support ΔPSI threshold of 0.1"
    
    # =========================================================================
    # CONTRACT TEST: Statistical Output
    # =========================================================================
    
    @pytest.mark.skipif(not PSI_CALCULATOR_EXISTS,
                       reason="PSI calculator not yet implemented")
    def test_psi_result_includes_standard_error(self, sample_junctions):
        """Contract: Standard error must be calculated for each PSI value."""
        calculator = PSICalculator()
        results = calculator.calculate_psi(sample_junctions)
        
        for result in results:
            assert result.standard_error >= 0, \
                "Standard error must be non-negative"
            # Standard error should decrease with more reads
            if result.total_reads > 100:
                assert result.standard_error < 0.1, \
                    "High read counts should yield low standard error"
    
    @pytest.mark.skipif(not PSI_CALCULATOR_EXISTS,
                       reason="PSI calculator not yet implemented")
    def test_psi_result_includes_coverage_metadata(self, sample_junctions):
        """Contract: Raw read counts must be preserved in output."""
        calculator = PSICalculator()
        results = calculator.calculate_psi(sample_junctions)
        
        for result in results:
            assert hasattr(result, 'included_reads'), \
                "Output must include included_reads"
            assert hasattr(result, 'excluded_reads'), \
                "Output must include excluded_reads"
            assert result.included_reads + result.excluded_reads == result.total_reads, \
                "Total reads must equal sum of included and excluded"