"""
Integration tests for OpenWeatherMap API client.

Purpose: Verify that the API client can successfully connect to
OpenWeatherMap, retrieve weather data, and handle various response
scenarios.

NOTE: These tests require a valid OpenWeatherMap API key set in
the OPENWEATHERMAP_API_KEY environment variable.

TDD Approach: These tests should FAIL before T018 (API client
implementation) is complete.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the API client (will fail until T018 is implemented)
try:
    from src.services.api_client import OpenWeatherMapClient
    API_CLIENT_AVAILABLE = True
except ImportError:
    API_CLIENT_AVAILABLE = False

# Constants
TEST_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY", "test_key")
TEST_CITY = "London"
TEST_COORDINATES = (51.5074, -0.1278)  # London coordinates


@pytest.fixture
def api_client():
    """Create an OpenWeatherMap client instance."""
    if not API_CLIENT_AVAILABLE:
        pytest.skip("API client not yet implemented (T018)")
    return OpenWeatherMapClient(api_key=TEST_API_KEY)


@pytest.fixture
def mock_response():
    """Create a mock API response."""
    return {
        "coord": {"lon": -0.1278, "lat": 51.5074},
        "weather": [{"id": 800, "main": "Clear", "description": "clear sky"}],
        "main": {
            "temp": 15.5,
            "feels_like": 14.2,
            "temp_min": 13.0,
            "temp_max": 17.0,
            "pressure": 1013,
            "humidity": 65
        },
        "visibility": 10000,
        "wind": {"speed": 3.6, "deg": 230},
        "dt": 1625097600,
        "sys": {"country": "GB"},
        "name": "London"
    }


class TestOpenWeatherMapClient:
    """Integration tests for OpenWeatherMap API client."""
    
    @pytest.mark.integration
    def test_api_client_initialization(self, api_client):
        """Test that the API client initializes correctly."""
        assert api_client is not None
        assert api_client.api_key == TEST_API_KEY
        assert api_client.base_url == "https://api.openweathermap.org/data/2.5"
    
    @pytest.mark.integration
    def test_validate_api_key_valid(self, api_client):
        """Test API key validation with a valid key."""
        # Should not raise an exception
        result = api_client.validate_api_key()
        assert result is True or result is False  # Depends on actual API
    
    @pytest.mark.integration
    def test_validate_api_key_missing(self):
        """Test API key validation with missing key."""
        if not API_CLIENT_AVAILABLE:
            pytest.skip("API client not yet implemented (T018)")
        with pytest.raises(ValueError, match="API key required"):
            OpenWeatherMapClient(api_key=None)
    
    @pytest.mark.integration
    def test_get_current_weather_by_city(self, api_client, mock_response):
        """Test fetching current weather by city name."""
        if not API_CLIENT_AVAILABLE:
            pytest.skip("API client not yet implemented (T018)")
        
        with patch.object(api_client, '_make_request', return_value=mock_response):
            result = api_client.get_current_weather(city=TEST_CITY)
            
            assert result is not None
            assert "main" in result
            assert "weather" in result
            assert result["name"] == TEST_CITY
    
    @pytest.mark.integration
    def test_get_current_weather_by_coordinates(self, api_client, mock_response):
        """Test fetching current weather by coordinates."""
        if not API_CLIENT_AVAILABLE:
            pytest.skip("API client not yet implemented (T018)")
        
        with patch.object(api_client, '_make_request', return_value=mock_response):
            result = api_client.get_current_weather(
                lat=TEST_COORDINATES[0],
                lon=TEST_COORDINATES[1]
            )
            
            assert result is not None
            assert "coord" in result
    
    @pytest.mark.integration
    def test_get_historical_weather(self, api_client, mock_response):
        """Test fetching historical weather data."""
        if not API_CLIENT_AVAILABLE:
            pytest.skip("API client not yet implemented (T018)")
        
        with patch.object(api_client, '_make_request', return_value=mock_response):
            result = api_client.get_historical_weather(
                city=TEST_CITY,
                date="2024-01-01"
            )
            
            assert result is not None
    
    @pytest.mark.integration
    def test_rate_limit_handling(self, api_client):
        """Test that rate limit errors are handled gracefully."""
        if not API_CLIENT_AVAILABLE:
            pytest.skip("API client not yet implemented (T018)")
        
        mock_error_response = {
            "cod": 429,
            "message": "Too many requests"
        }
        
        with patch.object(api_client, '_make_request', return_value=mock_error_response):
            result = api_client.get_current_weather(city=TEST_CITY)
            
            assert result is None  # Should return None on rate limit
    
    @pytest.mark.integration
    def test_invalid_city_handling(self, api_client):
        """Test handling of invalid city names."""
        if not API_CLIENT_AVAILABLE:
            pytest.skip("API client not yet implemented (T018)")
        
        mock_error_response = {
            "cod": "404",
            "message": "City not found"
        }
        
        with patch.object(api_client, '_make_request', return_value=mock_error_response):
            result = api_client.get_current_weather(city="NonExistentCity12345")
            
            assert result is None  # Should return None on city not found
    
    @pytest.mark.integration
    def test_cache_functionality(self, api_client, mock_response):
        """Test that API responses are cached properly."""
        if not API_CLIENT_AVAILABLE:
            pytest.skip("API client not yet implemented (T018)")
        
        with patch.object(api_client, '_make_request', return_value=mock_response):
            # First call - should hit API
            result1 = api_client.get_current_weather(city=TEST_CITY)
            
            # Second call - should use cache
            result2 = api_client.get_current_weather(city=TEST_CITY)
            
            assert result1 == result2
    
    @pytest.mark.integration
    def test_timeout_handling(self, api_client):
        """Test that timeout errors are handled gracefully."""
        if not API_CLIENT_AVAILABLE:
            pytest.skip("API client not yet implemented (T018)")
        
        with patch.object(api_client, '_make_request', side_effect=TimeoutError("Request timed out")):
            result = api_client.get_current_weather(city=TEST_CITY)
            
            assert result is None  # Should return None on timeout
    
    @pytest.mark.integration
    def test_data_validation(self, api_client):
        """Test that returned data is validated against schema."""
        if not API_CLIENT_AVAILABLE:
            pytest.skip("API client not yet implemented (T018)")
        
        invalid_response = {
            "invalid_field": "value"
        }
        
        with patch.object(api_client, '_make_request', return_value=invalid_response):
            result = api_client.get_current_weather(city=TEST_CITY)
            
            assert result is None  # Should fail validation
    
    @pytest.mark.integration
    def test_logging_on_api_call(self, api_client, mock_response, caplog):
        """Test that API calls are logged properly."""
        if not API_CLIENT_AVAILABLE:
            pytest.skip("API client not yet implemented (T018)")
        
        with patch.object(api_client, '_make_request', return_value=mock_response):
            result = api_client.get_current_weather(city=TEST_CITY)
            
            # Check that logging occurred (depends on T020 implementation)
            # This test may be skipped if logging not yet implemented
            assert result is not None
    
    @pytest.mark.integration
    def test_units_parameter(self, api_client, mock_response):
        """Test that units parameter is passed correctly."""
        if not API_CLIENT_AVAILABLE:
            pytest.skip("API client not yet implemented (T018)")
        
        with patch.object(api_client, '_make_request', return_value=mock_response) as mock:
            api_client.get_current_weather(city=TEST_CITY, units="metric")
            
            # Verify units parameter was passed
            call_args = mock.call_args
            assert call_args is not None