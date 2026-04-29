"""Climate data collector for weather and climate information."""
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class ClimateCollector:
    """Collects climate data from weather APIs and historical sources."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize climate collector with configuration.

        Args:
            config: Configuration dict with API keys, endpoints, etc.
        """
        self.config = config
        self.output_dir = Path(config.get('output_dir', 'data/raw/climate'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("ClimateCollector initialized with output_dir: %s", self.output_dir)

    def collect_current(self, coordinates: tuple) -> Optional[Dict[str, Any]]:
        """Collect current climate data for given coordinates.

        Args:
            coordinates: (latitude, longitude) tuple

        Returns:
            Current climate data dict or None if collection fails
        """
        logger.info("Starting current climate collection for coordinates=%s", coordinates)

        try:
            api_key = self.config.get('weather_api_key')
            if not api_key:
                logger.warning("Weather API key not configured")
                return None

            lat, lon = coordinates
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': api_key,
                'units': 'metric'
            }

            logger.debug("Fetching current climate data from OpenWeatherMap")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            logger.info("Successfully collected current climate data for coordinates=%s", coordinates)
            return response.json()

        except requests.RequestException as e:
            logger.error("Request failed during current climate collection: %s", str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error during current climate collection: %s", str(e), exc_info=True)
            return None

    def collect_historical(self, coordinates: tuple, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
        """Collect historical climate data for given date range.

        Args:
            coordinates: (latitude, longitude) tuple
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Historical climate data dict or None if collection fails
        """
        logger.info("Starting historical climate collection for coordinates=%s, range=%s to %s",
                   coordinates, start_date, end_date)

        try:
            api_key = self.config.get('weather_api_key')
            if not api_key:
                logger.warning("Weather API key not configured for historical data")
                return None

            lat, lon = coordinates
            url = "https://api.openweathermap.org/data/2.5/onecall/timemachine"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': api_key,
                'units': 'metric'
            }

            # Collect data point by point for the date range
            data_points = []
            current_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

            logger.debug("Collecting %d days of historical climate data",
                       (end_date_obj - current_date).days + 1)

            while current_date <= end_date_obj:
                params['dt'] = int(current_date.timestamp())
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data_points.append(response.json())
                current_date += timedelta(days=1)

            logger.info("Successfully collected %d days of historical climate data", len(data_points))

            # Save raw data
            output_file = self.output_dir / f"climate_historical_{lat}_{lon}_{start_date}_{end_date}.json"
            output_file.write_text(json.dumps(data_points))
            logger.info("Historical climate data saved to: %s", output_file)

            return {'data_points': data_points, 'count': len(data_points)}

        except requests.RequestException as e:
            logger.error("Request failed during historical climate collection: %s", str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error during historical climate collection: %s", str(e), exc_info=True)
            return None

    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate collected climate data.

        Args:
            data: Climate data to validate

        Returns:
            True if valid, False otherwise
        """
        logger.debug("Validating climate data")
        if not data:
            logger.warning("Climate data is empty")
            return False

        # Check for required climate fields
        required_fields = ['temperature', 'humidity', 'pressure']
        for field in required_fields:
            if field not in data:
                logger.warning("Missing required field in climate data: %s", field)
                return False

        logger.info("Climate data validation passed")
        return True
