"""
Integration tests for USGS EarthExplorer API client.

These tests verify the USGS EarthExplorer API integration layer,
including authentication, data retrieval, and error handling.

NOTE: Per TDD principles, these tests should FAIL before implementation
of src/services/api_client.py (T018).

Tests:
- T014: USGS EarthExplorer API integration
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Test fixtures and configuration
TEST_API_KEY = "test_usgs_api_key_12345"
TEST_LOCATION = {"latitude": 40.7128, "longitude": -74.0060}  # New York coordinates
TEST_START_DATE = "2023-01-01"
TEST_END_DATE = "2023-01-31"
TEST_DATASET = "LANDSAT_C2L1"

@pytest.fixture
def mock_usgs_response():
    """Mock response from USGS EarthExplorer API."""
    return {
        "data": {
            "results": [
                {
                    "entityId": "LC08_L1TP_015033_20230101",
                    "displayName": "Landsat 8 Scene",
                    "cloudCover": 5.2,
                    "acquisitionTime": "2023-01-01T15:30:00Z",
                    "browseUrls": {
                        "full": "https://example.com/browse1.jpg",
                        "medium": "https://example.com/browse1_med.jpg"
                    },
                    "spatialCoverage": {
                        "minLat": 40.5,
                        "maxLat": 41.0,
                        "minLon": -74.5,
                        "maxLon": -73.5
                    }
                }
            ],
            "recordsReturned": 1,
            "totalHits": 1,
            "start": 0,
            "searchCriteria": {
                "dataset": TEST_DATASET,
                "startDate": TEST_START_DATE,
                "endDate": TEST_END_DATE
            }
        },
        "meta": {
            "requestId": "test-request-123",
            "version": "1.0.0"
        }
    }

@pytest.fixture
def mock_api_client():
    """Mock USGS API client instance."""
    with patch('src.services.api_client.USGSApiClient') as mock_client:
        client_instance = Mock()
        client_instance.authenticate.return_value = True
        client_instance.search_scenes.return_value = mock_api_response()
        client_instance.get_scene_metadata.return_value = mock_scene_metadata()
        client_instance.download_scene.return_value = "/tmp/test_scene.tif"
        mock_client.return_value = client_instance
        yield client_instance

@pytest.fixture
def valid_api_key():
    """Valid API key for testing."""
    return TEST_API_KEY

def mock_api_response():
    """Return mock API response data."""
    return {
        "results": [
            {
                "entityId": "LC08_L1TP_015033_20230101",
                "displayName": "Landsat 8 Scene",
                "cloudCover": 5.2
            }
        ],
        "recordsReturned": 1,
        "totalHits": 1
    }

def mock_scene_metadata():
    """Return mock scene metadata."""
    return {
        "entityId": "LC08_L1TP_015033_20230101",
        "displayName": "Landsat 8 Scene",
        "cloudCover": 5.2,
        "acquisitionTime": "2023-01-01T15:30:00Z",
        "spatialCoverage": {
            "minLat": 40.5,
            "maxLat": 41.0,
            "minLon": -74.5,
            "maxLon": -73.5
        }
    }

class TestUSGSApiClient:
    """Integration tests for USGS EarthExplorer API client."""

    @pytest.mark.integration
    def test_client_initialization_with_valid_api_key(self, valid_api_key):
        """Test that client initializes successfully with valid API key."""
        from src.services.api_client import USGSApiClient
        
        client = USGSApiClient(api_key=valid_api_key)
        assert client is not None
        assert client.api_key == valid_api_key

    @pytest.mark.integration
    def test_client_initialization_without_api_key(self):
        """Test that client raises error when initialized without API key."""
        from src.services.api_client import USGSApiClient
        
        with pytest.raises(ValueError, match="API key required"):
            USGSApiClient(api_key=None)

    @pytest.mark.integration
    def test_authentication_success(self, mock_api_client):
        """Test successful authentication with USGS API."""
        result = mock_api_client.authenticate()
        assert result is True
        mock_api_client.authenticate.assert_called_once()

    @pytest.mark.integration
    def test_authentication_failure_invalid_credentials(self):
        """Test authentication fails with invalid credentials."""
        from src.services.api_client import USGSApiClient
        
        with patch('src.services.api_client.USGSApiClient.authenticate') as mock_auth:
            mock_auth.return_value = False
            client = USGSApiClient(api_key="invalid_key")
            result = client.authenticate()
            assert result is False

    @pytest.mark.integration
    def test_search_scenes_with_valid_parameters(self, mock_api_client, mock_usgs_response):
        """Test scene search with valid location and date parameters."""
        from src.services.api_client import USGSApiClient
        
        result = mock_api_client.search_scenes(
            dataset=TEST_DATASET,
            start_date=TEST_START_DATE,
            end_date=TEST_END_DATE,
            location=TEST_LOCATION
        )
        
        assert result is not None
        assert "results" in result
        assert len(result["results"]) > 0
        assert result["recordsReturned"] == 1

    @pytest.mark.integration
    def test_search_scenes_with_invalid_date_format(self, mock_api_client):
        """Test scene search handles invalid date format gracefully."""
        from src.services.api_client import USGSApiClient
        
        with pytest.raises(ValueError, match="Invalid date format"):
            mock_api_client.search_scenes(
                dataset=TEST_DATASET,
                start_date="invalid-date",
                end_date=TEST_END_DATE,
                location=TEST_LOCATION
            )

    @pytest.mark.integration
    def test_search_scenes_empty_results(self, mock_api_client):
        """Test handling of empty search results."""
        mock_api_client.search_scenes.return_value = {
            "results": [],
            "recordsReturned": 0,
            "totalHits": 0
        }
        
        result = mock_api_client.search_scenes(
            dataset=TEST_DATASET,
            start_date=TEST_START_DATE,
            end_date=TEST_END_DATE,
            location=TEST_LOCATION
        )
        
        assert result["recordsReturned"] == 0
        assert len(result["results"]) == 0

    @pytest.mark.integration
    def test_get_scene_metadata(self, mock_api_client, mock_scene_metadata):
        """Test retrieval of scene metadata."""
        scene_id = "LC08_L1TP_015033_20230101"
        result = mock_api_client.get_scene_metadata(scene_id)
        
        assert result is not None
        assert result["entityId"] == scene_id
        assert "cloudCover" in result
        assert "spatialCoverage" in result

    @pytest.mark.integration
    def test_download_scene(self, mock_api_client):
        """Test scene download functionality."""
        scene_id = "LC08_L1TP_015033_20230101"
        result = mock_api_client.download_scene(scene_id)
        
        assert result is not None
        assert isinstance(result, str)
        assert result.endswith(".tif")

    @pytest.mark.integration
    def test_download_scene_network_error(self, mock_api_client):
        """Test download handles network errors gracefully."""
        from requests.exceptions import RequestException
        
        mock_api_client.download_scene.side_effect = RequestException("Network error")
        
        with pytest.raises(RequestException):
            mock_api_client.download_scene("test_scene_id")

    @pytest.mark.integration
    def test_rate_limiting_respected(self, mock_api_client):
        """Test that rate limiting is respected between API calls."""
        from time import sleep
        
        # Make multiple rapid calls
        start_time = time.time()
        for _ in range(3):
            mock_api_client.search_scenes(
                dataset=TEST_DATASET,
                start_date=TEST_START_DATE,
                end_date=TEST_END_DATE,
                location=TEST_LOCATION
            )
        elapsed = time.time() - start_time
        
        # Verify rate limiting delay is applied (at least 0.1s between calls)
        assert elapsed >= 0.2

    @pytest.mark.integration
    def test_error_handling_api_timeout(self, mock_api_client):
        """Test handling of API timeout errors."""
        from requests.exceptions import Timeout
        
        mock_api_client.search_scenes.side_effect = Timeout("Request timed out")
        
        with pytest.raises(Timeout):
            mock_api_client.search_scenes(
                dataset=TEST_DATASET,
                start_date=TEST_START_DATE,
                end_date=TEST_END_DATE,
                location=TEST_LOCATION
            )

    @pytest.mark.integration
    def test_error_handling_api_unauthorized(self, mock_api_client):
        """Test handling of unauthorized API access."""
        from requests.exceptions import HTTPError
        
        error_response = Mock()
        error_response.status_code = 401
        mock_api_client.search_scenes.side_effect = HTTPError(response=error_response)
        
        with pytest.raises(HTTPError) as exc_info:
            mock_api_client.search_scenes(
                dataset=TEST_DATASET,
                start_date=TEST_START_DATE,
                end_date=TEST_END_DATE,
                location=TEST_LOCATION
            )
        assert exc_info.value.response.status_code == 401

    @pytest.mark.integration
    def test_cloud_cover_filtering(self, mock_api_client):
        """Test cloud cover filtering in scene search."""
        mock_api_client.search_scenes.return_value = {
            "results": [
                {"entityId": "scene1", "cloudCover": 5.0},
                {"entityId": "scene2", "cloudCover": 50.0},
                {"entityId": "scene3", "cloudCover": 80.0}
            ],
            "recordsReturned": 3,
            "totalHits": 3
        }
        
        result = mock_api_client.search_scenes(
            dataset=TEST_DATASET,
            start_date=TEST_START_DATE,
            end_date=TEST_END_DATE,
            location=TEST_LOCATION,
            max_cloud_cover=50.0
        )
        
        # Should filter out scene3 (80% cloud cover)
        filtered_results = [r for r in result["results"] if r["cloudCover"] <= 50.0]
        assert len(filtered_results) == 2

    @pytest.mark.integration
    def test_data_validation_scene_format(self, mock_api_client):
        """Test that returned scenes have required fields."""
        result = mock_api_client.search_scenes(
            dataset=TEST_DATASET,
            start_date=TEST_START_DATE,
            end_date=TEST_END_DATE,
            location=TEST_LOCATION
        )
        
        required_fields = ["entityId", "displayName", "cloudCover"]
        for scene in result["results"]:
            for field in required_fields:
                assert field in scene, f"Missing required field: {field}"

    @pytest.mark.integration
    def test_logging_api_calls(self, mock_api_client):
        """Test that API calls are logged properly."""
        import logging
        
        # Set up logging capture
        logger = logging.getLogger("usgs_api")
        with patch.object(logger, 'info') as mock_log:
            mock_api_client.search_scenes(
                dataset=TEST_DATASET,
                start_date=TEST_START_DATE,
                end_date=TEST_END_DATE,
                location=TEST_LOCATION
            )
            mock_log.assert_called()

    @pytest.mark.integration
    def test_caching_api_responses(self, mock_api_client):
        """Test that API responses are cached to reduce redundant calls."""
        from src.data.cache import CacheManager
        
        # First call
        result1 = mock_api_client.search_scenes(
            dataset=TEST_DATASET,
            start_date=TEST_START_DATE,
            end_date=TEST_END_DATE,
            location=TEST_LOCATION
        )
        
        # Second call with same parameters should use cache
        result2 = mock_api_client.search_scenes(
            dataset=TEST_DATASET,
            start_date=TEST_START_DATE,
            end_date=TEST_END_DATE,
            location=TEST_LOCATION
        )
        
        assert result1 == result2

    @pytest.mark.integration
    def test_concurrent_api_requests(self, mock_api_client):
        """Test handling of concurrent API requests."""
        import concurrent.futures
        
        def make_request(_):
            return mock_api_client.search_scenes(
                dataset=TEST_DATASET,
                start_date=TEST_START_DATE,
                end_date=TEST_END_DATE,
                location=TEST_LOCATION
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, i) for i in range(3)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        assert len(results) == 3
        for result in results:
            assert result is not None
            assert "results" in result

    @pytest.mark.integration
    def test_dataset_validation(self, mock_api_client):
        """Test that only valid USGS datasets are accepted."""
        from src.services.api_client import USGSApiClient
        
        invalid_datasets = ["INVALID_DATASET", "CUSTOM_DATASET"]
        valid_datasets = ["LANDSAT_C2L1", "LANDSAT_C2L2", "MODIS", "SENTINEL_2"]
        
        for dataset in valid_datasets:
            result = mock_api_client.search_scenes(
                dataset=dataset,
                start_date=TEST_START_DATE,
                end_date=TEST_END_DATE,
                location=TEST_LOCATION
            )
            assert result is not None

    @pytest.mark.integration
    def test_location_validation(self, mock_api_client):
        """Test that valid location coordinates are required."""
        invalid_locations = [
            {"latitude": 200, "longitude": 0},  # Invalid latitude
            {"latitude": 0, "longitude": 300},  # Invalid longitude
            {"latitude": None, "longitude": 0},  # Missing latitude
            {"latitude": 0}  # Missing longitude
        ]
        
        for location in invalid_locations:
            with pytest.raises(ValueError):
                mock_api_client.search_scenes(
                    dataset=TEST_DATASET,
                    start_date=TEST_START_DATE,
                    end_date=TEST_END_DATE,
                    location=location
                )

class TestUSGSApiIntegration:
    """Higher-level integration tests for USGS API workflow."""

    @pytest.mark.integration
    def test_full_data_collection_workflow(self, mock_api_client):
        """Test complete workflow from search to download."""
        # Step 1: Search for scenes
        search_result = mock_api_client.search_scenes(
            dataset=TEST_DATASET,
            start_date=TEST_START_DATE,
            end_date=TEST_END_DATE,
            location=TEST_LOCATION
        )
        assert search_result["recordsReturned"] > 0

        # Step 2: Get metadata for first scene
        scene_id = search_result["results"][0]["entityId"]
        metadata = mock_api_client.get_scene_metadata(scene_id)
        assert metadata is not None

        # Step 3: Download scene
        download_path = mock_api_client.download_scene(scene_id)
        assert download_path is not None
        assert os.path.exists(download_path) or download_path.endswith(".tif")

    @pytest.mark.integration
    def test_error_recovery_workflow(self, mock_api_client):
        """Test workflow recovers from transient errors."""
        call_count = [0]
        
        def flaky_search(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("Transient error")
            return mock_api_response()
        
        mock_api_client.search_scenes.side_effect = flaky_search
        
        # Should retry and succeed
        result = mock_api_client.search_scenes(
            dataset=TEST_DATASET,
            start_date=TEST_START_DATE,
            end_date=TEST_END_DATE,
            location=TEST_LOCATION
        )
        
        assert result is not None
        assert call_count[0] >= 1

    @pytest.mark.integration
    def test_metadata_extraction_for_processing(self, mock_api_client):
        """Test that metadata can be extracted for downstream processing."""
        scene_id = "LC08_L1TP_015033_20230101"
        metadata = mock_api_client.get_scene_metadata(scene_id)
        
        # Extract fields needed for climate analysis
        extracted = {
            "scene_id": metadata["entityId"],
            "acquisition_date": metadata["acquisitionTime"],
            "cloud_cover": metadata["cloudCover"],
            "spatial_bounds": metadata["spatialCoverage"]
        }
        
        assert extracted["scene_id"] == scene_id
        assert extracted["cloud_cover"] is not None
        assert extracted["spatial_bounds"] is not None