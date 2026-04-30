"""
Dirichlet Process Gaussian Mixture Model (DPGMM) for streaming anomaly detection.

Implements incremental DPGMM with stick-breaking construction and ADVI
variational inference for time series anomaly detection.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
import numpy as np
import logging
from datetime import datetime
from pathlib import Path

from .anomaly_score import AnomalyScore

# Configure logger
logger = logging.getLogger(__name__)


@dataclass
class ELBOHistory:
    """History of ELBO values during ADVI optimization."""
    values: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)

    def append(self, value: float, timestamp: Optional[datetime] = None) -> None:
        """Append an ELBO value to history."""
        self.values.append(value)
        self.timestamps.append(timestamp or datetime.now())

    def get_mean(self, window: Optional[int] = None) -> float:
        """Get mean ELBO over recent values."""
        if not self.values:
            return 0.0
        if window and len(self.values) > window:
            recent = self.values[-window:]
        else:
            recent = self.values
        return float(np.mean(recent))


@dataclass
class ClusterAnomalyResult:
    """Result of cluster-level anomaly analysis."""
    cluster_id: int
    anomaly_score: float
    membership_probability: float
    is_cluster_anomaly: bool
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DPGMMConfig:
    """Configuration for DPGMM model."""
    # Stick-breaking parameters
    concentration_parameter: float = 1.0
    max_components: int = 20
    min_components: int = 1

    # ADVI variational inference parameters
    learning_rate: float = 0.01
    elbo_tolerance: float = 1e-4
    max_iterations: int = 100
    mini_batch_size: int = 32

    # Gaussian component parameters
    prior_mean: float = 0.0
    prior_precision: float = 0.01
    prior_variance: float = 1.0
    prior_precision_variance: float = 0.01

    # Anomaly scoring
    anomaly_threshold: float = 95.0  # percentile
    min_obs_for_scoring: int = 10

    # Memory management
    max_cluster_age: int = 1000  # observations before potential pruning

    # Random seed for reproducibility
    random_seed: Optional[int] = 42

    def validate(self) -> None:
        """Validate configuration parameters."""
        if self.concentration_parameter <= 0:
            raise ValueError("concentration_parameter must be positive")
        if self.max_components < self.min_components:
            raise ValueError("max_components must be >= min_components")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")


class DPGMMModel:
    """
    Streaming Dirichlet Process Gaussian Mixture Model.

    Processes time series observations one at a time using stick-breaking
    construction and ADVI variational inference for posterior updates.
    """

    def __init__(self, config: Optional[DPGMMConfig] = None) -> None:
        """Initialize DPGMM model with configuration."""
        self.config = config or DPGMMConfig()
        self.config.validate()

        # Set random seed
        if self.config.random_seed is not None:
            np.random.seed(self.config.random_seed)

        # Model state
        self._n_obs: int = 0
        self._components: List[Dict[str, np.ndarray]] = []
        self._mixture_weights: np.ndarray = np.array([])
        self._concentration: float = self.config.concentration_parameter

        # ADVI state
        self._elbo_history: ELBOHistory = ELBOHistory()
        self._last_elbo: float = -np.inf

        # Logging
        self._logger = logging.getLogger(self.__class__.__name__)

    @property
    def n_components(self) -> int:
        """Get current number of active mixture components."""
        return len(self._components)

    @property
    def n_observations(self) -> int:
        """Get total number of observations processed."""
        return self._n_obs

    @property
    def concentration_parameter(self) -> float:
        """Get current concentration parameter."""
        return self._concentration

    def _initialize_new_component(self, observation: np.ndarray) -> Dict[str, np.ndarray]:
        """Initialize a new Gaussian component with given observation."""
        return {
            'mean': observation.copy(),
            'precision': self.config.prior_precision * np.ones_like(observation),
            'variance': self.config.prior_variance * np.ones_like(observation),
            'weight': 1.0 / max(self.n_components + 1, 1),
        }

    def _stick_breaking_weights(self, n_components: int) -> np.ndarray:
        """Compute mixture weights using stick-breaking construction."""
        weights = np.zeros(n_components)
        remaining = 1.0

        for i in range(n_components):
            beta = np.random.beta(1, self._concentration)
            weights[i] = remaining * beta
            remaining *= (1 - beta)

        # Normalize to ensure sum equals 1
        weights /= weights.sum()
        return weights

    def _compute_component_posterior(
        self,
        observation: np.ndarray,
        component: Dict[str, np.ndarray]
    ) -> Tuple[float, float]:
        """
        Compute posterior probability of observation belonging to component.

        Returns:
            Tuple of (log_likelihood, log_prior_weight)
        """
        mean = component['mean']
        precision = component['precision']

        # Compute Mahalanobis distance
        diff = observation - mean
        mahalanobis_sq = np.sum(precision * diff ** 2)

        # Log-likelihood under Gaussian
        log_likelihood = -0.5 * mahalanobis_sq
        log_likelihood -= 0.5 * np.sum(np.log(2 * np.pi / precision))

        # Log prior weight
        log_prior_weight = np.log(component['weight'] + 1e-300)

        return log_likelihood, log_prior_weight

    def _update_component(
        self,
        component: Dict[str, np.ndarray],
        observation: np.ndarray,
        responsibility: float
    ) -> None:
        """Update component parameters with new observation."""
        # Effective sample size
        n_eff = component.get('n_eff', 0) + responsibility

        # Update mean
        old_mean = component['mean'].copy()
        component['mean'] = old_mean + (responsibility / n_eff) * (observation - old_mean)

        # Update precision/variance
        diff = observation - old_mean
        component['variance'] = (
            component.get('variance', self.config.prior_variance) +
            responsibility * diff ** 2
        )
        component['precision'] = 1.0 / (component['variance'] + 1e-10)

        # Track effective sample size
        component['n_eff'] = n_eff

    def _compute_elbo(
        self,
        observations: np.ndarray,
        responsibilities: np.ndarray
    ) -> float:
        """
        Compute Evidence Lower Bound (ELBO) for ADVI optimization.

        Args:
            observations: Array of shape (n_obs, n_features)
            responsibilities: Array of shape (n_obs, n_components)

        Returns:
            ELBO value
        """
        if len(observations) == 0:
            return 0.0

        elbo = 0.0

        # Expected log-likelihood
        for i, obs in enumerate(observations):
            for j, comp in enumerate(self._components):
                log_lik, _ = self._compute_component_posterior(obs, comp)
                elbo += responsibilities[i, j] * log_lik

        # Entropy of responsibilities
        for i in range(len(observations)):
            for j in range(len(self._components)):
                r = responsibilities[i, j] + 1e-300
                elbo -= responsibilities[i, j] * np.log(r)

        # KL divergence from prior (simplified)
        elbo += self._concentration * np.log(self._concentration)

        return elbo

    def update_posterior(
        self,
        observation: np.ndarray,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Update model posterior with new observation.

        Args:
            observation: 1D array of feature values
            timestamp: Optional timestamp for logging
        """
        if observation.ndim == 0:
            observation = observation.reshape(1)
        elif observation.ndim > 1:
            observation = observation.flatten()

        self._n_obs += 1

        # Handle first observation
        if self.n_components == 0:
          self._components.append(self._initialize_new_component(observation))
          self._mixture_weights = np.array([1.0])
          return

        # Compute responsibilities (E-step)
        log_posteriors = np.zeros(self.n_components)
        for j, comp in enumerate(self._components):
            log_lik, log_prior = self._compute_component_posterior(observation, comp)
            log_posteriors[j] = log_lik + log_prior

        # Normalize to get responsibilities
        log_max = np.max(log_posteriors)
        log_posteriors_shifted = log_posteriors - log_max
        posteriors = np.exp(log_posteriors_shifted)
        posteriors /= posteriors.sum() + 1e-300

        # Update existing components (M-step)
        for j, comp in enumerate(self._components):
            if posteriors[j] > 1e-10:
                self._update_component(comp, observation, posteriors[j])

        # Potentially add new component if observation is anomalous
        min_responsibility = np.min(posteriors)
        if min_responsibility < 0.01 and self.n_components < self.config.max_components:
            self._components.append(self._initialize_new_component(observation))
            self._mixture_weights = self._stick_breaking_weights(self.n_components)

        # Update mixture weights
        self._mixture_weights = self._stick_breaking_weights(self.n_components)

        # Log ELBO periodically
        if self._n_obs % 10 == 0:
            elbo = self._compute_elbo(
                observation.reshape(1, -1),
                posteriors.reshape(1, -1)
            )
            self._elbo_history.append(elbo, timestamp)
            self._last_elbo = elbo

    def compute_anomaly_score(
        self,
        observation: np.ndarray,
        timestamp: Optional[datetime] = None
    ) -> AnomalyScore:
        """
        Compute anomaly score for observation.

        Args:
            observation: 1D array of feature values
            timestamp: Optional timestamp for the observation

        Returns:
            AnomalyScore with negative log posterior and uncertainty
        """
        if self.n_components == 0:
            return AnomalyScore(
                value=0.0,
                is_anomaly=False,
                uncertainty=1.0,
                timestamp=timestamp or datetime.now()
            )

        if observation.ndim == 0:
            observation = observation.reshape(1)
        elif observation.ndim > 1:
            observation = observation.flatten()

        # Compute minimum negative log posterior across components
        min_neg_log_post = np.inf
        best_component_idx = -1

        for j, comp in enumerate(self._components):
            log_lik, log_prior = self._compute_component_posterior(observation, comp)
            neg_log_post = -(log_lik + log_prior)
            if neg_log_post < min_neg_log_post:
                min_neg_log_post = neg_log_post
                best_component_idx = j

        # Compute uncertainty based on posterior spread
        log_posteriors = np.zeros(self.n_components)
        for j, comp in enumerate(self._components):
            log_lik, log_prior = self._compute_component_posterior(observation, comp)
            log_posteriors[j] = log_lik + log_prior

        log_max = np.max(log_posteriors)
        log_posteriors_shifted = log_posteriors - log_max
        posteriors = np.exp(log_posteriors_shifted)
        posteriors /= posteriors.sum() + 1e-300

        # Uncertainty: entropy of posterior distribution
        uncertainty = -np.sum(posteriors * np.log(posteriors + 1e-300))
        uncertainty = uncertainty / np.log(self.n_components + 1e-10)  # Normalize

        # Determine if anomaly based on threshold
        is_anomaly = min_neg_log_post > self.config.anomaly_threshold

        return AnomalyScore(
            value=float(min_neg_log_post),
            is_anomaly=is_anomaly,
            uncertainty=float(uncertainty),
            component_id=best_component_idx,
            timestamp=timestamp or datetime.now()
        )

    def analyze_cluster_anomalies(
        self,
        observation: np.ndarray,
        threshold: float = 2.0
    ) -> List[ClusterAnomalyResult]:
        """
        Analyze whether observation represents a cluster-level anomaly.

        Args:
            observation: 1D array of feature values
            threshold: Number of standard deviations for anomaly detection

        Returns:
            List of ClusterAnomalyResult for each component
        """
        results = []

        if self.n_components == 0:
            return results

        for j, comp in enumerate(self._components):
            mean = comp['mean']
            variance = comp.get('variance', self.config.prior_variance)

            # Compute z-score for each dimension
            z_scores = np.abs((observation - mean) / np.sqrt(variance + 1e-10))
            max_z = np.max(z_scores)
            avg_z = np.mean(z_scores)

            # Determine if cluster anomaly
            is_cluster_anomaly = max_z > threshold

            # Membership probability
            membership_prob = float(np.exp(-0.5 * np.mean(z_scores ** 2)))

            results.append(ClusterAnomalyResult(
                cluster_id=j,
                anomaly_score=float(avg_z),
                membership_probability=membership_prob,
                is_cluster_anomaly=is_cluster_anomaly
            ))

        return results

    def tune_concentration_parameter(self, target_components: int) -> float:
        """
        Adjust concentration parameter to achieve target number of components.

        Args:
            target_components: Desired number of mixture components

        Returns:
            Updated concentration parameter
        """
        current_components = self.n_components

        if current_components < target_components:
            # Increase concentration to encourage more components
            self._concentration *= 1.1
        elif current_components > target_components:
            # Decrease concentration to encourage fewer components
            self._concentration *= 0.9

        # Clamp to reasonable bounds
        self._concentration = np.clip(
            self._concentration,
            0.1,
            100.0
        )

        return self._concentration

    def get_elbo_convergence_status(self) -> Tuple[bool, float]:
        """
        Check if ELBO has converged.

        Returns:
            Tuple of (is_converged, current_elbo)
        """
        if len(self._elbo_history.values) < 5:
            return False, self._last_elbo

        recent = self._elbo_history.values[-5:]
        elbo_change = np.abs(recent[-1] - recent[0])

        is_converged = elbo_change < self.config.elbo_tolerance
        return is_converged, self._last_elbo

    def save_state(self, path: Union[str, Path]) -> None:
        """Save model state to file."""
        state = {
            'config': self.config.__dict__,
            'n_observations': self._n_obs,
            'n_components': self.n_components,
            'concentration': self._concentration,
            'components': [
                {k: v.tolist() if isinstance(v, np.ndarray) else v
                 for k, v in comp.items()}
                for comp in self._components
            ],
            'mixture_weights': self._mixture_weights.tolist(),
        }

        import json
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self, path: Union[str, Path]) -> None:
        """Load model state from file."""
        import json
        path = Path(path)
        with open(path, 'r') as f:
            state = json.load(f)

        # Restore configuration
        self.config = DPGMMConfig(**state['config'])

        # Restore model state
        self._n_obs = state['n_observations']
        self._concentration = state['concentration']

        # Restore components
        self._components = []
        for comp_state in state['components']:
            comp = {}
            for k, v in comp_state.items():
                if isinstance(v, list):
                    comp[k] = np.array(v)
                else:
                    comp[k] = v
            self._components.append(comp)

        # Restore mixture weights
        self._mixture_weights = np.array(state['mixture_weights'])

    def reset(self) -> None:
        """Reset model to initial state."""
        self._n_obs = 0
        self._components = []
        self._mixture_weights = np.array([])
        self._concentration = self.config.concentration_parameter
        self._elbo_history = ELBOHistory()
        self._last_elbo = -np.inf


def main() -> None:
    """Main entry point for standalone execution."""
    logging.basicConfig(level=logging.INFO)

    # Create model with default config
    config = DPGMMConfig()
    model = DPGMMModel(config)

    # Process synthetic observations
    logger.info("Processing synthetic observations...")
    for i in range(1000):
        observation = np.random.randn(1)
        model.update_posterior(observation)

        if i % 100 == 0:
            score = model.compute_anomaly_score(observation)
            logger.info(f"Obs {i}: score={score.value:.4f}, anomaly={score.is_anomaly}")

    # Check convergence
    is_converged, elbo = model.get_elbo_convergence_status()
    logger.info(f"Convergence: {is_converged}, ELBO: {elbo:.4f}")
    logger.info(f"Final components: {model.n_components}")
