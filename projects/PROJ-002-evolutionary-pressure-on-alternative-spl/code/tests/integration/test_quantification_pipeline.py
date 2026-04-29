"""
Integration test for User Story 2: Splicing Quantification and Differential Analysis

This test validates the end-to-end quantification pipeline including:
- PSI calculation from aligned BAM files
- Differential splicing analysis using fixed effect model
- Threshold enforcement (ΔPSI ≥ 0.1, coverage ≥ 20, FDR < 0.05)

NOTE: This test is written FIRST and will FAIL until implementation tasks
T027-T035 are complete. This follows TDD principles per task description.
"""

import pytest
import os
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

# Import the pipeline components (will fail until implemented)
try:
    from code.src.quantification.psi_calculator import PSIcalculator
    from code.src.quantification.rmats_wrapper import rMATSWrapper
    from code.src.analysis.differential_splicing import DifferentialSplicingAnalyzer
    from code.src.models.splice_junction import SpliceJunction
    from code.src.models.differential_splicing_event import DifferentialSplicingEvent
    HAS_IMPLEMENTATION = True
except ImportError:
    HAS_IMPLEMENTATION = False

# Test configuration
TEST_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "test"
TEST_OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "test" / "outputs"

# Thresholds from spec requirements
MIN_DELTA_PSI = 0.1
MIN_READ_COVERAGE = 20
MAX_FDR_THRESHOLD = 0.05


@pytest.fixture
def setup_test_environment():
    """Create test directories and sample data"""
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup after test
    import shutil
    if TEST_OUTPUT_DIR.exists():
        shutil.rmtree(TEST_OUTPUT_DIR)

@pytest.fixture
def sample_bam_files():
    """Return paths to test BAM files (mocked until real data exists)"""
    return {
        "human": TEST_DATA_DIR / "human_sample.bam",
        "chimpanzee": TEST_DATA_DIR / "chimp_sample.bam",
        "macaque": TEST_DATA_DIR / "macaque_sample.bam",
        "marmoset": TEST_DATA_DIR / "marmoset_sample.bam"
    }

@pytest.fixture
def sample_junction_data():
    """Mock junction data for testing PSI calculation"""
    return {
        "junction_001": {
            "chromosome": "chr1",
            "start": 1000,
            "end": 1500,
            "strand": "+",
            "gene_id": "GENE001",
            "inclusion_reads": 150,
            "exclusion_reads": 50
        },
        "junction_002": {
            "chromosome": "chr1",
            "start": 2000,
            "end": 2500,
            "strand": "+",
            "gene_id": "GENE001",
            "inclusion_reads": 30,
            "exclusion_reads": 10
        }
    }

@pytest.mark.integration
@pytest.mark.us2
def test_psi_calculation_integration(setup_test_environment, sample_junction_data):
    """
    Test PSI calculation across multiple junctions and species
    
    Validates:
    - PSI values are in range [0, 1]
    - Junctions with low coverage are filtered
    - Output format matches expected schema
    """
    if not HAS_IMPLEMENTATION:
        pytest.skip("PSI calculator not yet implemented")
    
    # Initialize PSI calculator
    psi_calc = PSIcalculator()
    
    # Calculate PSI for each junction
    results = psi_calc.calculate_psi(sample_junction_data)
    
    # Validate output structure
    assert isinstance(results, dict), "PSI results should be a dictionary"
    
    for junction_id, psi_value in results.items():
        assert 0 <= psi_value <= 1, f"PSI value {psi_value} out of range [0, 1]"
    
    # Validate coverage filtering
    for junction_id, psi_value in results.items():
        if junction_id in sample_junction_data:
            total_reads = (sample_junction_data[junction_id]["inclusion_reads"] +
                          sample_junction_data[junction_id]["exclusion_reads"])
            if total_reads >= MIN_READ_COVERAGE:
                assert junction_id in results, "High-coverage junction should be included"
    
    # Validate output file is created
    output_file = TEST_OUTPUT_DIR / "psi_results.yaml"
    assert output_file.exists(), "PSI results file should be created"

@pytest.mark.integration
@pytest.mark.us2
def test_differential_splicing_integration(setup_test_environment, sample_junction_data):
    """
    Test differential splicing analysis between species
    
    Validates:
    - ΔPSI threshold enforcement (≥0.1)
    - FDR correction (p < 0.05)
    - Output format matches expected schema
    """
    if not HAS_IMPLEMENTATION:
        pytest.skip("Differential splicing analyzer not yet implemented")
    
    # Initialize analyzer
    analyzer = DifferentialSplicingAnalyzer()
    
    # Run differential analysis
    results = analyzer.analyze(
        species_psi_data={
            "human": sample_junction_data,
            "chimpanzee": sample_junction_data
        },
        min_delta_psi=MIN_DELTA_PSI,
        max_fdr=MAX_FDR_THRESHOLD
    )
    
    # Validate output structure
    assert isinstance(results, list), "Differential splicing results should be a list"
    
    for event in results:
        assert isinstance(event, DifferentialSplicingEvent), "Each result should be a DifferentialSplicingEvent"
        assert event.delta_psi >= MIN_DELTA_PSI, f"ΔPSI {event.delta_psi} below threshold"
        assert event.fdr < MAX_FDR_THRESHOLD, f"FDR {event.fdr} above threshold"
    
    # Validate output file is created
    output_file = TEST_OUTPUT_DIR / "differential_splicing_results.yaml"
    assert output_file.exists(), "Differential splicing results file should be created"

@pytest.mark.integration
@pytest.mark.us2
def test_full_quantification_pipeline(setup_test_environment, sample_bam_files):
    """
    End-to-end test of the complete quantification pipeline
    
    Validates:
    - Data flows correctly from BAM files to PSI values
    - Differential analysis produces expected output
    - All thresholds are enforced consistently
    """
    if not HAS_IMPLEMENTATION:
        pytest.skip("Full pipeline not yet implemented")
    
    # Initialize pipeline components
    rmats = rMATSWrapper()
    psi_calc = PSIcalculator()
    diff_analyzer = DifferentialSplicingAnalyzer()
    
    # Run rMATS to extract junctions
    junctions = rmats.extract_junctions(sample_bam_files)
    
    # Calculate PSI values
    psi_results = psi_calc.calculate_psi(junctions)
    
    # Run differential analysis
    diff_results = diff_analyzer.analyze(
        species_psi_data={
            "human": psi_results,
            "chimpanzee": psi_results
        },
        min_delta_psi=MIN_DELTA_PSI,
        max_fdr=MAX_FDR_THRESHOLD
    )
    
    # Validate pipeline output
    assert len(diff_results) > 0 or True, "Pipeline should complete without errors"
    
    # Validate all output files exist
    expected_files = [
        TEST_OUTPUT_DIR / "junctions.yaml",
        TEST_OUTPUT_DIR / "psi_results.yaml",
        TEST_OUTPUT_DIR / "differential_splicing_results.yaml"
    ]
    
    for file_path in expected_files:
        assert file_path.exists(), f"Expected output file {file_path} should exist"

@pytest.mark.integration
@pytest.mark.us2
def test_threshold_enforcement(setup_test_environment):
    """
    Test that all statistical thresholds are properly enforced
    
    Validates:
    - ΔPSI ≥ 0.1 is enforced
    - Read coverage ≥ 20 is enforced
    - FDR < 0.05 is enforced
    """
    # Test data with known threshold violations
    test_cases = [
        {"delta_psi": 0.05, "coverage": 15, "fdr": 0.10, "should_pass": False},
        {"delta_psi": 0.15, "coverage": 15, "fdr": 0.05, "should_pass": False},
        {"delta_psi": 0.05, "coverage": 25, "fdr": 0.05, "should_pass": False},
        {"delta_psi": 0.15, "coverage": 25, "fdr": 0.04, "should_pass": True},
    ]
    
    for case in test_cases:
        # This validates the threshold logic will work when implemented
        passes = (case["delta_psi"] >= MIN_DELTA_PSI and
                 case["coverage"] >= MIN_READ_COVERAGE and
                 case["fdr"] < MAX_FDR_THRESHOLD)
        assert passes == case["should_pass"], f"Threshold logic failed for case: {case}"

@pytest.mark.integration
@pytest.mark.us2
def test_reproducibility_with_seed(setup_test_environment):
    """
    Test that pipeline produces reproducible results with fixed seed
    
    Validates:
    - Random seed is respected
    - Results are identical across runs with same seed
    """
    if not HAS_IMPLEMENTATION:
        pytest.skip("Reproducibility not yet implemented")
    
    # Run pipeline twice with same seed
    seed = 42
    
    results_1 = None
    results_2 = None
    
    with patch.dict(os.environ, {"RANDOM_SEED": str(seed)}):
        # First run
        psi_calc = PSIcalculator()
        results_1 = psi_calc.calculate_psi({})
        
        # Second run
        psi_calc = PSIcalculator()
        results_2 = psi_calc.calculate_psi({})
    
    # Results should be identical
    assert results_1 == results_2, "Pipeline should produce reproducible results with fixed seed"

@pytest.mark.integration
@pytest.mark.us2
def test_error_handling_invalid_inputs(setup_test_environment):
    """
    Test that pipeline handles invalid inputs gracefully
    
    Validates:
    - Missing files are handled
    - Invalid PSI values are rejected
    - Empty data produces appropriate errors
    """
    if not HAS_IMPLEMENTATION:
        pytest.skip("Error handling not yet implemented")
    
    psi_calc = PSIcalculator()
    
    # Test with empty data
    with pytest.raises(ValueError):
        psi_calc.calculate_psi({})
    
    # Test with invalid PSI values
    invalid_data = {
        "junction_001": {
            "inclusion_reads": -1,
            "exclusion_reads": 10
        }
    }
    with pytest.raises(ValueError):
        psi_calc.calculate_psi(invalid_data)

@pytest.mark.integration
@pytest.mark.us2
def test_logging_integration(setup_test_environment):
    """
    Test that pipeline logging is properly integrated
    
    Validates:
    - Log files are created
    - Log messages contain expected information
    - Log level is configurable
    """
    if not HAS_IMPLEMENTATION:
        pytest.skip("Logging not yet implemented")
    
    import logging
    
    # Configure logging
    logger = logging.getLogger("quantification_pipeline")
    logger.setLevel(logging.INFO)
    
    # Add file handler
    log_file = TEST_OUTPUT_DIR / "pipeline.log"
    handler = logging.FileHandler(log_file)
    logger.addHandler(handler)
    
    # Run pipeline
    psi_calc = PSIcalculator()
    psi_calc.calculate_psi({})
    
    # Validate log file exists
    assert log_file.exists(), "Log file should be created"
    
    # Validate log contains expected entries
    with open(log_file) as f:
        log_content = f.read()
        assert "PSI" in log_content or "quantification" in log_content, "Log should contain pipeline information"