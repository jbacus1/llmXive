"""
Time Series Analysis Module for Historical Climate Patterns

Part of User Story 2: Climate Risk Assessment
Implements temporal analysis of climate data including:
- Trend detection and analysis
- Seasonal decomposition
- Anomaly detection
- Short-term forecasting

Dependencies: pandas, numpy, scikit-learn, scipy
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from src.config.constants import CLIMATE_DATA_DIR, DATA_CACHE_TTL
from src.data.cache import ClimateDataCache

logger = logging.getLogger(__name__)
cache = ClimateDataCache()


class TimeSeriesClimateAnalyzer:
    """
    Analyzes historical climate data using time series methods.

    This class provides methods for:
    - Detecting climate trends (temperature, precipitation)
    - Decomposing seasonal patterns
    - Identifying anomalies and extreme events
    - Generating short-term forecasts

    Attributes:
        data: DataFrame with datetime index and climate variables
        trend_results: Dictionary storing trend analysis results
        seasonal_results: Dictionary storing seasonal decomposition results
    """

    def __init__(
        self,
        cache_ttl: int = DATA_CACHE_TTL,
        min_data_points: int = 12,
        confidence_level: float = 0.95
    ):
        """
        Initialize the time series analyzer.

        Args:
            cache_ttl: Cache time-to-live in seconds
            min_data_points: Minimum data points required for analysis
            confidence_level: Confidence level for statistical tests
        """
        self.cache_ttl = cache_ttl
        self.min_data_points = min_data_points
        self.confidence_level = confidence_level
        self.trend_results: Dict = {}
        self.seasonal_results: Dict = {}
        self.anomaly_results: Dict = {}

    def load_climate_timeseries(
        self,
        data_path: str,
        date_column: str = 'date',
        value_columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Load climate data and prepare for time series analysis.

        Args:
            data_path: Path to climate data file (CSV, parquet)
            date_column: Name of the date column
            value_columns: Columns to analyze (default: all numeric)

        Returns:
            DataFrame with datetime index, sorted chronologically

        Raises:
            ValueError: If data has insufficient points or invalid format
        """
        try:
            # Load data
            df = pd.read_csv(data_path)

            # Parse dates
            df[date_column] = pd.to_datetime(df[date_column])
            df = df.set_index(date_column)
            df = df.sort_index()

            # Select numeric columns if not specified
            if value_columns is None:
                value_columns = df.select_dtypes(include=[np.number]).columns.tolist()

            # Validate minimum data points
            if len(df) < self.min_data_points:
                raise ValueError(
                    f"Insufficient data points: {len(df)} < {self.min_data_points}"
                )

            # Check for missing values
            missing = df[value_columns].isnull().sum()
            if missing.any():
                logger.warning(
                    f"Missing values detected: {missing.to_dict()}"
                )
                # Forward fill for time series continuity
                df[value_columns] = df[value_columns].fillna(method='ffill')

            logger.info(
                f"Loaded {len(df)} climate records for analysis"
            )
            return df[value_columns]

        except Exception as e:
            logger.error(f"Failed to load climate timeseries: {e}")
            raise

    def detect_trend(
        self,
        data: pd.Series,
        method: str = 'linear'
    ) -> Dict[str, Union[float, str, bool]]:
        """
        Detect trend in climate data using specified method.

        Args:
            data: Series with datetime index and numeric values
            method: 'linear' for linear regression, 'mann-kendall' for non-parametric

        Returns:
            Dictionary with trend statistics:
            - slope: Trend direction and magnitude
            - p_value: Statistical significance
            - trend_direction: 'increasing', 'decreasing', or 'stable'
            - confidence: Confidence level of the trend
        """
        if len(data) < self.min_data_points:
            raise ValueError(
                f"Insufficient data for trend analysis: {len(data)} points"
            )

        # Create numeric time index
        time_index = np.arange(len(data))
        y_values = data.values

        if method == 'linear':
            return self._linear_trend(time_index, y_values)
        elif method == 'mann-kendall':
            return self._mann_kendall_test(y_values)
        else:
            raise ValueError(f"Unknown trend method: {method}")

    def _linear_trend(
        self,
        x: np.ndarray,
        y: np.ndarray
    ) -> Dict[str, Union[float, str, bool]]:
        """
        Perform linear regression trend analysis.

        Args:
            x: Time index array
            y: Value array

        Returns:
            Trend analysis results
        """
        model = LinearRegression()
        model.fit(x.reshape(-1, 1), y)

        slope = model.coef_[0]
        intercept = model.intercept_

        # Calculate R-squared
        y_pred = model.predict(x.reshape(-1, 1))
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # Calculate p-value for slope
        n = len(x)
        if n > 2:
            _, p_value = stats.pearsonr(x, y)
        else:
            p_value = 1.0

        # Determine trend direction
        if p_value < (1 - self.confidence_level):
            if slope > 0:
                direction = 'increasing'
            else:
                direction = 'decreasing'
        else:
            direction = 'stable'

        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'r_squared': float(r_squared),
            'p_value': float(p_value),
            'trend_direction': direction,
            'confidence': self.confidence_level,
            'significant': p_value < (1 - self.confidence_level)
        }

    def _mann_kendall_test(
        self,
        data: np.ndarray
    ) -> Dict[str, Union[float, str, bool]]:
        """
        Perform non-parametric Mann-Kendall trend test.

        Args:
            data: Value array

        Returns:
            Mann-Kendall test results
        """
        n = len(data)
        if n < self.min_data_points:
            raise ValueError("Insufficient data for Mann-Kendall test")

        # Calculate S statistic
        s = 0
        for i in range(n - 1):
            for j in range(i + 1, n):
                diff = data[j] - data[i]
                if diff > 0:
                    s += 1
                elif diff < 0:
                    s -= 1

        # Calculate variance
        var_s = (n * (n - 1) * (2 * n + 5)) / 18

        # Calculate Z-score
        if s > 0:
            z = (s - 1) / np.sqrt(var_s)
        elif s < 0:
            z = (s + 1) / np.sqrt(var_s)
        else:
            z = 0

        # Calculate p-value (two-tailed)
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))

        # Determine direction
        if p_value < (1 - self.confidence_level):
            direction = 'increasing' if s > 0 else 'decreasing'
        else:
            direction = 'stable'

        return {
            's_statistic': float(s),
            'z_score': float(z),
            'p_value': float(p_value),
            'trend_direction': direction,
            'confidence': self.confidence_level,
            'significant': p_value < (1 - self.confidence_level)
        }

    def decompose_seasonal(
        self,
        data: pd.Series,
        period: int = 12,
        method: str = 'additive'
    ) -> Dict[str, pd.Series]:
        """
        Decompose time series into trend, seasonal, and residual components.

        Args:
            data: Series with datetime index
            period: Number of observations per cycle (e.g., 12 for monthly)
            method: 'additive' or 'multiplicative' decomposition

        Returns:
            Dictionary with 'trend', 'seasonal', 'residual' components
        """
        if len(data) < period * 2:
            raise ValueError(
                f"Insufficient data for seasonal decomposition: "
                f"need at least {period * 2} points"
            )

        # Rolling window for trend
        trend = data.rolling(window=period, center=True).mean()

        # Detrended data
        if method == 'additive':
            detrended = data - trend
        else:
            detrended = data / trend

        # Average seasonal pattern
        seasonal = pd.DataFrame({
            'time': data.index,
            'detrended': detrended,
            'period_idx': data.index.month % period
        })

        seasonal_avg = seasonal.groupby('period_idx')['detrended'].mean()

        # Align seasonal pattern
        seasonal_series = pd.Series(
            seasonal_avg[data.index.month % period].values,
            index=data.index
        )

        # Calculate residual
        if method == 'additive':
            residual = data - trend - seasonal_series
        else:
            residual = data / (trend * seasonal_series)

        self.seasonal_results[data.name] = {
            'trend': trend,
            'seasonal': seasonal_series,
            'residual': residual,
            'period': period,
            'method': method
        }

        return {
            'trend': trend,
            'seasonal': seasonal_series,
            'residual': residual
        }

    def detect_anomalies(
        self,
        data: pd.Series,
        threshold: float = 2.5,
        method: str = 'zscore'
    ) -> Tuple[List[int], Dict]:
        """
        Detect anomalies in climate data.

        Args:
            data: Series with datetime index
            threshold: Number of standard deviations for anomaly threshold
            method: 'zscore', 'iqr', or 'rolling'

        Returns:
            Tuple of (anomaly indices, anomaly statistics)
        """
        if method == 'zscore':
            return self._zscore_anomaly(data, threshold)
        elif method == 'iqr':
            return self._iqr_anomaly(data)
        elif method == 'rolling':
            return self._rolling_anomaly(data, threshold)
        else:
            raise ValueError(f"Unknown anomaly method: {method}")

    def _zscore_anomaly(
        self,
        data: pd.Series,
        threshold: float
    ) -> Tuple[List[int], Dict]:
        """
        Detect anomalies using Z-score method.

        Args:
            data: Value series
            threshold: Z-score threshold

        Returns:
            Anomaly indices and statistics
        """
        mean = data.mean()
        std = data.std()

        if std == 0:
            return [], {'mean': mean, 'std': std, 'threshold': threshold}

        z_scores = np.abs((data - mean) / std)
        anomaly_indices = z_scores[z_scores > threshold].index.tolist()

        stats_dict = {
            'mean': float(mean),
            'std': float(std),
            'threshold': threshold,
            'anomaly_count': len(anomaly_indices),
            'anomaly_percentage': len(anomaly_indices) / len(data) * 100
        }

        self.anomaly_results[data.name] = stats_dict
        return anomaly_indices, stats_dict

    def _iqr_anomaly(
        self,
        data: pd.Series
    ) -> Tuple[List[int], Dict]:
        """
        Detect anomalies using Interquartile Range method.

        Args:
            data: Value series

        Returns:
            Anomaly indices and statistics
        """
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        anomaly_indices = data[
            (data < lower_bound) | (data > upper_bound)
        ].index.tolist()

        stats_dict = {
            'q1': float(q1),
            'q3': float(q3),
            'iqr': float(iqr),
            'lower_bound': float(lower_bound),
            'upper_bound': float(upper_bound),
            'anomaly_count': len(anomaly_indices),
            'anomaly_percentage': len(anomaly_indices) / len(data) * 100
        }

        self.anomaly_results[data.name] = stats_dict
        return anomaly_indices, stats_dict

    def _rolling_anomaly(
        self,
        data: pd.Series,
        threshold: float,
        window: int = 12
    ) -> Tuple[List[int], Dict]:
        """
        Detect anomalies using rolling statistics.

        Args:
            data: Value series
            threshold: Standard deviation threshold
            window: Rolling window size

        Returns:
            Anomaly indices and statistics
        """
        rolling_mean = data.rolling(window=window).mean()
        rolling_std = data.rolling(window=window).std()

        z_scores = np.abs((data - rolling_mean) / rolling_std)
        anomaly_indices = z_scores[z_scores > threshold].index.tolist()

        stats_dict = {
            'window': window,
            'threshold': threshold,
            'anomaly_count': len(anomaly_indices),
            'anomaly_percentage': len(anomaly_indices) / len(data) * 100
        }

        self.anomaly_results[data.name] = stats_dict
        return anomaly_indices, stats_dict

    def forecast_short_term(
        self,
        data: pd.Series,
        periods: int = 12,
        method: str = 'linear'
    ) -> pd.DataFrame:
        """
        Generate short-term forecast for climate variable.

        Args:
            data: Historical data series
            periods: Number of periods to forecast
            method: 'linear' for trend extrapolation

        Returns:
            DataFrame with forecasted values and confidence intervals
        """
        time_index = np.arange(len(data))
        y_values = data.values

        # Fit model
        model = LinearRegression()
        model.fit(time_index.reshape(-1, 1), y_values)

        # Generate forecast
        future_index = np.arange(len(data), len(data) + periods)
        forecast = model.predict(future_index.reshape(-1, 1))

        # Calculate confidence intervals
        residuals = y_values - model.predict(time_index.reshape(-1, 1))
        residual_std = np.std(residuals)

        # 95% confidence interval
        margin = 1.96 * residual_std

        # Create forecast dates
        last_date = data.index[-1]
        freq = pd.infer_freq(data.index)
        if freq is None:
            freq = 'M'  # Default to monthly
        forecast_dates = pd.date_range(
            start=last_date + pd.Timedelta(freq),
            periods=periods,
            freq=freq
        )

        forecast_df = pd.DataFrame({
            'forecast': forecast,
            'lower_bound': forecast - margin,
            'upper_bound': forecast + margin,
            'date': forecast_dates
        })
        forecast_df = forecast_df.set_index('date')

        logger.info(
            f"Generated {periods}-period forecast for {data.name}"
        )
        return forecast_df

    def analyze_climate_patterns(
        self,
        data_path: str,
        value_column: str,
        date_column: str = 'date'
    ) -> Dict:
        """
        Perform comprehensive climate pattern analysis.

        Args:
            data_path: Path to climate data file
            value_column: Column name for climate variable
            date_column: Column name for dates

        Returns:
            Dictionary with all analysis results
        """
        logger.info(f"Starting climate pattern analysis for {value_column}")

        # Load data
        df = self.load_climate_timeseries(data_path, date_column, [value_column])
        series = df[value_column]

        # Perform analyses
        results = {
            'data_info': {
                'start_date': str(series.index[0]),
                'end_date': str(series.index[-1]),
                'data_points': len(series),
                'value_column': value_column
            },
            'trend': self.detect_trend(series),
            'anomalies': None,
            'forecast': None
        }

        # Detect anomalies
        try:
            anomaly_indices, anomaly_stats = self.detect_anomalies(series)
            results['anomalies'] = anomaly_stats
            results['anomaly_dates'] = anomaly_indices
        except Exception as e:
            logger.warning(f"Anomaly detection failed: {e}")
            results['anomalies'] = {'error': str(e)}

        # Generate forecast
        try:
            forecast = self.forecast_short_term(series, periods=12)
            results['forecast'] = {
                'values': forecast['forecast'].tolist(),
                'lower_bound': forecast['lower_bound'].tolist(),
                'upper_bound': forecast['upper_bound'].tolist(),
                'dates': [str(d) for d in forecast.index]
            }
        except Exception as e:
            logger.warning(f"Forecast generation failed: {e}")
            results['forecast'] = {'error': str(e)}

        logger.info(
            f"Climate pattern analysis complete for {value_column}"
        )
        return results


def run_time_series_analysis(
    data_path: str,
    value_columns: List[str],
    date_column: str = 'date'
) -> Dict[str, Dict]:
    """
    Convenience function to run time series analysis on multiple climate variables.

    Args:
        data_path: Path to climate data file
        value_columns: List of climate variables to analyze
        date_column: Name of date column

    Returns:
        Dictionary with analysis results for each variable
    """
    analyzer = TimeSeriesClimateAnalyzer()
    results = {}

    for column in value_columns:
        try:
            results[column] = analyzer.analyze_climate_patterns(
                data_path=data_path,
                value_column=column,
                date_column=date_column
            )
        except Exception as e:
            logger.error(f"Failed to analyze {column}: {e}")
            results[column] = {'error': str(e)}

    return results