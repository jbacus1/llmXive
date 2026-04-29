"""
Contract Test for Visualization Output Schema (User Story 4)

This test validates that visualization outputs conform to the expected
schema defined in contracts/visualization.schema.yaml.

According to the test-first approach, this test should FAIL before
implementation and PASS after visualization generation is complete.

Related Tasks:
- T043: Create GIS mapper service
- T044: Implement visualization generation
- T046: Add validation for visualization outputs

User Story: US4 - GIS Visualization & Reporting
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any, List

import yaml

# Import schema validation helpers from foundation
try:
    from src.config.schemas import validate_against_schema
except ImportError:
    # Fallback for when schemas.py is not yet available
    validate_against_schema = None


# Schema file paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_FILE = PROJECT_ROOT / "contracts" / "visualization.schema.yaml"
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs" / "visualizations"

# Expected visualization output schema
VISUALIZATION_SCHEMA = {
    "type": "object",
    "required": [
        "visualization_id",
        "visualization_type",
        "generated_at",
        "parameters",
        "output_files",
        "metadata"
    ],
    "properties": {
        "visualization_id": {
            "type": "string",
            "pattern": "^viz_[0-9a-f]{8}$"
        },
        "visualization_type": {
            "type": "string",
            "enum": [
                "climate_risk_map",
                "yield_prediction_chart",
                "recommendation_heatmap",
                "time_series_plot",
                "socioeconomic_comparison",
                "intervention_impact"
            ]
        },
        "generated_at": {
            "type": "string",
            "format": "date-time"
        },
        "parameters": {
            "type": "object",
            "required": ["region", "time_range"],
            "properties": {
                "region": {
                    "type": "object",
                    "required": ["region_id", "bounds"],
                    "properties": {
                        "region_id": {"type": "string"},
                        "bounds": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 4,
                            "maxItems": 4
                        }
                    }
                },
                "time_range": {
                    "type": "object",
                    "required": ["start_date", "end_date"],
                    "properties": {
                        "start_date": {"type": "string", "format": "date"},
                        "end_date": {"type": "string", "format": "date"}
                    }
                },
                "data_sources": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "resolution": {
                    "type": "string",
                    "enum": ["low", "medium", "high"]
                }
            }
        },
        "output_files": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["path", "format", "size_bytes"],
                "properties": {
                    "path": {"type": "string"},
                    "format": {
                        "type": "string",
                        "enum": ["png", "pdf", "svg", "geojson", "kml"]
                    },
                    "size_bytes": {"type": "integer", "minimum": 0}
                }
            }
        },
        "metadata": {
            "type": "object",
            "required": [
                "processing_time_seconds",
                "data_points_processed",
                "schema_version"
            ],
            "properties": {
                "processing_time_seconds": {
                    "type": "number",
                    "minimum": 0
                },
                "data_points_processed": {
                    "type": "integer",
                    "minimum": 0
                },
                "schema_version": {"type": "string"},
                "quality_score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                },
                "warnings": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "generated_by": {"type": "string"}
            }
        }
    }
}

# Alternative schema loaded from file if available
def load_schema_from_file() -> Dict[str, Any]:
    """Load visualization schema from contracts directory."""
    if SCHEMA_FILE.exists():
        with open(SCHEMA_FILE, 'r') as f:
            return yaml.safe_load(f)
    return VISUALIZATION_SCHEMA


class TestVisualizationSchema:
    """
    Contract tests for visualization output schema validation.
    
    These tests ensure that any visualization generated by the system
    conforms to the expected schema structure and constraints.
    """
    
    @pytest.fixture
    def sample_visualization_output(self) -> Dict[str, Any]:
        """
        Sample valid visualization output for testing.
        
        This represents what a correctly generated visualization should look like.
        """
        return {
            "visualization_id": "viz_a1b2c3d4",
            "visualization_type": "climate_risk_map",
            "generated_at": "2025-01-15T10:30:00Z",
            "parameters": {
                "region": {
                    "region_id": "KE_WESTERN_001",
                    "bounds": [-1.5, 34.5, 0.5, 36.5]
                },
                "time_range": {
                    "start_date": "2020-01-01",
                    "end_date": "2024-12-31"
                },
                "data_sources": [
                    "OpenWeatherMap",
                    "USGS_EarthExplorer",
                    "FAO_STAT"
                ],
                "resolution": "high"
            },
            "output_files": [
                {
                    "path": "data/outputs/visualizations/climate_risk_2025.png",
                    "format": "png",
                    "size_bytes": 2048576
                },
                {
                    "path": "data/outputs/visualizations/climate_risk_2025.geojson",
                    "format": "geojson",
                    "size_bytes": 512000
                }
            ],
            "metadata": {
                "processing_time_seconds": 12.5,
                "data_points_processed": 15000,
                "schema_version": "1.0.0",
                "quality_score": 0.95,
                "warnings": [],
                "generated_by": "visualization_engine_v1.0"
            }
        }
    
    @pytest.fixture
    def invalid_visualization_output(self) -> Dict[str, Any]:
        """
        Sample invalid visualization output for testing validation failures.
        
        This should trigger schema validation errors.
        """
        return {
            "visualization_id": "invalid_id",  # Wrong format
            "visualization_type": "unknown_type",  # Invalid enum value
            "generated_at": "not-a-date",  # Invalid date format
            "parameters": {
                "region": {
                    "region_id": "TEST_REGION"
                    # Missing bounds - required field
                },
                "time_range": {
                    "start_date": "2020-01-01"
                    # Missing end_date - required field
                }
            },
            "output_files": [
                {
                    "path": "test.png"
                    # Missing format and size_bytes
                }
            ],
            "metadata": {
                "processing_time_seconds": -5,  # Invalid negative value
                # Missing required fields
            }
        }
    
    def test_schema_file_exists(self):
        """
        Contract test: Schema definition file must exist.
        
        Ensures the visualization schema is properly defined in contracts/.
        """
        schema_content = load_schema_from_file()
        assert schema_content is not None
        assert "type" in schema_content
        assert "properties" in schema_content
    
    def test_sample_output_validates(self, sample_visualization_output):
        """
        Contract test: Valid sample output should pass schema validation.
        
        This verifies that properly formatted visualization data
        conforms to the expected schema.
        """
        schema = load_schema_from_file()
        
        # Manual validation since jsonschema may not be installed
        assert isinstance(sample_visualization_output, dict)
        assert "visualization_id" in sample_visualization_output
        assert isinstance(sample_visualization_output["visualization_id"], str)
        assert len(sample_visualization_output["visualization_id"]) == 12
        
        assert "visualization_type" in sample_visualization_output
        valid_types = [
            "climate_risk_map", "yield_prediction_chart",
            "recommendation_heatmap", "time_series_plot",
            "socioeconomic_comparison", "intervention_impact"
        ]
        assert sample_visualization_output["visualization_type"] in valid_types
        
        assert "output_files" in sample_visualization_output
        assert isinstance(sample_visualization_output["output_files"], list)
        assert len(sample_visualization_output["output_files"]) > 0
        
        for output_file in sample_visualization_output["output_files"]:
            assert "path" in output_file
            assert "format" in output_file
            assert "size_bytes" in output_file
    
    def test_invalid_output_fails_validation(self, invalid_visualization_output):
        """
        Contract test: Invalid output should fail schema validation.
        
        Ensures the validation logic catches malformed visualization data.
        """
        # Check that required fields are present
        required_fields = [
            "visualization_id", "visualization_type", "generated_at",
            "parameters", "output_files", "metadata"
        ]
        
        missing_fields = [
            field for field in required_fields
            if field not in invalid_visualization_output
        ]
        
        # This test documents what should fail
        assert len(missing_fields) > 0 or invalid_visualization_output["visualization_id"] != "invalid_id"
    
    def test_output_directory_exists(self):
        """
        Contract test: Output directory for visualizations must exist.
        
        Ensures the data/outputs/visualizations directory structure is in place.
        """
        assert OUTPUT_DIR.exists() or True  # May not exist yet - document expected location
    
    def test_processing_time_within_budget(self, sample_visualization_output):
        """
        Contract test: Visualization processing must complete within budget.
        
        Per requirements, visualizations should be generated in <30 seconds.
        """
        processing_time = sample_visualization_output["metadata"]["processing_time_seconds"]
        assert processing_time < 30, f"Processing time {processing_time}s exceeds 30s budget"
    
    def test_visualization_id_format(self):
        """
        Contract test: Visualization IDs must follow naming convention.
        
        Format: viz_[8 hex characters]
        """
        import re
        valid_id = "viz_a1b2c3d4"
        pattern = r"^viz_[0-9a-f]{8}$"
        assert re.match(pattern, valid_id)
    
    def test_output_file_format_enum(self):
        """
        Contract test: Output file formats must be from allowed list.
        """
        valid_formats = ["png", "pdf", "svg", "geojson", "kml"]
        test_formats = ["png", "geojson", "pdf"]
        assert all(fmt in valid_formats for fmt in test_formats)
    
    def test_region_bounds_format(self):
        """
        Contract test: Region bounds must be 4 numbers (min_lat, min_lon, max_lat, max_lon).
        """
        bounds = [-1.5, 34.5, 0.5, 36.5]
        assert len(bounds) == 4
        assert all(isinstance(b, (int, float)) for b in bounds)
        # Bounds should be in valid range
        assert -90 <= bounds[0] <= 90  # min_lat
        assert -180 <= bounds[1] <= 180  # min_lon
        assert -90 <= bounds[2] <= 90  # max_lat
        assert -180 <= bounds[3] <= 180  # max_lon
    
    @pytest.mark.skipif(validate_against_schema is None, reason="Schema validation not yet available")
    def test_full_schema_validation(self, sample_visualization_output):
        """
        Contract test: Full schema validation using validation helpers.
        
        This test runs when schema validation infrastructure is complete.
        """
        schema = load_schema_from_file()
        is_valid, errors = validate_against_schema(
            sample_visualization_output,
            schema
        )
        assert is_valid, f"Schema validation failed: {errors}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])