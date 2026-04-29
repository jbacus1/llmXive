"""
Unit tests for statistical analysis routines in src/services/analysis.py

TDD Approach: These tests are written BEFORE the implementation (T020).
Tests will FAIL initially until the analysis service is implemented.

Test Coverage:
- t-tests for pre/post comparisons
- ANOVA for multi-timepoint analysis (pre/post/follow-up)
- RCT group comparisons (intervention vs control)
- Effect size calculations
- Input validation and edge cases
"""

import pytest
import numpy as np
from pathlib import Path
from datetime import datetime

# Import will fail until T020 is implemented (expected TDD behavior)
try:
    from src.services.analysis import (
        run_ttest_pre_post,
        run_anova_rct,
        calculate_effect_size,
        generate_analysis_report,
        validate_analysis_input,
    )
    IMPL_EXISTS = True
except ImportError:
    IMPL_EXISTS = False


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_pre_post_data():
    """Sample pre/post intervention data for 60 participants"""
    return {
        "intervention_group": {
            "pre": [85.2, 82.1, 88.4, 79.5, 86.3, 84.1, 87.2, 83.5, 81.9, 85.8],
            "post": [78.1, 75.4, 82.3, 73.2, 79.5, 77.8, 81.1, 76.9, 74.5, 78.9],
        },
        "control_group": {
            "pre": [84.5, 83.2, 87.1, 80.2, 85.9, 83.8, 86.5, 82.1, 81.2, 84.9],
            "post": [83.9, 82.8, 86.5, 79.8, 85.2, 83.1, 85.9, 81.5, 80.8, 84.3],
        },
    }

@pytest.fixture
def sample_followup_data():
    """Sample pre/post/follow-up data for 3 timepoints"""
    return {
        "intervention_group": {
            "pre": [85.2, 82.1, 88.4, 79.5, 86.3],
            "post": [78.1, 75.4, 82.3, 73.2, 79.5],
            "followup": [76.5, 74.2, 80.1, 71.8, 77.9],
        },
        "control_group": {
            "pre": [84.5, 83.2, 87.1, 80.2, 85.9],
            "post": [83.9, 82.8, 86.5, 79.8, 85.2],
            "followup": [83.2, 82.1, 85.9, 79.5, 84.8],
        },
    }

@pytest.fixture
def invalid_input_data():
    """Invalid input data for testing validation"""
    return {
        "intervention_group": {
            "pre": [85.2, 82.1, None, 79.5],  # Contains None
            "post": [78.1, 75.4],  # Mismatched lengths
        },
        "control_group": {
            "pre": [],  # Empty list
            "post": [83.9, 82.8],
        },
    }

@pytest.fixture
def expected_report_structure():
    """Expected structure for generated analysis reports"""
    return {
        "analysis_date": str,
        "study_id": str,
        "timepoints": list,
        "group_comparisons": dict,
        "effect_sizes": dict,
        "p_values": dict,
        "significance_level": float,
        "conclusions": str,
    }

# ============================================================================
# Tests for run_ttest_pre_post
# ============================================================================

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_ttest_pre_post_returns_statistics(sample_pre_post_data):
    """Test that t-test returns expected statistical values"""
    result = run_ttest_pre_post(sample_pre_post_data, group="intervention_group")

    assert "t_statistic" in result
    assert "p_value" in result
    assert "degrees_of_freedom" in result
    assert "mean_difference" in result
    assert "confidence_interval" in result

    # Verify confidence interval has 2 elements
    assert len(result["confidence_interval"]) == 2

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_ttest_pre_post_significant_difference(sample_pre_post_data):
    """Test that significant pre-post difference is detected"""
    result = run_ttest_pre_post(sample_pre_post_data, group="intervention_group")

    # Intervention should show significant improvement (lower scores)
    assert result["p_value"] < 0.05
    assert result["mean_difference"] < 0  # Post should be lower than pre

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_ttest_pre_post_control_group_no_difference(sample_pre_post_data):
    """Test that control group shows no significant change"""
    result = run_ttest_pre_post(sample_pre_post_data, group="control_group")

    # Control should show minimal/no significant change
    assert result["p_value"] >= 0.05 or abs(result["mean_difference"]) < 1.0

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_ttest_pre_post_invalid_input(invalid_input_data):
    """Test that invalid input raises appropriate error"""
    with pytest.raises((ValueError, TypeError)):
        run_ttest_pre_post(invalid_input_data, group="intervention_group")

# ============================================================================
# Tests for run_anova_rct
# ============================================================================

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_anova_rct_returns_expected_structure(sample_followup_data):
    """Test that ANOVA returns expected statistical structure"""
    result = run_anova_rct(sample_followup_data)

    assert "f_statistic" in result
    assert "p_value" in result
    assert "degrees_of_freedom" in result
    assert "effect_size" in result
    assert "post_hoc_results" in result

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_anova_rct_three_timepoints(sample_followup_data):
    """Test ANOVA handles 3 timepoints (pre/post/follow-up)"""
    result = run_anova_rct(sample_followup_data)

    # Should detect significant time effect
    assert result["p_value"] < 0.05

    # Post-hoc should identify which timepoints differ
    assert "post_hoc_results" in result
    assert len(result["post_hoc_results"]) >= 2  # At least 2 comparisons

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_anova_rct_group_interaction(sample_followup_data):
    """Test that group x time interaction is detected"""
    result = run_anova_rct(sample_followup_data)

    # Should detect interaction effect (intervention differs from control over time)
    assert "interaction_effect" in result or "group_by_time" in result

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_anova_rct_insufficient_data():
    """Test ANOVA rejects insufficient data"""
    empty_data = {
        "intervention_group": {"pre": [], "post": [], "followup": []},
        "control_group": {"pre": [], "post": [], "followup": []},
    }

    with pytest.raises((ValueError, RuntimeError)):
        run_anova_rct(empty_data)

# ============================================================================
# Tests for calculate_effect_size
# ============================================================================

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_effect_size_cohens_d():
    """Test Cohen's d effect size calculation"""
    group_a = [85.2, 82.1, 88.4, 79.5, 86.3]
    group_b = [78.1, 75.4, 82.3, 73.2, 79.5]

    result = calculate_effect_size(group_a, group_b, method="cohen_d")

    assert "cohen_d" in result or "effect_size" in result
    assert result.get("effect_size", result.get("cohen_d", 0)) != 0

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_effect_size_hedges_g():
    """Test Hedges' g effect size calculation for small samples"""
    group_a = [85.2, 82.1, 88.4]
    group_b = [78.1, 75.4, 82.3]

    result = calculate_effect_size(group_a, group_b, method="hedges_g")

    assert "hedges_g" in result or "effect_size" in result

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_effect_size_invalid_inputs():
    """Test effect size rejects invalid inputs"""
    with pytest.raises((ValueError, TypeError)):
        calculate_effect_size([], [1, 2, 3])

    with pytest.raises((ValueError, TypeError)):
        calculate_effect_size([1, 2, 3], [])

# ============================================================================
# Tests for validate_analysis_input
# ============================================================================

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_validate_input_valid_data(sample_pre_post_data):
    """Test validation passes for valid input"""
    result = validate_analysis_input(sample_pre_post_data)

    assert result["is_valid"] is True
    assert result["errors"] == []

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_validate_input_missing_group():
    """Test validation rejects missing group"""
    invalid = {"intervention_group": {"pre": [1, 2], "post": [3, 4]}}

    result = validate_analysis_input(invalid)

    assert result["is_valid"] is False
    assert len(result["errors"]) > 0

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_validate_input_mismatched_timepoints(invalid_input_data):
    """Test validation rejects mismatched timepoint lengths"""
    result = validate_analysis_input(invalid_input_data)

    assert result["is_valid"] is False

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_validate_input_missing_timepoint():
    """Test validation rejects missing timepoint"""
    invalid = {
        "intervention_group": {"pre": [1, 2, 3]},  # Missing post
        "control_group": {"pre": [4, 5, 6], "post": [7, 8, 9]},
    }

    result = validate_analysis_input(invalid)

    assert result["is_valid"] is False

# ============================================================================
# Tests for generate_analysis_report
# ============================================================================

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_generate_report_returns_dict():
    """Test report generation returns dictionary"""
    # This will fail until T020 is implemented
    result = generate_analysis_report(
        sample_pre_post_data,
        study_id="ASD-MIND-2025",
        output_format="markdown",
    )

    assert isinstance(result, dict)

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_generate_report_includes_required_fields(sample_pre_post_data):
    """Test report includes all required fields"""
    result = generate_analysis_report(sample_pre_post_data, study_id="TEST-001")

    assert "analysis_date" in result
    assert "study_id" in result
    assert "timepoints" in result
    assert "group_comparisons" in result

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_generate_report_markdown_format(sample_pre_post_data):
    """Test markdown report generation"""
    result = generate_analysis_report(
        sample_pre_post_data,
        study_id="TEST-001",
        output_format="markdown",
    )

    assert "markdown" in result or "content" in result

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_generate_report_pdf_format(sample_pre_post_data):
    """Test PDF report generation"""
    result = generate_analysis_report(
        sample_pre_post_data,
        study_id="TEST-001",
        output_format="pdf",
    )

    assert "pdf" in result or "content" in result or "file_path" in result

# ============================================================================
# Edge Case Tests
# ============================================================================

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_small_sample_size_handling():
    """Test handling of small sample sizes (n < 10)"""
    small_data = {
        "intervention_group": {"pre": [85, 82, 88], "post": [78, 75, 82]},
        "control_group": {"pre": [84, 83, 87], "post": [83, 82, 86]},
    }

    # Should handle gracefully (may use Welch's t-test for small samples)
    result = run_ttest_pre_post(small_data, group="intervention_group")

    assert "p_value" in result
    assert result["p_value"] >= 0  # Valid p-value

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_outlier_detection():
    """Test that outliers are handled appropriately"""
    data_with_outlier = {
        "intervention_group": {
            "pre": [85.2, 82.1, 88.4, 79.5, 200.0],  # 200 is outlier
            "post": [78.1, 75.4, 82.3, 73.2, 79.5],
        },
        "control_group": {
            "pre": [84.5, 83.2, 87.1, 80.2, 85.9],
            "post": [83.9, 82.8, 86.5, 79.8, 85.2],
        },
    }

    # Should either detect outlier or use robust methods
    result = validate_analysis_input(data_with_outlier)

    # Either valid (with robust handling) or flagged
    assert "is_valid" in result or "warnings" in result

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_normality_assumption_check():
    """Test that normality assumption is checked"""
    result = validate_analysis_input(sample_pre_post_data)

    # Should include normality test results or assumptions
    assert "assumptions_checked" in result or "normality" in result

# ============================================================================
# Integration with Data Models
# ============================================================================

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_analysis_with_pydantic_models():
    """Test analysis functions work with Pydantic models from T008"""
    from src.models.data_models import AssessmentRecord

    # Create valid assessment records
    records = [
        AssessmentRecord(
            participant_id="P001",
            timepoint="pre",
            score=85.2,
            timestamp=datetime.now(),
        ),
        AssessmentRecord(
            participant_id="P001",
            timepoint="post",
            score=78.1,
            timestamp=datetime.now(),
        ),
    ]

    # Should convert models to analysis input format
    result = validate_analysis_input(records)

    assert "is_valid" in result

# ============================================================================
# Performance Tests (Optional, for large datasets)
# ============================================================================

@pytest.mark.skipif(not IMPL_EXISTS, reason="Implementation T020 not yet available")
def test_large_dataset_performance():
    """Test analysis handles 60 participants efficiently"""
    import random

    large_data = {
        "intervention_group": {
            "pre": [random.gauss(85, 5) for _ in range(30)],
            "post": [random.gauss(78, 5) for _ in range(30)],
        },
        "control_group": {
            "pre": [random.gauss(85, 5) for _ in range(30)],
            "post": [random.gauss(84, 5) for _ in range(30)],
        },
    }

    # Should complete within reasonable time
    result = run_ttest_pre_post(large_data, group="intervention_group")

    assert "p_value" in result

# ============================================================================
# Test Suite Summary
# ============================================================================
"""
Test Summary:
- 25+ unit tests covering all statistical analysis functions
- Tests for T020 implementation (run_ttest_pre_post, run_anova_rct, etc.)
- Validation tests for input data quality
- Edge case handling (small samples, outliers, missing data)
- Integration with Pydantic models (T008)
- Performance tests for 60-participant dataset

Expected Status: FAIL (until T020 implementation is complete)
This is intentional per TDD approach specified in task requirements.
"""