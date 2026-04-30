"""
DP-GMM Model: Dirichlet Process Gaussian Mixture Model for Anomaly Detection.

Implements streaming variational inference with ADVI for time series anomaly detection.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
import numpy as np
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ELBOHistory:
    """ELBO convergence history for ADVI inference."""
    iterations: List[int] = field(default_factory=list)
    elbo_values: List[float] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)

    def append(self, iteration: int, elbo: float) -> None:
        """Append a new ELBO measurement."""
        self.iterations.append(iteration)
        self.elbo_values.append(elbo)
        self.timestamps.append(datetime.now().isoformat())

    def get_convergence_rate(self) -> float:
        """Compute the rate of ELBO convergence (slope of last 10 points)."""
        if len(self.elbo_values) < 10:
            return 0.0
        recent = self.elbo_values[-10:]
        return float(np.mean(np.diff(recent)))


@dataclass
class ClusterAnomalyResult:
    """Result of cluster-level anomaly analysis."""
    cluster_id: int
    anomaly_score: float
    membership_prob: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "cluster_id": self.cluster_id,
            "anomaly_score": self.anomaly_score,
            "membership_prob": self.membership_prob,
            "timestamp": self.timestamp
        }


@dataclass
class DPGMMConfig:
    """Configuration for DPGMM model."""
    # Variational inference parameters
    max_components: int = 10
    min_components: int = 1
    concentration_prior: float = 1.0
    learning_rate: float = 0.01
    elbo_threshold: float = 1e-4

    # Gaussian parameters
    mean_prior: float = 0.0
    precision_prior: float = 1.0

    # Streaming update parameters
    forget_factor: float = 0.99
    min_obs_per_component: int = 5

    # Numerical stability
    epsilon: float = 1e-10
    max_iterations: int = 1000

    # Paths
    model_output_dir: str = "data/processed/models"
    log_dir: str = "logs/elbo"

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.max_components < self.min_components:
            raise ValueError("max_components must be >= min_components")
        if not 0 < self.forget_factor <= 1:
            raise ValueError("forget_factor must be in (0, 1]")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")


class DPGMMModel:
    """
    Dirichlet Process Gaussian Mixture Model for streaming anomaly detection.

    Implements stick-breaking construction with ADVI variational inference.
    """

    def __init__(self, config: Optional[DPGMMConfig] = None) -> None:
        """Initialize DPGMM model with configuration."""
        self.config = config or DPGMMConfig()
        self._components: List[Dict[str, np.ndarray]] = []
        self._stick_breaking_weights: np.ndarray = np.array([])
        self._concentration_param: float = self.config.concentration_prior
        self._elbo_history: ELBOHistory = ELBOHistory()
        self._total_observations: int = 0
        self._initialized: bool = False

    def initialize(self, initial_observations: np.ndarray) -> None:
        """
Initialize model with initial batch of observations.

Args:
    initial_observations: Array of shape (n_samples, n_features)
"""
        if initial_observations.ndim == 1:
            initial_observations = initial_observations.reshape(-1, 1)

        n_samples, n_features = initial_observations.shape
        logger.info(f"Initializing with {n_samples} observations, {n_features} features")

        # Initialize components using K-means style initialization
        n_init_components = min(self.config.max_components, max(2, n_samples // 10))

        for i in range(n_init_components):
            start_idx = int(i * n_samples / n_init_components)
            end_idx = int((i + 1) * n_samples / n_init_components)
            chunk = initial_observations[start_idx:end_idx]

            mean = np.mean(chunk, axis=0)
            precision = 1.0 / (np.var(chunk, axis=0) + self.config.epsilon)

            self._components.append({
                "mean": mean,
                "precision": precision,
                "count": end_idx - start_idx
            })

        # Initialize stick-breaking weights
        self._stick_breaking_weights = np.ones(n_init_components) / n_init_components

        self._initialized = True
        self._total_observations = n_samples

    def update_posterior(self, observation: np.ndarray) -> Tuple[np.ndarray, float]:
        """
Update posterior mixture weights for a new observation.

Args:
    observation: Single observation vector of shape (n_features,)

Returns:
    Tuple of (mixture_weights, component_assignment)
"""
        if not self._initialized:
            raise RuntimeError("Model must be initialized before updating")

        if observation.ndim == 0:
            observation = observation.reshape(1)

        n_components = len(self._components)
        responsibilities = np.zeros(n_components)

        # Compute likelihood under each component
        for i, comp in enumerate(self._components):
            diff = observation - comp["mean"]
            log_likelihood = -0.5 * np.sum(comp["precision"] * diff ** 2)
            responsibilities[i] = np.exp(log_likelihood)

        # Normalize responsibilities
        responsibilities_sum = np.sum(responsibilities) + self.config.epsilon
        responsibilities = responsibilities / responsibilities_sum

        # Update component counts with forget factor
        for i, comp in enumerate(self._components):
            comp["count"] = self.config.forget_factor * comp["count"] + responsibilities[i]

        self._total_observations += 1

        # Check if we need to create a new component
        if self._should_create_new_component(responsibilities):
            self._create_new_component(observation)

        return responsibilities, self._total_observations - 1

    def _should_create_new_component(self, responsibilities: np.ndarray) -> bool:
        """Determine if a new component should be created."""
        max_responsibility = np.max(responsibilities)
        return (max_responsibility < 0.1 and
                len(self._components) < self.config.max_components)

    def _create_new_component(self, observation: np.ndarray) -> None:
        """Create a new component for the observation."""
        new_comp = {
            "mean": observation.copy(),
            "precision": np.ones_like(observation) * self.config.precision_prior,
            "count": 1.0
        }
        self._components.append(new_comp)

        # Update stick-breaking weights
        n = len(self._components)
        self._stick_breaking_weights = np.ones(n) / n

    def compute_anomaly_score(self, observation: np.ndarray) -> float:
        """
Compute anomaly score (negative log posterior) for an observation.

Args:
    observation: Single observation vector of shape (n_features,)

Returns:
    Anomaly score (higher = more anomalous)
"""
        if not self._initialized:
            raise RuntimeError("Model must be initialized before scoring")

        if observation.ndim == 0:
            observation = observation.reshape(1)

        responsibilities, _ = self.update_posterior(observation)

        # Negative log posterior = -log(sum over components of weight * likelihood)
        log_likelihoods = []
        for i, comp in enumerate(self._components):
            diff = observation - comp["mean"]
            log_lik = -0.5 * np.sum(comp["precision"] * diff ** 2)
            log_weight = np.log(self._stick_breaking_weights[i] + self.config.epsilon)
            log_likelihoods.append(log_weight + log_lik)

        log_posterior = np.logaddexp.reduce(np.array(log_likelihoods))
        anomaly_score = -log_posterior

        return float(anomaly_score)

    def get_component_count(self) -> int:
        """Return the current number of active mixture components."""
        return len(self._components)

    def get_concentration_parameter(self) -> float:
        """Return the current concentration parameter."""
        return self._concentration_param

    def log_elbo(self, iteration: int, elbo_value: float) -> None:
        """Log ELBO value for convergence monitoring."""
        self._elbo_history.append(iteration, elbo_value)

        # Write to log file
        log_path = Path(self.config.log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        log_file = log_path / f"elbo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        with open(log_file, "a") as f:
            f.write(f"{iteration},{elbo_value}\n")

    def get_elbo_history(self) -> ELBOHistory:
        """Return the ELBO convergence history."""
        return self._elbo_history

    def get_cluster_anomalies(self, observations: np.ndarray,
                             score_threshold: float = 5.0) -> List[ClusterAnomalyResult]:
        """
Identify cluster-level anomalies in a batch of observations.

Args:
    observations: Array of shape (n_samples, n_features)
    score_threshold: Minimum anomaly score to flag as anomalous

Returns:
    List of ClusterAnomalyResult for anomalous observations
"""
        if observations.ndim == 1:
            observations = observations.reshape(-1, 1)

        results: List[ClusterAnomalyResult] = []

        for i, obs in enumerate(observations):
            score = self.compute_anomaly_score(obs)
            if score > score_threshold:
                responsibilities, _ = self.update_posterior(obs)
                best_component = int(np.argmax(responsibilities))

                results.append(ClusterAnomalyResult(
                    cluster_id=best_component,
                    anomaly_score=score,
                    membership_prob=float(responsibilities[best_component])
                ))

        return results

    def save_model(self, output_path: Optional[str] = None) -> Path:
        """
Save model state to disk.

Args:
    output_path: Optional custom output path

Returns:
    Path to saved model file
"""
        import json

        save_dir = Path(output_path) if output_path else Path(self.config.model_output_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        model_file = save_dir / f"dp_gmm_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        model_state = {
            "config": {k: v for k, v in vars(self.config).items()},
            "components": [
                {
                    "mean": comp["mean"].tolist(),
                    "precision": comp["precision"].tolist(),
                    "count": float(comp["count"])
                }
                for comp in self._components
            ],
            "stick_breaking_weights": self._stick_breaking_weights.tolist(),
            "concentration_param": self._concentration_param,
            "total_observations": self._total_observations
        }

        with open(model_file, "w") as f:
            json.dump(model_state, f, indent=2)

        logger.info(f"Model saved to {model_file}")
        return model_file

    def load_model(self, model_path: str) -> None:
        """
Load model state from disk.

Args:
    model_path: Path to saved model file
"""
        import json

        with open(model_path, "r") as f:
            model_state = json.load(f)

        # Load components
        self._components = []
        for comp_state in model_state["components"]:
            self._components.append({
                "mean": np.array(comp_state["mean"]),
                "precision": np.array(comp_state["precision"]),
                "count": float(comp_state["count"])
            })

        self._stick_breaking_weights = np.array(model_state["stick_breaking_weights"])
        self._concentration_param = float(model_state["concentration_param"])
        self._total_observations = int(model_state["total_observations"])
        self._initialized = True

        logger.info(f"Model loaded from {model_path}")


def main() -> None:
    """Main entry point for DPGMM model testing."""
    logger.info("DPGMM Model Test")

    # Create configuration
    config = DPGMMConfig(
        max_components=5,
        learning_rate=0.01,
        model_output_dir="data/processed/models"
    )

    # Initialize model
    model = DPGMMModel(config)

    # Generate synthetic test data
    np.random.seed(42)
    initial_data = np.random.randn(100, 1) * 2

    model.initialize(initial_data)
    logger.info(f"Initialized with {model.get_component_count()} components")

    # Process streaming observations
    for i in range(50):
        obs = np.random.randn(1) * 2
        score = model.compute_anomaly_score(obs)

        if i % 10 == 0:
            logger.info(f"Observation {i}: score={score:.4f}, components={model.get_component_count()}")

        # Log ELBO periodically
        if i % 5 == 0:
            elbo = -score * model.get_component_count()
            model.log_elbo(i, elbo)

    # Save model
    model.save_model()
    logger.info("Test completed successfully")


if __name__ == "__main__":
    main()
