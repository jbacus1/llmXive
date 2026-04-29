"""
Survey Data Preprocessing Module

Preprocesses survey data collected from agricultural communities.
Handles data cleaning, transformation, normalization, and validation.

Part of User Story 1: Data Collection & Ingestion (MVP)
"""

import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime

# Local imports
from src.config.schemas import validate_schema, SurveyDataSchema
from src.data.cache import DataCache
from src.config.constants import DATA_DIR, VALIDATION_STRICT

# Configure logging
logger = logging.getLogger(__name__)

# Survey data column standards
SURVEY_REQUIRED_COLUMNS = [
    'survey_id',
    'community_id',
    'respondent_id',
    'crop_type',
    'farm_size_acres',
    'yield_kg_per_hectare',
    'water_source',
    'irrigation_method',
    'fertilizer_type',
    'collection_date'
]

SURVEY_NUMERIC_COLUMNS = [
    'farm_size_acres',
    'yield_kg_per_hectare',
    'family_size',
    'annual_income_usd',
    'years_farming'
]

SURVEY_CATEGORICAL_COLUMNS = [
    'crop_type',
    'water_source',
    'irrigation_method',
    'fertilizer_type',
    'soil_type',
    'climate_zone'
]

SURVEY_DATE_COLUMNS = [
    'collection_date',
    'last_harvest_date',
    'planting_date'
]

# Valid values for categorical columns
VALID_CROP_TYPES = [
    'maize', 'wheat', 'rice', 'cassava', 'yams',
    'beans', 'sorghum', 'millet', 'potato', 'vegetables',
    'other'
]

VALID_WATER_SOURCES = [
    'rain', 'river', 'lake', 'groundwater', 'irrigation',
    'pond', 'reservoir', 'other'
]

VALID_IRRIGATION_METHODS = [
    'none', 'drip', 'sprinkler', 'flood', 'furrow',
    'center_pivot', 'manual', 'other'
]

VALID_FERTILIZER_TYPES = [
    'none', 'organic', 'chemical', 'mixed', 'biofertilizer', 'other'
]

# Default values for missing numeric data
NUMERIC_DEFAULTS = {
    'farm_size_acres': 0.0,
    'yield_kg_per_hectare': 0.0,
    'family_size': 1,
    'annual_income_usd': 0.0,
    'years_farming': 0
}

class SurveyProcessor:
    """
    Preprocesses survey data for climate-smart agriculture analysis.
    
    Responsibilities:
    - Load and validate raw survey data
    - Clean and standardize data values
    - Handle missing values with appropriate strategies
    - Normalize and transform data for downstream analysis
    - Cache processed results for efficiency
    """
    
    def __init__(
        self,
        cache_enabled: bool = True,
        strict_validation: bool = VALIDATION_STRICT
    ):
        """
        Initialize the survey processor.
        
        Args:
            cache_enabled: Whether to use the caching layer
            strict_validation: Whether to fail on validation errors
        """
        self.cache = DataCache() if cache_enabled else None
        self.strict_validation = strict_validation
        self._processing_stats = {
            'records_processed': 0,
            'records_cleaned': 0,
            'records_dropped': 0,
            'missing_values_handled': 0,
            'validation_errors': 0
        }
    
    def load_survey_data(
        self,
        file_path: str | Path,
        file_format: str = 'csv'
    ) -> pd.DataFrame:
        """
        Load survey data from a file.
        
        Args:
            file_path: Path to the survey data file
            file_format: Format of the file (csv, json, parquet)
        
        Returns:
            Loaded DataFrame with survey data
        
        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file format is unsupported
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"Survey data file not found: {file_path}")
            raise FileNotFoundError(f"Survey data file not found: {file_path}")
        
        logger.info(f"Loading survey data from {file_path}")
        
        try:
            if file_format.lower() == 'csv':
                df = pd.read_csv(file_path)
            elif file_format.lower() == 'json':
                df = pd.read_json(file_path)
            elif file_format.lower() == 'parquet':
                df = pd.read_parquet(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
        
            logger.info(f"Loaded {len(df)} records from {file_path}")
            return df
        
        except Exception as e:
            logger.error(f"Failed to load survey data: {e}")
            raise
    
    def validate_survey_schema(
        self,
        df: pd.DataFrame,
        raise_on_error: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        Validate survey data against expected schema.
        
        Args:
            df: DataFrame to validate
            raise_on_error: Whether to raise on validation failure
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Check required columns
        missing_columns = set(SURVEY_REQUIRED_COLUMNS) - set(df.columns)
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
            logger.warning(f"Missing columns in survey data: {missing_columns}")
        
        # Check data types for numeric columns
        for col in SURVEY_NUMERIC_COLUMNS:
            if col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    errors.append(f"Column '{col}' should be numeric")
        
        # Check date columns
        for col in SURVEY_DATE_COLUMNS:
            if col in df.columns:
                try:
                    pd.to_datetime(df[col])
                except (ValueError, TypeError):
                    errors.append(f"Column '{col}' should be parseable as date")
        
        # Validate against schema if schema module is available
        try:
            schema_valid, schema_errors = validate_schema(
                df.to_dict(orient='records'),
                SurveyDataSchema()
            )
            if not schema_valid:
                errors.extend(schema_errors)
        except Exception as e:
            logger.warning(f"Schema validation skipped: {e}")
        
        is_valid = len(errors) == 0
        
        if not is_valid and raise_on_error:
            logger.error(f"Survey data validation failed: {errors}")
            raise ValueError(f"Survey data validation failed: {errors}")
        
        if errors:
            logger.warning(f"Survey data validation warnings: {errors}")
        
        return is_valid, errors
    
    def clean_survey_data(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Clean survey data by standardizing values and removing invalid entries.
        
        Args:
            df: Raw survey DataFrame
        
        Returns:
            Cleaned DataFrame
        """
        logger.info("Starting survey data cleaning")
        df_clean = df.copy()
        
        # Trim whitespace from string columns
        for col in df_clean.select_dtypes(include=['object']).columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()
        
        # Standardize categorical values
        df_clean = self._standardize_categorical_columns(df_clean)
        
        # Remove duplicate survey IDs
        if 'survey_id' in df_clean.columns:
            duplicates = df_clean['survey_id'].duplicated().sum()
            if duplicates > 0:
                logger.warning(f"Removing {duplicates} duplicate survey IDs")
                df_clean = df_clean.drop_duplicates(subset=['survey_id'])
                self._processing_stats['records_dropped'] += duplicates
        
        # Filter out records with missing required fields
        required_present = df_clean[SURVEY_REQUIRED_COLUMNS].notna().all(axis=1)
        missing_required = (~required_present).sum()
        if missing_required > 0:
            logger.warning(f"Removing {missing_required} records with missing required fields")
            df_clean = df_clean[required_present]
            self._processing_stats['records_dropped'] += missing_required
        
        logger.info(f"Data cleaning complete. {len(df_clean)} records remaining")
        return df_clean
    
    def _standardize_categorical_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize categorical column values.
        
        Args:
            df: DataFrame with categorical columns
        
        Returns:
            DataFrame with standardized categorical values
        """
        df_std = df.copy()
        
        # Crop type standardization
        if 'crop_type' in df_std.columns:
            df_std['crop_type'] = df_std['crop_type'].str.lower()
            valid_mask = df_std['crop_type'].isin(VALID_CROP_TYPES)
            invalid_mask = ~valid_mask
            if invalid_mask.any():
                logger.warning(f"Standardizing {invalid_mask.sum()} non-standard crop types to 'other'")
                df_std.loc[invalid_mask, 'crop_type'] = 'other'
        
        # Water source standardization
        if 'water_source' in df_std.columns:
            df_std['water_source'] = df_std['water_source'].str.lower()
            valid_mask = df_std['water_source'].isin(VALID_WATER_SOURCES)
            invalid_mask = ~valid_mask
            if invalid_mask.any():
                logger.warning(f"Standardizing {invalid_mask.sum()} non-standard water sources to 'other'")
                df_std.loc[invalid_mask, 'water_source'] = 'other'
        
        # Irrigation method standardization
        if 'irrigation_method' in df_std.columns:
            df_std['irrigation_method'] = df_std['irrigation_method'].str.lower()
            valid_mask = df_std['irrigation_method'].isin(VALID_IRRIGATION_METHODS)
            invalid_mask = ~valid_mask
            if invalid_mask.any():
                logger.warning(f"Standardizing {invalid_mask.sum()} non-standard irrigation methods to 'other'")
                df_std.loc[invalid_mask, 'irrigation_method'] = 'other'
        
        # Fertilizer type standardization
        if 'fertilizer_type' in df_std.columns:
            df_std['fertilizer_type'] = df_std['fertilizer_type'].str.lower()
            valid_mask = df_std['fertilizer_type'].isin(VALID_FERTILIZER_TYPES)
            invalid_mask = ~valid_mask
            if invalid_mask.any():
                logger.warning(f"Standardizing {invalid_mask.sum()} non-standard fertilizer types to 'other'")
                df_std.loc[invalid_mask, 'fertilizer_type'] = 'other'
        
        return df_std
    
    def handle_missing_values(
        self,
        df: pd.DataFrame,
        strategy: str = 'default'
    ) -> pd.DataFrame:
        """
        Handle missing values in survey data.
        
        Args:
            df: DataFrame with potential missing values
            strategy: Handling strategy ('default', 'drop', 'impute', 'median')
        
        Returns:
            DataFrame with missing values handled
        """
        logger.info(f"Handling missing values with strategy: {strategy}")
        df_handled = df.copy()
        initial_null_count = df_handled.isnull().sum().sum()
        
        if strategy == 'drop':
            df_handled = df_handled.dropna()
        
        elif strategy == 'impute':
            # Impute numeric columns with defaults
            for col in SURVEY_NUMERIC_COLUMNS:
                if col in df_handled.columns:
                    null_count = df_handled[col].isnull().sum()
                    if null_count > 0:
                        df_handled[col] = df_handled[col].fillna(NUMERIC_DEFAULTS.get(col, 0))
                        self._processing_stats['missing_values_handled'] += null_count
            
            # Impute categorical columns with 'unknown'
            for col in SURVEY_CATEGORICAL_COLUMNS:
                if col in df_handled.columns:
                    null_count = df_handled[col].isnull().sum()
                    if null_count > 0:
                        df_handled[col] = df_handled[col].fillna('unknown')
                        self._processing_stats['missing_values_handled'] += null_count
        
        elif strategy == 'median':
            # Impute numeric columns with median values
            for col in SURVEY_NUMERIC_COLUMNS:
                if col in df_handled.columns:
                    null_count = df_handled[col].isnull().sum()
                    if null_count > 0:
                        median_val = df_handled[col].median()
                        df_handled[col] = df_handled[col].fillna(median_val)
                        self._processing_stats['missing_values_handled'] += null_count
        
        else:  # default strategy
            for col in SURVEY_NUMERIC_COLUMNS:
                if col in df_handled.columns:
                    null_count = df_handled[col].isnull().sum()
                    if null_count > 0:
                        df_handled[col] = df_handled[col].fillna(NUMERIC_DEFAULTS.get(col, 0))
                        self._processing_stats['missing_values_handled'] += null_count
        
        final_null_count = df_handled.isnull().sum().sum()
        logger.info(f"Missing values handled: {initial_null_count - final_null_count}")
        
        return df_handled
    
    def normalize_survey_data(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Normalize numeric columns in survey data.
        
        Args:
            df: DataFrame to normalize
            columns: Specific columns to normalize (None = all numeric)
        
        Returns:
            DataFrame with normalized values
        """
        logger.info("Normalizing survey data")
        df_norm = df.copy()
        
        # Determine columns to normalize
        if columns is None:
            columns = SURVEY_NUMERIC_COLUMNS
        
        for col in columns:
            if col not in df_norm.columns:
                continue
            
            if not pd.api.types.is_numeric_dtype(df_norm[col]):
                continue
            
            # Min-max normalization (0-1 scale)
            col_min = df_norm[col].min()
            col_max = df_norm[col].max()
            
            if col_max > col_min:
                df_norm[f'{col}_normalized'] = (df_norm[col] - col_min) / (col_max - col_min)
            else:
                df_norm[f'{col}_normalized'] = 0.0
            
            logger.debug(f"Normalized column '{col}' (min={col_min}, max={col_max})")
        
        return df_norm
    
    def preprocess_survey_data(
        self,
        file_path: str | Path,
        file_format: str = 'csv',
        missing_value_strategy: str = 'default',
        normalize: bool = True,
        cache_key: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Complete preprocessing pipeline for survey data.
        
        Args:
            file_path: Path to raw survey data file
            file_format: Format of input file
            missing_value_strategy: Strategy for handling missing values
            normalize: Whether to normalize numeric columns
            cache_key: Optional cache key for processed results
        
        Returns:
            Preprocessed DataFrame ready for analysis
        """
        # Check cache first
        if self.cache and cache_key:
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Loaded preprocessed survey data from cache: {cache_key}")
                return cached_result
        
        logger.info(f"Starting full preprocessing pipeline for {file_path}")
        start_time = datetime.now()
        
        # Step 1: Load data
        df = self.load_survey_data(file_path, file_format)
        self._processing_stats['records_processed'] = len(df)
        
        # Step 2: Validate schema
        self.validate_survey_schema(df, raise_on_error=self.strict_validation)
        
        # Step 3: Clean data
        df = self.clean_survey_data(df)
        self._processing_stats['records_cleaned'] = len(df)
        
        # Step 4: Handle missing values
        df = self.handle_missing_values(df, strategy=missing_value_strategy)
        
        # Step 5: Normalize if requested
        if normalize:
            df = self.normalize_survey_data(df)
        
        # Step 6: Add processing metadata
        df['processed_at'] = datetime.now().isoformat()
        df['processor_version'] = '1.0.0'
        
        # Cache results
        if self.cache and cache_key:
            self.cache.set(cache_key, df)
            logger.info(f"Cached preprocessed survey data: {cache_key}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Survey data preprocessing complete in {elapsed:.2f} seconds")
        logger.info(f"Processing statistics: {self._processing_stats}")
        
        return df
    
    def get_processing_stats(self) -> Dict[str, int]:
        """
        Get statistics from the last processing run.
        
        Returns:
            Dictionary of processing statistics
        """
        return self._processing_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self._processing_stats = {
            'records_processed': 0,
            'records_cleaned': 0,
            'records_dropped': 0,
            'missing_values_handled': 0,
            'validation_errors': 0
        }


# Convenience function for quick preprocessing
def preprocess_survey(
    file_path: str | Path,
    file_format: str = 'csv',
    missing_value_strategy: str = 'default'
) -> pd.DataFrame:
    """
    Quick preprocessing function for survey data.
    
    Args:
        file_path: Path to survey data file
        file_format: Format of input file
        missing_value_strategy: Strategy for missing values
    
    Returns:
        Preprocessed DataFrame
    """
    processor = SurveyProcessor()
    return processor.preprocess_survey_data(
        file_path,
        file_format=file_format,
        missing_value_strategy=missing_value_strategy
    )