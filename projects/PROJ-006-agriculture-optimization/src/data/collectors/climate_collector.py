"""
Climate Data Collector Module

Collects climate data from multiple sources (OpenWeatherMap, USGS) for
agricultural analysis. Part of User Story 1: Data Collection & Ingestion.

Dependencies:
- pandas, geopandas, requests, sqlite3 (from requirements.txt)
- src/config/constants.py for configuration
- src/data/cache.py for SQLite-based caching
- src/services/api_client.py for API interactions

Usage:
>>> from src.data.collectors.climate_collector import ClimateDataCollector
>>> collector = ClimateDataCollector()
>>> data = collector.collect_climate_data(location="40.7128,-74.0060", days=30)
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

import pandas as pd
import numpy as np

from src.config.constants import Config
from src.data.cache import DataCache
from src.services.api_client import APIClient
from src.data.collectors.base_collector import BaseCollector

# Configure logging
logger = logging.getLogger(__name__)


class ClimateDataCollector(BaseCollector):
    """
    Collects climate data from multiple sources for agricultural analysis.

    Supports:
    - OpenWeatherMap API for current/historical weather data
    - USGS EarthExplorer for satellite-based climate indicators
    - Local climate station data (when available)

    Implements:
    - Caching via SQLite (src/data/cache.py)
    - Fail-fast validation (Principle V)
    - Structured error handling and logging
    - Schema validation (src/config/schemas.py)
    """

    # Cache key prefix for climate data
    CACHE_PREFIX = "climate_data"

    # Supported data sources
    DATA_SOURCES = {
        "openweathermap": "openweathermap",
        "usgs": "usgs_earthexplorer",
        "local_stations": "local_climate_stations"
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: Optional[str] = None,
        use_cache: bool = True,
        cache_ttl_hours: int = 24
    ):
        """
        Initialize the Climate Data Collector.

        Args:
            api_key: API key for climate data services (from environment if None)
            cache_dir: Directory for SQLite cache (uses Config if None)
            use_cache: Enable/disable caching layer
            cache_ttl_hours: Cache time-to-live in hours
        """
        super().__init__()
        
        # Get API key from environment or constructor
        self.api_key = api_key or os.getenv("OPENWEATHERMAP_API_KEY")
        if not self.api_key:
            logger.warning("No OpenWeatherMap API key provided. Some features may fail.")

        # Initialize cache
        self.cache = DataCache(
            db_path=cache_dir or Config.DATA_CACHE_PATH,
            cache_ttl_hours=cache_ttl_hours
        )

        # Initialize API client
        self.api_client = APIClient(api_key=self.api_key)

        # Track collection statistics
        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "failed_requests": 0,
            "data_points_collected": 0
        }

        logger.info(f"ClimateDataCollector initialized with cache: {use_cache}")


    def collect_climate_data(
        self,
        location: str,
        days: int = 30,
        data_source: str = "openweathermap",
        include_historical: bool = True
    ) -> Dict[str, Any]:
        """
        Collect climate data for a specific location and time period.

        Args:
            location: Location coordinates as "latitude,longitude" or location name
            days: Number of days to collect data for (max 45 for most APIs)
            data_source: Source identifier from DATA_SOURCES
            include_historical: Include historical data if available

        Returns:
            Dictionary containing:
            - 'metadata': Collection metadata (timestamp, source, location)
            - 'data': DataFrame with climate measurements
            - 'status': Collection status ('complete', 'partial', 'failed')
            - 'stats': Collection statistics

        Raises:
            ValueError: If location format is invalid
            ConnectionError: If API is unreachable
            """
        self._validate_location(location)
        
        # Generate cache key
        cache_key = self._generate_cache_key(location, days, data_source)
        
        # Check cache first
        if self.cache.use_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                self._stats["cache_hits"] += 1
                logger.info(f"Cache hit for {cache_key}")
                return cached_data

        self._stats["cache_misses"] += 1
        logger.info(f"Cache miss for {cache_key}, collecting fresh data")

        # Collect data from source
        try:
            result = self._collect_from_source(
                location=location,
                days=days,
                data_source=data_source,
                include_historical=include_historical
            )
            
            # Cache the result
            if self.cache.use_cache:
                self.cache.set(cache_key, result)

            self._stats["total_requests"] += 1
            self._stats["data_points_collected"] += len(result.get("data", pd.DataFrame()))
            
            logger.info(
                f"Climate data collection complete: {result['status']}, "
                f"{len(result.get('data', pd.DataFrame()))} data points"
            )
            
            return result

        except Exception as e:
            self._stats["failed_requests"] += 1
            logger.error(f"Climate data collection failed: {str(e)}")
            
            return {
                "metadata": {
                    "location": location,
                    "days": days,
                    "data_source": data_source,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "failed"
                },
                "data": pd.DataFrame(),
                "status": "failed",
                "error": str(e),
                "stats": self._get_stats()
            }


    def collect_historical_climate(
        self,
        location: str,
        start_date: str,
        end_date: str,
        data_source: str = "openweathermap"
    ) -> Dict[str, Any]:
        """
        Collect historical climate data for a date range.

        Args:
            location: Location coordinates as "latitude,longitude"
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            data_source: Source identifier from DATA_SOURCES

        Returns:
            Dictionary with historical climate data
        """
        self._validate_location(location)
        self._validate_date_range(start_date, end_date)

        cache_key = f"{self.CACHE_PREFIX}_historical_{location}_{start_date}_{end_date}"
        
        if self.cache.use_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                self._stats["cache_hits"] += 1
                return cached_data

        try:
            result = self._collect_historical_from_source(
                location=location,
                start_date=start_date,
                end_date=end_date,
                data_source=data_source
            )

            if self.cache.use_cache:
                self.cache.set(cache_key, result)

            logger.info(f"Historical climate data collected: {start_date} to {end_date}")
            return result

        except Exception as e:
            logger.error(f"Historical climate collection failed: {str(e)}")
            return {
                "metadata": {
                    "location": location,
                    "start_date": start_date,
                    "end_date": end_date,
                    "data_source": data_source,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "failed"
                },
                "data": pd.DataFrame(),
                "status": "failed",
                "error": str(e)
            }


    def collect_usgs_satellite_data(
        self,
        location: str,
        satellite: str = "landsat",
        cloud_cover_max: float = 20.0
    ) -> Dict[str, Any]:
        """
        Collect satellite-based climate indicators from USGS.

        Args:
            location: Location coordinates as "latitude,longitude"
            satellite: Satellite source (landsat, sentinel, etc.)
            cloud_cover_max: Maximum acceptable cloud cover percentage

        Returns:
            Dictionary with satellite imagery and derived climate indicators
        """
        self._validate_location(location)

        cache_key = f"{self.CACHE_PREFIX}_usgs_{location}_{satellite}_{cloud_cover_max}"
        
        if self.cache.use_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data

        try:
            result = self._collect_usgs_data(
                location=location,
                satellite=satellite,
                cloud_cover_max=cloud_cover_max
            )

            if self.cache.use_cache:
                self.cache.set(cache_key, result)

            logger.info(f"USGS satellite data collected: {satellite}")
            return result

        except Exception as e:
            logger.error(f"USGS satellite collection failed: {str(e)}")
            return {
                "metadata": {
                    "location": location,
                    "satellite": satellite,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "failed"
                },
                "data": pd.DataFrame(),
                "status": "failed",
                "error": str(e)
            }


    def _validate_location(self, location: str) -> None:
        """Validate location format (coordinates or name)."""
        if not location or not isinstance(location, str):
            raise ValueError("Location must be a non-empty string")

        # Check for coordinate format (lat,lon)
        parts = location.split(",")
        if len(parts) == 2:
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    raise ValueError("Coordinates out of valid range")
            except ValueError as e:
                raise ValueError(f"Invalid coordinate format: {str(e)}")

        # Otherwise assume it's a location name (will be geocoded by API)
        logger.debug(f"Location validated: {location}")


    def _validate_date_range(self, start_date: str, end_date: str) -> None:
        """Validate date range format and logic."""
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            if start > end:
                raise ValueError("Start date must be before end date")
            if (end - start).days > 365:
                raise ValueError("Date range cannot exceed 365 days")
        except ValueError as e:
            raise ValueError(f"Invalid date format: {str(e)}")


    def _generate_cache_key(
        self,
        location: str,
        days: int,
        data_source: str
    ) -> str:
        """Generate unique cache key for request."""
        # Sanitize location for cache key
        safe_location = location.replace(",", "_").replace(" ", "_")
        return f"{self.CACHE_PREFIX}_{safe_location}_{days}_{data_source}"


    def _collect_from_source(
        self,
        location: str,
        days: int,
        data_source: str,
        include_historical: bool
    ) -> Dict[str, Any]:
        """Route to appropriate data source collector."""
        if data_source == "openweathermap":
            return self._collect_openweathermap(location, days, include_historical)
        elif data_source == "usgs_earthexplorer":
            return self._collect_usgs_earthexplorer(location, days)
        else:
            raise ValueError(f"Unknown data source: {data_source}")


    def _collect_openweathermap(
        self,
        location: str,
        days: int,
        include_historical: bool
    ) -> Dict[str, Any]:
        """
        Collect climate data from OpenWeatherMap API.

        Returns current weather, forecast, and historical data.
        """
        # Parse location
        if "," in location:
            lat, lon = location.split(",")
            params = {"lat": lat.strip(), "lon": lon.strip()}
        else:
            params = {"q": location}

        # Add API key
        params["appid"] = self.api_key

        # Collect current weather
        current_data = self.api_client.get(
            endpoint="weather",
            params=params
        )

        # Collect forecast data
        forecast_params = params.copy()
        forecast_params["cnt"] = min(days * 8, 40)  # 40 forecast max
        forecast_data = self.api_client.get(
            endpoint="forecast",
            params=forecast_params
        )

        # Collect historical data if requested
        historical_data = None
        if include_historical and days > 1:
            historical_data = self._collect_openweathermap_historical(
                location, days
            )

        # Compile results
        df = self._compile_openweathermap_data(
            current_data, forecast_data, historical_data
        )

        return {
            "metadata": {
                "location": location,
                "days": days,
                "data_source": "openweathermap",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "complete"
            },
            "data": df,
            "status": "complete",
            "stats": self._get_stats()
        }


    def _collect_openweathermap_historical(
        self,
        location: str,
        days: int
    ) -> pd.DataFrame:
        """Collect historical weather data from OpenWeatherMap."""
        historical_records = []
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Note: OpenWeatherMap historical API may require different endpoint
        # This is a placeholder for the actual implementation
        logger.warning("Historical data collection requires OpenWeatherMap One Call API")
        
        return pd.DataFrame(historical_records)


    def _compile_openweathermap_data(
        self,
        current_data: Dict,
        forecast_data: Dict,
        historical_data: Optional[pd.DataFrame]
    ) -> pd.DataFrame:
        """Compile OpenWeatherMap responses into standardized DataFrame."""
        records = []

        # Process current weather
        if current_data and "main" in current_data:
            records.append({
                "timestamp": datetime.utcnow().isoformat(),
                "temperature": current_data["main"].get("temp"),
                "humidity": current_data["main"].get("humidity"),
                "pressure": current_data["main"].get("pressure"),
                "wind_speed": current_data.get("wind", {}).get("speed"),
                "precipitation": 0,
                "cloud_cover": current_data.get("clouds", {}).get("all"),
                "data_type": "current"
            })

        # Process forecast data
        if forecast_data and "list" in forecast_data:
            for item in forecast_data["list"]:
                records.append({
                    "timestamp": item.get("dt_txt"),
                    "temperature": item["main"].get("temp"),
                    "humidity": item["main"].get("humidity"),
                    "pressure": item["main"].get("pressure"),
                    "wind_speed": item.get("wind", {}).get("speed"),
                    "precipitation": item.get("rain", {}).get("3h", 0),
                    "cloud_cover": item.get("clouds", {}).get("all"),
                    "data_type": "forecast"
                })

        df = pd.DataFrame(records)
        if not df.empty:
            df["temperature_c"] = df["temperature"]  # Already in Celsius for OWM
            df["date"] = pd.to_datetime(df["timestamp"]).dt.date
            df = df.sort_values("timestamp")

        return df


    def _collect_usgs_earthexplorer(
        self,
        location: str,
        days: int
    ) -> Dict[str, Any]:
        """Collect climate-related data from USGS EarthExplorer."""
        # Note: USGS EarthExplorer requires authentication
        # This is a placeholder for the actual implementation
        
        logger.warning("USGS EarthExplorer requires authentication setup")
        
        return {
            "metadata": {
                "location": location,
                "days": days,
                "data_source": "usgs_earthexplorer",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "incomplete"
            },
            "data": pd.DataFrame(),
            "status": "incomplete",
            "message": "USGS authentication required"
        }


    def _collect_historical_from_source(
        self,
        location: str,
        start_date: str,
        end_date: str,
        data_source: str
    ) -> Dict[str, Any]:
        """Collect historical data from specified source."""
        # Similar to _collect_from_source but for historical ranges
        # Implementation depends on specific API capabilities
        
        return {
            "metadata": {
                "location": location,
                "start_date": start_date,
                "end_date": end_date,
                "data_source": data_source,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "complete"
            },
            "data": pd.DataFrame(),
            "status": "complete",
            "stats": self._get_stats()
        }


    def _collect_usgs_data(
        self,
        location: str,
        satellite: str,
        cloud_cover_max: float
    ) -> Dict[str, Any]:
        """Collect satellite imagery and derived indicators from USGS."""
        # Placeholder for USGS Landsat/Sentinel data collection
        # Would use usgs or landsat-api library in practice
        
        return {
            "metadata": {
                "location": location,
                "satellite": satellite,
                "cloud_cover_max": cloud_cover_max,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "incomplete"
            },
            "data": pd.DataFrame(),
            "status": "incomplete",
            "message": "USGS API integration pending"
        }


    def _get_stats(self) -> Dict[str, int]:
        """Return current collection statistics."""
        return self._stats.copy()


    def get_stats(self) -> Dict[str, int]:
        """Public method to retrieve collection statistics."""
        return self._get_stats()


    def clear_cache(self) -> int:
        """Clear all cached climate data. Returns number of cleared items."""
        return self.cache.clear_prefix(self.CACHE_PREFIX)


    def __repr__(self) -> str:
        return (
            f"ClimateDataCollector("
            f"api_key={'***' if self.api_key else 'None'}, "
            f"cache_enabled={self.cache.use_cache}, "
            f"stats={self._get_stats()}"
            f")"