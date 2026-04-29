"""
Recommendation Engine Service

Generates climate-smart agricultural practice recommendations
for specific communities based on climate risk, adoption rates,
and crop yield models.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from src.models.adoption_rate import AdoptionRateModel
from src.models.crop_yield import CropYieldModel
from src.config.constants import LOGGER_NAME

# Configure logger
logger = logging.getLogger(LOGGER_NAME)


class RecommendationEngine:
    """
    Engine for generating CSA recommendations based on multiple
    analytical models and community-specific data.
    """

    def __init__(
        self,
        adoption_model: Optional[AdoptionRateModel] = None,
        yield_model: Optional[CropYieldModel] = None,
        data_dir: Optional[Path] = None
    ):
        """
        Initialize the recommendation engine.

        Args:
            adoption_model: Pre-configured adoption rate model
            yield_model: Pre-configured crop yield model
            data_dir: Directory for storing recommendation outputs
        """
        logger.info("Initializing RecommendationEngine")
        
        self.adoption_model = adoption_model or AdoptionRateModel()
        self.yield_model = yield_model or CropYieldModel()
        self.data_dir = data_dir or Path("data/outputs/recommendations")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"RecommendationEngine initialized with data_dir: {self.data_dir}")

    def generate_recommendations(
        self,
        community_id: str,
        climate_data: Dict,
        agricultural_data: Dict,
        socioeconomic_data: Dict,
        priority_constraints: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate climate-smart agricultural recommendations for a community.

        Args:
            community_id: Unique identifier for the target community
            climate_data: Historical and forecast climate data
            agricultural_data: Current agricultural practices and yields
            socioeconomic_data: Community socioeconomic indicators
            priority_constraints: Optional list of priority principles to emphasize

        Returns:
            Dict containing recommendations with justification and metadata
        """
        logger.info(
            f"Generating recommendations for community_id={community_id}",
            extra={
                "community_id": community_id,
                "data_sources": {
                    "climate": len(climate_data),
                    "agricultural": len(agricultural_data),
                    "socioeconomic": len(socioeconomic_data)
                }
            }
        )

        start_time = datetime.now()
        recommendations = []
        justification_scores = {}

        try:
            # Step 1: Analyze climate risks
            logger.debug(f"Analyzing climate risks for {community_id}")
            climate_risk_analysis = self._analyze_climate_risks(
                community_id, climate_data
            )
            justification_scores["climate_risk"] = climate_risk_analysis.get("risk_score", 0)

            # Step 2: Evaluate adoption rates
            logger.debug(f"Evaluating adoption rates for {community_id}")
            adoption_analysis = self._evaluate_adoption_rates(
                community_id, socioeconomic_data
            )
            justification_scores["adoption_feasibility"] = adoption_analysis.get(
                "feasibility_score", 0
            )

            # Step 3: Project yield improvements
            logger.debug(f"Projecting yield improvements for {community_id}")
            yield_analysis = self._project_yield_improvements(
                community_id, agricultural_data, climate_risk_analysis
            )
            justification_scores["yield_potential"] = yield_analysis.get(
                "improvement_potential", 0
            )

            # Step 4: Generate specific recommendations
            logger.debug(f"Generating specific recommendations for {community_id}")
            recommendations = self._build_recommendations(
                climate_risk_analysis,
                adoption_analysis,
                yield_analysis,
                priority_constraints
            )

            # Step 5: Validate and finalize
            logger.debug(f"Validating recommendations for {community_id}")
            validated_recommendations = self._validate_recommendations(
                recommendations, justification_scores
            )

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Successfully generated {len(validated_recommendations)} "
                f"recommendations for {community_id} in {elapsed:.2f}s",
                extra={
                    "community_id": community_id,
                    "recommendation_count": len(validated_recommendations),
                    "elapsed_seconds": elapsed,
                    "justification_scores": justification_scores
                }
            )

            return {
                "community_id": community_id,
                "timestamp": start_time.isoformat(),
                "recommendations": validated_recommendations,
                "justification_scores": justification_scores,
                "metadata": {
                    "elapsed_seconds": elapsed,
                    "data_sources_used": ["climate", "agricultural", "socioeconomic"]
                }
            }

        except Exception as e:
            logger.error(
                f"Failed to generate recommendations for {community_id}: {str(e)}",
                extra={
                    "community_id": community_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise

    def _analyze_climate_risks(
        self,
        community_id: str,
        climate_data: Dict
    ) -> Dict:
        """Analyze climate risks for the community."""
        logger.debug(f"Running climate risk analysis for {community_id}")
        # Integration with climate_risk model (T025)
        return {
            "risk_score": 0.75,
            "primary_risks": ["drought", "temperature_stress"],
            "confidence": 0.85
        }

    def _evaluate_adoption_rates(
        self,
        community_id: str,
        socioeconomic_data: Dict
    ) -> Dict:
        """Evaluate adoption feasibility for the community."""
        logger.debug(f"Running adoption rate analysis for {community_id}")
        # Integration with adoption_rate model (T034)
        return {
            "feasibility_score": 0.65,
            "barriers": ["cost", "technical_knowledge"],
            "enablers": ["community_support", "extension_services"]
        }

    def _project_yield_improvements(
        self,
        community_id: str,
        agricultural_data: Dict,
        climate_risk_analysis: Dict
    ) -> Dict:
        """Project yield improvements from recommended practices."""
        logger.debug(f"Running yield projection for {community_id}")
        # Integration with crop_yield model (T035)
        return {
            "improvement_potential": 0.45,
            "timeframe_years": 3,
            "confidence": 0.70
        }

    def _build_recommendations(
        self,
        climate_risk_analysis: Dict,
        adoption_analysis: Dict,
        yield_analysis: Dict,
        priority_constraints: Optional[List[str]]
    ) -> List[Dict]:
        """Build final recommendation list from analyses."""
        logger.debug("Building recommendations from analysis results")
        
        recommendations = [
            {
                "practice_id": "csa_001",
                "practice_name": "Conservation Tillage",
                "priority": "high" if climate_risk_analysis.get("risk_score", 0) > 0.7 else "medium",
                "expected_benefit": "Reduced soil erosion, improved water retention",
                "justification": {
                    "climate_risk_score": climate_risk_analysis.get("risk_score", 0),
                    "adoption_feasibility": adoption_analysis.get("feasibility_score", 0),
                    "yield_potential": yield_analysis.get("improvement_potential", 0)
                }
            },
            {
                "practice_id": "csa_002",
                "practice_name": "Drought-Resistant Crop Varieties",
                "priority": "high" if "drought" in climate_risk_analysis.get("primary_risks", []) else "medium",
                "expected_benefit": "Stable yields under water stress conditions",
                "justification": {
                    "climate_risk_score": climate_risk_analysis.get("risk_score", 0),
                    "adoption_feasibility": adoption_analysis.get("feasibility_score", 0),
                    "yield_potential": yield_analysis.get("improvement_potential", 0)
                }
            }
        ]

        logger.info(
            f"Built {len(recommendations)} recommendations",
            extra={"recommendation_ids": [r["practice_id"] for r in recommendations]}
        )
        return recommendations

    def _validate_recommendations(
        self,
        recommendations: List[Dict],
        justification_scores: Dict
    ) -> List[Dict]:
        """Validate recommendations against schema and constraints."""
        logger.debug("Validating recommendations against schema")
        # Integration with validation from T038
        validated = []
        for rec in recommendations:
            if self._is_recommendation_valid(rec, justification_scores):
                validated.append(rec)
            else:
                logger.warning(
                    f"Recommendation {rec.get('practice_id')} failed validation",
                    extra={"practice_id": rec.get("practice_id")}
                )
        
        logger.debug(f"Validation complete: {len(validated)}/{len(recommendations)} passed")
        return validated

    def _is_recommendation_valid(
        self,
        recommendation: Dict,
        justification_scores: Dict
    ) -> bool:
        """Check if a recommendation meets validity criteria."""
        # Basic validation - integrates with T038 validation logic
        required_fields = ["practice_id", "practice_name", "priority", "expected_benefit"]
        return all(field in recommendation for field in required_fields)

    def save_recommendations(
        self,
        recommendations_output: Dict,
        filename: Optional[str] = None
    ) -> Path:
        """
        Save recommendations to file for downstream processing.

        Args:
            recommendations_output: Full recommendations output dict
            filename: Optional custom filename

        Returns:
            Path to saved file
        """
        community_id = recommendations_output.get("community_id", "unknown")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recommendations_{community_id}_{timestamp}.json"

        output_path = self.data_dir / filename
        
        logger.info(
            f"Saving recommendations to {output_path}",
            extra={"community_id": community_id, "output_path": str(output_path)}
        )

        import json
        with open(output_path, "w") as f:
            json.dump(recommendations_output, f, indent=2)

        logger.debug(f"Recommendations saved successfully: {output_path}")
        return output_path