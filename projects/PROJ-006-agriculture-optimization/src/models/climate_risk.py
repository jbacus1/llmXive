"""
Climate Risk Assessment Model

Implements statistical analysis for climate risk assessment using pandas
and scikit-learn. Provides core statistical functions for analyzing
climate data and assessing agricultural risks.

User Story: US2 - Climate Risk Assessment
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

import logging

logger = logging.getLogger(__name__)


class ClimateRiskAnalyzer:
    """
    Statistical analysis engine for climate risk assessment.
    
    Provides functions for:
    - Trend analysis of climate variables
    - Correlation analysis between climate and yield
    - Risk scoring based on statistical thresholds
    - Basic predictive modeling for yield impacts
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the climate risk analyzer.
        
        Args:
            config: Optional configuration dictionary with risk thresholds
        """
        self.config = config or self._default_config()
        self._validate_config()
    
    def _default_config(self) -> Dict:
        """Return default configuration for risk assessment."""
        return {
            'risk_thresholds': {
                'low': 0.3,
                'medium': 0.6,
                'high': 0.8
            },
            'trend_significance': 0.05,
            'correlation_threshold': 0.5,
            'min_samples': 10
        }
    
    def _validate_config(self):
        """Validate configuration parameters."""
        if not isinstance(self.config.get('risk_thresholds'), dict):
            raise ValueError("risk_thresholds must be a dictionary")
        if not 0 < self.config.get('trend_significance', 0.05) < 1:
            raise ValueError("trend_significance must be between 0 and 1")
    
    def calculate_trend(self, 
                       data: pd.Series,
                       time_index: Optional[pd.Series] = None) -> Dict:
        """
        Calculate linear trend for a time series.
        
        Args:
            data: Time series data (e.g., temperature, rainfall)
            time_index: Optional time index for trend calculation
        
        Returns:
            Dictionary with trend slope, p-value, and significance
        """
        if len(data) < self.config['min_samples']:
            logger.warning(f"Insufficient samples ({len(data)}) for trend analysis")
            return {
                'slope': np.nan,
                'intercept': np.nan,
                'p_value': np.nan,
                'significant': False,
                'r_squared': np.nan
            }
        
        if time_index is None:
            time_index = pd.RangeIndex(len(data))
        
        # Linear regression for trend
        X = time_index.values.reshape(-1, 1)
        y = data.values
        
        model = LinearRegression()
        model.fit(X, y)
        
        slope = model.coef_[0]
        intercept = model.intercept_
        r_squared = model.score(X, y)
        
        # Calculate p-value using scipy
        n = len(data)
        if n < 3:
            p_value = np.nan
        else:
            correlation, p_value = stats.pearsonr(time_index, data)
        
        return {
            'slope': slope,
            'intercept': intercept,
            'p_value': p_value,
            'significant': p_value < self.config['trend_significance'] if p_value else False,
            'r_squared': r_squared,
            'trend_direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
        }
    
    def calculate_correlation_matrix(self, 
                                    df: pd.DataFrame, 
                                    columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Calculate correlation matrix for climate variables.
        
        Args:
            df: DataFrame with climate variables
            columns: Optional list of columns to include
        
        Returns:
            Correlation matrix as DataFrame
        """
        if columns:
            df = df[columns]
        
        # Drop non-numeric columns
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            logger.warning("No numeric columns found for correlation analysis")
            return pd.DataFrame()
        
        return numeric_df.corr()
    
    def identify_significant_correlations(self, 
                                         correlation_matrix: pd.DataFrame,
                                         threshold: Optional[float] = None) -> List[Dict]:
        """
        Identify significant correlations above threshold.
        
        Args:
            correlation_matrix: Correlation matrix from calculate_correlation_matrix
            threshold: Correlation threshold (default from config)
        
        Returns:
            List of dictionaries with variable pairs and correlation values
        """
        threshold = threshold or self.config['correlation_threshold']
        significant_correlations = []
        
        if correlation_matrix.empty:
            return significant_correlations
        
        # Get upper triangle (avoid duplicates)
        for i in range(len(correlation_matrix.columns)):
            for j in range(i + 1, len(correlation_matrix.columns)):
                corr_value = correlation_matrix.iloc[i, j]
                
                if abs(corr_value) >= threshold:
                    significant_correlations.append({
                        'variable_1': correlation_matrix.columns[i],
                        'variable_2': correlation_matrix.columns[j],
                        'correlation': corr_value,
                        'strength': self._classify_correlation_strength(abs(corr_value))
                    })
        
        return significant_correlations
    
    def _classify_correlation_strength(self, value: float) -> str:
        """Classify correlation strength."""
        if value >= 0.8:
            return 'very_strong'
        elif value >= 0.6:
            return 'strong'
        elif value >= 0.4:
            return 'moderate'
        elif value >= 0.2:
            return 'weak'
        else:
            return 'very_weak'
    
    def calculate_risk_score(self,
                            climate_data: pd.DataFrame,
                            risk_factors: Dict[str, float],
                            weights: Optional[Dict[str, float]] = None) -> Dict:
        """
        Calculate composite risk score based on climate factors.
        
        Args:
            climate_data: DataFrame with climate variables
            risk_factors: Dictionary mapping column names to risk direction
                         (positive = higher value increases risk)
            weights: Optional dictionary of factor weights (default equal)
        
        Returns:
            Dictionary with risk score and breakdown
        """
        if weights is None:
            weights = {k: 1.0 for k in risk_factors.keys()}
        
        # Normalize each factor to 0-1 range
        normalized_scores = {}
        
        for factor, direction in risk_factors.items():
            if factor not in climate_data.columns:
                logger.warning(f"Risk factor '{factor}' not found in data")
                continue
            
            values = climate_data[factor].dropna()
            
            if len(values) == 0:
                normalized_scores[factor] = 0.0
                continue
            
            # Min-max normalization
            min_val = values.min()
            max_val = values.max()
            
            if max_val == min_val:
                normalized = 0.5
            else:
                normalized = (values - min_val) / (max_val - min_val)
            
            # Adjust for risk direction
            if direction < 0:
                normalized = 1 - normalized
            
            normalized_scores[factor] = normalized
        
        # Calculate weighted composite score
        if not normalized_scores:
            return {
                'risk_score': np.nan,
                'risk_level': 'unknown',
                'factor_scores': {},
                'weights_used': {}
            }
        
        total_weight = sum(weights.values())
        composite_score = sum(
            normalized_scores[factor] * weights.get(factor, 1.0)
            for factor in normalized_scores
        ) / total_weight
        
        # Classify risk level
        thresholds = self.config['risk_thresholds']
        if composite_score <= thresholds['low']:
            risk_level = 'low'
        elif composite_score <= thresholds['medium']:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        return {
            'risk_score': float(composite_score),
            'risk_level': risk_level,
            'factor_scores': {k: float(v.mean()) if hasattr(v, 'mean') else float(v) 
                             for k, v in normalized_scores.items()},
            'weights_used': weights
        }
    
    def predict_yield_impact(self,
                            historical_data: pd.DataFrame,
                            target_features: List[str],
                            target_column: str,
                            test_size: float = 0.2) -> Dict:
        """
        Predict yield impact based on climate variables.
        
        Args:
            historical_data: DataFrame with historical climate and yield data
            target_features: List of feature columns to use for prediction
            target_column: Column name for yield values
            test_size: Proportion of data to use for testing
        
        Returns:
            Dictionary with model metrics and predictions
        """
        # Prepare data
        X = historical_data[target_features].dropna()
        y = historical_data.loc[X.index, target_column]
        
        if len(X) < self.config['min_samples']:
            logger.warning(f"Insufficient samples ({len(X)}) for prediction model")
            return {
                'model_trained': False,
                'reason': 'insufficient_samples',
                'metrics': {}
            }
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        model = LinearRegression()
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Feature importance (absolute coefficients)
        feature_importance = dict(
            zip(target_features, abs(model.coef_))
        )
        
        return {
            'model_trained': True,
            'mse': float(mse),
            'r_squared': float(r2),
            'feature_importance': feature_importance,
            'predictions': y_pred.tolist(),
            'actual_values': y_test.tolist(),
            'scaler': scaler,
            'model': model
        }
    
    def analyze_extreme_events(self,
                              data: pd.Series,
                              threshold_percentile: float = 90) -> Dict:
        """
        Analyze extreme climate events in time series.
        
        Args:
            data: Time series data (e.g., temperature, rainfall)
            threshold_percentile: Percentile threshold for extreme events
        
        Returns:
            Dictionary with extreme event statistics
        """
        threshold = np.percentile(data, threshold_percentile)
        extreme_values = data[data > threshold]
        
        if len(extreme_values) == 0:
            return {
                'extreme_event_count': 0,
                'threshold_value': threshold,
                'extreme_events': [],
                'average_extreme_value': np.nan,
                'max_extreme_value': np.nan
            }
        
        return {
            'extreme_event_count': int(len(extreme_values)),
            'threshold_value': float(threshold),
            'extreme_events': extreme_values.tolist(),
            'average_extreme_value': float(extreme_values.mean()),
            'max_extreme_value': float(extreme_values.max()),
            'extreme_event_frequency': len(extreme_values) / len(data)
        }
    
    def generate_risk_summary(self,
                             climate_data: pd.DataFrame,
                             risk_factors: Dict[str, float]) -> Dict:
        """
        Generate comprehensive risk assessment summary.
        
        Args:
            climate_data: DataFrame with climate variables
            risk_factors: Dictionary mapping variables to risk direction
        
        Returns:
            Dictionary with complete risk assessment summary
        """
        summary = {
            'data_points': len(climate_data),
            'variables_analyzed': list(climate_data.columns),
            'trend_analysis': {},
            'correlation_analysis': {},
            'risk_score': {},
            'extreme_events': {}
        }
        
        # Trend analysis for each variable
        for col in climate_data.select_dtypes(include=[np.number]).columns:
            if col in risk_factors:
                summary['trend_analysis'][col] = self.calculate_trend(
                    climate_data[col]
                )
        
        # Correlation analysis
        corr_matrix = self.calculate_correlation_matrix(climate_data)
        if not corr_matrix.empty:
            summary['correlation_analysis'] = {
                'matrix': corr_matrix.to_dict(),
                'significant_correlations': self.identify_significant_correlations(
                    corr_matrix
                )
            }
        
        # Risk score
        summary['risk_score'] = self.calculate_risk_score(
            climate_data, risk_factors
        )
        
        # Extreme events
        for col in climate_data.select_dtypes(include=[np.number]).columns:
            if col in risk_factors:
                summary['extreme_events'][col] = self.analyze_extreme_events(
                    climate_data[col]
                )
        
        return summary