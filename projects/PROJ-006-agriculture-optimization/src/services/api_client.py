"""API client for external data sources (OpenWeatherMap, USGS EarthExplorer)."""
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import requests
import time
from functools import wraps

logger = logging.getLogger(__name__)

def rate_limit(max_calls: int = 100, period: int = 60):
    """Rate limiting decorator for API calls.

    Args:
        max_calls: Maximum number of calls allowed in period
        period: Time period in seconds
    """
    def decorator(func):
        call_times = []

        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            # Remove old calls outside the period
            call_times[:] = [t for t in call_times if current_time - t < period]

            if len(call_times) >= max_calls:
                logger.warning("Rate limit exceeded for %s, waiting...", func.__name__)
                time.sleep(period - (current_time - call_times[0]))

            call_times.append(time.time())
            return func(*args, **kwargs)
        return wrapper
    return decorator

class APIClient:
    """Client for managing API interactions with external data sources."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize API client with configuration.

        Args:
            config: Configuration dict with API keys, endpoints, rate limits, etc.
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})

        # Log initialization
        logger.info("APIClient initialized")
        logger.debug("Configured API sources: %s", list(config.keys()))

    @rate_limit(max_calls=100, period=60)
    def call_weather_api(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call OpenWeatherMap API with rate limiting.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            API response dict or None if call fails
        """
        logger.info("Calling OpenWeatherMap API: %s", endpoint)

        try:
            # Inject API key
            api_key = self.config.get('weather_api_key')
            if not api_key:
                logger.error("Weather API key not configured")
                return None

            params['appid'] = api_key

            url = f"https://api.openweathermap.org/data/2.5/{endpoint}"
            logger.debug("Weather API request URL: %s with params: %s", url, params)

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                logger.info("Weather API call successful: %s", endpoint)
                return response.json()
            elif response.status_code == 401:
                logger.error("Weather API authentication failed")
                return None
            elif response.status_code == 429:
                logger.warning("Weather API rate limit hit")
                return None
            else:
                logger.error("Weather API call failed with status %d: %s",
                           response.status_code, response.text)
                return None

        except requests.RequestException as e:
            logger.error("Weather API request exception: %s", str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error in weather API call: %s", str(e), exc_info=True)
            return None

    @rate_limit(max_calls=100, period=60)
    def call_usgs_api(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call USGS EarthExplorer API with rate limiting.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            API response dict or None if call fails
        """
        logger.info("Calling USGS EarthExplorer API: %s", endpoint)

        try:
            # Inject API key
            api_key = self.config.get('usgs_api_key')
            if not api_key:
                logger.error("USGS API key not configured")
                return None

            params['api_key'] = api_key

            url = f"https://earthexplorer.usgs.gov/api/{endpoint}"
            logger.debug("USGS API request URL: %s with params: %s", url, params)

            response = self.session.get(url, params=params, timeout=60)

            if response.status_code == 200:
                logger.info("USGS API call successful: %s", endpoint)
                return response.json()
            elif response.status_code == 401:
                logger.error("USGS API authentication failed")
                return None
            elif response.status_code == 429:
                logger.warning("USGS API rate limit hit")
                return None
            else:
                logger.error("USGS API call failed with status %d: %s",
                           response.status_code, response.text)
                return None

        except requests.RequestException as e:
            logger.error("USGS API request exception: %s", str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error in USGS API call: %s", str(e), exc_info=True)
            return None

    def validate_api_credentials(self) -> bool:
        """Validate that configured API credentials are working.

        Returns:
            True if credentials are valid, False otherwise
        """
        logger.info("Validating API credentials")

        try:
            # Test weather API
            weather_valid = self.call_weather_api('weather', {'q': 'London'}) is not None
            if weather_valid:
                logger.info("Weather API credentials valid")
            else:
                logger.warning("Weather API credentials may be invalid")

            # Test USGS API
            usgs_valid = self.call_usgs_api('search', {'lat': 0, 'lon': 0}) is not None
            if usgs_valid:
                logger.info("USGS API credentials valid")
            else:
                logger.warning("USGS API credentials may be invalid")

            return weather_valid and usgs_valid

        except Exception as e:
            logger.error("Error during API credential validation: %s", str(e))
            return False