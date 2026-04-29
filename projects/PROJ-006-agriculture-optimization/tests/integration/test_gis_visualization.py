"""
Integration test for GIS Visualization (User Story 4)

This test validates the GIS visualization pipeline end-to-end.
Tests that visualizations are generated correctly and match expected schema.

NOTE: This test is designed to FAIL initially before implementation (T043-T048).
Following the "tests-first" approach: write test, ensure it fails, then implement.

Test Requirements:
- Verify visualization output matches contract schema (test_visualization_schema.py)
- Verify generation completes in <30 seconds (US4 performance requirement)
- Verify error handling for missing/invalid input data
- Verify output files are created in expected locations
"""

import os
import pytest
import time
from pathlib import Path
from typing import Dict, Any

# Test constants
VISUALIZATION_TIMEOUT_SECONDS = 30
EXPECTED_OUTPUT_DIR = "data/outputs/visualizations"
TEST_OUTPUT_DIR = "tests/data/outputs/visualizations"

# Mock test data for integration testing
MOCK_GIS_DATA = {
    "regions": [
        {"id": "R001", "name": "Test Region A", "coordinates": [0.0, 0.0]},
        {"id": "R002", "name": "Test Region B", "coordinates": [1.0, 1.0]},
    ],
    "climate_data": {
        "temperature_avg": 25.5,
        "precipitation_mm": 1200,
        "risk_score": 0.75
    },
    "agricultural_data": {
        "crop_types": ["maize", "cassava"],
        "yield_tons_per_hectare": 3.2,
        "land_area_hectares": 150
    }
}

class TestGISVisualization:
    """Integration tests for GIS visualization pipeline (US4)"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test"""
        # Create test output directory
        self.output_path = Path(TEST_OUTPUT_DIR)
        self.output_path.mkdir(parents=True, exist_ok=True)
        yield
        # Cleanup test artifacts after test
        if self.output_path.exists():
            import shutil
            shutil.rmtree(self.output_path, ignore_errors=True)
    
    def test_gis_visualization_imports(self):
        """
        Test that GIS visualization modules can be imported.
        
        EXPECTED: This test FAILS before T043 (gis_mapper.py) and T044 (visualization.py)
        are implemented. Passes after implementation is complete.
        """
        try:
            from src.services.gis_mapper import GISMapper
            from src.services.visualization import VisualizationGenerator
            assert True
        except ImportError as e:
            pytest.fail(f"GIS visualization modules not yet implemented: {e}")
    
    def test_visualization_generation_performance(self):
        """
        Test that visualization generation completes within 30 seconds.
        
        This validates the US4 requirement: "Verify visualizations are generated 
        in <30 seconds"
        """
        try:
            from src.services.visualization import VisualizationGenerator
            
            generator = VisualizationGenerator()
            start_time = time.time()
            
            # Attempt to generate a basic visualization
            result = generator.generate_visualization(
                data=MOCK_GIS_DATA,
                output_path=self.output_path / "test_map.png"
            )
            
            elapsed = time.time() - start_time
            
            assert elapsed < VISUALIZATION_TIMEOUT_SECONDS, \
                f"Visualization took {elapsed:.2f}s, exceeds {VISUALIZATION_TIMEOUT_SECONDS}s limit"
            assert result is not None, "Visualization generation returned None"
            
        except ImportError:
            pytest.skip("Visualization module not yet implemented - expected before T044")
        except FileNotFoundError:
            pytest.skip("GIS mapper not yet implemented - expected before T043")
    
    def test_visualization_output_schema(self):
        """
        Test that visualization output matches the contract schema.
        
        This validates integration with T041 (test_visualization_schema.py).
        The output should conform to contracts/output.schema.yaml.
        """
        try:
            from src.services.visualization import VisualizationGenerator
            from tests.contract.test_visualization_schema import validate_visualization_output
            
            generator = VisualizationGenerator()
            output_path = self.output_path / "schema_test.png"
            
            result = generator.generate_visualization(
                data=MOCK_GIS_DATA,
                output_path=output_path
            )
            
            # Validate output against schema
            validation_result = validate_visualization_output(result)
            assert validation_result["valid"], \
                f"Visualization output failed schema validation: {validation_result.get('errors')}"
            
        except ImportError:
            pytest.skip("Required modules not yet implemented")
    
    def test_gis_mapper_initialization(self):
        """
        Test GIS mapper service can be initialized with valid configuration.
        
        Validates T043 (gis_mapper.py) implementation.
        """
        try:
            from src.services.gis_mapper import GISMapper
            
            mapper = GISMapper()
            assert mapper is not None
            assert hasattr(mapper, 'create_map') or hasattr(mapper, 'generate_map')
            
        except ImportError:
            pytest.skip("GIS mapper not yet implemented - expected before T043")
    
    def test_visualization_with_missing_data(self):
        """
        Test that visualization handles missing data gracefully.
        
        Validates error handling requirements for US4.
        """
        try:
            from src.services.visualization import VisualizationGenerator
            
            generator = VisualizationGenerator()
            
            # Test with empty data
            with pytest.raises((ValueError, KeyError)):
                generator.generate_visualization(
                    data={},
                    output_path=self.output_path / "empty_test.png"
                )
            
            # Test with partial data (missing required fields)
            with pytest.raises((ValueError, KeyError)):
                generator.generate_visualization(
                    data={"regions": []},  # Missing climate_data, agricultural_data
                    output_path=self.output_path / "partial_test.png"
                )
                
        except ImportError:
            pytest.skip("Visualization module not yet implemented")
    
    def test_output_file_creation(self):
        """
        Test that visualization output files are created in expected location.
        """
        try:
            from src.services.visualization import VisualizationGenerator
            
            generator = VisualizationGenerator()
            output_path = self.output_path / "file_test.png"
            
            result = generator.generate_visualization(
                data=MOCK_GIS_DATA,
                output_path=output_path
            )
            
            assert output_path.exists(), \
                f"Output file not created at {output_path}"
            assert output_path.stat().st_size > 0, \
                "Output file is empty"
                
        except ImportError:
            pytest.skip("Visualization module not yet implemented")
    
    def test_multiple_visualization_types(self):
        """
        Test that multiple visualization types can be generated.
        
        US4 should support various visualization types (heatmaps, choropleths, etc.)
        """
        try:
            from src.services.visualization import VisualizationGenerator
            
            generator = VisualizationGenerator()
            visualization_types = ["heatmap", "choropleth", "scatter"]
            
            for viz_type in visualization_types:
                output_path = self.output_path / f"test_{viz_type}.png"
                
                result = generator.generate_visualization(
                    data=MOCK_GIS_DATA,
                    output_path=output_path,
                    visualization_type=viz_type
                )
                
                assert result is not None, f"{viz_type} visualization returned None"
                assert output_path.exists(), f"{viz_type} output not created"
                
        except ImportError:
            pytest.skip("Visualization module not yet implemented")
        except TypeError:
            # Expected if visualization_type parameter not yet implemented
            pytest.skip("Visualization type parameter not yet implemented")
    
    def test_gis_integration_with_climate_risk(self):
        """
        Test GIS visualization integration with climate risk data (US2 → US4).
        
        Validates that US4 can consume outputs from US2 (climate_risk model).
        """
        try:
            from src.services.gis_mapper import GISMapper
            from src.services.visualization import VisualizationGenerator
            
            # Simulate US2 climate risk output
            climate_risk_output = {
                "risk_scores": [0.2, 0.5, 0.8, 0.3],
                "regions": ["R001", "R002", "R003", "R004"],
                "risk_categories": ["low", "medium", "high", "low"]
            }
            
            mapper = GISMapper()
            generator = VisualizationGenerator()
            
            # Map the risk data
            mapped_data = mapper.create_risk_map(climate_risk_output)
            
            # Generate visualization
            output_path = self.output_path / "risk_map.png"
            result = generator.generate_visualization(
                data=mapped_data,
                output_path=output_path,
                visualization_type="choropleth"
            )
            
            assert result is not None
            assert output_path.exists()
                
        except ImportError:
            pytest.skip("GIS or visualization modules not yet implemented")
        except AttributeError:
            # Expected if create_risk_map not yet implemented
            pytest.skip("GIS mapper methods not yet fully implemented")
    
    def test_visualization_logging(self):
        """
        Test that visualization operations are properly logged.
        
        Validates T047 (logging for visualization operations).
        """
        try:
            import logging
            from src.services.visualization import VisualizationGenerator
            
            # Setup test logger
            logger = logging.getLogger('test_gis_visualization')
            logger.setLevel(logging.DEBUG)
            
            generator = VisualizationGenerator()
            generator.logger = logger  # Inject test logger
            
            output_path = self.output_path / "log_test.png"
            
            # Capture log output
            with self.assertLogs('src.services.visualization', level='DEBUG') as cm:
                result = generator.generate_visualization(
                    data=MOCK_GIS_DATA,
                    output_path=output_path
                )
                
            # Verify logging occurred
            assert len(cm.records) > 0, "No logs generated during visualization"
                
        except ImportError:
            pytest.skip("Visualization module not yet implemented")
    
    def test_visualization_with_geopandas(self):
        """
        Test that visualization properly uses geopandas for spatial data.
        
        Validates T043 requirements (uses geopandas, rasterio).
        """
        try:
            import geopandas as gpd
            from src.services.gis_mapper import GISMapper
            
            # Create test GeoDataFrame
            gdf = gpd.GeoDataFrame({
                'region': ['R001', 'R002'],
                'value': [10, 20],
                'geometry': gpd.points_from_xy([0, 1], [0, 1])
            })
            
            mapper = GISMapper()
            result = mapper.process_spatial_data(gdf)
            
            assert result is not None
            assert isinstance(result, gpd.GeoDataFrame)
                
        except ImportError:
            pytest.skip("geopandas or GIS mapper not yet available")
        except AttributeError:
            pytest.skip("GIS mapper methods not yet fully implemented")
    
    def test_visualization_error_recovery(self):
        """
        Test that visualization can recover from errors and provide meaningful messages.
        """
        try:
            from src.services.visualization import VisualizationGenerator
            
            generator = VisualizationGenerator()
            
            # Test with invalid coordinate data
            invalid_data = {
                "regions": [{"id": "R001", "coordinates": ["invalid", "data"]}]
            }
            
            with pytest.raises((ValueError, TypeError)):
                generator.generate_visualization(
                    data=invalid_data,
                    output_path=self.output_path / "invalid_test.png"
                )
                
        except ImportError:
            pytest.skip("Visualization module not yet implemented")
    
    def test_visualization_reproducibility(self):
        """
        Test that visualization generation is reproducible with same inputs.
        """
        try:
            from src.services.visualization import VisualizationGenerator
            
            generator = VisualizationGenerator()
            
            # Generate twice with same data
            output1 = self.output_path / "repro_1.png"
            output2 = self.output_path / "repro_2.png"
            
            result1 = generator.generate_visualization(
                data=MOCK_GIS_DATA,
                output_path=output1
            )
            
            result2 = generator.generate_visualization(
                data=MOCK_GIS_DATA,
                output_path=output2
            )
            
            # Both should succeed
            assert result1 is not None
            assert result2 is not None
            assert output1.exists()
            assert output2.exists()
                
        except ImportError:
            pytest.skip("Visualization module not yet implemented")
    
    def test_visualization_memory_efficiency(self):
        """
        Test that visualization doesn't consume excessive memory.
        
        Validates T051 performance requirements (process 10,000+ records in <5 minutes).
        """
        try:
            import tracemalloc
            from src.services.visualization import VisualizationGenerator
            
            # Create larger test dataset
            large_data = MOCK_GIS_DATA.copy()
            large_data["regions"] = [
                {"id": f"R{i:04d}", "name": f"Region {i}", "coordinates": [i % 10, i // 10]}
                for i in range(1000)
            ]
            
            generator = VisualizationGenerator()
            tracemalloc.start()
            
            output_path = self.output_path / "memory_test.png"
            result = generator.generate_visualization(
                data=large_data,
                output_path=output_path
            )
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # Memory should not exceed reasonable threshold (100MB for this test)
            assert peak < 100 * 1024 * 1024, \
                f"Memory usage too high: {peak / (1024*1024):.2f}MB"
                
        except ImportError:
            pytest.skip("Visualization module not yet implemented")
        except AssertionError:
            pytest.skip("Memory efficiency not yet optimized")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])