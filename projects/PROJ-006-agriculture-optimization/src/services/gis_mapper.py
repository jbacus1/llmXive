"""
GIS Mapper Service for Climate-Smart Agricultural Practices

Provides spatial data processing, analysis, and mapping capabilities
using geopandas and rasterio for climate risk visualization and reporting.

This service is part of User Story 4 (GIS Visualization & Reporting)
and integrates with the data collected in US1 and risk assessments from US2.

Dependencies:
  - geopandas >= 0.14.0
  - rasterio >= 1.3.0
  - pandas >= 2.0.0
  - shapely >= 2.0.0
"""

from typing import Optional, Dict, Any, List, Union, Tuple
from pathlib import Path
import logging
import json

import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.features import rasterize
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import Point, Polygon, mapping
from shapely.ops import unary_union
import numpy as np

from src.config.constants import CONFIG
from src.data.cache import CacheManager

logger = logging.getLogger(__name__)


class GISMapperError(Exception):
    """Custom exception for GIS mapper operations."""
    pass


class GISMapper:
    """
    Service for GIS-based spatial data processing and mapping.

    Provides functionality for:
    - Loading and processing vector data (shapefiles, GeoJSON)
    - Loading and processing raster data (GeoTIFF, satellite imagery)
    - Spatial joins and overlays
    - Coordinate reference system (CRS) transformations
    - Spatial analysis (buffer, clip, dissolve)
    - Raster-vector integration for risk mapping

    Attributes:
        cache_manager: CacheManager instance for storing processed spatial data
        supported_vector_formats: List of supported vector file extensions
        supported_raster_formats: List of supported raster file extensions
    """

    supported_vector_formats = ['.shp', '.geojson', '.json', '.gpkg', '.gpx', '.kml']
    supported_raster_formats = ['.tif', '.tiff', '.gtiff', '.img', '.jp2']

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the GIS mapper service.

        Args:
            cache_dir: Directory for caching processed spatial data.
                      Defaults to CONFIG['cache']['gis_cache_dir']
        """
        self.cache_manager = CacheManager(cache_dir or CONFIG.get('cache', {}).get('gis_cache_dir', 'data/cache/gis'))
        self._loaded_layers: Dict[str, gpd.GeoDataFrame] = {}
        self._loaded_rasters: Dict[str, rasterio.DatasetReader] = {}

    # =========================================================================
    # Vector Data Operations
    # =========================================================================

    def load_vector(
        self,
        file_path: Union[str, Path],
        layer_name: Optional[str] = None,
        crs: Optional[str] = None,
        use_cache: bool = True
    ) -> gpd.GeoDataFrame:
        """
        Load vector data from a file (shapefile, GeoJSON, etc.).

        Args:
            file_path: Path to the vector file
            layer_name: Optional layer name for multi-layer formats
            crs: Optional target CRS (EPSG code or PROJ string)
            use_cache: Whether to use cached version if available

        Returns:
            GeoDataFrame with loaded spatial data

        Raises:
            GISMapperError: If file not found or invalid format
        """
        file_path = Path(file_path)

        # Validate file exists
        if not file_path.exists():
            raise GISMapperError(f"Vector file not found: {file_path}")

        # Validate file extension
        if file_path.suffix.lower() not in self.supported_vector_formats:
            raise GISMapperError(
                f"Unsupported vector format: {file_path.suffix}. "
                f"Supported: {self.supported_vector_formats}"
            )

        # Check cache
        cache_key = f"vector_{file_path.stem}"
        if use_cache and self.cache_manager.exists(cache_key):
            logger.info(f"Loading vector from cache: {cache_key}")
            gdf = self.cache_manager.load(cache_key)
            return gdf

        # Load the data
        logger.info(f"Loading vector data: {file_path}")
        try:
            if layer_name:
                gdf = gpd.read_file(str(file_path), layer=layer_name)
            else:
                gdf = gpd.read_file(str(file_path))

            # Set CRS if provided
            if crs:
                if gdf.crs is None:
                    gdf.set_crs(crs, inplace=True)
                else:
                    gdf = gdf.to_crs(crs)

            # Validate geometry
            if gdf.empty:
                logger.warning(f"Loaded empty GeoDataFrame from: {file_path}")
            elif gdf.geometry.is_empty.all():
                logger.warning(f"All geometries are empty in: {file_path}")

            # Cache the result
            if use_cache:
                self.cache_manager.save(cache_key, gdf)

            self._loaded_layers[file_path.name] = gdf
            return gdf

        except Exception as e:
            raise GISMapperError(f"Failed to load vector data from {file_path}: {str(e)}")

    def load_raster(
        self,
        file_path: Union[str, Path],
        use_cache: bool = True
    ) -> Tuple[np.ndarray, rasterio.DatasetReader]:
        """
        Load raster data from a file (GeoTIFF, etc.).

        Args:
            file_path: Path to the raster file
            use_cache: Whether to use cached version if available

        Returns:
            Tuple of (numpy array of raster values, rasterio dataset)

        Raises:
            GISMapperError: If file not found or invalid format
        """
        file_path = Path(file_path)

        # Validate file exists
        if not file_path.exists():
            raise GISMapperError(f"Raster file not found: {file_path}")

        # Validate file extension
        if file_path.suffix.lower() not in self.supported_raster_formats:
            raise GISMapperError(
                f"Unsupported raster format: {file_path.suffix}. "
                f"Supported: {self.supported_raster_formats}"
            )

        # Check cache
        cache_key = f"raster_{file_path.stem}"
        if use_cache and self.cache_manager.exists(cache_key):
            logger.info(f"Loading raster from cache: {cache_key}")
            return self.cache_manager.load(cache_key)

        # Load the data
        logger.info(f"Loading raster data: {file_path}")
        try:
            with rasterio.open(file_path) as src:
                raster_data = src.read()
                dataset = src

            if use_cache:
                self.cache_manager.save(cache_key, (raster_data, dataset))

            self._loaded_rasters[file_path.name] = dataset
            return raster_data, dataset

        except Exception as e:
            raise GISMapperError(f"Failed to load raster data from {file_path}: {str(e)}")

    # =========================================================================
    # CRS Operations
    # =========================================================================

    def transform_crs(
        self,
        gdf: gpd.GeoDataFrame,
        target_crs: str
    ) -> gpd.GeoDataFrame:
        """
        Transform GeoDataFrame to a different coordinate reference system.

        Args:
            gdf: Source GeoDataFrame
            target_crs: Target CRS (EPSG code or PROJ string)

        Returns:
            Transformed GeoDataFrame
        """
        if gdf.crs is None:
            logger.warning("Source GeoDataFrame has no CRS. Setting target CRS as source.")
            gdf.set_crs(target_crs, inplace=True)
            return gdf

        if gdf.crs.to_epsg() == target_crs:
            return gdf

        logger.info(f"Transforming CRS from {gdf.crs} to {target_crs}")
        return gdf.to_crs(target_crs)

    def get_crs_info(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Get detailed CRS information for a GeoDataFrame.

        Args:
            gdf: GeoDataFrame to inspect

        Returns:
            Dictionary with CRS details
        """
        if gdf.crs is None:
            return {'has_crs': False}

        return {
            'has_crs': True,
            'epsg': gdf.crs.to_epsg(),
            'proj4': gdf.crs.to_proj4(),
            'wkt': gdf.crs.to_wkt(),
            'name': gdf.crs.name
        }

    # =========================================================================
    # Spatial Analysis Operations
    # =========================================================================

    def buffer(
        self,
        gdf: gpd.GeoDataFrame,
        distance: float,
        units: str = 'meters'
    ) -> gpd.GeoDataFrame:
        """
        Create a buffer around geometries.

        Args:
            gdf: Source GeoDataFrame
            distance: Buffer distance
            units: 'meters' or 'degrees' (affects distance interpretation)

        Returns:
            Buffered GeoDataFrame
        """
        if units == 'degrees':
            # For degree-based buffers, ensure CRS is in degrees
            if gdf.crs and gdf.crs.is_geographic:
                return gdf.copy()
            else:
                raise GISMapperError(
                    "For degree-based buffers, GeoDataFrame must be in a "
                    "geographic CRS (e.g., EPSG:4326)"
                )

        if units == 'meters':
            # Ensure CRS is projected
            if gdf.crs and gdf.crs.is_geographic:
                gdf = self.transform_crs(gdf, 'EPSG:3857')

        return gdf.copy().buffer(distance)

    def clip(
        self,
        gdf: gpd.GeoDataFrame,
        mask: Union[gpd.GeoDataFrame, Polygon],
        keep_geom_type: bool = True
    ) -> gpd.GeoDataFrame:
        """
        Clip GeoDataFrame to a mask geometry.

        Args:
            gdf: Source GeoDataFrame to clip
            mask: Geometry or GeoDataFrame to clip by
            keep_geom_type: If True, filter out non-geometry types after clipping

        Returns:
            Clipped GeoDataFrame
        """
        try:
            result = gpd.clip(gdf, mask)
            if keep_geom_type:
                result = gpd.GeoDataFrame(result, geometry='geometry')
            return result
        except Exception as e:
            raise GISMapperError(f"Clipping operation failed: {str(e)}")

    def dissolve(
        self,
        gdf: gpd.GeoDataFrame,
        by: Optional[str] = None,
        aggfunc: str = 'first',
        as_index: bool = False
    ) -> gpd.GeoDataFrame:
        """
        Dissolve geometries based on attribute values.

        Args:
            gdf: Source GeoDataFrame
            by: Column name to group by (None for all geometries)
            aggfunc: Aggregation function for non-geometry columns
            as_index: If True, use dissolved values as index

        Returns:
            Dissolved GeoDataFrame
        """
        if by is None:
            # Dissolve all geometries into one
            dissolved = gdf.dissolve(aggfunc=aggfunc)
        else:
            dissolved = gdf.dissolve(by=by, aggfunc=aggfunc, as_index=as_index)

        return dissolved

    def spatial_join(
        self,
        left_gdf: gpd.GeoDataFrame,
        right_gdf: gpd.GeoDataFrame,
        how: str = 'inner',
        predicate: str = 'intersects'
    ) -> gpd.GeoDataFrame:
        """
        Perform spatial join between two GeoDataFrames.

        Args:
            left_gdf: Left GeoDataFrame
            right_gdf: Right GeoDataFrame
            how: Join type ('inner', 'left', 'right', 'outer')
            predicate: Spatial predicate ('intersects', 'contains', 'within', etc.)

        Returns:
            Joined GeoDataFrame
        """
        # Ensure same CRS
        if left_gdf.crs != right_gdf.crs:
            logger.info("Mismatched CRS detected. Transforming right_gdf to left_gdf CRS")
            right_gdf = right_gdf.to_crs(left_gdf.crs)

        try:
            result = gpd.sjoin(left_gdf, right_gdf, how=how, predicate=predicate)
            # Clean up index column added by sjoin
            if 'index_right' in result.columns:
                result = result.drop(columns=['index_right'])
            return result
        except Exception as e:
            raise GISMapperError(f"Spatial join failed: {str(e)}")

    # =========================================================================
    # Raster-Vector Integration
    # =========================================================================

    def rasterize(
        self,
        gdf: gpd.GeoDataFrame,
        target_raster: rasterio.DatasetReader,
        value_column: Optional[str] = None,
        fill_value: float = 0,
        all_touched: bool = False
    ) -> np.ndarray:
        """
        Rasterize vector geometries to match a target raster.

        Args:
            gdf: GeoDataFrame to rasterize
            target_raster: Target raster dataset for shape/transform
            value_column: Column to use as raster values (None for 1)
            fill_value: Value for non-geometry pixels
            all_touched: Include all pixels touched by geometry

        Returns:
            Numpy array of rasterized values
        """
        # Ensure CRS match
        if gdf.crs != target_raster.crs:
            logger.info("Transforming GeoDataFrame to match raster CRS")
            gdf = gdf.to_crs(target_raster.crs)

        # Prepare features
        if value_column:
            features = (
                (mapping(geometry), value)
                for geometry, value in zip(gdf.geometry, gdf[value_column])
            )
        else:
            features = ((mapping(geometry), 1) for geometry in gdf.geometry)

        # Rasterize
        out_shape = (target_raster.height, target_raster.width)
        result = rasterize(
            features,
            out_shape=out_shape,
            transform=target_raster.transform,
            fill=fill_value,
            all_touched=all_touched
        )

        return result

    def extract_raster_values(
        self,
        gdf: gpd.GeoDataFrame,
        raster_file: Union[str, Path],
        band: int = 1
    ) -> gpd.GeoDataFrame:
        """
        Extract raster values at vector geometry locations.

        Args:
            gdf: GeoDataFrame with point or polygon geometries
            raster_file: Path to raster file
            band: Raster band number (1-indexed)

        Returns:
            GeoDataFrame with added raster value column
        """
        from rasterio.sample import sample_gen

        raster_data, dataset = self.load_raster(raster_file)

        # Ensure CRS match
        if gdf.crs != dataset.crs:
            logger.info("Transforming GeoDataFrame to match raster CRS")
            gdf = gdf.to_crs(dataset.crs)

        # Extract values
        gdf = gdf.copy()
        gdf['raster_value'] = None

        if gdf.crs is None:
            raise GISMapperError("GeoDataFrame must have a CRS for raster extraction")

        # Sample raster at geometry locations
        for idx, row in gdf.iterrows():
            geom = row.geometry
            if geom.is_empty:
                continue

            if geom.geom_type == 'Point':
                # Point sampling
                x, y = geom.x, geom.y
                coords = [(x, y)]
            else:
                # Polygon: sample centroid
                coords = [geom.centroid.coords[0]]

            values = list(sample_gen(dataset, coords, indexes=[band]))
            if values and values[0][0] is not None:
                gdf.at[idx, 'raster_value'] = values[0][0]

        return gdf

    # =========================================================================
    # Risk Mapping Operations
    # =========================================================================

    def create_risk_map(
        self,
        risk_gdf: gpd.GeoDataFrame,
        base_raster: Optional[Union[str, Path]] = None,
        risk_column: str = 'risk_score',
        output_path: Optional[Path] = None
    ) -> gpd.GeoDataFrame:
        """
        Create a risk map from spatial risk data.

        Args:
            risk_gdf: GeoDataFrame with risk scores
            base_raster: Optional base raster for context
            risk_column: Column name containing risk scores
            output_path: Optional path to save the risk map

        Returns:
            Risk-scored GeoDataFrame with metadata
        """
        # Validate input
        if risk_column not in risk_gdf.columns:
            raise GISMapperError(f"Risk column '{risk_column}' not found in GeoDataFrame")

        # Add risk metadata
        risk_map = risk_gdf.copy()
        risk_map['risk_category'] = pd.cut(
            risk_map[risk_column],
            bins=[0, 0.25, 0.5, 0.75, 1.0],
            labels=['low', 'moderate', 'high', 'critical']
        )

        # Calculate summary statistics
        risk_stats = {
            'mean_risk': risk_map[risk_column].mean(),
            'std_risk': risk_map[risk_column].std(),
            'max_risk': risk_map[risk_column].max(),
            'min_risk': risk_map[risk_column].min(),
            'area_at_risk': risk_map[risk_column].sum()
        }
        risk_map.attrs['risk_stats'] = risk_stats

        # Save if output path provided
        if output_path:
            self.save_vector(risk_map, output_path)

        logger.info(f"Risk map created with {len(risk_map)} features")
        return risk_map

    # =========================================================================
    # Export Operations
    # =========================================================================

    def save_vector(
        self,
        gdf: gpd.GeoDataFrame,
        output_path: Union[str, Path],
        driver: Optional[str] = None
    ) -> Path:
        """
        Save GeoDataFrame to a file.

        Args:
            gdf: GeoDataFrame to save
            output_path: Output file path
            driver: Output format driver (auto-detected if None)

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine driver from extension
        if driver is None:
            ext = output_path.suffix.lower()
            driver_map = {
                '.shp': 'ESRI Shapefile',
                '.geojson': 'GeoJSON',
                '.json': 'GeoJSON',
                '.gpkg': 'GPKG',
                '.gpx': 'GPX',
                '.kml': 'KML'
            }
            driver = driver_map.get(ext, 'GeoJSON')

        logger.info(f"Saving vector data to: {output_path} (driver: {driver})")

        # Clean geometry for export
        gdf_clean = gdf.copy()
        if hasattr(gdf_clean.geometry, 'make_valid'):
            gdf_clean.geometry = gdf_clean.geometry.make_valid()

        gdf_clean.to_file(str(output_path), driver=driver)
        return output_path

    def save_raster(
        self,
        raster_data: np.ndarray,
        output_path: Union[str, Path],
        template_raster: Optional[rasterio.DatasetReader] = None,
        crs: Optional[str] = None,
        transform: Optional[Any] = None
    ) -> Path:
        """
        Save raster data to a GeoTIFF file.

        Args:
            raster_data: Numpy array of raster values
            output_path: Output file path
            template_raster: Template raster for metadata
            crs: CRS to use (required if template not provided)
            transform: Transform to use (required if template not provided)

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get metadata from template or parameters
        if template_raster:
            profile = template_raster.profile
        else:
            if crs is None or transform is None:
                raise GISMapperError("Either template_raster or (crs, transform) required")
            profile = {
                'driver': 'GTiff',
                'height': raster_data.shape[0],
                'width': raster_data.shape[1],
                'count': 1,
                'dtype': raster_data.dtype,
                'crs': crs,
                'transform': transform
            }

        logger.info(f"Saving raster data to: {output_path}")

        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(raster_data, 1)

        return output_path

    # =========================================================================
    # Utility Operations
    # =========================================================================

    def get_bounds(self, gdf: gpd.GeoDataFrame) -> Dict[str, float]:
        """
        Get bounding box of a GeoDataFrame.

        Args:
            gdf: GeoDataFrame to inspect

        Returns:
            Dictionary with minx, miny, maxx, maxy
        """
        bounds = gdf.total_bounds
        return {
            'minx': float(bounds[0]),
            'miny': float(bounds[1]),
            'maxx': float(bounds[2]),
            'maxy': float(bounds[3])
        }

    def calculate_area(self, gdf: gpd.GeoDataFrame, units: str = 'hectares') -> gpd.GeoDataFrame:
        """
        Calculate area for each geometry.

        Args:
            gdf: GeoDataFrame with polygon geometries
            units: 'hectares', 'square_meters', or 'square_kilometers'

        Returns:
            GeoDataFrame with added 'area' column
        """
        gdf = gdf.copy()

        # Ensure projected CRS for area calculation
        if gdf.crs and gdf.crs.is_geographic:
            gdf = self.transform_crs(gdf, 'EPSG:3857')

        gdf['area_sqm'] = gdf.geometry.area

        # Convert to requested units
        if units == 'hectares':
            gdf['area'] = gdf['area_sqm'] / 10000
        elif units == 'square_kilometers':
            gdf['area'] = gdf['area_sqm'] / 1000000
        else:
            gdf['area'] = gdf['area_sqm']

        return gdf

    def clear_cache(self) -> int:
        """
        Clear all cached spatial data.

        Returns:
            Number of cache entries cleared
        """
        count = self.cache_manager.clear()
        self._loaded_layers.clear()
        self._loaded_rasters.clear()
        logger.info(f"Cleared {count} cache entries")
        return count

    def get_statistics(
        self,
        gdf: gpd.GeoDataFrame,
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics for a GeoDataFrame.

        Args:
            gdf: GeoDataFrame to analyze
            columns: Columns to include in statistics (None for all numeric)

        Returns:
            Dictionary with statistics
        """
        stats = {
            'feature_count': len(gdf),
            'crs': str(gdf.crs) if gdf.crs else None,
            'bounds': self.get_bounds(gdf),
            'geometry_types': gdf.geometry.type.value_counts().to_dict()
        }

        # Add column statistics
        if columns is None:
            numeric_cols = gdf.select_dtypes(include=[np.number]).columns
        else:
            numeric_cols = [c for c in columns if c in gdf.columns]

        for col in numeric_cols:
            stats[f'{col}_stats'] = {
                'mean': float(gdf[col].mean()),
                'std': float(gdf[col].std()),
                'min': float(gdf[col].min()),
                'max': float(gdf[col].max())
            }

        return stats


# =========================================================================
# Factory Function
# =========================================================================

def create_gis_mapper(cache_dir: Optional[Path] = None) -> GISMapper:
    """
    Factory function to create a GISMapper instance.

    Args:
        cache_dir: Optional cache directory

    Returns:
        Configured GISMapper instance
    """
    return GISMapper(cache_dir=cache_dir)