"""
Contract tests for differential splicing analysis module.

These tests verify the interface contract for the differential splicing
analysis functionality BEFORE implementation (T031).

Following TDD principles, these tests should FAIL initially and PASS
after implementation is complete.

Test Scope:
- API interface contract verification
- Input/output format validation
- Statistical threshold enforcement (ΔPSI ≥ 0.1, coverage ≥ 20, FDR < 0.05)
- Benjamini-Hochberg FDR correction contract
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional

# Import paths - will fail until implementation exists
# This is intentional for contract testing
try:
    from code.src.analysis.differential_splicing import (
        DifferentialSplicingAnalyzer,
        DifferentialSplicingResult,
        SplicingEvent,
        apply_fdr_correction,
        calculate_delta_psi,
        filter_by_coverage,
        filter_by_psi_threshold,
    )
    IMPLEMENTATION_EXISTS = True
except ImportError:
    IMPLEMENTATION_EXISTS = False

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_psi_data():
    """Sample PSI values for two groups (baseline vs condition)."""
    return {
        "human": {
            "event_id": "E001",
            "junction_id": "J001",
            "inclusion_reads": [150, 160, 145, 155, 148],
            "exclusion_reads": [50, 55, 48, 52, 50],
            "group": "baseline"
        },
        "chimpanzee": {
            "event_id": "E001",
            "junction_id": "J001",
            "inclusion_reads": [200, 210, 195, 205, 198],
            "exclusion_reads": [30, 35, 28, 32, 30],
            "group": "condition"
        }
    }

@pytest.fixture
def sample_splicing_events():
    """Sample splicing events with PSI values."""
    return [
        SplicingEvent(
            event_id="E001",
            event_type="SE",
            junction_id="J001",
            psi_baseline=0.75,
            psi_condition=0.85,
            coverage_baseline=200,
            coverage_condition=230
        ),
        SplicingEvent(
            event_id="E002",
            event_type="SE",
            junction_id="J002",
            psi_baseline=0.40,
            psi_condition=0.45,
            coverage_baseline=180,
            coverage_condition=190
        ),
        SplicingEvent(
            event_id="E003",
            event_type="RI",
            junction_id="J003",
            psi_baseline=0.10,
            psi_condition=0.25,
            coverage_baseline=250,
            coverage_condition=260
        ),
        SplicingEvent(
            event_id="E004",
            event_type="SE",
            junction_id="J004",
            psi_baseline=0.60,
            psi_condition=0.62,
            coverage_baseline=15,
            coverage_condition=18
        ),
    ]

@pytest.fixture
def sample_p_values():
    """Sample p-values for FDR correction."""
    return [0.001, 0.005, 0.01, 0.03, 0.05, 0.1, 0.2, 0.5]

# ============================================================================
# CONTRACT: Class Interface
# ============================================================================

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_analyzer_class_exists():
    """Contract: DifferentialSplicingAnalyzer class must exist."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    assert hasattr(DifferentialSplicingAnalyzer, "__init__")
    assert hasattr(DifferentialSplicingAnalyzer, "analyze")
    assert hasattr(DifferentialSplicingAnalyzer, "filter_results")

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_analyzer_initialization():
    """Contract: Analyzer must accept configuration parameters."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    # Should accept delta_psi_threshold and min_coverage
    analyzer = DifferentialSplicingAnalyzer(
        delta_psi_threshold=0.1,
        min_coverage=20,
        fdr_threshold=0.05
    )
    
    assert analyzer.delta_psi_threshold == 0.1
    assert analyzer.min_coverage == 20
    assert analyzer.fdr_threshold == 0.05

# ============================================================================
# CONTRACT: Result Data Structure
# ============================================================================

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_result_dataclass_structure():
    """Contract: DifferentialSplicingResult must have required fields."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    # Verify the result structure has all required fields
    required_fields = [
        "event_id",
        "event_type",
        "junction_id",
        "psi_baseline",
        "psi_condition",
        "delta_psi",
        "p_value",
        "fdr_corrected_p",
        "coverage_baseline",
        "coverage_condition",
        "significant"
    ]
    
    # Create a sample result
    result = DifferentialSplicingResult(
        event_id="E001",
        event_type="SE",
        junction_id="J001",
        psi_baseline=0.75,
        psi_condition=0.85,
        delta_psi=0.10,
        p_value=0.03,
        fdr_corrected_p=0.04,
        coverage_baseline=200,
        coverage_condition=230,
        significant=True
    )
    
    for field in required_fields:
        assert hasattr(result, field), f"Missing required field: {field}"

# ============================================================================
# CONTRACT: Delta PSI Calculation
# ============================================================================

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_delta_psi_calculation():
    """Contract: Delta PSI must be calculated as psi_condition - psi_baseline."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    # Test positive delta
    delta = calculate_delta_psi(0.85, 0.75)
    assert delta == 0.10
    
    # Test negative delta
    delta = calculate_delta_psi(0.60, 0.75)
    assert delta == -0.15
    
    # Test zero delta
    delta = calculate_delta_psi(0.50, 0.50)
    assert delta == 0.0

# ============================================================================
# CONTRACT: Coverage Filtering (SC-002: ≥20 reads per junction)
# ============================================================================

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_coverage_filter_enforcement():
    """Contract: Events with coverage < 20 must be filtered out."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    events = sample_splicing_events
    filtered = filter_by_coverage(events, min_coverage=20)
    
    # E004 has coverage 15 and 18, should be filtered
    event_ids = [e.event_id for e in filtered]
    assert "E004" not in event_ids
    assert "E001" in event_ids
    assert "E002" in event_ids
    assert "E003" in event_ids

# ============================================================================
# CONTRACT: PSI Threshold Filtering (SC-002: ΔPSI ≥ 0.1)
# ============================================================================

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_psi_threshold_filter_enforcement():
    """Contract: Events with |ΔPSI| < 0.1 must be filtered out."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    events = sample_splicing_events
    filtered = filter_by_psi_threshold(events, delta_psi_threshold=0.1)
    
    event_ids = [e.event_id for e in filtered]
    
    # E002 has ΔPSI = 0.05, should be filtered
    assert "E002" not in event_ids
    # E001 has ΔPSI = 0.10, should pass (boundary case)
    assert "E001" in event_ids
    # E003 has ΔPSI = 0.15, should pass
    assert "E003" in event_ids

# ============================================================================
# CONTRACT: FDR Correction (SC-003: Benjamini-Hochberg, p < 0.05)
# ============================================================================

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_fdr_correction_algorithm():
    """Contract: Benjamini-Hochberg FDR correction must be applied correctly."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    p_values = sample_p_values
    corrected = apply_fdr_correction(p_values)
    
    # FDR corrected values should be >= original p-values
    for i, (orig, corr) in enumerate(zip(p_values, corrected)):
        assert corr >= orig, f"FDR corrected {corr} < original {orig}"
    
    # First value should remain unchanged (rank 1)
    assert corrected[0] == p_values[0]
    
    # Length should be preserved
    assert len(corrected) == len(p_values)

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_fdr_threshold_application():
    """Contract: Results must be marked significant if FDR < 0.05."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    p_values = sample_p_values
    corrected = apply_fdr_correction(p_values)
    
    # Count significant results at FDR < 0.05
    significant_count = sum(1 for p in corrected if p < 0.05)
    
    # At least first few should be significant
    assert significant_count >= 1

# ============================================================================
# CONTRACT: End-to-End Analysis Pipeline
# ============================================================================

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_analyze_method_returns_results():
    """Contract: analyze() must return list of DifferentialSplicingResult."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    analyzer = DifferentialSplicingAnalyzer(
        delta_psi_threshold=0.1,
        min_coverage=20,
        fdr_threshold=0.05
    )
    
    # Should return a list
    results = analyzer.analyze(sample_splicing_events)
    
    assert isinstance(results, list)
    if len(results) > 0:
        assert isinstance(results[0], DifferentialSplicingResult)

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_analyze_applies_all_filters():
    """Contract: analyze() must apply coverage, PSI, and FDR filters."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    analyzer = DifferentialSplicingAnalyzer(
        delta_psi_threshold=0.1,
        min_coverage=20,
        fdr_threshold=0.05
    )
    
    results = analyzer.analyze(sample_splicing_events)
    
    # All results should pass coverage filter
    for result in results:
        assert result.coverage_baseline >= 20
        assert result.coverage_condition >= 20
    
    # All results should pass PSI threshold
    for result in results:
        assert abs(result.delta_psi) >= 0.1

# ============================================================================
# CONTRACT: Input Validation
# ============================================================================

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_empty_input_handling():
    """Contract: Empty input should return empty results, not raise."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    analyzer = DifferentialSplicingAnalyzer(
        delta_psi_threshold=0.1,
        min_coverage=20,
        fdr_threshold=0.05
    )
    
    results = analyzer.analyze([])
    assert results == []

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_invalid_psi_values_handling():
    """Contract: PSI values outside [0, 1] should raise ValueError."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    # This test validates input validation is in place
    with pytest.raises(ValueError):
        calculate_delta_psi(-0.1, 0.5)
    
    with pytest.raises(ValueError):
        calculate_delta_psi(0.5, 1.5)

# ============================================================================
# CONTRACT: Output Format for Downstream Consumption
# ============================================================================

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_result_to_dict_conversion():
    """Contract: Results must be convertible to dict for JSON/CSV export."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    result = DifferentialSplicingResult(
        event_id="E001",
        event_type="SE",
        junction_id="J001",
        psi_baseline=0.75,
        psi_condition=0.85,
        delta_psi=0.10,
        p_value=0.03,
        fdr_corrected_p=0.04,
        coverage_baseline=200,
        coverage_condition=230,
        significant=True
    )
    
    result_dict = result.to_dict()
    
    assert isinstance(result_dict, dict)
    assert result_dict["event_id"] == "E001"
    assert result_dict["delta_psi"] == 0.10
    assert result_dict["significant"] == True

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_results_to_dataframe_conversion():
    """Contract: Results must be convertible to pandas DataFrame."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    results = [
        DifferentialSplicingResult(
            event_id="E001",
            event_type="SE",
            junction_id="J001",
            psi_baseline=0.75,
            psi_condition=0.85,
            delta_psi=0.10,
            p_value=0.03,
            fdr_corrected_p=0.04,
            coverage_baseline=200,
            coverage_condition=230,
            significant=True
        ),
        DifferentialSplicingResult(
            event_id="E002",
            event_type="SE",
            junction_id="J002",
            psi_baseline=0.40,
            psi_condition=0.45,
            delta_psi=0.05,
            p_value=0.15,
            fdr_corrected_p=0.20,
            coverage_baseline=180,
            coverage_condition=190,
            significant=False
        )
    ]
    
    df = DifferentialSplicingResult.results_to_dataframe(results)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "event_id" in df.columns
    assert "delta_psi" in df.columns
    assert "significant" in df.columns

# ============================================================================
# CONTRACT: Logging Integration
# ============================================================================

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_logging_integration():
    """Contract: Analyzer must log analysis operations."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    # Verify logging is set up in the analyzer
    analyzer = DifferentialSplicingAnalyzer(
        delta_psi_threshold=0.1,
        min_coverage=20,
        fdr_threshold=0.05
    )
    
    # Should have a logger attribute
    assert hasattr(analyzer, "logger")

# ============================================================================
# CONTRACT: Reproducibility
# ============================================================================

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_reproducibility_seed_handling():
    """Contract: Analyzer must accept random seed for reproducibility."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    analyzer = DifferentialSplicingAnalyzer(
        delta_psi_threshold=0.1,
        min_coverage=20,
        fdr_threshold=0.05,
        random_seed=42
    )
    
    assert analyzer.random_seed == 42

# ============================================================================
# CONTRACT: Edge Cases
# ============================================================================

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_single_event_analysis():
    """Contract: Single event should be processed correctly."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    analyzer = DifferentialSplicingAnalyzer(
        delta_psi_threshold=0.1,
        min_coverage=20,
        fdr_threshold=0.05
    )
    
    single_event = [sample_splicing_events[0]]
    results = analyzer.analyze(single_event)
    
    assert len(results) == 1

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_all_events_filtered():
    """Contract: When all events fail filters, return empty list."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    # Create events that all fail coverage filter
    low_coverage_events = [
        SplicingEvent(
            event_id="E001",
            event_type="SE",
            junction_id="J001",
            psi_baseline=0.75,
            psi_condition=0.85,
            coverage_baseline=5,
            coverage_condition=8
        )
    ]
    
    analyzer = DifferentialSplicingAnalyzer(
        delta_psi_threshold=0.1,
        min_coverage=20,
        fdr_threshold=0.05
    )
    
    results = analyzer.analyze(low_coverage_events)
    assert results == []

# ============================================================================
# CONTRACT: Event Type Support
# ============================================================================

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_event_type_validation():
    """Contract: Supported event types must be validated."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    # Valid event types per rMATS
    valid_types = ["SE", "RI", "A5SS", "A3SS", "MXE"]
    
    for event_type in valid_types:
        event = SplicingEvent(
            event_id="E001",
            event_type=event_type,
            junction_id="J001",
            psi_baseline=0.5,
            psi_condition=0.6,
            coverage_baseline=100,
            coverage_condition=110
        )
        assert event.event_type == event_type

@pytest.mark.contract
@pytest.mark.differential_splicing
def test_unsupported_event_type_rejected():
    """Contract: Unsupported event types should be rejected."""
    if not IMPLEMENTATION_EXISTS:
        pytest.skip("Implementation not yet created - contract test placeholder")
    
    with pytest.raises(ValueError):
        SplicingEvent(
            event_id="E001",
            event_type="INVALID",
            junction_id="J001",
            psi_baseline=0.5,
            psi_condition=0.6,
            coverage_baseline=100,
            coverage_condition=110
        )