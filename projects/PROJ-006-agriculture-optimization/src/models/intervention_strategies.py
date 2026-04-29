"""
Intervention Strategies Module for Climate-Smart Agriculture

This module implements intervention strategy classes that define
climate-smart agricultural practices with their characteristics,
expected outcomes, and implementation requirements.

Part of User Story 3: CSA Recommendation Engine
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from src.config.schemas import validate_schema
from src.data.cache import get_cache

logger = logging.getLogger(__name__)


class InterventionType(Enum):
    """Types of climate-smart agricultural interventions."""
    SOIL_MANAGEMENT = "soil_management"
    WATER_CONSERVATION = "water_conservation"
    CROP_DIVERSIFICATION = "crop_diversification"
    AGROFORESTRY = "agroforestry"
    INTEGRATED_PEST = "integrated_pest_management"
    CLIMATE_RESILIENT_CROPS = "climate_resilient_crops"
    NUTRIENT_MANAGEMENT = "nutrient_management"
    LIVESTOCK_INTEGRATION = "livestock_integration"


class ImplementationScale(Enum):
    """Scale of intervention implementation."""
    HOUSEHOLD = "household"
    COMMUNITY = "community"
    REGIONAL = "regional"
    NATIONAL = "national"


@dataclass
class InterventionCost:
    """Cost structure for an intervention."""
    initial_capital: float  # USD per hectare
    annual_maintenance: float  # USD per hectare per year
    labor_hours_per_year: float
    subsidy_eligible: bool = True
    financing_available: bool = True

    def validate(self) -> bool:
        """Validate cost values are non-negative."""
        if self.initial_capital < 0:
            logger.error("Initial capital cannot be negative")
            return False
        if self.annual_maintenance < 0:
            logger.error("Annual maintenance cannot be negative")
            return False
        if self.labor_hours_per_year < 0:
            logger.error("Labor hours cannot be negative")
            return False
        return True


@dataclass
class InterventionOutcome:
    """Expected outcomes of an intervention."""
    yield_increase_pct: float  # Expected yield increase percentage
    carbon_sequestration_kg_ha: float  # kg CO2 equivalent per hectare per year
    water_savings_pct: float  # Percentage water savings
    income_increase_pct: float  # Expected income increase percentage
    risk_reduction_score: float  # 0-10 scale for climate risk reduction

    def validate(self) -> bool:
        """Validate outcome values are within reasonable bounds."""
        if not 0 <= self.yield_increase_pct <= 200:
            logger.error(f"Yield increase {self.yield_increase_pct}% out of bounds")
            return False
        if self.carbon_sequestration_kg_ha < 0:
            logger.error("Carbon sequestration cannot be negative")
            return False
        if not 0 <= self.water_savings_pct <= 100:
            logger.error(f"Water savings {self.water_savings_pct}% out of bounds")
            return False
        if not 0 <= self.income_increase_pct <= 500:
            logger.error(f"Income increase {self.income_increase_pct}% out of bounds")
            return False
        if not 0 <= self.risk_reduction_score <= 10:
            logger.error(f"Risk reduction {self.risk_reduction_score} out of bounds")
            return False
        return True


@dataclass
class InterventionStrategy:
    """
    Climate-smart agricultural intervention strategy.

    This class represents a specific agricultural practice or combination
    of practices that can be recommended to communities for climate
    adaptation and mitigation.
    """
    id: str
    name: str
    intervention_type: InterventionType
    implementation_scale: ImplementationScale
    description: str
    cost: InterventionCost
    outcomes: InterventionOutcome
    implementation_timeline_months: int
    technical_complexity: int  # 1-10 scale
    prerequisites: List[str] = field(default_factory=list)
    compatible_crops: List[str] = field(default_factory=list)
    climate_zones: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """
        Validate the intervention strategy.

        Returns:
            bool: True if valid, False otherwise
        """
        logger.debug(f"Validating intervention strategy: {self.id}")

        # Validate cost structure
        if not self.cost.validate():
            logger.error(f"Cost validation failed for {self.id}")
            return False

        # Validate outcomes
        if not self.outcomes.validate():
            logger.error(f"Outcome validation failed for {self.id}")
            return False

        # Validate technical complexity
        if not 1 <= self.technical_complexity <= 10:
            logger.error(f"Technical complexity {self.technical_complexity} out of bounds")
            return False

        # Validate timeline
        if self.implementation_timeline_months <= 0:
            logger.error(f"Timeline must be positive for {self.id}")
            return False

        logger.info(f"Intervention strategy {self.id} validated successfully")
        return True

    def get_adoption_score(self, community_profile: Dict[str, Any]) -> float:
        """
        Calculate adoption score based on community profile.

        Args:
            community_profile: Dictionary with community characteristics

        Returns:
            float: Adoption score 0-100
        """
        score = 50.0  # Base score

        # Adjust for financial capacity
        financial_capacity = community_profile.get("financial_capacity", 0.5)
        if self.cost.subsidy_eligible:
            score += 15 * financial_capacity
        else:
            score += 10 * financial_capacity

        # Adjust for technical capacity
        technical_capacity = community_profile.get("technical_capacity", 0.5)
        complexity_factor = (11 - self.technical_complexity) / 10
        score += 20 * technical_capacity * complexity_factor

        # Adjust for climate zone match
        community_zone = community_profile.get("climate_zone", "")
        if community_zone in self.climate_zones:
            score += 15

        return min(100.0, max(0.0, score))

    def to_dict(self) -> Dict[str, Any]:
        """Convert intervention strategy to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "intervention_type": self.intervention_type.value,
            "implementation_scale": self.implementation_scale.value,
            "description": self.description,
            "cost": {
                "initial_capital": self.cost.initial_capital,
                "annual_maintenance": self.cost.annual_maintenance,
                "labor_hours_per_year": self.cost.labor_hours_per_year,
                "subsidy_eligible": self.cost.subsidy_eligible,
                "financing_available": self.cost.financing_available
            },
            "outcomes": {
                "yield_increase_pct": self.outcomes.yield_increase_pct,
                "carbon_sequestration_kg_ha": self.outcomes.carbon_sequestration_kg_ha,
                "water_savings_pct": self.outcomes.water_savings_pct,
                "income_increase_pct": self.outcomes.income_increase_pct,
                "risk_reduction_score": self.outcomes.risk_reduction_score
            },
            "implementation_timeline_months": self.implementation_timeline_months,
            "technical_complexity": self.technical_complexity,
            "prerequisites": self.prerequisites,
            "compatible_crops": self.compatible_crops,
            "climate_zones": self.climate_zones,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterventionStrategy":
        """Create intervention strategy from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            intervention_type=InterventionType(data["intervention_type"]),
            implementation_scale=ImplementationScale(data["implementation_scale"]),
            description=data["description"],
            cost=InterventionCost(
                initial_capital=data["cost"]["initial_capital"],
                annual_maintenance=data["cost"]["annual_maintenance"],
                labor_hours_per_year=data["cost"]["labor_hours_per_year"],
                subsidy_eligible=data["cost"].get("subsidy_eligible", True),
                financing_available=data["cost"].get("financing_available", True)
            ),
            outcomes=InterventionOutcome(
                yield_increase_pct=data["outcomes"]["yield_increase_pct"],
                carbon_sequestration_kg_ha=data["outcomes"]["carbon_sequestration_kg_ha"],
                water_savings_pct=data["outcomes"]["water_savings_pct"],
                income_increase_pct=data["outcomes"]["income_increase_pct"],
                risk_reduction_score=data["outcomes"]["risk_reduction_score"]
            ),
            implementation_timeline_months=data["implementation_timeline_months"],
            technical_complexity=data["technical_complexity"],
            prerequisites=data.get("prerequisites", []),
            compatible_crops=data.get("compatible_crops", []),
            climate_zones=data.get("climate_zones", []),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            last_updated=datetime.fromisoformat(data["last_updated"]) if "last_updated" in data else datetime.now(),
            metadata=data.get("metadata", {})
        )


class InterventionRepository:
    """
    Repository for managing intervention strategies.

    Provides methods to register, retrieve, and query intervention
    strategies with caching support.
    """

    def __init__(self):
        self._strategies: Dict[str, InterventionStrategy] = {}
        self._cache = get_cache()
        logger.info("InterventionRepository initialized")

    def register(self, strategy: InterventionStrategy) -> bool:
        """
        Register a new intervention strategy.

        Args:
            strategy: InterventionStrategy to register

        Returns:
            bool: True if registered successfully
        """
        if not strategy.validate():
            logger.error(f"Failed to register invalid strategy: {strategy.id}")
            return False

        self._strategies[strategy.id] = strategy
        logger.info(f"Registered intervention strategy: {strategy.id}")
        return True

    def get(self, strategy_id: str) -> Optional[InterventionStrategy]:
        """
        Get a strategy by ID.

        Args:
            strategy_id: Unique identifier

        Returns:
            InterventionStrategy or None
        """
        # Check cache first
        cache_key = f"intervention:{strategy_id}"
        cached = self._cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for {strategy_id}")
            return cached

        # Check in-memory
        strategy = self._strategies.get(strategy_id)
        if strategy:
            self._cache.set(cache_key, strategy, ttl=3600)
            return strategy

        logger.warning(f"Strategy not found: {strategy_id}")
        return None

    def query_by_type(self, intervention_type: InterventionType) -> List[InterventionStrategy]:
        """Query strategies by intervention type."""
        return [
            s for s in self._strategies.values()
            if s.intervention_type == intervention_type
        ]

    def query_by_scale(self, scale: ImplementationScale) -> List[InterventionStrategy]:
        """Query strategies by implementation scale."""
        return [
            s for s in self._strategies.values()
            if s.implementation_scale == scale
        ]

    def query_by_complexity(self, max_complexity: int) -> List[InterventionStrategy]:
        """Query strategies by maximum technical complexity."""
        return [
            s for s in self._strategies.values()
            if s.technical_complexity <= max_complexity
        ]

    def query_by_climate_zone(self, climate_zone: str) -> List[InterventionStrategy]:
        """Query strategies compatible with a climate zone."""
        return [
            s for s in self._strategies.values()
            if climate_zone in s.climate_zones
        ]

    def get_all(self) -> List[InterventionStrategy]:
        """Get all registered strategies."""
        return list(self._strategies.values())

    def clear_cache(self):
        """Clear the strategy cache."""
        self._cache.clear_pattern("intervention:*")
        logger.info("Intervention strategy cache cleared")


# Global repository instance
_repository: Optional[InterventionRepository] = None


def get_intervention_repository() -> InterventionRepository:
    """Get or create the global intervention repository."""
    global _repository
    if _repository is None:
        _repository = InterventionRepository()
    return _repository


def register_intervention_strategy(strategy: InterventionStrategy) -> bool:
    """Convenience function to register a strategy."""
    return get_intervention_repository().register(strategy)


def get_intervention_strategy(strategy_id: str) -> Optional[InterventionStrategy]:
    """Convenience function to get a strategy by ID."""
    return get_intervention_repository().get(strategy_id)

# Example intervention strategies (can be extended with more)
EXAMPLE_STRATEGIES = [
    InterventionStrategy(
        id="IS001",
        name="Conservation Tillage",
        intervention_type=InterventionType.SOIL_MANAGEMENT,
        implementation_scale=ImplementationScale.HOUSEHOLD,
        description="Reduce soil disturbance through minimal tillage practices",
        cost=InterventionCost(
            initial_capital=150.0,
            annual_maintenance=50.0,
            labor_hours_per_year=20.0,
            subsidy_eligible=True
        ),
        outcomes=InterventionOutcome(
            yield_increase_pct=15.0,
            carbon_sequestration_kg_ha=500.0,
            water_savings_pct=25.0,
            income_increase_pct=10.0,
            risk_reduction_score=7.0
        ),
        implementation_timeline_months=12,
        technical_complexity=4,
        prerequisites=["Soil health assessment", "Tillage equipment"],
        compatible_crops=["maize", "wheat", "sorghum", "millet"],
        climate_zones=["tropical", "subtropical", "temperate"]
    ),
    InterventionStrategy(
        id="IS002",
        name="Drip Irrigation System",
        intervention_type=InterventionType.WATER_CONSERVATION,
        implementation_scale=ImplementationScale.HOUSEHOLD,
        description="Efficient water delivery system for crops",
        cost=InterventionCost(
            initial_capital=800.0,
            annual_maintenance=100.0,
            labor_hours_per_year=30.0,
            subsidy_eligible=True,
            financing_available=True
        ),
        outcomes=InterventionOutcome(
            yield_increase_pct=30.0,
            carbon_sequestration_kg_ha=100.0,
            water_savings_pct=50.0,
            income_increase_pct=25.0,
            risk_reduction_score=8.0
        ),
        implementation_timeline_months=6,
        technical_complexity=6,
        prerequisites=["Water source access", "Basic plumbing skills"],
        compatible_crops=["vegetables", "fruits", "maize", "cotton"],
        climate_zones=["arid", "semi-arid", "tropical"]
    ),
    InterventionStrategy(
        id="IS003",
        name="Agroforestry Integration",
        intervention_type=InterventionType.AGROFORESTRY,
        implementation_scale=ImplementationScale.COMMUNITY,
        description="Integrate trees with crops for multiple benefits",
        cost=InterventionCost(
            initial_capital=300.0,
            annual_maintenance=75.0,
            labor_hours_per_year=40.0,
            subsidy_eligible=True
        ),
        outcomes=InterventionOutcome(
            yield_increase_pct=20.0,
            carbon_sequestration_kg_ha=1500.0,
            water_savings_pct=15.0,
            income_increase_pct=35.0,
            risk_reduction_score=9.0
        ),
        implementation_timeline_months=24,
        technical_complexity=7,
        prerequisites=["Land tenure security", "Tree species selection"],
        compatible_crops=["coffee", "cocoa", "maize", "beans"],
        climate_zones=["tropical", "subtropical"]
    )
]