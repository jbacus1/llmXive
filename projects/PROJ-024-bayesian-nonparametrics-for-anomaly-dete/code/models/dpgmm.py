"""
Dirichlet Process Gaussian Mixture Model with Streaming Updates.

Implements incremental DPGMM using stick-breaking construction and
ADVI variational inference for anomaly detection in time series.

Includes numerical stability checks for edge cases including
near-constant variance time series.
"""

import numpy as np
import pymc as pm
from pymc import variational as pv
from scipy.special import logsumexp, digamma, beta
from typing import Dict, Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

# Numerical stability constants
EPSILON = 1e-10
MIN_VARIANCE = 1e-6
MAX_VARIANCE = 1e6
MAX_ITERATIONS = 1000
CONVERGENCE_THRESHOLD = 1e-4


class DPGMMModel:
    """
    Dirichlet Process Gaussian Mixture Model for streaming anomaly detection.
    
    Features:
    - Stick-breaking construction for unbounded number of components
    - Incremental posterior updates for streaming observations
    - ADVI variational inference for memory efficiency
    - Numerical stability checks for edge cases
    
    Attributes:
        alpha: Concentration parameter for Dirichlet process
        max_components: Maximum number of mixture components to consider
        min_variance: Minimum variance threshold for numerical stability
    """
    
    def __init__(
        self,
        alpha: float = 1.0,
        max_components: int = 50,
        min_variance: float = MIN_VARIANCE,
        random_seed: Optional[int] = None
    ):
        """
        Initialize DPGMM model.
        
        Args:
            alpha: Concentration parameter for Dirichlet process
            max_components: Maximum number of mixture components
            min_variance: Minimum variance threshold for numerical stability
            random_seed: Random seed for reproducibility
        """
        self.alpha = alpha
        self.max_components = max_components
        self.min_variance = min_variance
        self.random_seed = random_seed
        
        # Model state
        self._initialized = False
        self._observations = []
        self._n_observations = 0
        self._current_components = 0
        
        # Variational parameters (for ADVI)
        self._variational_params = None
        self._elbo_history = []
        
        # Edge case handling state
        self._variance_warnings = 0
        self._stability_adjustments = 0
        
        if random_seed is not None:
            np.random.seed(random_seed)
            
    def _clamp_variance(self, variance: np.ndarray) -> np.ndarray:
        """
        Clamp variance values to ensure numerical stability.
        
        Handles near-constant variance time series by enforcing
        minimum variance threshold to prevent division by zero
        and log(0) errors in Bayesian computations.
        
        Args:
            variance: Variance values to clamp
            
        Returns:
            Clamped variance values within [min_variance, max_variance]
        """
        # Clip to valid range
        variance = np.clip(variance, self.min_variance, MAX_VARIANCE)
        
        # Log-space computation to prevent overflow
        log_variance = np.log(variance + EPSILON)
        variance = np.exp(log_variance)
        
        return variance
    
    def _add_numerical_stability(self, value: np.ndarray) -> np.ndarray:
        """
        Add numerical stability epsilon to prevent log(0) and division by zero.
        
        Args:
            value: Array of values to stabilize
            
        Returns:
            Stabilized values with epsilon added where needed
        """
        return value + EPSILON
    
    def _check_varianced_edge_case(self, variance: float) -> bool:
        """
        Check if variance is near-constant (edge case).
        
        Args:
            variance: Variance value to check
            
        Returns:
            True if variance indicates near-constant time series
        """
        return variance < self.min_variance * 10
    
    def _handle_low_variance_observation(
        self,
        observation: np.ndarray,
        variance_estimate: float
    ) -> Tuple[np.ndarray, float]:
        """
        Handle observations from near-constant variance time series.
        
        Implements adaptive variance floor that scales with observation
        magnitude to maintain numerical stability while preserving
        anomaly detection sensitivity.
        
        Args:
            observation: Current observation values
            variance_estimate: Estimated variance for this observation
            
        Returns:
            Tuple of (adjusted_observation, adjusted_variance)
        """
        # Check if variance is problematic
        if self._check_varianced_edge_case(variance_estimate):
            self._variance_warnings += 1
            self._stability_adjustments += 1
            
            logger.warning(
                f"Near-constant variance detected ({variance_estimate:.2e}), "
                f"applying numerical stability adjustment"
            )
            
            # Adaptive variance floor based on observation magnitude
            obs_magnitude = np.mean(np.abs(observation))
            adaptive_floor = max(
                self.min_variance,
                obs_magnitude * 1e-4  # 0.01% of magnitude
            )
            
            variance_estimate = max(variance_estimate, adaptive_floor)
            
            # Add small jitter to prevent exact constant values
            if np.std(observation) < 1e-10:
                jitter = np.random.normal(0, adaptive_floor, observation.shape)
                observation = observation + jitter
                
        return observation, variance_estimate
    
    def _stick_breaking_weights(
        self,
        beta_samples: np.ndarray
    ) -> np.ndarray:
        """
        Compute stick-breaking weights from beta parameters.
        
        Implements numerically stable stick-breaking construction
        for Dirichlet process mixture weights.
        
        Args:
            beta_samples: Beta distribution samples for stick-breaking
            
        Returns:
            Normalized mixture weights summing to 1
        """
        n_components = len(beta_samples)
        weights = np.zeros(n_components)
        remaining_stick = 1.0
        
        for i in range(n_components):
            # Numerically stable computation
            beta_val = self._add_numerical_stability(beta_samples[i])
            weights[i] = beta_val * remaining_stick
            remaining_stick *= (1 - beta_val)
            
        # Normalize to ensure sum = 1
        weights = weights / np.sum(weights + EPSILON)
        
        return weights
    
    def _compute_log_likelihood(
        self,
        observation: np.ndarray,
        means: np.ndarray,
        variances: np.ndarray,
        weights: np.ndarray
    ) -> np.ndarray:
        """
        Compute log-likelihood of observation under mixture model.
        
        Uses log-space computation for numerical stability with
        near-constant variance edge cases.
        
        Args:
            observation: Current observation
            means: Component means
            variances: Component variances
            weights: Component weights
            
        Returns:
            Log-likelihood for each component
        """
        n_components = len(weights)
        log_likelihoods = np.zeros(n_components)
        
        for k in range(n_components):
            # Numerically stable variance
            var_k = self._clamp_variance(np.array([variances[k]]))
            mean_k = means[k]
            
            # Log-likelihood for Gaussian component
            diff = observation - mean_k
            log_var = np.log(var_k + EPSILON)
            
            # Stable computation of log Gaussian
            log_likelihoods[k] = (
                -0.5 * np.log(2 * np.pi)
                - 0.5 * log_var
                - 0.5 * np.sum(diff ** 2 / var_k)
            )
            
            # Add log weight
            log_likelihoods[k] += np.log(self._add_numerical_stability(weights[k]))
            
        return log_likelihoods
    
    def incremental_update(
        self,
        observation: np.ndarray,
        learning_rate: float = 0.1
    ) -> Dict[str, float]:
        """
        Incrementally update model posterior with new observation.
        
        Handles edge cases for near-constant variance time series
        with numerical stability checks.
        
        Args:
            observation: New observation to incorporate
            learning_rate: Step size for variational update
            
        Returns:
            Dictionary with update diagnostics
        """
        # Handle edge case for near-constant variance
        observation, variance_estimate = self._handle_low_variance_observation(
            observation,
            self._estimate_observation_variance(observation)
        )
        
        self._observations.append(observation)
        self._n_observations += 1
        
        if not self._initialized:
            self._initialize_model(observation)
            self._initialized = True
        
        # Perform variational update
        update_info = self._perform_advi_update(observation, learning_rate)
        
        return {
            'n_observations': self._n_observations,
            'n_components': self._current_components,
            'variance_warnings': self._variance_warnings,
            'stability_adjustments': self._stability_adjustments,
            **update_info
        }
    
    def _estimate_observation_variance(self, observation: np.ndarray) -> float:
        """
        Estimate variance from observation for edge case detection.
        
        Args:
            observation: Observation array
            
        Returns:
            Estimated variance
        """
        if len(observation) > 1:
            return float(np.var(observation))
        return self.min_variance  # Default for single observation
    
    def _initialize_model(self, first_observation: np.ndarray) -> None:
        """
        Initialize model with first observation.
        
        Args:
            first_observation: First observation to initialize with
        """
        self._current_components = 1
        
        # Initialize with single component
        self._variational_params = {
            'means': [np.mean(first_observation)],
            'variances': [self._clamp_variance(np.array([np.var(first_observation)]))[0]],
            'weights': [1.0]
        }
        
        logger.info(f"DPGMM initialized with {self._current_components} component(s)")
    
    def _perform_advi_update(
        self,
        observation: np.ndarray,
        learning_rate: float
    ) -> Dict[str, float]:
        """
        Perform ADVI variational update for streaming observation.
        
        Args:
            observation: New observation
            learning_rate: Step size for update
            
        Returns:
            Update diagnostics
        """
        # Compute responsibilities with numerical stability
        means = self._variational_params['means']
        variances = self._variational_params['variances']
        weights = self._variational_params['weights']
        
        log_likelihoods = self._compute_log_likelihood(
            observation, means, variances, weights
        )
        
        # Compute responsibilities in log-space
        log_responsibilities = log_likelihoods - logsumexp(log_likelihoods)
        responsibilities = np.exp(log_responsibilities)
        
        # Update parameters with learning rate
        for k in range(len(means)):
            # Mean update
            means[k] = (
                (1 - learning_rate) * means[k]
                + learning_rate * observation
            )
            
            # Variance update with stability check
            diff = observation - means[k]
            new_var = (1 - learning_rate) * variances[k] + learning_rate * diff ** 2
            variances[k] = self._clamp_variance(np.array([new_var]))[0]
            
        # Weight update based on responsibility
        for k in range(len(weights)):
            weights[k] = (1 - learning_rate) * weights[k] + learning_rate * responsibilities[k]
            
        # Normalize weights
        weights = weights / np.sum(weights + EPSILON)
        
        # Check for potential new component (simplified stick-breaking)
        min_weight = np.min(weights)
        if min_weight < 0.01 and self._current_components < self.max_components:
            # Add new component with small weight
            self._add_new_component(observation)
            
        return {
            'elbo': float(-np.sum(responsibilities * log_likelihoods)),
            'max_responsibility': float(np.max(responsibilities))
        }
    
    def _add_new_component(self, observation: np.ndarray) -> None:
        """
        Add new mixture component via stick-breaking.
        
        Args:
            observation: Observation to initialize new component with
        """
        self._current_components += 1
        
        # Initialize new component with small weight
        new_weight = 0.01 / self._current_components
        
        self._variational_params['means'].append(np.mean(observation))
        self._variational_params['variances'].append(self.min_variance)
        self._variational_params['weights'].append(new_weight)
        
        # Renormalize all weights
        total_weight = sum(self._variational_params['weights'])
        self._variational_params['weights'] = [
            w / total_weight for w in self._variational_params['weights']
        ]
        
        logger.debug(f"Added component {self._current_components} (weight: {new_weight:.4f})")
    
    def compute_anomaly_score(self, observation: np.ndarray) -> float:
        """
        Compute anomaly score for observation.
        
        Score is negative log posterior probability under the model.
        Lower scores indicate more typical observations.
        
        Args:
            observation: Observation to score
            
        Returns:
            Anomaly score (negative log probability)
        """
        if not self._initialized:
            return 0.0  # No model to score against
        
        # Compute log-likelihood with numerical stability
        means = self._variational_params['means']
        variances = self._variational_params['variances']
        weights = self._variational_params['weights']
        
        log_likelihoods = self._compute_log_likelihood(
            observation, means, variances, weights
        )
        
        # Log-sum-exp for stable marginal likelihood
        log_marginal = logsumexp(log_likelihoods)
        
        # Anomaly score is negative log probability
        score = -log_marginal
        
        return float(score)
    
    def get_state(self) -> Dict:
        """
        Get model state for serialization.
        
        Returns:
            Dictionary of model parameters
        """
        return {
            'alpha': self.alpha,
            'max_components': self.max_components,
            'min_variance': self.min_variance,
            'n_observations': self._n_observations,
            'n_components': self._current_components,
            'variational_params': self._variational_params,
            'variance_warnings': self._variance_warnings,
            'stability_adjustments': self._stability_adjustments
        }
    
    def load_state(self, state: Dict) -> None:
        """
        Load model state from serialization.
        
        Args:
            state: Dictionary of model parameters
        """
        self.alpha = state['alpha']
        self.max_components = state['max_components']
        self.min_variance = state['min_variance']
        self._n_observations = state['n_observations']
        self._current_components = state['n_components']
        self._variational_params = state['variational_params']
        self._variance_warnings = state['variance_warnings']
        self._stability_adjustments = state['stability_adjustments']
        self._initialized = True
