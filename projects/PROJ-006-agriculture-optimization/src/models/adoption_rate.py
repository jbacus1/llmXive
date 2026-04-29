"""
Adoption Rate Model for Climate-Smart Agricultural Practices

This module implements models to predict and analyze adoption rates of
climate-smart agricultural (CSA) practices among farming communities.

The model considers factors such as:
- Economic incentives
- Social influence and peer effects
- Accessibility and availability of resources
- Training and education levels
- Risk perception
- Policy support

Author: Climate-Smart Agriculture Project
Version: 1.0.0
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
import logging
import numpy as np
import pandas as pd
from datetime import datetime

from src.config.constants import MODEL_VERSION, ADOPTION_THRESHOLD


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AdoptionFactors:
    """Data class representing factors influencing CSA practice adoption."""
    economic_incentive: float = 0.0  # 0-1 scale
    social_influence: float = 0.0  # 0-1 scale
    resource_accessibility: float = 0.0  # 0-1 scale
    training_level: float = 0.0  # 0-1 scale
    risk_perception: float = 0.0  # 0-1 scale (higher = more risk-averse)
    policy_support: float = 0.0  # 0-1 scale
    farm_size: float = 0.0  # in hectares
    years_farming: int = 0
    education_level: str = "basic"  # basic, intermediate, advanced
    access_to_credit: bool = False
    technology_readiness: float = 0.0  # 0-1 scale


@dataclass
class AdoptionRateResult:
    """Data class representing adoption rate calculation results."""
    community_id: str
    practice_type: str
    predicted_adoption_rate: float  # 0-100 percentage
    confidence_score: float  # 0-1
    influencing_factors: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    calculation_timestamp: str = ""
    model_version: str = MODEL_VERSION


class AdoptionRateModel:
    """
    Model for predicting adoption rates of climate-smart agricultural practices.
    
    This model uses a weighted scoring approach combined with logistic regression
    to estimate the likelihood of practice adoption across different communities.
    """
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize the adoption rate model.
        
        Args:
            weights: Optional custom weights for factors. If None, uses defaults.
        """
        self.model_version = MODEL_VERSION
        self.weights = weights or self._get_default_weights()
        self._validate_weights()
        logger.info(f"AdoptionRateModel initialized with version {self.model_version}")
    
    def _get_default_weights(self) -> Dict[str, float]:
        """Get default weights for adoption factors."""
        return {
            'economic_incentive': 0.25,
            'social_influence': 0.20,
            'resource_accessibility': 0.15,
            'training_level': 0.15,
            'risk_perception': 0.10,
            'policy_support': 0.10,
            'technology_readiness': 0.05
        }
    
    def _validate_weights(self) -> None:
        """Validate that weights sum to 1.0 and are within valid range."""
        total = sum(self.weights.values())
        if not (0.95 <= total <= 1.05):
            logger.warning(f"Weights sum to {total}, normalizing to 1.0")
            for key in self.weights:
                self.weights[key] = self.weights[key] / total
        
        for key, value in self.weights.items():
            if not 0 <= value <= 1:
                raise ValueError(f"Weight for {key} must be between 0 and 1, got {value}")
    
    def calculate_adoption_rate(self, factors: AdoptionFactors) -> AdoptionRateResult:
        """
        Calculate the predicted adoption rate for a community based on factors.
        
        Args:
            factors: AdoptionFactors object containing community characteristics
            
        Returns:
            AdoptionRateResult with predicted rate and analysis
        """
        try:
            self._validate_factors(factors)
            weighted_score = self._calculate_weighted_score(factors)
            adoption_rate = self._logistic_transform(weighted_score)
            confidence = self._calculate_confidence(factors)
            recommendations = self._generate_recommendations(factors, weighted_score)
            
            result = AdoptionRateResult(
                community_id=str(factors.farm_size),
                practice_type="climate_smart_agriculture",
                predicted_adoption_rate=round(adoption_rate, 2),
                confidence_score=round(confidence, 2),
                influencing_factors={k: v for k, v in self.weights.items()},
                recommendations=recommendations,
                calculation_timestamp=self._get_timestamp(),
                model_version=self.model_version
            )
            
            logger.info(f"Adoption rate calculated: {adoption_rate:.2f}%")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating adoption rate: {str(e)}")
            raise
    
    def _validate_factors(self, factors: AdoptionFactors) -> None:
        """Validate that all factors are within acceptable ranges."""
        scale_factors = [
            'economic_incentive', 'social_influence', 'resource_accessibility',
            'training_level', 'risk_perception', 'policy_support', 'technology_readiness'
        ]
        
        for factor in scale_factors:
            value = getattr(factors, factor)
            if not 0 <= value <= 1:
                raise ValueError(f"{factor} must be between 0 and 1, got {value}")
        
        if factors.farm_size < 0:
            raise ValueError(f"farm_size must be non-negative, got {factors.farm_size}")
        
        valid_education = ['basic', 'intermediate', 'advanced']
        if factors.education_level not in valid_education:
            raise ValueError(f"education_level must be one of {valid_education}, got {factors.education_level}")
    
    def _calculate_weighted_score(self, factors: AdoptionFactors) -> float:
        """Calculate weighted score from adoption factors."""
        score = 0.0
        
        score += self.weights['economic_incentive'] * factors.economic_incentive
        score += self.weights['social_influence'] * factors.social_influence
        score += self.weights['resource_accessibility'] * factors.resource_accessibility
        score += self.weights['training_level'] * factors.training_level
        score += self.weights['risk_perception'] * (1 - factors.risk_perception)
        score += self.weights['policy_support'] * factors.policy_support
        score += self.weights['technology_readiness'] * factors.technology_readiness
        
        if factors.farm_size > 50:
            score *= 0.9
        elif factors.farm_size < 5:
            score *= 1.1
        
        education_adjustments = {'basic': 0.9, 'intermediate': 1.0, 'advanced': 1.1}
        score *= education_adjustments[factors.education_level]
        
        if factors.access_to_credit:
            score *= 1.15
        
        if factors.years_farming > 20:
            score *= 1.05
        
        return min(max(score, 0), 1)
    
    def _logistic_transform(self, score: float) -> float:
        """Apply logistic transformation to convert score to percentage."""
        k = 6
        x0 = 0.5
        probability = 1 / (1 + np.exp(-k * (score - x0)))
        return probability * 100
    
    def _calculate_confidence(self, factors: AdoptionFactors) -> float:
        """Calculate confidence score based on data completeness and quality."""
        confidence = 0.8
        
        extreme_count = 0
        for factor in ['economic_incentive', 'social_influence', 'resource_accessibility',
                       'training_level', 'risk_perception', 'policy_support']:
            value = getattr(factors, factor)
            if value <= 0.1 or value >= 0.9:
                extreme_count += 1
        
        confidence -= extreme_count * 0.05
        
        if factors.education_level == 'advanced':
            confidence += 0.05
        elif factors.education_level == 'basic':
            confidence -= 0.05
        
        if factors.access_to_credit:
            confidence += 0.03
        
        return max(0.3, min(0.95, confidence))
    
    def _generate_recommendations(self, factors: AdoptionFactors, score: float) -> List[str]:
        """Generate recommendations based on weak factors."""
        recommendations = []
        
        if factors.economic_incentive < 0.5:
            recommendations.append("Improve economic incentives through subsidies or market access programs")
        
        if factors.social_influence < 0.5:
            recommendations.append("Establish farmer-to-farmer demonstration programs to leverage peer influence")
        
        if factors.resource_accessibility < 0.5:
            recommendations.append("Enhance access to required resources (seeds, equipment, inputs)")
        
        if factors.training_level < 0.5:
            recommendations.append("Increase training and extension services for CSA practices")
        
        if factors.risk_perception > 0.5:
            recommendations.append("Provide risk mitigation tools (insurance, guarantee programs)")
        
        if factors.policy_support < 0.5:
            recommendations.append("Strengthen policy support and regulatory framework for CSA adoption")
        
        if factors.technology_readiness < 0.5:
            recommendations.append("Invest in technology infrastructure and digital tools for farmers")
        
        if not factors.access_to_credit:
            recommendations.append("Establish credit facilities and microfinance options for smallholder farmers")
        
        if factors.farm_size < 5:
            recommendations.append("Consider group-based approaches for smallholder farmers to achieve economies of scale")
        
        if factors.years_farming < 10:
            recommendations.append("Target young farmers with innovative and technology-focused CSA practices")
        
        return recommendations
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for calculation."""
        return datetime.now().isoformat()
    
    def batch_calculate(self, factors_list: List[AdoptionFactors]) -> List[AdoptionRateResult]:
        """
        Calculate adoption rates for multiple communities.
        
        Args:
            factors_list: List of AdoptionFactors objects
            
        Returns:
            List of AdoptionRateResult objects
        """
        results = []
        for factors in factors_list:
            try:
                result = self.calculate_adoption_rate(factors)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to calculate adoption rate: {str(e)}")
                continue
        
        logger.info(f"Batch calculation completed: {len(results)}/{len(factors_list)} successful")
        return results
    
    def to_dataframe(self, results: List[AdoptionRateResult]) -> pd.DataFrame:
        """
        Convert adoption rate results to pandas DataFrame.
        
        Args:
            results: List of AdoptionRateResult objects
            
        Returns:
            pandas DataFrame with results
        """
        data = []
        for result in results:
            data.append({
                'community_id': result.community_id,
                'practice_type': result.practice_type,
                'predicted_adoption_rate': result.predicted_adoption_rate,
                'confidence_score': result.confidence_score,
                'recommendation_count': len(result.recommendations),
                'model_version': result.model_version,
                'calculation_timestamp': result.calculation_timestamp
            })
        
        return pd.DataFrame(data)


def calculate_adoption_rate_simple(
    economic_incentive: float,
    social_influence: float,
    resource_accessibility: float,
    training_level: float,
    risk_perception: float,
    policy_support: float,
    technology_readiness: float = 0.5,
    farm_size: float = 10.0,
    years_farming: int = 10,
    education_level: str = "intermediate",
    access_to_credit: bool = False
) -> Dict:
    """
    Simple function to calculate adoption rate without creating model instance.
    
    Args:
        economic_incentive: Economic incentive score (0-1)
        social_influence: Social influence score (0-1)
        resource_accessibility: Resource accessibility score (0-1)
        training_level: Training level score (0-1)
        risk_perception: Risk perception score (0-1, higher = more risk-averse)
        policy_support: Policy support score (0-1)
        technology_readiness: Technology readiness score (0-1, default 0.5)
        farm_size: Farm size in hectares (default 10)
        years_farming: Years of farming experience (default 10)
        education_level: Education level (basic, intermediate, advanced)
        access_to_credit: Whether farmer has access to credit
        
    Returns:
        Dictionary with adoption rate and analysis
    """
    factors = AdoptionFactors(
        economic_incentive=economic_incentive,
        social_influence=social_influence,
        resource_accessibility=resource_accessibility,
        training_level=training_level,
        risk_perception=risk_perception,
        policy_support=policy_support,
        technology_readiness=technology_readiness,
        farm_size=farm_size,
        years_farming=years_farming,
        education_level=education_level,
        access_to_credit=access_to_credit
    )
    
    model = AdoptionRateModel()
    result = model.calculate_adoption_rate(factors)
    
    return {
        'predicted_adoption_rate': result.predicted_adoption_rate,
        'confidence_score': result.confidence_score,
        'recommendations': result.recommendations,
        'model_version': result.model_version
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    sample_factors = AdoptionFactors(
        economic_incentive=0.7,
        social_influence=0.6,
        resource_accessibility=0.5,
        training_level=0.6,
        risk_perception=0.4,
        policy_support=0.5,
        technology_readiness=0.5,
        farm_size=15.0,
        years_farming=15,
        education_level="intermediate",
        access_to_credit=True
    )
    
    model = AdoptionRateModel()
    result = model.calculate_adoption_rate(sample_factors)
    
    print(f"Predicted Adoption Rate: {result.predicted_adoption_rate}%")
    print(f"Confidence Score: {result.confidence_score}")
    print(f"Recommendations: {len(result.recommendations)} items")
    for rec in result.recommendations:
        print(f"  - {rec}")