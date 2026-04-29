"""Remote sensing data collector using USGS EarthExplorer and satellite imagery."""
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import rasterio
import requests

logger = logging.getLogger(__name__)

class RemoteSensingCollector:
    """Collects remote sensing data from satellite sources."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize remote sensing collector with configuration.

        Args:
            config: Configuration dict with API keys, endpoints, etc.
        """
        self.config = config
        self.output_dir = Path(config.get('output_dir', 'data/raw/remote_sensing'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("RemoteSensingCollector initialized with output_dir: %s", self.output_dir)

    def collect_satellite_image(self, coordinates: tuple, date: str, sensor: str = 'Landsat8') -> Optional[Dict[str, Any]]:
        """Collect satellite imagery for given location and date.

        Args:
            coordinates: (latitude, longitude) tuple
            date: Target date in YYYY-MM-DD format
            sensor: Satellite sensor type (default: Landsat8)

        Returns:
            Remote sensing data dict or None if collection fails
        """
        logger.info("Starting remote sensing collection for coordinates=%s, date=%s, sensor=%s",
                   coordinates, date, sensor)

        try:
            # Validate coordinates
            lat, lon = coordinates
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                logger.error("Invalid coordinates: lat=%s, lon=%s", lat, lon)
                return None

            api_key = self.config.get('usgs_api_key')
            if not api_key:
                logger.warning("USGS API key not configured")
                return None

            # Search for available scenes
            url = "https://earthexplorer.usgs.gov/api/search"
            params = {
                'lat': lat,
                'lon': lon,
                'date': date,
                'sensor': sensor,
                'api_key': api_key
            }

            logger.debug("Searching USGS EarthExplorer for satellite scenes")
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()

            scenes = response.json().get('results', [])
            if not scenes:
                logger.warning("No satellite scenes found for coordinates=%s, date=%s", coordinates, date)
                return None

            logger.info("Found %d satellite scenes for coordinates=%s, date=%s", len(scenes), coordinates, date)

            # Download first available scene
            scene_id = scenes[0]['id']
            download_url = f"https://earthexplorer.usgs.gov/api/download/{scene_id}"

            logger.debug("Downloading satellite scene: %s", scene_id)
            download_response = requests.get(download_url, params={'api_key': api_key}, timeout=300)
            download_response.raise_for_status()

            # Save raw data
            output_file = self.output_dir / f"remote_sensing_{sensor}_{lat}_{lon}_{date}.tif"
            output_file.write_bytes(download_response.content)
            logger.info("Remote sensing data saved to: %s", output_file)

            return {
                'scene_id': scene_id,
                'sensor': sensor,
                'coordinates': coordinates,
                'date': date,
                'file_path': str(output_file)
            }

        except requests.RequestException as e:
            logger.error("Request failed during remote sensing collection: %s", str(e))
            return None
        except rasterio.errors.RasterioIOError as e:
            logger.error("RasterIO error during remote sensing collection: %s", str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error during remote sensing collection: %s", str(e), exc_info=True)
            return None

    def process_raster(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Process a raster file and extract metadata.

        Args:
            file_path: Path to the raster file

        Returns:
            Raster metadata dict or None if processing fails
        """
        logger.info("Processing raster file: %s", file_path)

        try:
            with rasterio.open(file_path) as src:
                metadata = {
                    'crs': str(src.crs),
                    'width': src.width,
                    'height': src.height,
                    'count': src.count,
                    'dtype': src.dtype,
                    'bounds': src.bounds,
                    'transform': src.transform
                }
                logger.info("Raster metadata extracted: width=%d, height=%d, bands=%d",
                           metadata['width'], metadata['height'], metadata['count'])
                return metadata

        except rasterio.errors.RasterioIOError as e:
            logger.error("Failed to open raster file: %s", str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error during raster processing: %s", str(e), exc_info=True)
            return None

    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate collected remote sensing data.

        Args:
            data: Remote sensing data to validate

        Returns:
            True if valid, False otherwise
        """
        logger.debug("Validating remote sensing data")
        if not data:
            logger.warning("Remote sensing data is empty")
            return False

        required_fields = ['scene_id', 'file_path']
        for field in required_fields:
            if field not in data:
                logger.warning("Missing required field in remote sensing data: %s", field)
                return False

        # Check file exists
        if not Path(data['file_path']).exists():
            logger.warning("Remote sensing file does not exist: %s", data['file_path'])
            return False

        logger.info("Remote sensing data validation passed")
        return True
