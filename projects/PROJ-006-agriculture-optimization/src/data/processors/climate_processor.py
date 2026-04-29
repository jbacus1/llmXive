"""
Climate Data Preprocessor Module

This module handles preprocessing of raw climate data collected from
OpenWeatherMap, USGS EarthExplorer, and other climate data sources.

Features:
  - Schema validation against contracts/dataset.schema.yaml
  - Missing value handling and imputation
  - Temporal aggregation and normalization
  - Spatial coordinate standardization
  - Caching for repeated processing

Dependencies:
  - pandas: Data manipulation
  - numpy: Numerical operations
  - logging: Event tracking
  - src/config/constants: Configuration management
  - src/config/schemas: Schema validation
  - src/data/cache: SQLite caching layer
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd
from pydantic import ValidationError

from src.config.constants import DATA_DIR, PROCESSED_DIR, RAW_DIR
from src.config.schemas import ClimateDataSchema, validate_climate_data
from src.data.cache import DataCache

# Configure logger
logger = logging.getLogger(__name__)


class ClimateProcessor:
    """
    Preprocess raw climate data for downstream analysis.

    Handles data cleaning, validation, transformation, and caching
    for climate datasets collected from various sources.
    """

    def __init__(self, cache_enabled: bool = True):
        """
        Initialize the climate processor.

        Args:
            cache_enabled: Whether to use the SQLite caching layer
        """
        self.cache = DataCache() if cache_enabled else None
        self.raw_dir = Path(DATA_DIR) / RAW_DIR
        self.processed_dir = Path(DATA_DIR) / PROCESSED_DIR

        # Ensure output directory exists
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        # Processing configuration
        self.default_temp_unit = 'celsius'
        self.default_precip_unit = 'mm'
        self.temporal_resolution = 'daily'

        logger.info("ClimateProcessor initialized")

    def load_raw_climate_data(
        self,
        source: str,
        file_pattern: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load raw climate data from the data/raw directory.

        Args:
            source: Data source identifier (e.g., 'openweathermap', 'usgs')
            file_pattern: Optional glob pattern for file selection

        Returns:
            DataFrame containing raw climate data

        Raises:
            FileNotFoundError: If no matching files found
            ValueError: If file format is unsupported
        """
        logger.info(f"Loading raw climate data from source: {source}")

        source_dir = self.raw_dir / source
        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")

        # Find matching files
        if file_pattern:
            files = list(source_dir.glob(file_pattern))
        else:
            files = list(source_dir.glob("*"))

        if not files:
            raise FileNotFoundError(f"No files found in {source_dir}")

        logger.info(f"Found {len(files)} files for processing")

        # Load and concatenate all files
        dataframes = []
        for file_path in files:
            logger.debug(f"Loading file: {file_path}")
            df = self._load_single_file(file_path)
            if df is not None:
                df['source'] = source
                df['file_path'] = str(file_path)
                dataframes.append(df)

        if not dataframes:
            raise ValueError("No valid data loaded from files")

        combined_df = pd.concat(dataframes, ignore_index=True)
        logger.info(f"Loaded {len(combined_df)} records from {len(files)} files")

        return combined_df

    def _load_single_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """
        Load a single climate data file based on its extension.

        Args:
            file_path: Path to the data file

        Returns:
            DataFrame or None if file cannot be loaded
        """
        suffix = file_path.suffix.lower()

        try:
            if suffix in ['.csv', '.tsv']:
                sep = '\t' if suffix == '.tsv' else ','
                return pd.read_csv(file_path, sep=sep)
            elif suffix in ['.json']:
                return pd.read_json(file_path)
            elif suffix in ['.parquet']:
                return pd.read_parquet(file_path)
            elif suffix in ['.xlsx', '.xls']:
                return pd.read_excel(file_path)
            else:
                logger.warning(f"Unsupported file format: {suffix}")
                return None
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None

    def validate_schema(self, df: pd.DataFrame) -> bool:
        """
        Validate data against the climate data schema.

        Args:
            df: DataFrame to validate

        Returns:
            True if validation passes, False otherwise
        """
        logger.info("Validating data against climate schema")

        try:
            # Convert to dict for pydantic validation
            data_dict = df.to_dict(orient='records')
            validate_climate_data(data_dict)
            logger.info("Schema validation passed")
            return True
        except ValidationError as e:
            logger.error(f"Schema validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False

    def clean_data(
        self,
        df: pd.DataFrame,
        handle_missing: str = 'drop',
        fill_value: Optional[Union[int, float, str]] = None
    ) -> pd.DataFrame:
        """
        Clean climate data by handling missing values and outliers.

        Args:
            df: Input DataFrame
            handle_missing: Strategy - 'drop', 'fill', 'impute'
            fill_value: Value to use when handle_missing='fill'

        Returns:
            Cleaned DataFrame
        """
        logger.info(f"Cleaning data with missing handling strategy: {handle_missing}")

        # Make a copy to avoid modifying original
        df_clean = df.copy()

        # Identify numeric columns for cleaning
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns

        # Handle missing values
        if handle_missing == 'drop':
            df_clean = df_clean.dropna()
            logger.info(f"Dropped {len(df) - len(df_clean)} rows with missing values")

        elif handle_missing == 'fill':
            if fill_value is None:
                # Use column-specific defaults
                fill_value = {col: 0 for col in numeric_cols}
            df_clean = df_clean.fillna(fill_value)
            logger.info(f"Filled missing values with {fill_value}")

        elif handle_missing == 'impute':
            for col in numeric_cols:
                df_clean[col] = df_clean[col].fillna(df_clean[col].median())
            logger.info("Imputed missing values with column medians")

        # Remove duplicates
        before_count = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        logger.info(f"Removed {before_count - len(df_clean)} duplicate rows")

        # Remove outliers (IQR method for numeric columns)
        df_clean = self._remove_outliers(df_clean, numeric_cols)

        logger.info(f"Data cleaning complete. Final record count: {len(df_clean)}")
        return df_clean

    def _remove_outliers(
        self,
        df: pd.DataFrame,
        columns: List[str],
        iqr_multiplier: float = 3.0
    ) -> pd.DataFrame:
        """
        Remove outliers using the IQR method.

        Args:
            df: Input DataFrame
            columns: List of column names to check
            iqr_multiplier: Multiplier for IQR bounds

        Returns:
            DataFrame with outliers removed
        """
        df_no_outliers = df.copy()

        for col in columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - iqr_multiplier * IQR
            upper_bound = Q3 + iqr_multiplier * IQR

            mask = (df[col] >= lower_bound) & (df[col] <= upper_bound)
            df_no_outliers = df_no_outliers[mask]

            logger.debug(f"Removed {sum(~mask)} outliers from {col}")

        return df_no_outliers

    def normalize_units(
        self,
        df: pd.DataFrame,
        temperature_col: Optional[str] = None,
        precipitation_col: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Normalize units across the dataset.

        Args:
            df: Input DataFrame
            temperature_col: Column name for temperature data
            precipitation_col: Column name for precipitation data

        Returns:
            DataFrame with normalized units
        """
        logger.info("Normalizing units")

        df_norm = df.copy()

        # Convert temperature to Celsius if needed
        if temperature_col and temperature_col in df_norm.columns:
            if 'unit' in df_norm.columns:
                unit_col = 'unit'
            else:
                unit_col = f'{temperature_col}_unit'

            if unit_col in df_norm.columns:
                # Convert from Fahrenheit to Celsius
                mask_f = df_norm[unit_col].str.lower() == 'fahrenheit'
                df_norm.loc[mask_f, temperature_col] = (
                    df_norm.loc[mask_f, temperature_col] - 32
                ) * 5/9
                df_norm.loc[mask_f, unit_col] = 'celsius'

        # Convert precipitation to mm if needed
        if precipitation_col and precipitation_col in df_norm.columns:
            if 'unit' in df_norm.columns:
                unit_col = 'unit'
            else:
                unit_col = f'{precipitation_col}_unit'

            if unit_col in df_norm.columns:
                # Convert from inches to mm
                mask_in = df_norm[unit_col].str.lower() == 'inch'
                df_norm.loc[mask_in, precipitation_col] = (
                    df_norm.loc[mask_in, precipitation_col] * 25.4
                )
                df_norm.loc[mask_in, unit_col] = 'mm'

        logger.info("Unit normalization complete")
        return df_norm

    def aggregate_temporal(
        self,
        df: pd.DataFrame,
        date_col: str,
        agg_level: str = 'daily'
    ) -> pd.DataFrame:
        """
        Aggregate climate data to a specified temporal resolution.

        Args:
            df: Input DataFrame
            date_col: Column name containing dates
            agg_level: Aggregation level ('daily', 'weekly', 'monthly', 'yearly')

        Returns:
            Aggregated DataFrame
        """
        logger.info(f"Aggregating data to {agg_level} resolution")

        df_agg = df.copy()

        # Ensure date column is datetime
        df_agg[date_col] = pd.to_datetime(df_agg[date_col])

        # Set date as index
        df_agg = df_agg.set_index(date_col)

        # Define aggregation mappings
        agg_mapping = {
            'daily': 'D',
            'weekly': 'W',
            'monthly': 'M',
            'yearly': 'Y'
        }

        freq = agg_mapping.get(agg_level, 'D')

        # Aggregate numeric columns
        numeric_cols = df_agg.select_dtypes(include=[np.number]).columns
        agg_funcs = {col: 'mean' for col in numeric_cols}
        agg_funcs.update({col: 'first' for col in df_agg.select_dtypes(include=['object']).columns})

        df_agg = df_agg.resample(freq).agg(agg_funcs)
        df_agg = df_agg.reset_index()

        logger.info(f"Aggregation complete. Rows: {len(df_agg)}")
        return df_agg

    def add_derived_features(
        self,
        df: pd.DataFrame,
        temperature_col: str = 'temperature',
        precipitation_col: str = 'precipitation'
    ) -> pd.DataFrame:
        """
        Add derived features for climate analysis.

        Args:
            df: Input DataFrame
            temperature_col: Temperature column name
            precipitation_col: Precipitation column name

        Returns:
            DataFrame with derived features
        """
        logger.info("Adding derived features")

        df_derived = df.copy()

        # Calculate growing degree days (GDD)
        if temperature_col in df_derived.columns:
            base_temp = 10.0  # Base temperature for most crops
            df_derived['gdd'] = np.maximum(
                df_derived[temperature_col] - base_temp,
                0
            )

        # Calculate drought index (precipitation deficit)
        if precipitation_col in df_derived.columns:
            threshold = 50.0  # mm threshold
            df_derived['drought_risk'] = (
                df_derived[precipitation_col] < threshold
            ).astype(int)

        # Calculate temperature variability
        if temperature_col in df_derived.columns:
            df_derived['temp_std'] = df_derived[temperature_col].rolling(
                window=7, min_periods=1
            ).std()

        # Add season indicator
        if 'date' in df_derived.columns or df_derived.index.name == 'date':
            df_derived['month'] = pd.to_datetime(
                df_derived.index if df_derived.index.name == 'date' else df_derived['date']
            ).month
            df_derived['season'] = df_derived['month'].apply(
                lambda m: 'winter' if m in [12, 1, 2] else
                           'spring' if m in [3, 4, 5] else
                           'summer' if m in [6, 7, 8] else 'fall'
            )

        logger.info(f"Added {len([c for c in df_derived.columns if c not in df.columns])} derived features")
        return df_derived

    def process(
        self,
        source: str,
        file_pattern: Optional[str] = None,
        handle_missing: str = 'impute',
        agg_level: str = 'daily',
        cache_key: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Complete preprocessing pipeline for climate data.

        Args:
            source: Data source identifier
            file_pattern: Optional file pattern for loading
            handle_missing: Missing value handling strategy
            agg_level: Temporal aggregation level
            cache_key: Optional cache key for this processing run

        Returns:
            Processed DataFrame
        """
        # Check cache first
        if self.cache and cache_key:
            cached_df = self.cache.get(cache_key)
            if cached_df is not None:
                logger.info(f"Returning cached result for key: {cache_key}")
                return cached_df

        logger.info(f"Starting complete preprocessing pipeline for source: {source}")

        # 1. Load raw data
        df = self.load_raw_climate_data(source, file_pattern)

        # 2. Validate schema
        if not self.validate_schema(df):
            logger.warning("Schema validation failed, proceeding with warnings")

        # 3. Clean data
        df = self.clean_data(df, handle_missing=handle_missing)

        # 4. Normalize units
        df = self.normalize_units(df)

        # 5. Aggregate temporal
        df = self.aggregate_temporal(df, date_col='date', agg_level=agg_level)

        # 6. Add derived features
        df = self.add_derived_features(df)

        # 7. Save to processed directory
        output_file = self.processed_dir / f"{source}_processed_{agg_level}.parquet"
        df.to_parquet(output_file, index=False)
        logger.info(f"Saved processed data to: {output_file}")

        # 8. Cache result
        if self.cache and cache_key:
            self.cache.set(cache_key, df)

        logger.info(f"Preprocessing pipeline complete for {source}")
        return df

    def get_processing_report(
        self,
        df: pd.DataFrame,
        source: str
    ) -> Dict:
        """
        Generate a processing report for the dataset.

        Args:
            df: Processed DataFrame
            source: Data source identifier

        Returns:
            Dictionary containing processing statistics
        """
        report = {
            'source': source,
            'record_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'numeric_stats': {},
            'missing_counts': df.isnull().sum().to_dict(),
            'processing_timestamp': datetime.now().isoformat()
        }

        # Add numeric column statistics
        for col in df.select_dtypes(include=[np.number]).columns:
            report['numeric_stats'][col] = {
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'median': float(df[col].median())
            }

        logger.info(f"Processing report generated for {source}")
        return report


def main():
    """
    Main entry point for standalone climate preprocessing.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    processor = ClimateProcessor(cache_enabled=True)

    # Example usage
    try:
        # Process a specific source
        df = processor.process(
            source='openweathermap',
            file_pattern='*.csv',
            handle_missing='impute',
            agg_level='daily',
            cache_key='openweathermap_daily_v1'
        )

        # Generate and print report
        report = processor.get_processing_report(df, 'openweathermap')
        print(f"Processed {report['record_count']} records")
        print(f"Columns: {report['columns']}")

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise


if __name__ == '__main__':
    main()