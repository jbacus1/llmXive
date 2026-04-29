import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class ClimateRiskModel:
    """Climate risk assessment model for agricultural productivity."""
    
    def __init__(self, config: Dict):
        self.config = config
        logger.info("Initializing ClimateRiskModel with config keys: %s", list(config.keys()))
    
    def assess_risk(self, climate_data: pd.DataFrame, 
                   agricultural_data: pd.DataFrame) -> Dict:
        """
        Assess climate risk to agricultural productivity.
        
        Args:
            climate_data: DataFrame with climate variables
            agricultural_data: DataFrame with agricultural metrics
        
        Returns:
            Dictionary with risk scores and metadata
        """
        logger.info("Starting climate risk assessment with %d climate records, %d agricultural records",
                   len(climate_data), len(agricultural_data))
        
        try:
            # Validate inputs
            if climate_data.empty or agricultural_data.empty:
                logger.warning("Empty input data provided for risk assessment")
                return {"risk_score": 0, "status": "empty_input"}
            
            # Calculate risk components
            drought_risk = self._calculate_drought_risk(climate_data)
            flood_risk = self._calculate_flood_risk(climate_data)
            temperature_risk = self._calculate_temperature_risk(climate_data)
            precipitation_risk = self._calculate_precipitation_risk(climate_data)
            
            # Aggregate risk score
            risk_score = self._aggregate_risk_scores(
                drought_risk, flood_risk, temperature_risk, precipitation_risk
            )
            
            logger.info("Risk assessment completed: drought=%.2f, flood=%.2f, temp=%.2f, precip=%.2f, overall=%.2f",
                       drought_risk, flood_risk, temperature_risk, precipitation_risk, risk_score)
            
            return {
                "risk_score": risk_score,
                "components": {
                    "drought": drought_risk,
                    "flood": flood_risk,
                    "temperature": temperature_risk,
                    "precipitation": precipitation_risk
                },
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "record_count": len(climate_data),
                    "status": "success"
                }
            }
            
        except Exception as e:
            logger.error("Climate risk assessment failed: %s", str(e), exc_info=True)
            raise
    
    def _calculate_drought_risk(self, climate_data: pd.DataFrame) -> float:
        """Calculate drought risk score (0-1 scale)."""
        logger.debug("Calculating drought risk from precipitation data")
        try:
            precipitation = climate_data.get('precipitation_mm', pd.Series([0]))
            drought_threshold = self.config.get('drought_threshold_mm', 50)
            drought_ratio = (precipitation < drought_threshold).mean()
            return min(1.0, drought_ratio)
        except Exception as e:
            logger.warning("Drought risk calculation failed: %s", str(e))
            return 0.0
    
    def _calculate_flood_risk(self, climate_data: pd.DataFrame) -> float:
        """Calculate flood risk score (0-1 scale)."""
        logger.debug("Calculating flood risk from precipitation data")
        try:
            precipitation = climate_data.get('precipitation_mm', pd.Series([0]))
            flood_threshold = self.config.get('flood_threshold_mm', 200)
            flood_ratio = (precipitation > flood_threshold).mean()
            return min(1.0, flood_ratio)
        except Exception as e:
            logger.warning("Flood risk calculation failed: %s", str(e))
            return 0.0
    
    def _calculate_temperature_risk(self, climate_data: pd.DataFrame) -> float:
        """Calculate temperature risk score (0-1 scale)."""
        logger.debug("Calculating temperature risk")
        try:
            temp = climate_data.get('temperature_celsius', pd.Series([0]))
            temp_threshold = self.config.get('max_temp_threshold_celsius', 35)
            temp_ratio = (temp > temp_threshold).mean()
            return min(1.0, temp_ratio)
        except Exception as e:
            logger.warning("Temperature risk calculation failed: %s", str(e))
            return 0.0
    
    def _calculate_precipitation_risk(self, climate_data: pd.DataFrame) -> float:
        """Calculate precipitation variability risk score (0-1 scale)."""
        logger.debug("Calculating precipitation variability risk")
        try:
            precipitation = climate_data.get('precipitation_mm', pd.Series([0]))
            if len(precipitation) > 1:
                cv = precipitation.std() / precipitation.mean() if precipitation.mean() > 0 else 0
                return min(1.0, cv / 2.0)  # Normalize CV to 0-1
            return 0.0
        except Exception as e:
            logger.warning("Precipitation risk calculation failed: %s", str(e))
            return 0.0
    
    def _aggregate_risk_scores(self, *scores: float) -> float:
        """Aggregate multiple risk scores into overall score."""
        logger.debug("Aggregating %d risk scores", len(scores))
        try:
            return np.mean(scores)
        except Exception as e:
            logger.error("Risk score aggregation failed: %s", str(e))
            raise
    
    def batch_assess_risk(self, climate_datasets: List[pd.DataFrame],
                         agricultural_datasets: List[pd.DataFrame]) -> List[Dict]:
        """
        Assess risk for multiple datasets.
        
        Args:
            climate_datasets: List of climate DataFrames
            agricultural_datasets: List of agricultural DataFrames
        
        Returns:
            List of risk assessment results
        """
        logger.info("Starting batch risk assessment for %d datasets", len(climate_datasets))
        results = []
        
        for i, (climate_df, ag_df) in enumerate(zip(climate_datasets, agricultural_datasets)):
            logger.debug("Processing batch item %d/%d", i + 1, len(climate_datasets))
            try:
                result = self.assess_risk(climate_df, ag_df)
                result['batch_index'] = i
                results.append(result)
            except Exception as e:
                logger.error("Batch item %d failed: %s", i, str(e))
                results.append({"batch_index": i, "status": "failed", "error": str(e)})
        
        logger.info("Batch assessment completed: %d successful, %d failed",
                   sum(1 for r in results if r.get('status') == 'success'),
                   sum(1 for r in results if r.get('status') == 'failed'))
        
        return results