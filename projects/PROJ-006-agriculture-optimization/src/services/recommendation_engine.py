"""
CSA Recommendation Engine

Generates climate-smart agricultural practice recommendations based on:
1. Local climate and environmental conditions
2. Community socioeconomic profile
3. CSA principles (sustainability, ecosystem services, social equity)

This module integrates with T036 (recommendation logic) and T037 (principles).
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from src.models.principles import (
    PrincipleScorer,
    evaluate_practice,
    PrincipleCategory,
    PRACTICE_DATA_SCHEMA
)

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    """
    Structured recommendation output.

    Attributes:
        practice_id: Unique identifier for the recommended practice
        practice_name: Human-readable name
        confidence: Confidence score (0-1)
        justification: List of justification strings
        principle_scores: Dict of scores by principle category
        implementation_priority: Priority level (high/medium/low)
    """
    practice_id: str
    practice_name: str
    confidence: float
    justification: List[str]
    principle_scores: Dict[str, float]
    implementation_priority: str
    metadata: Dict = field(default_factory=dict)

@dataclass
class CommunityProfile:
    """
    Community context for recommendations.

    Attributes:
        region: Geographic region identifier
        climate_zone: Climate classification
        dominant_crops: List of main crops grown
        farm_size_avg: Average farm size (hectares)
        income_level: Economic classification (low/medium/high)
        gender_ratio: Women in farming (% of agricultural labor)
        water_availability: Water stress index (0-1, lower=better)
        soil_quality: Soil quality index (0-1)
    """
    region: str
    climate_zone: str
    dominant_crops: List[str]
    farm_size_avg: float
    income_level: str
    gender_ratio: float
    water_availability: float
    soil_quality: float


@dataclass
class Practice:
    """
    Agricultural practice definition.

    Attributes:
        practice_id: Unique identifier
        name: Human-readable name
        description: Detailed description
        required_resources: Dict of resource requirements
        principle_scores: Dict mapping metric names to values (0-1)
        applicable_crops: List of crops this applies to
        applicable_climates: List of climate zones
        min_farm_size: Minimum farm size for viability
    """
    practice_id: str
    name: str
    description: str
    required_resources: Dict[str, float]
    principle_scores: Dict[str, float]
    applicable_crops: List[str]
    applicable_climates: List[str]
    min_farm_size: float = 0.0


class RecommendationEngine:
    """
    Main recommendation engine integrating CSA principles.

    Usage:
        engine = RecommendationEngine()
        engine.load_practices("data/practices.json")
        recommendations = engine.generate_recommendations(community_profile)
    """

    def __init__(self, principle_threshold: float = 0.5):
        self._practices: List[Practice] = []
        self._principle_scorer = PrincipleScorer()
        self._principle_threshold = principle_threshold
        self._recommendation_cache: Dict[str, List[Recommendation]] = {}

    def load_practices(self, practices_path: str) -> None:
        """
        Load practices from JSON file.

        Expected format:
        [
            {
                "practice_id": "intercropping_001",
                "name": "Legume-Cereal Intercropping",
                "description": "...",
                "required_resources": {...},
                "principle_scores": {...},
                "applicable_crops": [...],
                "applicable_climates": [...],
                "min_farm_size": 0.5
            }
        ]
        """
        import json

        logger.info(f"Loading practices from {practices_path}")
        with open(practices_path, 'r') as f:
            data = json.load(f)

        self._practices = [
            Practice(
                practice_id=p["practice_id"],
                name=p["name"],
                description=p["description"],
                required_resources=p.get("required_resources", {}),
                principle_scores=p.get("principle_scores", {}),
                applicable_crops=p.get("applicable_crops", []),
                applicable_climates=p.get("applicable_climates", []),
                min_farm_size=p.get("min_farm_size", 0.0)
            )
            for p in data
        ]

        logger.info(f"Loaded {len(self._practices)} practices")

    def generate_recommendations(
        self,
        community: CommunityProfile,
        top_n: int = 5,
        min_confidence: float = 0.6
    ) -> List[Recommendation]:
        """
        Generate recommendations for a community.

        Args:
            community: Community profile for context
            top_n: Number of top recommendations to return
            min_confidence: Minimum confidence threshold

        Returns:
            List of recommendations sorted by confidence
        """
        cache_key = self._get_cache_key(community)
        if cache_key in self._recommendation_cache:
            logger.debug(f"Returning cached recommendations for {cache_key}")
            return self._recommendation_cache[cache_key][:top_n]

        recommendations = []

        for practice in self._practices:
            # Filter by applicability
            if not self._is_applicable(practice, community):
                continue

            # Calculate compatibility score
            compatibility = self._calculate_compatibility(practice, community)

            # Evaluate against CSA principles
            principle_evaluation = evaluate_practice(
                practice.practice_id,
                practice.principle_scores,
                threshold=self._principle_threshold
            )

            # Combine scores for final confidence
            confidence = self._calculate_confidence(
                compatibility,
                principle_evaluation["overall_score"]
            )

            if confidence >= min_confidence:
                recommendation = Recommendation(
                    practice_id=practice.practice_id,
                    practice_name=practice.name,
                    confidence=confidence,
                    justification=principle_evaluation["justification"],
                    principle_scores=principle_evaluation["category_scores"],
                    implementation_priority=self._get_priority(confidence),
                    metadata={
                        "description": practice.description,
                        "required_resources": practice.required_resources,
                        "min_farm_size": practice.min_farm_size
                    }
                )
                recommendations.append(recommendation)

        # Sort by confidence and cache
        recommendations.sort(key=lambda r: r.confidence, reverse=True)
        self._recommendation_cache[cache_key] = recommendations

        logger.info(
            f"Generated {len(recommendations)} recommendations "
            f"for community in {community.region}"
        )

        return recommendations[:top_n]

    def _is_applicable(
        self,
        practice: Practice,
        community: CommunityProfile
    ) -> bool:
        """Check if practice is applicable to this community"""
        # Check crop compatibility
        if practice.applicable_crops:
            if not any(crop in community.dominant_crops
                     for crop in practice.applicable_crops):
                return False

        # Check climate compatibility
        if practice.applicable_climates:
            if community.climate_zone not in practice.applicable_climates:
                return False

        # Check farm size viability
        if community.farm_size_avg < practice.min_farm_size:
            return False

        return True

    def _calculate_compatibility(
        self,
        practice: Practice,
        community: CommunityProfile
    ) -> float:
        """Calculate compatibility between practice and community"""
        compatibility_scores = []

        # Water availability match
        water_score = 1.0 - abs(
            practice.required_resources.get("water_stress_tolerance", 0.5) -
            (1 - community.water_availability)
        )
        compatibility_scores.append(water_score)

        # Soil quality match
        soil_score = 1.0 - abs(
            practice.required_resources.get("soil_quality_min", 0.5) -
            community.soil_quality
        )
        compatibility_scores.append(soil_score)

        # Economic accessibility (income level vs resource requirements)
        income_multipliers = {"low": 1.0, "medium": 1.5, "high": 2.0}
        income_mult = income_multipliers.get(community.income_level, 1.0)
        resource_cost = sum(
            practice.required_resources.values()
        ) / 10.0  # Normalize
        economic_score = max(0, 1.0 - resource_cost / income_mult)
        compatibility_scores.append(economic_score)

        return sum(compatibility_scores) / len(compatibility_scores)

    def _calculate_confidence(
        self,
        compatibility: float,
        principle_score: float
    ) -> float:
        """Calculate final confidence score"""
        # Weight principles slightly higher for CSA alignment
        return 0.4 * compatibility + 0.6 * principle_score

    def _get_priority(self, confidence: float) -> str:
        """Determine implementation priority based on confidence"""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.65:
            return "medium"
        else:
            return "low"

    def _get_cache_key(self, community: CommunityProfile) -> str:
        """Generate cache key for community"""
        return f"{community.region}_{community.climate_zone}"

    def get_principle_report(
        self,
        recommendations: List[Recommendation]
    ) -> Dict:
        """
        Generate summary report on principle alignment.

        Returns aggregated scores across all recommendations.
        """
        if not recommendations:
            return {"error": "No recommendations provided"}

        category_totals = {
            cat.value: 0.0 for cat in PrincipleCategory
        }
        category_counts = {
            cat.value: 0 for cat in PrincipleCategory
        }

        for rec in recommendations:
            for cat, score in rec.principle_scores.items():
                category_totals[cat] += score
                category_counts[cat] += 1

        averages = {
            cat: category_totals[cat] / category_counts[cat]
            for cat in category_totals
            if category_counts[cat] > 0
        }

        return {
            "total_recommendations": len(recommendations),
            "category_averages": averages,
            "overall_alignment": sum(averages.values()) / len(averages)
            if averages else 0.0
        }


# =========================================================================
# CONVENIENCE FUNCTIONS
# =========================================================================
def generate_recommendations_for_region(
    region: str,
    climate_zone: str,
    practices_file: str = "data/practices.json"
) -> List[Recommendation]:
    """
    Convenience function for generating recommendations.

    Creates a default community profile and returns recommendations.
    """
    default_community = CommunityProfile(
        region=region,
        climate_zone=climate_zone,
        dominant_crops=["maize", "cassava"],
        farm_size_avg=2.0,
        income_level="low",
        gender_ratio=0.45,
        water_availability=0.6,
        soil_quality=0.5
    )

    engine = RecommendationEngine()
    engine.load_practices(practices_file)

    return engine.generate_recommendations(default_community)