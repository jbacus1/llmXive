"""
Crop Yield Prediction Model

User Story 3: CSA Recommendation Engine
Purpose: Predict crop yields based on climate, soil, and management data

This model integrates with:
- US1: Data collection (climate, soil, survey data)
- US2: Climate risk assessment outputs
- US3: Recommendation engine (T036)

Schema: contracts/dataset.schema.yaml (input)
        contracts/output.schema.yaml (output)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

from src.config.constants import Constants
from src.data.cache import CacheManager

logger = logging.getLogger(__name__)

# =============================================================================
# Data Classes for Type Safety
# =============================================================================

@dataclass
class CropYieldInput:
    """
    Input schema for crop yield prediction.
    
    Matches data-model.md requirements for US3 integration.
    """
    climate_data: Dict[str, float]  # temperature, precipitation, etc.
    soil_data: Dict[str, float]     # pH, nitrogen, phosphorus, etc.
    management_data: Dict[str, float]  # irrigation, fertilizer, etc.
    crop_type: str
    region: str
    historical_yield: Optional[float] = None
    season: Optional[str] = None
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert input to DataFrame for model processing."""
        features = {
            **self.climate_data,
            **self.soil_data,
            **self.management_data,
            'crop_type_encoded': self._encode_crop_type(),
            'historical_yield': self.historical_yield or 0,
        }
        return pd.DataFrame([features])
    
    def _encode_crop_type(self) -> int:
        """Encode crop type as integer for model compatibility."""
        crop_types = Constants.CROP_TYPES
        return crop_types.index(self.crop_type) if self.crop_type in crop_types else -1
    
    def validate(self) -> List[str]:
        """Validate input data against schema requirements."""
        errors = []
        
        required_climate = ['temperature_avg', 'precipitation_total']
        for key in required_climate:
            if key not in self.climate_data:
                errors.append(f"Missing required climate field: {key}")
        
        required_soil = ['ph', 'nitrogen']
        for key in required_soil:
            if key not in self.soil_data:
                errors.append(f"Missing required soil field: {key}")
        
        if self.crop_type not in Constants.CROP_TYPES:
            errors.append(f"Invalid crop_type: {self.crop_type}")
        
        return errors

@dataclass
class CropYieldOutput:
    """
    Output schema for crop yield prediction.
    
    Matches contracts/output.schema.yaml for US3 integration.
    """
    predicted_yield: float  # kg/hectare
    uncertainty_range: tuple  # (lower, upper)
    confidence: float  # 0-1
    contributing_factors: Dict[str, float]
    model_version: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'predicted_yield': self.predicted_yield,
            'uncertainty_range': list(self.uncertainty_range),
            'confidence': self.confidence,
            'contributing_factors': self.contributing_factors,
            'model_version': self.model_version,
        }

# =============================================================================
# Crop Yield Model
# =============================================================================

class CropYieldModel:
    """
    Crop yield prediction model using ensemble methods.
    
    Implements climate-smart agricultural yield prediction per US3 requirements.
    Integrates climate risk assessment (US2) and feeds into recommendation engine (T036).
    
    Model Architecture:
    - Primary: RandomForestRegressor for non-linear relationships
    - Fallback: Ridge regression for interpretability
    - Uncertainty estimation via prediction intervals
    
    Attributes:
        model: Trained RandomForestRegressor
        scaler: StandardScaler for feature normalization
        is_trained: Whether model has been trained
        model_version: Version string for tracking
    """
    
    MODEL_VERSION = "1.0.0"
    DEFAULT_SEED = 42
    
    def __init__(self, use_cache: bool = True):
        """
        Initialize the crop yield model.
        
        Args:
            use_cache: Whether to use SQLite cache for predictions
        """
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=self.DEFAULT_SEED,
            n_jobs=-1
        )
        self.ridge_model = Ridge(alpha=1.0, random_state=self.DEFAULT_SEED)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.cache = CacheManager() if use_cache else None
        
        # Feature names (order matters for consistency)
        self.feature_names = [
            'temperature_avg', 'temperature_max', 'temperature_min',
            'precipitation_total', 'precipitation_days',
            'humidity_avg', 'wind_speed_avg',
            'ph', 'nitrogen', 'phosphorus', 'potassium',
            'organic_matter', 'soil_moisture',
            'irrigation_rate', 'fertilizer_n', 'fertilizer_p', 'fertilizer_k',
            'crop_type_encoded', 'historical_yield'
        ]
        
        logger.info(f"CropYieldModel initialized (version {self.MODEL_VERSION})")
    
    def train(
        self,
        training_data: pd.DataFrame,
        target_column: str = 'actual_yield',
        test_size: float = 0.2,
        validate: bool = True
    ) -> Dict:
        """
        Train the crop yield model on historical data.
        
        Args:
            training_data: DataFrame with features and target yield
            target_column: Name of the yield column
            test_size: Proportion for test split
            validate: Whether to validate training metrics
        
        Returns:
            Dictionary with training metrics and status
        """
        logger.info(f"Training crop yield model on {len(training_data)} samples")
        
        # Separate features and target
        X = training_data[self.feature_names].copy()
        y = training_data[target_column].copy()
        
        # Handle missing values
        X = X.fillna(X.median())
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.DEFAULT_SEED
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train primary model
        self.model.fit(X_train_scaled, y_train)
        
        # Train fallback model
        self.ridge_model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred_rf = self.model.predict(X_test_scaled)
        y_pred_ridge = self.ridge_model.predict(X_test_scaled)
        
        metrics = {
            'rf_mse': float(mean_squared_error(y_test, y_pred_rf)),
            'rf_r2': float(r2_score(y_test, y_pred_rf)),
            'ridge_mse': float(mean_squared_error(y_test, y_pred_ridge)),
            'ridge_r2': float(r2_score(y_test, y_pred_ridge)),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
        }
        
        # Select best model based on R2
        if metrics['rf_r2'] > metrics['ridge_r2']:
            self._best_model = 'random_forest'
        else:
            self._best_model = 'ridge'
        
        metrics['best_model'] = self._best_model
        
        self.is_trained = True
        
        logger.info(
            f"Training complete - Best model: {self._best_model}, "
            f"R2: {metrics[f'{self._best_model}_r2']:.3f}"
        )
        
        return metrics
    
    def predict(
        self,
        inputs: Union[CropYieldInput, List[CropYieldInput]],
        use_cache: bool = True
    ) -> Union[CropYieldOutput, List[CropYieldOutput]]:
        """
        Predict crop yield for given inputs.
        
        Args:
            inputs: Single or list of CropYieldInput objects
            use_cache: Whether to check cache first
        
        Returns:
            Single or list of CropYieldOutput objects
        
        Raises:
            ValueError: If model not trained or input invalid
        """
        if not self.is_trained:
            raise ValueError(
                "Model not trained. Call train() with historical data first."
            )
        
        # Handle single input
        if isinstance(inputs, CropYieldInput):
            return self._predict_single(inputs, use_cache)
        
        # Handle batch
        return [self._predict_single(inp, use_cache) for inp in inputs]
    
    def _predict_single(
        self,
        input_obj: CropYieldInput,
        use_cache: bool
    ) -> CropYieldOutput:
        """Predict yield for a single input."""
        # Validate input
        errors = input_obj.validate()
        if errors:
            raise ValueError(f"Invalid input: {errors}")
        
        # Check cache
        cache_key = f"yield_{input_obj.crop_type}_{input_obj.region}"
        if use_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return CropYieldOutput(**cached)
        
        # Prepare features
        df = input_obj.to_dataframe()
        X = df[self.feature_names].fillna(df[self.feature_names].median())
        X_scaled = self.scaler.transform(X)
        
        # Get predictions from both models
        rf_pred = self.model.predict(X_scaled)[0]
        ridge_pred = self.ridge_model.predict(X_scaled)[0]
        
        # Ensemble prediction
        if self._best_model == 'random_forest':
            predicted_yield = rf_pred
            confidence = 0.85
        else:
            predicted_yield = ridge_pred
            confidence = 0.75
        
        # Uncertainty estimation (simplified prediction interval)
        uncertainty = abs(predicted_yield * 0.15)  # 15% uncertainty
        uncertainty_range = (
            max(0, predicted_yield - uncertainty),
            predicted_yield + uncertainty
        )
        
        # Feature importance for contributing factors
        importances = self.model.feature_importances_
        contributing_factors = {
            name: float(imp)
            for name, imp in zip(self.feature_names, importances)
            if imp > 0
        }
        
        # Create output
        output = CropYieldOutput(
            predicted_yield=float(predicted_yield),
            uncertainty_range=uncertainty_range,
            confidence=float(confidence),
            contributing_factors=contributing_factors,
            model_version=self.MODEL_VERSION
        )
        
        # Cache result
        if use_cache and self.cache:
            self.cache.set(cache_key, output.to_dict())
        
        logger.debug(
            f"Predicted yield: {output.predicted_yield:.2f} kg/ha "
            f"(confidence: {output.confidence})"
        )
        
        return output
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores from the model.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        return {
            name: float(imp)
            for name, imp in zip(self.feature_names, self.model.feature_importances_)
        }
    
    def export_model(self, path: str) -> None:
        """
        Export trained model to disk.
        
        Args:
            path: File path for model serialization
        """
        import joblib
        
        model_data = {
            'model': self.model,
            'ridge_model': self.ridge_model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'model_version': self.MODEL_VERSION
        }
        
        joblib.dump(model_data, path)
        logger.info(f"Model exported to {path}")
    
    def import_model(self, path: str) -> None:
        """
        Load trained model from disk.
        
        Args:
            path: File path for model deserialization
        """
        import joblib
        
        model_data = joblib.load(path)
        self.model = model_data['model']
        self.ridge_model = model_data['ridge_model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.is_trained = True
        
        logger.info(f"Model imported from {path}")