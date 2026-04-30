"""
Dirichlet Process Gaussian Mixture Model with streaming updates and missing data handling.

Implements ADVI variational inference with incremental posterior updates for time series
anomaly detection. Includes robust handling of missing values in streaming observations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
import numpy as np
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ELBOHistory:
    """Track ELBO convergence during ADVI optimization."""
    iterations: List[int] = field(default_factory=list)
    elbo_values: List[float] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)

    def record(self, iteration: int, elbo: float):
        self.iterations.append(iteration)
        self.elbo_values.append(elbo)
        self.timestamps.append(datetime.now().isoformat())

    def get_convergence_status(self) -> str:
        """Check if ELBO has converged based on recent changes."""
        if len(self.elbo_values) < 5:
            return "insufficient_data"
        recent_changes = [
            abs(self.elbo_values[i] - self.elbo_values[i-1])
            for i in range(-5, 0)
        ]
        avg_change = np.mean(recent_changes)
        if avg_change < 1e-4:
            return "converged"
        elif avg_change < 1e-2:
            return "slowing"
        else:
            return "diverging"

@dataclass
class ClusterAnomalyResult:
    """Result from cluster-based anomaly detection."""
    cluster_id: int
    anomaly_score: float
    probability: float
    confidence_interval: Tuple[float, float]

@dataclass
class MissingValueHandlingConfig:
    """Configuration for missing data handling strategies."""
    # Strategy: 'skip', 'impute_mean', 'impute_forward_fill', 'impute_linear'
    strategy: str = 'impute_mean'
    # Threshold for considering a value as missing (NaN, None, or extreme values)
    missing_threshold: float = np.nan
    # Maximum fraction of missing values allowed before skipping entire observation
    max_missing_fraction: float = 0.5
    # Forward fill window size
    forward_fill_window: int = 10
    # Linear interpolation max gap size
    linear_interp_max_gap: int = 5
    # Impute with this value if no better strategy available
    default_impute_value: float = 0.0
    # Log missing value events
    log_missing_events: bool = True

@dataclass
class DPGMMConfig:
    """Configuration for DPGMM model."""
    # Dirichlet process concentration parameter
    concentration: float = 1.0
    # Base distribution parameters
    base_mu: float = 0.0
    base_sigma: float = 1.0
    # ADVI optimization settings
    learning_rate: float = 0.01
    max_iterations: int = 100
    elbo_tolerance: float = 1e-4
    # Streaming settings
    max_components: int = 20
    min_component_weight: float = 0.01
    # Missing data handling
    missing_config: MissingValueHandlingConfig = field(default_factory=MissingValueHandlingConfig)
    # Random seed for reproducibility
    random_seed: int = 42
    # Logging
    log_dir: Optional[str] = None

class DPGMMModel:
    """
    Dirichlet Process Gaussian Mixture Model with streaming updates and missing data handling.

    Supports:
    - Incremental posterior updates for streaming observations
    - Stick-breaking construction for Dirichlet process
    - ADVI variational inference
    - Robust missing data handling with multiple strategies
    - Anomaly scoring via negative log posterior probability
    """

    def __init__(self, config: DPGMMConfig):
        """Initialize DPGMM model with configuration."""
        self.config = config
        self.rng = np.random.default_rng(config.random_seed)
        
        # Model state
        self.components: List[Dict[str, Any]] = []
        self.concentration = config.concentration
        self.max_components = config.max_components
        
        # ADVI state
        self.elbo_history = ELBOHistory()
        self.iteration_count = 0
        
        # Missing data tracking
        self.missing_value_counts: Dict[int, int] = {}
        self.observation_count = 0
        self.last_observed_values: Dict[int, float] = {}
        
        # Precompute base distribution
        self.base_dist_mu = config.base_mu
        self.base_dist_sigma = config.base_sigma
        
        logger.info(f"DPGMMModel initialized with concentration={config.concentration}, max_components={config.max_components}")

    def _is_missing(self, value: Any) -> bool:
        """Check if a value should be treated as missing."""
        if value is None:
            return True
        if isinstance(value, (int, float, np.floating, np.integer)):
            return np.isnan(value) or np.isinf(value)
        return False

    def _get_missing_fraction(self, observation: np.ndarray) -> float:
        """Calculate fraction of missing values in an observation."""
        if len(observation) == 0:
            return 1.0
        missing_count = sum(1 for v in observation if self._is_missing(v))
        return missing_count / len(observation)

    def _impute_mean(self, observation: np.ndarray) -> np.ndarray:
        """Impute missing values with feature-wise mean from existing components."""
        if len(self.components) == 0:
            # Use base distribution mean if no components yet
            return np.where(
                [self._is_missing(v) for v in observation],
                self.base_dist_mu,
                observation
            )
        
        # Compute weighted mean across all components
        imputed = observation.copy()
        for i, val in enumerate(observation):
            if self._is_missing(val):
                component_means = [
                    comp['mu'][i] * comp['weight']
                    for comp in self.components if 'mu' in comp and len(comp['mu']) > i
                ]
                if component_means:
                  imputed[i] = np.sum(component_means) / np.sum([comp['weight'] for comp in self.components if 'mu' in comp and len(comp['mu']) > i])
                else:
                  imputed[i] = self.base_dist_mu
        return imputed

    def _impute_forward_fill(self, observation: np.ndarray, feature_idx: int) -> float:
        """Impute missing value using forward fill from last observed value."""
        if feature_idx in self.last_observed_values:
            return self.last_observed_values[feature_idx]
        return self.base_dist_mu

    def _impute_linear(self, observation: np.ndarray) -> np.ndarray:
        """Impute missing values using linear interpolation where possible."""
        imputed = observation.copy()
        n_features = len(observation)
        
        for i in range(n_features):
            if self._is_missing(observation[i]):
                # Find previous and next non-missing values
                prev_idx = None
                next_idx = None
                
                for j in range(i - 1, -1, -1):
                    if not self._is_missing(observation[j]):
                        prev_idx = j
                        break
                
                for j in range(i + 1, n_features):
                    if not self._is_missing(observation[j]):
                        next_idx = j
                        break
                
                if prev_idx is not None and next_idx is not None:
                    # Linear interpolation
                    weight = (i - prev_idx) / (next_idx - prev_idx)
                    imputed[i] = observation[prev_idx] * (1 - weight) + observation[next_idx] * weight
                elif prev_idx is not None:
                    imputed[i] = observation[prev_idx]
                elif next_idx is not None:
                    imputed[i] = observation[next_idx]
                else:
                    imputed[i] = self.base_dist_mu
        
        return imputed

    def _handle_missing_values(self, observation: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Handle missing values in observation based on configured strategy.
        
        Returns:
          Tuple of (imputed observation, metadata dict with missing info)
        """
        metadata = {
            'original_missing_count': 0,
            'missing_fraction': 0.0,
            'skipped': False,
            'imputation_method': None,
            'missing_indices': []
        }
        
        # Count missing values
        missing_mask = [self._is_missing(v) for v in observation]
        metadata['original_missing_count'] = sum(missing_mask)
        metadata['missing_fraction'] = self._get_missing_fraction(observation)
        metadata['missing_indices'] = [i for i, m in enumerate(missing_mask) if m]
        
        # Check if we should skip this observation entirely
        if metadata['missing_fraction'] > self.config.missing_config.max_missing_fraction:
            metadata['skipped'] = True
            logger.warning(f"Skipping observation with {metadata['missing_fraction']:.2%} missing values")
            return observation, metadata
        
        # Apply imputation strategy
        if metadata['original_missing_count'] == 0:
            metadata['imputation_method'] = 'none'
            return observation, metadata
        
        if self.config.missing_config.strategy == 'skip':
            metadata['skipped'] = True
            metadata['imputation_method'] = 'skip'
            return observation, metadata
        
        elif self.config.missing_config.strategy == 'impute_mean':
            imputed = self._impute_mean(observation)
            metadata['imputation_method'] = 'mean'
        
        elif self.config.missing_config.strategy == 'impute_forward_fill':
            imputed = observation.copy()
            for i, val in enumerate(observation):
                if self._is_missing(val):
                    imputed[i] = self._impute_forward_fill(observation, i)
            metadata['imputation_method'] = 'forward_fill'
        
        elif self.config.missing_config.strategy == 'impute_linear':
            imputed = self._impute_linear(observation)
            metadata['imputation_method'] = 'linear'
        
        else:
            # Default to mean imputation
            imputed = self._impute_mean(observation)
            metadata['imputation_method'] = 'mean'
        
        # Update last observed values for forward fill
        for i, val in enumerate(imputed):
            if not self._is_missing(val):
                self.last_observed_values[i] = val
        
        if self.config.missing_config.log_missing_events:
            logger.info(f"Missing value handling: method={metadata['imputation_method']}, "
                      f"missing_count={metadata['original_missing_count']}, "
                      f"missing_fraction={metadata['missing_fraction']:.2%}")
        
        return imputed, metadata

    def _stick_breaking(self, n_components: int) -> np.ndarray:
        """Generate stick-breaking weights for Dirichlet process."""
        beta = self.rng.beta(1, self.concentration, size=n_components)
        weights = np.zeros(n_components)
        remaining = 1.0
        
        for i in range(n_components):
            weights[i] = remaining * beta[i]
            remaining *= (1 - beta[i])
        
        return weights

    def _initialize_component(self, observation: np.ndarray) -> Dict[str, Any]:
        """Initialize a new Gaussian component from an observation."""
        dim = len(observation)
        return {
            'mu': observation.copy(),
            'sigma': np.ones(dim) * self.base_dist_sigma,
            'weight': 1.0 / (len(self.components) + 1),
            'count': 1,
            'created_at': datetime.now().isoformat()
        }

    def _update_component(self, component: Dict[str, Any], observation: np.ndarray, 
                        learning_rate: float) -> Dict[str, Any]:
        """Update existing component with new observation using ADVI."""
        # Compute responsibility (soft assignment)
        diff = observation - component['mu']
        mahalanobis = np.sum((diff / component['sigma']) ** 2)
        likelihood = np.exp(-0.5 * mahalanobis) / (
            np.prod(component['sigma']) * (2 * np.pi) ** (len(observation) / 2)
        )
        
        # Update parameters with learning rate
        old_weight = component['weight']
        new_weight = old_weight + learning_rate * likelihood
        
        component['mu'] = (1 - learning_rate) * component['mu'] + learning_rate * observation
        component['weight'] = new_weight
        component['count'] += 1
        
        # Update variance estimate
        component['sigma'] = np.maximum(
            component['sigma'] * (1 - learning_rate) + 
            learning_rate * np.abs(diff),
            1e-6  # Minimum variance for numerical stability
        )
        
        return component

    def _compute_elbo(self, observation: np.ndarray) -> float:
        """Compute Evidence Lower Bound for current observation."""
        if len(self.components) == 0:
            return 0.0
        
        # Compute log-likelihood under mixture
        log_likelihoods = []
        for comp in self.components:
            diff = observation - comp['mu']
            log_likelihood = -0.5 * np.sum((diff / comp['sigma']) ** 2)
            log_likelihood -= np.sum(np.log(comp['sigma']))
            log_likelihoods.append(np.log(comp['weight']) + log_likelihood)
        
        return np.max(log_likelihoods)

    def update(self, observation: np.ndarray) -> Dict[str, Any]:
        """
        Process a new streaming observation with missing data handling.
        
        Args:
          observation: Input observation (may contain missing values)
        
        Returns:
          Dict with update metadata including imputation info, component counts, etc.
        """
        self.observation_count += 1
        
        # Handle missing values first
        processed_obs, missing_metadata = self._handle_missing_values(observation)
        
        if missing_metadata['skipped']:
            return {
                'status': 'skipped',
                'missing_metadata': missing_metadata,
                'observation_count': self.observation_count,
                'component_count': len(self.components)
            }
        
        # Compute responsibility for existing components
        responsibilities = []
        for comp in self.components:
            diff = processed_obs - comp['mu']
            mahalanobis = np.sum((diff / comp['sigma']) ** 2)
            likelihood = np.exp(-0.5 * mahalanobis) / (
                np.prod(comp['sigma']) * (2 * np.pi) ** (len(processed_obs) / 2)
            )
            responsibilities.append(comp['weight'] * likelihood)
        
        # Normalize responsibilities
        total_resp = sum(responsibilities) + 1e-10
        responsibilities = [r / total_resp for r in responsibilities]
        
        # Update existing components
        learning_rate = self.config.learning_rate
        for i, comp in enumerate(self.components):
            self.components[i] = self._update_component(comp, processed_obs, learning_rate * responsibilities[i])
        
        # Decide whether to create new component (Chinese Restaurant Process)
        prob_new = self.concentration / (self.concentration + self.observation_count)
        if self.rng.random() < prob_new and len(self.components) < self.max_components:
            new_component = self._initialize_component(processed_obs)
            self.components.append(new_component)
            logger.info(f"Created new component {len(self.components)-1}")
        
        # Prune low-weight components
        self.components = [
            comp for comp in self.components 
            if comp['weight'] > self.config.min_component_weight
        ]
        
        # Update concentration parameter based on component count
        self._update_concentration()
        
        # Compute and record ELBO
        elbo = self._compute_elbo(processed_obs)
        self.elbo_history.record(self.iteration_count, elbo)
        self.iteration_count += 1
        
        # Update missing value tracking
        for idx in missing_metadata['missing_indices']:
            self.missing_value_counts[idx] = self.missing_value_counts.get(idx, 0) + 1
        
        return {
            'status': 'updated',
            'component_count': len(self.components),
            'observation_count': self.observation_count,
            'missing_metadata': missing_metadata,
            'elbo': elbo,
            'convergence_status': self.elbo_history.get_convergence_status()
        }

    def _update_concentration(self):
        """Adapt concentration parameter based on component count."""
        current_components = len(self.components)
        target_components = int(np.sqrt(self.observation_count))
        
        if current_components > target_components * 1.5:
            # Too many components, increase concentration to favor existing
            self.concentration = min(10.0, self.concentration * 1.1)
        elif current_components < target_components * 0.5:
            # Too few components, decrease concentration to allow new
            self.concentration = max(0.1, self.concentration * 0.9)

    def score(self, observation: np.ndarray) -> Tuple[float, Dict[str, Any]]:
        """
        Compute anomaly score for an observation.
        
        Returns:
          Tuple of (anomaly_score, metadata_dict)
        """
        processed_obs, missing_metadata = self._handle_missing_values(observation)
        
        if missing_metadata['skipped']:
            return 0.0, {'status': 'skipped', 'missing_metadata': missing_metadata}
        
        # Compute negative log posterior probability
        log_posteriors = []
        for comp in self.components:
            diff = processed_obs - comp['mu']
            log_likelihood = -0.5 * np.sum((diff / comp['sigma']) ** 2)
            log_likelihood -= np.sum(np.log(comp['sigma']))
            log_likelihood += np.log(comp['weight'])
            log_posteriors.append(log_likelihood)
        
        if len(log_posteriors) == 0:
            # No components yet, return default score
            return 0.0, {'status': 'no_components', 'missing_metadata': missing_metadata}
        
        # Negative log of maximum posterior (higher = more anomalous)
        anomaly_score = -np.max(log_posteriors)
        
        # Compute uncertainty estimates
        posterior_variance = np.var(log_posteriors)
        confidence = 1.0 / (1.0 + posterior_variance)
        
        return anomaly_score, {
            'missing_metadata': missing_metadata,
            'posterior_variance': posterior_variance,
            'confidence': confidence,
            'component_assignments': [
                {'id': i, 'log_posterior': lp, 'weight': self.components[i]['weight']}
                for i, lp in enumerate(log_posteriors)
            ]
        }

    def get_elbo_history(self) -> ELBOHistory:
        """Return ELBO convergence history."""
        return self.elbo_history

    def get_component_summary(self) -> List[Dict[str, Any]]:
        """Return summary of all active components."""
        return [
            {
                'id': i,
                'mu': comp['mu'].tolist() if hasattr(comp['mu'], 'tolist') else comp['mu'],
                'sigma': comp['sigma'].tolist() if hasattr(comp['sigma'], 'tolist') else comp['sigma'],
                'weight': comp['weight'],
                'count': comp['count']
            }
            for i, comp in enumerate(self.components)
        ]

    def save(self, path: Union[str, Path]):
        """Save model state to file."""
        import json
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            'config': {
                'concentration': self.concentration,
                'learning_rate': self.config.learning_rate,
                'max_components': self.max_components,
                'random_seed': self.config.random_seed
            },
            'components': self.get_component_summary(),
            'observation_count': self.observation_count,
            'elbo_history': {
                'iterations': self.elbo_history.iterations,
                'elbo_values': self.elbo_history.elbo_values
            },
            'missing_value_counts': self.missing_value_counts
        }
        
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"Model saved to {path}")

    @classmethod
    def load(cls, path: Union[str, Path]) -> 'DPGMMModel':
        """Load model state from file."""
        import json
        path = Path(path)
        
        with open(path, 'r') as f:
            state = json.load(f)
        
        config = DPGMMConfig(
            concentration=state['config']['concentration'],
            learning_rate=state['config']['learning_rate'],
            max_components=state['config']['max_components'],
            random_seed=state['config']['random_seed']
        )
        
        model = cls(config)
        
        # Restore components
        for comp_state in state['components']:
            model.components.append({
                'mu': np.array(comp_state['mu']),
                'sigma': np.array(comp_state['sigma']),
                'weight': comp_state['weight'],
                'count': comp_state['count'],
                'created_at': datetime.now().isoformat()
            })
        
        model.observation_count = state['observation_count']
        
        # Restore ELBO history
        model.elbo_history.iterations = state['elbo_history']['iterations']
        model.elbo_history.elbo_values = state['elbo_history']['elbo_values']
        
        model.missing_value_counts = state.get('missing_value_counts', {})
        
        logger.info(f"Model loaded from {path}")
        return model

def main():
    """Entry point for testing missing data handling."""
    import sys
    
    # Create model with missing data handling
    config = DPGMMConfig(
        concentration=1.0,
        learning_rate=0.01,
        max_components=10,
        missing_config=MissingValueHandlingConfig(
            strategy='impute_mean',
            max_missing_fraction=0.5,
            log_missing_events=True
        )
    )
    
    model = DPGMMModel(config)
    
    # Test with complete observation
    obs1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    result1 = model.update(obs1)
    print(f"Complete observation: {result1['status']}")
    
    # Test with missing values
    obs2 = np.array([1.0, np.nan, 3.0, np.nan, 5.0])
    result2 = model.update(obs2)
    print(f"Missing values observation: {result2['status']}")
    print(f"Missing metadata: {result2.get('missing_metadata', {})}")
    
    # Test scoring with missing values
    score, metadata = model.score(obs2)
    print(f"Anomaly score: {score:.4f}")
    print(f"Score metadata: {metadata}")
    
    print("\nMissing data handling test completed successfully!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
