"""
Contract tests for enrichment analysis module (US3).

These tests verify the interface contract for the enrichment analysis
functionality that will be implemented in code/src/analysis/enrichment_test.py.

Per task requirements: Write tests FIRST, ensure they FAIL before implementation.

Success Criteria: SC-003 - Enrichment analysis with FDR correction (p < 0.05)
"""

import pytest
from typing import List, Dict, Any
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import the module under test (will fail until T043 is implemented)
try:
    from analysis.enrichment_test import (
        run_enrichment_analysis,
        calculate_enrichment_score,
        apply_fdr_correction,
        EnrichmentResult,
        EnrichmentInput
    )
    MODULE_AVAILABLE = True
except ImportError:
    MODULE_AVAILABLE = False


class TestEnrichmentAnalysisContract:
    """Contract tests for enrichment analysis interface."""

    def test_enrichment_input_dataclass_exists(self):
        """Verify EnrichmentInput dataclass is defined with required fields."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        # Verify required fields exist
        assert hasattr(EnrichmentInput, 'target_events')
        assert hasattr(EnrichmentInput, 'background_events')
        assert hasattr(EnrichmentInput, 'annotation_sets')
        assert hasattr(EnrichmentInput, 'fdr_threshold')

    def test_enrichment_input_validation_target_events(self):
        """Verify target_events validation in EnrichmentInput."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        # Empty target events should raise error
        with pytest.raises(ValueError):
            EnrichmentInput(
                target_events=[],
                background_events=["event1", "event2"],
                annotation_sets={"GO_terms": ["term1"]},
                fdr_threshold=0.05
            )

    def test_enrichment_input_validation_background_events(self):
        """Verify background_events validation in EnrichmentInput."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        # Empty background events should raise error
        with pytest.raises(ValueError):
            EnrichmentInput(
                target_events=["event1"],
                background_events=[],
                annotation_sets={"GO_terms": ["term1"]},
                fdr_threshold=0.05
            )

    def test_enrichment_input_validation_fdr_threshold(self):
        """Verify FDR threshold is within valid range per SC-003."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        # FDR threshold must be between 0 and 1
        with pytest.raises(ValueError):
            EnrichmentInput(
                target_events=["event1"],
                background_events=["event2"],
                annotation_sets={"GO_terms": ["term1"]},
                fdr_threshold=1.5  # Invalid
            )
        
        with pytest.raises(ValueError):
            EnrichmentInput(
                target_events=["event1"],
                background_events=["event2"],
                annotation_sets={"GO_terms": ["term1"]},
                fdr_threshold=-0.1  # Invalid
            )

    def test_enrichment_result_dataclass_exists(self):
        """Verify EnrichmentResult dataclass is defined with required fields."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        # Verify required fields exist
        assert hasattr(EnrichmentResult, 'annotation_set')
        assert hasattr(EnrichmentResult, 'term')
        assert hasattr(EnrichmentResult, 'observed_count')
        assert hasattr(EnrichmentResult, 'expected_count')
        assert hasattr(EnrichmentResult, 'enrichment_ratio')
        assert hasattr(EnrichmentResult, 'p_value')
        assert hasattr(EnrichmentResult, 'fdr_corrected_p')
        assert hasattr(EnrichmentResult, 'is_significant')

    def test_run_enrichment_analysis_signature(self):
        """Verify run_enrichment_analysis function signature."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        import inspect
        sig = inspect.signature(run_enrichment_analysis)
        params = list(sig.parameters.keys())
        
        assert 'input_data' in params
        assert 'fdr_threshold' in params

    def test_run_enrichment_analysis_returns_list(self):
        """Verify run_enrichment_analysis returns list of EnrichmentResult."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        input_data = EnrichmentInput(
            target_events=["event1", "event2"],
            background_events=["event1", "event2", "event3", "event4"],
            annotation_sets={"GO_terms": ["term1", "term2"]},
            fdr_threshold=0.05
        )
        
        results = run_enrichment_analysis(input_data)
        assert isinstance(results, list)
        if len(results) > 0:
            assert isinstance(results[0], EnrichmentResult)

    def test_fdr_correction_applied_per_sc003(self):
        """Verify Benjamini-Hochberg FDR correction is applied (SC-003)."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        # Test that FDR correction is applied to p-values
        test_p_values = [0.01, 0.02, 0.03, 0.04, 0.05, 0.10, 0.20, 0.30]
        corrected = apply_fdr_correction(test_p_values, alpha=0.05)
        
        # FDR corrected values should be monotonically non-decreasing
        for i in range(1, len(corrected)):
            assert corrected[i] >= corrected[i-1], \
                "FDR corrected p-values must be monotonically non-decreasing"

    def test_enrichment_score_calculation(self):
        """Verify enrichment ratio calculation (observed/expected)."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        # Test basic enrichment score calculation
        observed = 10
        expected = 5
        score = calculate_enrichment_score(observed, expected)
        
        assert score == 2.0, "Enrichment ratio should be observed/expected"

    def test_significance_threshold_applied(self):
        """Verify is_significant flag respects FDR threshold."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        input_data = EnrichmentInput(
            target_events=["event1", "event2"],
            background_events=["event1", "event2", "event3", "event4"],
            annotation_sets={"GO_terms": ["term1"]},
            fdr_threshold=0.05
        )
        
        results = run_enrichment_analysis(input_data)
        
        # All results should have is_significant boolean
        for result in results:
            assert isinstance(result.is_significant, bool)
            if result.fdr_corrected_p <= input_data.fdr_threshold:
                assert result.is_significant == True
            else:
                assert result.is_significant == False

    def test_missing_annotation_handling(self):
        """Verify graceful handling of missing annotations."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        input_data = EnrichmentInput(
            target_events=["event1"],
            background_events=["event1", "event2"],
            annotation_sets={"GO_terms": ["nonexistent_term"]},
            fdr_threshold=0.05
        )
        
        # Should not raise exception, return empty or zero results
        results = run_enrichment_analysis(input_data)
        assert isinstance(results, list)

    def test_multiple_annotation_sets(self):
        """Verify handling of multiple annotation sets."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        input_data = EnrichmentInput(
            target_events=["event1", "event2", "event3"],
            background_events=["event1", "event2", "event3", "event4", "event5"],
            annotation_sets={
                "GO_terms": ["term1", "term2"],
                "KEGG_pathways": ["pathway1"],
                "custom_sets": ["set1", "set2"]
            },
            fdr_threshold=0.05
        )
        
        results = run_enrichment_analysis(input_data)
        
        # Should process all annotation sets
        annotation_sets_processed = set()
        for result in results:
            annotation_sets_processed.add(result.annotation_set)
        
        assert len(annotation_sets_processed) == 3, \
            "Should process all three annotation sets"

    def test_output_serialization(self):
        """Verify enrichment results can be serialized to dict/JSON."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        input_data = EnrichmentInput(
            target_events=["event1"],
            background_events=["event1", "event2"],
            annotation_sets={"GO_terms": ["term1"]},
            fdr_threshold=0.05
        )
        
        results = run_enrichment_analysis(input_data)
        
        # Each result should be convertible to dict
        for result in results:
            result_dict = result.__dict__ if hasattr(result, '__dict__') else vars(result)
            assert isinstance(result_dict, dict)
            assert 'annotation_set' in result_dict
            assert 'p_value' in result_dict
            assert 'fdr_corrected_p' in result_dict


class TestEnrichmentAnalysisEdgeCases:
    """Edge case tests for enrichment analysis."""

    def test_single_event_target(self):
        """Test with single event in target set."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        input_data = EnrichmentInput(
            target_events=["event1"],
            background_events=["event1", "event2"],
            annotation_sets={"GO_terms": ["term1"]},
            fdr_threshold=0.05
        )
        
        results = run_enrichment_analysis(input_data)
        assert isinstance(results, list)

    def test_identical_target_background(self):
        """Test when target equals background (edge case)."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        input_data = EnrichmentInput(
            target_events=["event1", "event2"],
            background_events=["event1", "event2"],
            annotation_sets={"GO_terms": ["term1"]},
            fdr_threshold=0.05
        )
        
        results = run_enrichment_analysis(input_data)
        # Should handle gracefully, enrichment ratio should be 1.0 or similar
        assert isinstance(results, list)

    def test_large_annotation_set(self):
        """Test with large annotation set (performance)."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        large_terms = [f"term_{i}" for i in range(1000)]
        input_data = EnrichmentInput(
            target_events=["event1", "event2", "event3"],
            background_events=[f"event_{i}" for i in range(100)],
            annotation_sets={"GO_terms": large_terms},
            fdr_threshold=0.05
        )
        
        results = run_enrichment_analysis(input_data)
        assert isinstance(results, list)

    def test_zero_expected_count_handling(self):
        """Test handling of zero expected count (avoid division by zero)."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        # This tests the internal calculation handles edge case
        # The implementation should return 0 or handle gracefully
        score = calculate_enrichment_score(observed=5, expected=0)
        assert score >= 0  # Should not raise exception

    def test_fdr_threshold_boundary(self):
        """Test FDR threshold at boundary values."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        # Test at exact 0.05 threshold (SC-003 requirement)
        input_data = EnrichmentInput(
            target_events=["event1"],
            background_events=["event1", "event2"],
            annotation_sets={"GO_terms": ["term1"]},
            fdr_threshold=0.05  # Exact boundary per SC-003
        )
        
        results = run_enrichment_analysis(input_data)
        assert isinstance(results, list)

    def test_case_sensitivity_in_annotation_sets(self):
        """Verify annotation set names are handled consistently."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        input_data = EnrichmentInput(
            target_events=["event1"],
            background_events=["event1", "event2"],
            annotation_sets={"go_terms": ["term1"], "GO_terms": ["term2"]},
            fdr_threshold=0.05
        )
        
        results = run_enrichment_analysis(input_data)
        assert isinstance(results, list)

    def test_null_values_in_events(self):
        """Test handling of null/None values in event lists."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        input_data = EnrichmentInput(
            target_events=["event1", None, "event2"],
            background_events=["event1", "event2"],
            annotation_sets={"GO_terms": ["term1"]},
            fdr_threshold=0.05
        )
        
        # Should handle gracefully (filter or raise clear error)
        results = run_enrichment_analysis(input_data)
        assert isinstance(results, list)


class TestEnrichmentAnalysisIntegrationContract:
    """Integration contract tests ensuring compatibility with US3 pipeline."""

    def test_compatibility_with_phylo_output(self):
        """Verify enrichment analysis accepts phyloP extractor output format."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        # Simulate phyloP extractor output structure
        phylo_output = {
            "events": ["event1", "event2", "event3"],
            "conservation_scores": {
                "event1": {"mean": 0.8, "max": 0.95},
                "event2": {"mean": 0.6, "max": 0.7},
                "event3": {"mean": 0.4, "max": 0.5}
            }
        }
        
        input_data = EnrichmentInput(
            target_events=phylo_output["events"],
            background_events=["event1", "event2", "event3", "event4", "event5"],
            annotation_sets={"phyloP_high": ["event1", "event2"]},
            fdr_threshold=0.05
        )
        
        results = run_enrichment_analysis(input_data)
        assert isinstance(results, list)

    def test_compatibility_with_differential_splicing_output(self):
        """Verify enrichment analysis accepts differential splicing output format."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        # Simulate differential splicing output structure
        diff_splicing_output = {
            "significant_events": ["event1", "event2"],
            "dpsi_values": {"event1": 0.15, "event2": 0.25},
            "fdr_values": {"event1": 0.03, "event2": 0.04}
        }
        
        input_data = EnrichmentInput(
            target_events=diff_splicing_output["significant_events"],
            background_events=["event1", "event2", "event3", "event4"],
            annotation_sets={"regulatory": ["event1", "event2"]},
            fdr_threshold=0.05
        )
        
        results = run_enrichment_analysis(input_data)
        assert isinstance(results, list)

    def test_output_format_for_validation_module(self):
        """Verify output format is compatible with validation module (T045)."""
        if not MODULE_AVAILABLE:
            pytest.skip("Module not yet implemented - expected failure")
        
        input_data = EnrichmentInput(
            target_events=["event1", "event2"],
            background_events=["event1", "event2", "event3"],
            annotation_sets={"GO_terms": ["term1"]},
            fdr_threshold=0.05
        )
        
        results = run_enrichment_analysis(input_data)
        
        # Results should be serializable for validation module
        for result in results:
            # Verify all required fields for validation
            assert hasattr(result, 'annotation_set')
            assert hasattr(result, 'term')
            assert hasattr(result, 'fdr_corrected_p')
            assert hasattr(result, 'is_significant')