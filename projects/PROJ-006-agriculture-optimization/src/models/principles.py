"""
CSA Principles Module - Sustainability, Ecosystem Services, and Social Equity

This module defines the core principles for Climate-Smart Agricultural (CSA)
recommendation scoring and evaluation. These principles ensure that all
recommendations align with:

1. Sustainability - Long-term agricultural viability
2. Ecosystem Services - Environmental benefits and biodiversity
3. Social Equity - Fair access and community benefit

References:
- FAO Climate-Smart Agriculture Sourcebook (2013)
- IPCC Special Report on Climate Change and Land (2019)
- UN Sustainable Development Goals (SDGs 2, 12, 13)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Callable
import numpy as np


class PrincipleCategory(Enum):
    """Categories of CSA principles for scoring"""
    SUSTAINABILITY = "sustainability"
    ECOSYSTEM_SERVICE = "ecosystem_service"
    SOCIAL_EQUITY = "social_equity"


@dataclass
class PrincipleMetric:
    """
    Definition of a single principle metric.

    Attributes:
        name: Unique identifier for the metric
        category: Which principle category this belongs to
        description: Human-readable description
        weight: Relative importance (0-1, normalized internally)
        min_value: Minimum acceptable value (if applicable)
        max_value: Maximum acceptable value (if applicable)
        scoring_fn: Optional custom scoring function
    """
    name: str
    category: PrincipleCategory
    description: str
    weight: float = 1.0
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    scoring_fn: Optional[Callable[[float], float]] = None


# =========================================================================
# SUSTAINABILITY PRINCIPLES
# =========================================================================
SUSTAINABILITY_METRICS: List[PrincipleMetric] = [
    PrincipleMetric(
        name="soil_health",
        category=PrincipleCategory.SUSTAINABILITY,
        description="Maintains or improves soil organic matter and structure",
        weight=1.2,
        min_value=0.0,
        max_value=1.0,
        scoring_fn=lambda x: np.clip(x, 0, 1)
    ),
    PrincipleMetric(
        name="water_efficiency",
        category=PrincipleCategory.SUSTAINABILITY,
        description="Reduces water consumption per unit of yield",
        weight=1.1,
        min_value=0.0,
        max_value=1.0,
        scoring_fn=lambda x: np.clip(x, 0, 1)
    ),
    PrincipleMetric(
        name="input_reduction",
        category=PrincipleCategory.SUSTAINABILITY,
        description="Decreases reliance on synthetic fertilizers and pesticides",
        weight=1.0,
        min_value=0.0,
        max_value=1.0,
        scoring_fn=lambda x: np.clip(x, 0, 1)
    ),
    PrincipleMetric(
        name="economic_viability",
        category=PrincipleCategory.SUSTAINABILITY,
        description="Provides long-term economic returns for farmers",
        weight=1.3,
        min_value=0.0,
        max_value=1.0,
        scoring_fn=lambda x: np.clip(x, 0, 1)
    ),
    PrincipleMetric(
        name="climate_resilience",
        category=PrincipleCategory.SUSTAINABILITY,
        description="Builds adaptive capacity to climate variability",
        weight=1.4,
        min_value=0.0,
        max_value=1.0,
        scoring_fn=lambda x: np.clip(x, 0, 1)
    ),
]


# =========================================================================
# ECOSYSTEM SERVICES PRINCIPLES
# =========================================================================
ECOSYSTEM_METRICS: List[PrincipleMetric] = [
    PrincipleMetric(
        name="biodiversity_impact",
        category=PrincipleCategory.ECOSYSTEM_SERVICE,
        description="Supports or enhances local biodiversity",
        weight=1.3,
        min_value=0.0,
        max_value=1.0,
        scoring_fn=lambda x: np.clip(x, 0, 1)
    ),
    PrincipleMetric(
        name="carbon_sequestration",
        category=PrincipleCategory.ECOSYSTEM_SERVICE,
        description="Contributes to carbon storage in soils and biomass",
        weight=1.2,
        min_value=0.0,
        max_value=1.0,
        scoring_fn=lambda x: np.clip(x, 0, 1)
    ),
    PrincipleMetric(
        name="pollinator_support",
        category=PrincipleCategory.ECOSYSTEM_SERVICE,
        description="Provides habitat and resources for pollinators",
        weight=1.1,
        min_value=0.0,
        max_value=1.0,
        scoring_fn=lambda x: np.clip(x, 0, 1)
    ),
    PrincipleMetric(
        name="water_quality",
        category=PrincipleCategory.ECOSYSTEM_SERVICE,
        description="Reduces nutrient and chemical runoff to waterways",
        weight=1.2,
        min_value=0.0,
        max_value=1.0,
        scoring_fn=lambda x: np.clip(x, 0, 1)
    ),
    PrincipleMetric(
        name="habitat_connectivity",
        category=PrincipleCategory.ECOSYSTEM_SERVICE,
        description="Maintains ecological corridors and habitat patches",
        weight=1.0,
        min_value=0.0,
        max_value=1.0,
        scoring_fn=lambda x: np.clip(x, 0, 1)
    ),
]


# =========================================================================
# SOCIAL EQUITY PRINCIPLES
# =========================================================================
SOCIAL_EQUITY_METRICS: List[PrincipleMetric] = [
    PrincipleMetric(
        name="accessibility",
        category=PrincipleCategory.SOCIAL_EQUITY,
        description="Accessible to smallholder and resource-poor farmers",
        weight=1.4,
        min_value=0.0,
        max_value=1.0,
        scoring_fn=lambda x: np.clip(x, 0, 1)
    ),
    PrincipleMetric(
        name="gender_inclusion",
        category=PrincipleCategory.SOCIAL_EQUITY,
        description="Benefits women farmers equally with men",
        weight=1.3,
        min_value=0.0,
        max_value=1.0,
        scoring_fn=lambda x: np.clip(x, 0, 1)
    ),
    PrincipleMetric(
        name="knowledge_transfer",
        category=PrincipleCategory.SOCIAL_EQUITY,
        description="Builds local capacity and indigenous knowledge",
        weight=1.2,
        min_value=0.0,
        max_value=1.0,
        scoring_fn=lambda x: np.clip(x, 0, 1)
    ),
    PrincipleMetric(
        name="food_security",
        category=PrincipleCategory.SOCIAL_EQUITY,
        description="Improves local food availability and nutrition",
        weight=1.5,
        min_value=0.0,
        max_value=1.0,
        scoring_fn=lambda x: np.clip(x, 0, 1)
    ),
    PrincipleMetric(
        name="labor_conditions",
        category=PrincipleCategory.SOCIAL_EQUITY,
        description="Ensures fair labor practices and working conditions",
        weight=1.3,
        min_value=0.0,
        max_value=1.0,
        scoring_fn=lambda x: np.clip(x, 0, 1)
    ),
]


# =========================================================================
# PRINCIPLE SCORING ENGINE
# =========================================================================
class PrincipleScorer:
    """
    Scores agricultural practices against CSA principles.

    Usage:
        scorer = PrincipleScorer()
        scores = scorer.evaluate(practice_data)
        overall = scorer.get_overall_score(scores)
    """

    def __init__(self):
        self._all_metrics = (
            SUSTAINABILITY_METRICS +
            ECOSYSTEM_METRICS +
            SOCIAL_EQUITY_METRICS
        )
        self._normalize_weights()

    def _normalize_weights(self) -> None:
        """Normalize weights within each category to sum to 1.0"""
        for category in PrincipleCategory:
            category_metrics = [
                m for m in self._all_metrics if m.category == category
            ]
            total_weight = sum(m.weight for m in category_metrics)
            for metric in category_metrics:
                metric.weight = metric.weight / total_weight

    def evaluate(
        self,
        practice_data: Dict[str, float],
        metric_filter: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Evaluate a practice against all principle metrics.

        Args:
            practice_data: Dict mapping metric names to values (0-1 scale)
            metric_filter: Optional list of metric names to include

        Returns:
            Nested dict with category scores and individual metric scores
        """
        results = {
            category.value: {
                "metrics": {},
                "category_score": 0.0
            }
            for category in PrincipleCategory
        }

        for metric in self._all_metrics:
            if metric_filter and metric.name not in metric_filter:
                continue

            value = practice_data.get(metric.name, 0.5)
            score = self._score_metric(metric, value)
            results[metric.category.value]["metrics"][metric.name] = {
                "score": score,
                "weight": metric.weight,
                "description": metric.description
            }

        # Calculate category scores (weighted average)
        for category in PrincipleCategory:
            category_data = results[category.value]
            metrics = category_data["metrics"]
            if metrics:
                total_weight = sum(m["weight"] for m in metrics.values())
                weighted_sum = sum(
                    m["score"] * m["weight"]
                    for m in metrics.values()
                )
                category_data["category_score"] = weighted_sum / total_weight

        return results

    def _score_metric(
        self,
        metric: PrincipleMetric,
        value: float
    ) -> float:
        """Score a single metric value"""
        # Apply value constraints if specified
        if metric.min_value is not None:
            value = max(value, metric.min_value)
        if metric.max_value is not None:
            value = min(value, metric.max_value)

        # Apply custom scoring function or use raw value
        if metric.scoring_fn:
            return metric.scoring_fn(value)
        return np.clip(value, 0, 1)

    def get_overall_score(
        self,
        evaluation_results: Dict[str, Dict[str, float]]
    ) -> float:
        """
        Calculate overall CSA principle score.

        Returns weighted average across all three categories.
        """
        category_scores = [
            evaluation_results[cat.value]["category_score"]
            for cat in PrincipleCategory
        ]
        # Equal weighting across categories by default
        return sum(category_scores) / len(category_scores)

    def get_justification(
        self,
        evaluation_results: Dict[str, Dict[str, float]]
    ) -> List[str]:
        """
        Generate human-readable justification for scores.

        Returns list of justification strings for reporting.
        """
        justifications = []

        for category in PrincipleCategory:
            cat_data = evaluation_results[category.value]
            cat_score = cat_data["category_score"]
            score_desc = "High" if cat_score >= 0.7 else \
                        "Moderate" if cat_score >= 0.4 else "Low"
            justifications.append(
                f"{category.value.replace('_', ' ').title()}: "
                f"{score_desc} ({cat_score:.2f})"
            )

            for metric_name, metric_data in cat_data["metrics"].items():
                if metric_data["score"] >= 0.7:
                    justifications.append(
                        f"  ✓ {metric_name}: {metric_data['description']}"
                    )

        return justifications


# =========================================================================
# PRACTICE EVALUATION HELPER
# =========================================================================
def evaluate_practice(
    practice_id: str,
    practice_data: Dict[str, float],
    threshold: float = 0.5
) -> Dict:
    """
    Convenience function to evaluate a single practice.

    Args:
        practice_id: Unique identifier for the practice
        practice_data: Metric values for this practice
        threshold: Minimum score to be considered CSA-aligned

    Returns:
        Dict with scores, justification, and alignment status
    """
    scorer = PrincipleScorer()
    evaluation = scorer.evaluate(practice_data)
    overall = scorer.get_overall_score(evaluation)
    justification = scorer.get_justification(evaluation)

    return {
        "practice_id": practice_id,
        "overall_score": overall,
        "is_csa_aligned": overall >= threshold,
        "category_scores": {
            cat.value: evaluation[cat.value]["category_score"]
            for cat in PrincipleCategory
        },
        "justification": justification,
        "detailed_metrics": evaluation
    }


# =========================================================================
# DEFAULT PRACTICE DATA SCHEMAS
# =========================================================================
PRACTICE_DATA_SCHEMA = {
    "sustainability": {
        "soil_health": "float (0-1)",
        "water_efficiency": "float (0-1)",
        "input_reduction": "float (0-1)",
        "economic_viability": "float (0-1)",
        "climate_resilience": "float (0-1)",
    },
    "ecosystem_service": {
        "biodiversity_impact": "float (0-1)",
        "carbon_sequestration": "float (0-1)",
        "pollinator_support": "float (0-1)",
        "water_quality": "float (0-1)",
        "habitat_connectivity": "float (0-1)",
    },
    "social_equity": {
        "accessibility": "float (0-1)",
        "gender_inclusion": "float (0-1)",
        "knowledge_transfer": "float (0-1)",
        "food_security": "float (0-1)",
        "labor_conditions": "float (0-1)",
    }
}
