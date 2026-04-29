"""Survey data collector for agricultural and socioeconomic data."""
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import requests

logger = logging.getLogger(__name__)

class SurveyCollector:
    """Collects survey data from configured sources."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize survey collector with configuration.

        Args:
            config: Configuration dict with API keys, endpoints, etc.
        """
        self.config = config
        self.output_dir = Path(config.get('output_dir', 'data/raw/survey'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("SurveyCollector initialized with output_dir: %s", self.output_dir)

    def collect(self, region: str, year: int) -> Optional[Dict[str, Any]]:
        """Collect survey data for specified region and year.

        Args:
            region: Geographic region identifier
            year: Data collection year

        Returns:
            Survey data dict or None if collection fails
        """
        logger.info("Starting survey collection for region=%s, year=%s", region, year)

        try:
            # Validate inputs
            if not region or not region.strip():
                logger.error("Invalid region parameter: %s", region)
                return None

            # Attempt to fetch data
            source_url = self.config.get('survey_source_url')
            if not source_url:
                logger.warning("No survey_source_url configured in survey_collector")
                return None

            logger.debug("Fetching survey data from: %s", source_url)
            response = requests.get(source_url, timeout=30)
            response.raise_for_status()

            logger.info("Successfully collected survey data for region=%s, year=%s", region, year)

            # Save raw data
            output_file = self.output_dir / f"survey_{region}_{year}.json"
            output_file.write_text(response.text)
            logger.info("Survey data saved to: %s", output_file)

            return response.json()

        except requests.RequestException as e:
            logger.error("Request failed during survey collection: %s", str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error during survey collection: %s", str(e), exc_info=True)
            return None

    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate collected survey data.

        Args:
            data: Survey data to validate

        Returns:
            True if valid, False otherwise
        """
        logger.debug("Validating survey data")
        if not data:
            logger.warning("Survey data is empty")
            return False

        required_fields = ['region', 'year', 'respondents']
        for field in required_fields:
            if field not in data:
                logger.warning("Missing required field in survey data: %s", field)
                return False

        logger.info("Survey data validation passed")
        return True
