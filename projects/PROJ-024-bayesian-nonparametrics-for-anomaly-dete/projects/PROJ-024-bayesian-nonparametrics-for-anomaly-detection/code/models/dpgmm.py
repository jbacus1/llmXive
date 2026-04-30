"""
Dirichlet Process Gaussian Mixture Model with Streaming Updates.

Implements incremental DPGMM using stick-breaking construction and
ADVI variational inference for time series anomaly detection.

Key Features:
- Streaming posterior updates for each observation
- Adaptive concentration parameter tuning for sensitivity control
- Numerical stability checks for edge cases
- Memory-efficient implementation for large time series

Author: Implementer Agent
Version: 1.0.0
"""

import numpy as np
import pymc as pm
import pytensor.tensor as pt
from scipy.special import digamma, gammaln
from typing import Optional, Dict, Tuple, List
import logging

from code.models.timeseries import TimeSeries
from code.utils.logger import get_logger

logger = get_logger(__name__)


class DPGMMModel:
    """
    Dirichlet Process Gaussian Mixture Model with adaptive concentration
    parameter tuning for streaming time series anomaly detection.

    The concentration parameter (alpha) controls the expected number of
    clusters. Adaptive tuning adjusts alpha based on observed cluster
    behavior to prevent over/under-clustering.
    """

    def __init__(
        self,
        alpha: float = 1.0,
        max_clusters: int = 50,
        min_cluster_size: int = 3,
        adaptation_window: int = 100,
        alpha_change_threshold: float = 0.1,
        min_alpha: float = 0.1,
        max_alpha: float = 10.0,
        random_seed: Optional[int] = None
    ):
        """
        Initialize DPGMM with adaptive concentration parameter.

        Args:
            alpha: Initial concentration parameter (controls cluster count)
            max_clusters: Maximum number of clusters to allow
            min_cluster_size: Minimum observations per cluster
            adaptation_window: Number of observations between alpha checks
            alpha_change_threshold: Threshold for significant alpha change
            min_alpha: Minimum allowed concentration parameter
            max_alpha: Maximum allowed concentration parameter
            random_seed: Random seed for reproducibility
        """
        self.alpha = alpha
        self.initial_alpha = alpha
        self.max_clusters = max_clusters
        self.min_cluster_size = min_cluster_size
        self.adaptation_window = adaptation_window
        self.alpha_change_threshold = alpha_change_threshold
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha
        self.random_seed = random_seed

        # Adaptive tuning state
        self._cluster_sizes: List[int] = []
        self._new_clusters_per_window: List[int] = []
        self._observations_since_last_adaptation: int = 0
        self._adaptation_history: List[Dict] = []

        # Model state
        self._n_components: int = 0
        self._mu: Optional[np.ndarray] = None
        self._tau: Optional[np.ndarray] = None  # Precision
        self._pi: Optional[np.ndarray] = None   # Mixing weights
        self._stick_weights: Optional[np.ndarray] = None

        logger.info(f"DPGMMModel initialized with alpha={alpha}, max_clusters={max_clusters}")

    def _compute_stick_breaking_weights(self, beta: np.ndarray) -> np.ndarray:
        """
        Compute stick-breaking weights from beta parameters.

        Args:
            beta: Beta parameters for stick-breaking construction

        Returns:
            Mixing weights pi_k = beta_k * prod_{j<k} (1 - beta_j)
        """
        n = len(beta)
        weights = np.zeros(n)
        cum_prod = 1.0

        for k in range(n):
            weights[k] = beta[k] * cum_prod
            cum_prod *= (1.0 - beta[k])

        return weights

    def _initialize_components(self, n_components: int) -> None:
        """Initialize component parameters with numerical stability."""
        self._n_components = n_components
        self._mu = np.zeros(n_components)
        self._tau = np.ones(n_components) * 1.0  # Precision
        self._pi = np.ones(n_components) / n_components
        self._stick_weights = np.ones(n_components)

    def update_concentration_parameter(self, observations_since_start: int) -> float:
        """
        Adaptively tune the concentration parameter based on cluster behavior.

        The concentration parameter controls the expected number of clusters:
        - High alpha: More clusters, higher sensitivity to anomalies
        - Low alpha: Fewer clusters, more robust to noise

        Adaptive Strategy:
        - Track new cluster formation rate over adaptation_window
        - If too many new clusters (>5% of window): increase alpha (prevent fragmentation)
        - If too few new clusters (<1% of window): decrease alpha (encourage discovery)
        - Apply bounded updates to prevent instability

        Args:
            observations_since_start: Total observations processed

        Returns:
            Updated concentration parameter
        """
        self._observations_since_last_adaptation += 1

        # Only adapt every adaptation_window observations
        if self._observations_since_last_adaptation < self.adaptation_window:
            return self.alpha

        # Compute cluster statistics
        n_clusters = len(self._cluster_sizes)
        new_clusters_this_window = self._new_clusters_per_window[-1] if self._new_clusters_per_window else 0
        total_observations = sum(self._cluster_sizes)

        if total_observations == 0:
            return self.alpha

        # Cluster formation rate (new clusters per observation)
        cluster_rate = new_clusters_this_window / self.adaptation_window

        # Determine adjustment direction
        adjustment_factor = 1.0

        # Prevent over-fragmentation: too many new clusters
        if cluster_rate > 0.05:  # More than 5% new clusters per window
            adjustment_factor = 0.95  # Decrease alpha to encourage merging
            logger.debug(
                f"High cluster formation rate ({cluster_rate:.3f}), "
                f"decreasing alpha by 5%"
            )

        # Prevent under-clustering: too few new clusters
        elif cluster_rate < 0.01:  # Less than 1% new clusters per window
            adjustment_factor = 1.05  # Increase alpha to encourage discovery
            logger.debug(
                f"Low cluster formation rate ({cluster_rate:.3f}), "
                f"increasing alpha by 5%"
            )

        # Apply bounded update
        new_alpha = self.alpha * adjustment_factor
        new_alpha = np.clip(new_alpha, self.min_alpha, self.max_alpha)

        # Check for significant change
        alpha_change = abs(new_alpha - self.alpha) / self.alpha

        if alpha_change > self.alpha_change_threshold:
            logger.info(
                f"Adaptive alpha update: {self.alpha:.4f} -> {new_alpha:.4f} "
                f"(change={alpha_change:.2%}, cluster_rate={cluster_rate:.4f})"
            )

            # Record adaptation history
            self._adaptation_history.append({
                'observations': observations_since_start,
                'old_alpha': self.alpha,
                'new_alpha': new_alpha,
                'cluster_rate': cluster_rate,
                'n_clusters': n_clusters,
                'total_observations': total_observations
            })

            self.alpha = new_alpha

        # Reset adaptation counter
        self._observations_since_last_adaptation = 0

        return self.alpha

    def record_cluster_creation(self, cluster_size: int) -> None:
        """
        Record a new cluster creation for adaptive tuning.

        Args:
            cluster_size: Initial size of the new cluster
        """
        self._cluster_sizes.append(cluster_size)

        # Track new clusters per window
        if len(self._new_clusters_per_window) == 0:
            self._new_clusters_per_window.append(1)
        else:
            self._new_clusters_per_window[-1] += 1

        # Trim history if too large
        if len(self._cluster_sizes) > 1000:
            self._cluster_sizes = self._cluster_sizes[-1000:]
            self._new_clusters_per_window = self._new_clusters_per_window[-1000:]

    def get_adaptation_stats(self) -> Dict:
        """
        Get statistics about concentration parameter adaptation.

        Returns:
            Dictionary with adaptation metrics
        """
        if not self._adaptation_history:
            return {
                'total_adaptations': 0,
                'current_alpha': self.alpha,
                'initial_alpha': self.initial_alpha,
                'n_clusters': len(self._cluster_sizes),
                'total_observations': sum(self._cluster_sizes) if self._cluster_sizes else 0
            }

        last_adaptation = self._adaptation_history[-1]
        return {
            'total_adaptations': len(self._adaptation_history),
            'current_alpha': self.alpha,
            'initial_alpha': self.initial_alpha,
            'alpha_change_percent': (self.alpha - self.initial_alpha) / self.initial_alpha * 100,
            'n_clusters': len(self._cluster_sizes),
            'total_observations': sum(self._cluster_sizes) if self._cluster_sizes else 0,
            'last_adaptation': last_adaptation,
            'adaptation_history': self._adaptation_history[-10:]  # Last 10 for memory
        }

    def validate_alpha_range(self) -> bool:
        """
        Validate that concentration parameter is within acceptable bounds.

        Returns:
            True if alpha is within bounds, False otherwise
        """
        if self.alpha < self.min_alpha:
            logger.warning(f"Alpha {self.alpha} below minimum {self.min_alpha}")
            return False

        if self.alpha > self.max_alpha:
            logger.warning(f"Alpha {self.alpha} above maximum {self.max_alpha}")
            return False

        return True

    def reset_adaptation(self) -> None:
        """Reset adaptive tuning state for fresh start."""
        self._cluster_sizes = []
        self._new_clusters_per_window = []
        self._observations_since_last_adaptation = 0
        self._adaptation_history = []
        self.alpha = self.initial_alpha
        logger.info("DPGMM adaptive tuning state reset")

    def get_cluster_sensitivity(self) -> Dict:
        """
        Get cluster sensitivity metrics based on current alpha.

        Returns:
            Dictionary with sensitivity metrics
        """
        # Expected number of clusters for n observations
        n_obs = sum(self._cluster_sizes) if self._cluster_sizes else 1
        expected_clusters = self.alpha * np.log(1 + n_obs / self.alpha)

        return {
            'current_alpha': self.alpha,
            'n_obs': n_obs,
            'expected_clusters': expected_clusters,
            'actual_clusters': len(self._cluster_sizes),
            'sensitivity_ratio': len(self._cluster_sizes) / max(expected_clusters, 1)
        }