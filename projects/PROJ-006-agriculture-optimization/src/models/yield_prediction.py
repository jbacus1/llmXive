"""
Yield Prediction Model using Regression Analysis

This module implements regression-based yield prediction models
using climate and agricultural data. Part of User Story 2 -
Climate Risk Assessment.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import logging

from src.config.constants import MODEL_SAVE_PATH
from src.models.climate_risk import ClimateRiskModel

logger = logging.getLogger(__name__)


class YieldPredictionModel:
    """
    Regression-based yield prediction model for agricultural productivity assessment.
    
    Supports multiple regression algorithms and provides methods for training,
    prediction, and model evaluation.
    """
    
    def __init__(self, model_type: str = "random_forest"):
        """
        Initialize the yield prediction model.
        
        Args:
            model_type: Regression algorithm to use. Options:
                       - "linear": Linear Regression
                       - "ridge": Ridge Regression
                       - "lasso": Lasso Regression
                       - "random_forest": Random Forest Regressor
                       - "gradient_boosting": Gradient Boosting Regressor
        """
        self.model_type = model_type
        self.model = self._initialize_model(model_type)
        self.is_fitted = False
        self.feature_names: List[str] = []
        self.training_metrics: Dict[str, float] = {}
        
        logger.info(f"Initialized YieldPredictionModel with {model_type}")
    
    def _initialize_model(self, model_type: str):
        """Initialize the appropriate regression model."""
        models = {
            "linear": LinearRegression(),
            "ridge": Ridge(alpha=1.0),
            "lasso": Lasso(alpha=1.0),
            "random_forest": RandomForestRegressor(
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            ),
            "gradient_boosting": GradientBoostingRegressor(
                n_estimators=100,
                random_state=42
            )
        }
        
        if model_type not in models:
            raise ValueError(
                f"Unknown model type: {model_type}. "
                f"Available options: {list(models.keys())}"
            )
        
        return models[model_type]
    
    def _validate_input_data(self, X: pd.DataFrame, y: Optional[pd.Series] = None):
        """Validate input data for regression analysis."""
        if not isinstance(X, (pd.DataFrame, np.ndarray)):
            raise TypeError("X must be a pandas DataFrame or numpy array")
        
        if isinstance(X, pd.DataFrame):
            if X.empty:
                raise ValueError("Input DataFrame X is empty")
            
            if y is not None and len(X) != len(y):
                raise ValueError(
                    f"X and y have different lengths: {len(X)} vs {len(y)}"
                )
        
        # Check for missing values
        if isinstance(X, pd.DataFrame):
            missing = X.isnull().sum()
            if missing.any():
                logger.warning(
                    f"Input data contains missing values: {missing[missing > 0].to_dict()}"
                )
    
    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        random_state: int = 42,
        cv_folds: int = 5
    ) -> Dict[str, float]:
        """
        Train the regression model on provided data.
        
        Args:
            X: Feature matrix (climate, soil, agricultural data)
            y: Target variable (crop yield)
            test_size: Proportion of data for testing
            random_state: Random seed for reproducibility
            cv_folds: Number of cross-validation folds
            
        Returns:
            Dictionary containing training metrics
        """
        self._validate_input_data(X, y)
        
        # Store feature names
        if isinstance(X, pd.DataFrame):
            self.feature_names = list(X.columns)
        else:
            self.feature_names = [f"feature_{i}" for i in range(X.shape[1])]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        self.is_fitted = True
        
        # Calculate metrics
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        metrics = {
            "train_r2": r2_score(y_train, y_pred_train),
            "test_r2": r2_score(y_test, y_pred_test),
            "train_mse": mean_squared_error(y_train, y_pred_train),
            "test_mse": mean_squared_error(y_test, y_pred_test),
            "train_mae": mean_absolute_error(y_train, y_pred_train),
            "test_mae": mean_absolute_error(y_test, y_pred_test)
        }
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X, y,
            cv=cv_folds,
            scoring='r2'
        )
        metrics["cv_mean_r2"] = cv_scores.mean()
        metrics["cv_std_r2"] = cv_scores.std()
        
        self.training_metrics = metrics
        
        logger.info(
            f"Model trained successfully. Test R²: {metrics['test_r2']:.4f}, "
            f"CV R²: {metrics['cv_mean_r2']:.4f} ± {metrics['cv_std_r2']:.4f}"
        )
        
        return metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make yield predictions on new data.
        
        Args:
            X: Feature matrix for prediction
            
        Returns:
            Array of predicted yield values
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be trained before making predictions")
        
        self._validate_input_data(X)
        
        predictions = self.model.predict(X)
        logger.debug(f"Made {len(predictions)} predictions")
        
        return predictions
    
    def predict_with_uncertainty(
        self,
        X: pd.DataFrame,
        n_samples: int = 100
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions with uncertainty estimates (for Random Forest only).
        
        Args:
            X: Feature matrix for prediction
            n_samples: Number of bootstrap samples for uncertainty
            
        Returns:
            Tuple of (mean predictions, standard deviation)
        """
        if self.model_type not in ["random_forest", "gradient_boosting"]:
            logger.warning(
                f"Uncertainty estimation only available for tree-based models. "
                f"Current model: {self.model_type}"
            )
            predictions = self.predict(X)
            return predictions, np.zeros(len(predictions))
        
        if not self.is_fitted:
            raise RuntimeError("Model must be trained before making predictions")
        
        # Get individual tree predictions for uncertainty estimation
        if hasattr(self.model, 'estimators_'):
            all_predictions = np.array([
                tree.predict(X) for tree in self.model.estimators_
            ])
            mean_predictions = all_predictions.mean(axis=0)
            std_predictions = all_predictions.std(axis=0)
        else:
            predictions = self.predict(X)
            return predictions, np.zeros(len(predictions))
        
        logger.debug(
            f"Generated predictions with uncertainty. "
            f"Mean std: {std_predictions.mean():.4f}"
        )
        
        return mean_predictions, std_predictions
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance scores (for tree-based models).
        
        Returns:
            DataFrame with feature names and importance scores
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be trained before getting feature importance")
        
        if not hasattr(self.model, 'feature_importances_'):
            logger.warning(
                f"Feature importance not available for {self.model_type} model"
            )
            return pd.DataFrame({
                'feature': self.feature_names,
                'importance': [0.0] * len(self.feature_names)
            })
        
        importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.debug(f"Retrieved feature importance for {len(importance)} features")
        
        return importance
    
    def save(self, path: Optional[str] = None) -> str:
        """
        Save the trained model to disk.
        
        Args:
            path: Optional path to save model. Defaults to MODEL_SAVE_PATH.
            
        Returns:
            Path where model was saved
        """
        if not self.is_fitted:
            raise RuntimeError("Cannot save untrained model")
        
        save_path = path or f"{MODEL_SAVE_PATH}/yield_prediction_{self.model_type}.pkl"
        
        model_data = {
            'model': self.model,
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'is_fitted': self.is_fitted,
            'training_metrics': self.training_metrics
        }
        
        joblib.dump(model_data, save_path)
        logger.info(f"Model saved to {save_path}")
        
        return save_path
    
    @classmethod
    def load(cls, path: str) -> 'YieldPredictionModel':
        """
        Load a trained model from disk.
        
        Args:
            path: Path to saved model file
            
        Returns:
            Loaded YieldPredictionModel instance
        """
        model_data = joblib.load(path)
        
        instance = cls(model_type=model_data['model_type'])
        instance.model = model_data['model']
        instance.feature_names = model_data['feature_names']
        instance.is_fitted = model_data['is_fitted']
        instance.training_metrics = model_data['training_metrics']
        
        logger.info(f"Model loaded from {path}")
        
        return instance


def prepare_features(
    climate_data: pd.DataFrame,
    soil_data: pd.DataFrame,
    agricultural_data: pd.DataFrame
) -> pd.DataFrame:
    """
    Prepare feature matrix from multiple data sources.
    
    Args:
        climate_data: Climate variables (temperature, precipitation, etc.)
        soil_data: Soil properties (pH, nutrients, texture, etc.)
        agricultural_data: Agricultural practices (irrigation, fertilizer, etc.)
        
    Returns:
        Combined feature matrix ready for regression
    """
    logger.debug("Preparing feature matrix from multiple data sources")
    
    # Combine all data sources
    features = pd.concat([
        climate_data,
        soil_data,
        agricultural_data
    ], axis=1)
    
    # Remove any duplicate columns
    features = features.loc[:, ~features.columns.duplicated()]
    
    # Handle missing values
    features = features.fillna(features.median())
    
    # Remove constant columns
    constant_cols = [col for col in features.columns if features[col].nunique() == 1]
    if constant_cols:
        features = features.drop(columns=constant_cols)
        logger.warning(f"Removed {len(constant_cols)} constant columns")
    
    logger.info(f"Prepared feature matrix with {features.shape[1]} features")
    
    return features