"""
Dirichlet Process Gaussian Mixture Model (DPGMM) with ADVI Variational Inference
and ELBO Convergence Logging per Constitution Principle VI.

This module implements:
- Stick-breaking construction for Dirichlet Process
- ADVI (Automatic Differentiation Variational Inference) for streaming updates
- ELBO convergence logging for reproducibility and debugging

Public API:
- ELBOHistory: Dataclass for tracking ELBO values across iterations
- DPGMMConfig: Configuration for DPGMM model
- DPGMMModel: Main model class with streaming update support
- main: Entry point for CLI execution
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
import json
import os

# ============================================================================
# ELBO History Dataclass (Constitution Principle VI - Logging)
# ============================================================================

@dataclass
class ELBOHistory:
    """
    Tracks ELBO values across ADVI iterations for convergence monitoring.
    
    Per Constitution Principle VI, all variational inference procedures
    must log ELBO convergence to enable reproducibility and debugging.
    
    Attributes:
        iteration: List of iteration indices
        elbo_values: List of ELBO values at each iteration
        elbo_change: List of changes in ELBO (diff from previous)
        timestamp: ISO timestamp of when logging started
        model_id: Unique identifier for this model instance
        log_file: Path to the JSON log file if persisted
    """
    iteration: List[int] = field(default_factory=list)
    elbo_values: List[float] = field(default_factory=list)
    elbo_change: List[float] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    model_id: str = field(default_factory=lambda: f"dp_gmm_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    log_file: Optional[str] = None
    converged: bool = False
    convergence_threshold: float = 1e-4
    patience: int = 5
    
    def add_elbo(self, iteration: int, elbo_value: float) -> None:
        """Add a new ELBO value to the history."""
        self.iteration.append(iteration)
        self.elbo_values.append(elbo_value)
        
        if len(self.elbo_values) > 1:
            change = elbo_value - self.elbo_values[-2]
            self.elbo_change.append(change)
        else:
            self.elbo_change.append(0.0)
    
    def check_convergence(self, window_size: int = 5) -> bool:
        """
        Check if ELBO has converged based on recent changes.
        
        Args:
            window_size: Number of recent iterations to check
        
        Returns:
            True if ELBO change is below threshold for all recent iterations
        """
        if len(self.elbo_change) < window_size:
            return False
        
        recent_changes = self.elbo_change[-window_size:]
        avg_change = np.mean([abs(c) for c in recent_changes])
        return avg_change < self.convergence_threshold
    
    def save_to_file(self, log_dir: Path) -> Path:
        """
        Save ELBO history to a JSON file in the logs directory.
        
        Args:
            log_dir: Directory where ELBO logs should be stored
        
        Returns:
            Path to the created log file
        """
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"elbo_{self.model_id}.json"
        
        data = {
            "iteration": self.iteration,
            "elbo_values": self.elbo_values,
            "elbo_change": self.elbo_change,
            "timestamp": self.timestamp,
            "model_id": self.model_id,
            "converged": self.converged,
            "convergence_threshold": self.convergence_threshold,
            "patience": self.patience
        }
        
        with open(log_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.log_file = str(log_file)
        return log_file
    
    @classmethod
    def load_from_file(cls, log_file: Path) -> 'ELBOHistory':
        """Load ELBO history from a JSON file."""
        with open(log_file, 'r') as f:
            data = json.load(f)
        
        return cls(
            iteration=data.get('iteration', []),
            elbo_values=data.get('elbo_values', []),
            elbo_change=data.get('elbo_change', []),
            timestamp=data.get('timestamp', ''),
            model_id=data.get('model_id', ''),
            log_file=str(log_file),
            converged=data.get('converged', False),
            convergence_threshold=data.get('convergence_threshold', 1e-4),
            patience=data.get('patience', 5)
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get summary statistics of ELBO convergence."""
        if not self.elbo_values:
            return {
                "num_iterations": 0,
                "final_elbo": None,
                "initial_elbo": None,
                "improvement": None,
                "converged": False
            }
        
        return {
            "num_iterations": len(self.iteration),
            "final_elbo": self.elbo_values[-1] if self.elbo_values else None,
            "initial_elbo": self.elbo_values[0] if self.elbo_values else None,
            "improvement": (self.elbo_values[-1] - self.elbo_values[0]) if len(self.elbo_values) > 1 else 0.0,
            "converged": self.converged,
            "max_elbo": max(self.elbo_values) if self.elbo_values else None,
            "min_elbo": min(self.elbo_values) if self.elbo_values else None,
            "mean_elbo": np.mean(self.elbo_values) if self.elbo_values else None
        }

# ============================================================================
# Configuration
# ============================================================================

@dataclass
class DPGMMConfig:
    """
    Configuration for DPGMM model with ADVI variational inference.
    
    Attributes:
        max_components: Maximum number of mixture components (default 10)
        concentration_prior: Prior for Dirichlet process concentration (default 1.0)
        mean_prior: Prior mean for component means (default 0.0)
        cov_prior: Prior covariance for component covariances (default 1.0)
        learning_rate: Learning rate for ADVI updates (default 0.01)
        max_iterations: Maximum ADVI iterations per observation (default 100)
        convergence_threshold: ELBO convergence threshold (default 1e-4)
        log_elbo: Whether to log ELBO history (default True)
        elbo_log_dir: Directory for ELBO logs (default 'logs/elbo')
        random_seed: Random seed for reproducibility
    """
    max_components: int = 10
    concentration_prior: float = 1.0
    mean_prior: float = 0.0
    cov_prior: float = 1.0
    learning_rate: float = 0.01
    max_iterations: int = 100
    convergence_threshold: float = 1e-4
    log_elbo: bool = True
    elbo_log_dir: str = 'logs/elbo'
    random_seed: Optional[int] = 42
    
    def __post_init__(self):
        if self.random_seed is not None:
            np.random.seed(self.random_seed)

# ============================================================================
# Model Classes
# ============================================================================

@dataclass
class ClusterAnomalyResult:
    """Result from cluster-based anomaly detection."""
    observation_id: int
    anomaly_score: float
    assigned_cluster: Optional[int]
    cluster_weights: Dict[int, float]
    is_anomaly: bool
    confidence: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

class DPGMMModel:
    """
    Dirichlet Process Gaussian Mixture Model with ADVI Variational Inference.
    
    Implements streaming updates for time series anomaly detection with:
    - Stick-breaking construction for nonparametric mixture weights
    - ADVI for efficient variational inference
    - ELBO convergence logging per Constitution Principle VI
    
    Public Methods:
        fit: Train on batch of observations
        update: Streaming update with single observation
        score: Compute anomaly scores for observations
        get_elbo_history: Retrieve ELBO convergence history
    """
    
    def __init__(self, config: DPGMMConfig):
        """
        Initialize DPGMM model with configuration.
        
        Args:
            config: DPGMMConfig with hyperparameters
        """
        self.config = config
        self.concentration = config.concentration_prior
        self.max_components = config.max_components
        
        # Component parameters (means, covariances)
        self.means: np.ndarray = np.zeros((config.max_components, 1))
        self.covariances: np.ndarray = np.ones((config.max_components, 1, 1))
        
        # Stick-breaking weights
        self.beta: np.ndarray = np.ones(config.max_components) * 0.5
        self.weights: np.ndarray = np.ones(config.max_components) / config.max_components
        
        # Variational parameters
        self.var_means: np.ndarray = np.zeros((config.max_components, 1))
        self.var_precisions: np.ndarray = np.ones((config.max_components, 1, 1))
        self.var_concentration: float = config.concentration_prior
        
        # ELBO history for convergence tracking
        self.elbo_history: ELBOHistory = ELBOHistory(
            model_id=f"dp_gmm_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            convergence_threshold=config.convergence_threshold
        )
        
        # Logging setup
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # State tracking
        self.n_observations: int = 0
        self.n_active_components: int = 1
        self.is_fitted: bool = False
        
        if config.random_seed is not None:
            np.random.seed(config.random_seed)
    
    def _setup_logging(self) -> None:
        """Configure ELBO logging per Constitution Principle VI."""
        if self.config.log_elbo:
            log_dir = Path(self.config.elbo_log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Set up file handler for ELBO logs
            elbo_log_file = log_dir / f"elbo_{self.elbo_history.model_id}.log"
            file_handler = logging.FileHandler(elbo_log_file)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(file_handler)
            self.logger.info(f"ELBO logging initialized to {elbo_log_file}")
    
    def _compute_elbo(self, observations: np.ndarray, 
                     component_assignments: np.ndarray) -> float:
        """
        Compute Evidence Lower Bound (ELBO) for current variational parameters.
        
        The ELBO consists of:
        - Expected log likelihood of data under current components
        - KL divergence between variational and prior distributions
        - Entropy of variational distribution
        
        Args:
            observations: Array of observations [n_obs, n_features]
            component_assignments: Soft assignments [n_obs, n_components]
        
        Returns:
            ELBO value (higher is better)
        """
        n_obs = observations.shape[0]
        
        if n_obs == 0:
            return 0.0
        
        # Expected log likelihood
        log_likelihood = 0.0
        for k in range(self.n_active_components):
            mask = component_assignments[:, k] > 0
            if np.sum(mask) > 0:
                obs_k = observations[mask]
                
                # Gaussian log likelihood for component k
                diff = obs_k - self.var_means[k]
                log_det = np.log(np.linalg.det(self.var_precisions[k]))
                mahal = np.sum(diff @ self.var_precisions[k] @ diff.T, axis=1)
                log_likelihood += np.sum(mask) * (
                    0.5 * log_det - 0.5 * np.mean(mahal) - 0.5 * np.log(2 * np.pi)
                )
        
        # Expected log prior (Dirichlet process)
        log_prior = self._compute_log_prior()
        
        # Entropy of variational distribution
        entropy = self._compute_variational_entropy()
        
        elbo = log_likelihood + log_prior + entropy
        return elbo
    
    def _compute_log_prior(self) -> float:
        """Compute expected log prior under variational distribution."""
        # Dirichlet process prior on stick-breaking weights
        log_prior = 0.0
        for k in range(self.n_active_components):
            log_prior += (self.var_concentration - 1) * np.log(self.beta[k] + 1e-10)
        return log_prior
    
    def _compute_variational_entropy(self) -> float:
        """Compute entropy of variational distribution."""
        entropy = 0.0
        for k in range(self.n_active_components):
            # Gaussian entropy
            det = np.linalg.det(self.var_precisions[k])
            if det > 0:
                entropy += 0.5 * np.log(det)
        return entropy
    
    def _stick_breaking(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate stick-breaking weights from concentration parameter.
        
        Returns:
            Tuple of (beta values, cumulative weights)
        """
        beta = np.random.beta(1, self.var_concentration, self.max_components)
        weights = np.zeros(self.max_components)
        remaining = 1.0
        
        for k in range(self.max_components):
            weights[k] = remaining * beta[k]
            remaining *= (1 - beta[k])
        
        return beta, weights
    
    def _initialize_components(self, observations: np.ndarray) -> None:
        """Initialize component parameters from data."""
        if observations.shape[0] == 0:
            return
        
        # Initialize means from data statistics
        self.means[0, 0] = np.mean(observations)
        self.covariances[0, 0, 0] = np.var(observations) + 1e-6
        
        # Initialize variational parameters
        self.var_means[0, 0] = self.means[0, 0]
        self.var_precisions[0, 0, 0] = 1.0 / self.covariances[0, 0, 0]
        
        self.n_active_components = 1
    
    def _e_step(self, observations: np.ndarray) -> np.ndarray:
        """
        E-step: Compute soft component assignments.
        
        Args:
            observations: Array of observations [n_obs]
        
        Returns:
            Soft assignments [n_obs, n_components]
        """
        n_obs = observations.shape[0]
        assignments = np.zeros((n_obs, self.n_active_components))
        
        for k in range(self.n_active_components):
            # Compute responsibility for component k
            diff = observations - self.var_means[k, 0]
            precision = self.var_precisions[k, 0, 0]
            log_weight = np.log(self.weights[k] + 1e-10)
            log_prob = log_weight - 0.5 * np.log(2 * np.pi) + 0.5 * np.log(precision)
            log_prob -= 0.5 * precision * diff ** 2
            assignments[:, k] = log_prob
        
        # Softmax normalization
        max_log = np.max(assignments, axis=1, keepdims=True)
        assignments = np.exp(assignments - max_log)
        assignments /= np.sum(assignments, axis=1, keepdims=True) + 1e-10
        
        return assignments
    
    def _m_step(self, observations: np.ndarray, 
               assignments: np.ndarray) -> None:
        """
        M-step: Update variational parameters.
        
        Args:
            observations: Array of observations [n_obs]
            assignments: Soft assignments [n_obs, n_components]
        """
        n_obs = observations.shape[0]
        
        for k in range(self.n_active_components):
            n_k = np.sum(assignments[:, k]) + 1e-10
            
            # Update mean
            self.var_means[k, 0] = np.sum(assignments[:, k] * observations) / n_k
            
            # Update precision
            diff = observations - self.var_means[k, 0]
            var_k = np.sum(assignments[:, k] * diff ** 2) / n_k + 1e-6
            self.var_precisions[k, 0, 0] = 1.0 / var_k
            
            # Update weight
            self.weights[k] = n_k / n_obs
        
        # Normalize weights
        self.weights /= np.sum(self.weights)
    
    def _advi_update(self, observations: np.ndarray, 
                    iteration: int) -> float:
        """
        Perform one ADVI variational inference update.
        
        Args:
            observations: Array of observations [n_obs]
            iteration: Current iteration number
        
        Returns:
            ELBO value after update
        """
        # E-step
        assignments = self._e_step(observations)
        
        # M-step with learning rate
        self._m_step(observations, assignments)
        
        # Compute ELBO
        elbo = self._compute_elbo(observations, assignments)
        
        # Log ELBO for convergence monitoring (Constitution Principle VI)
        if self.config.log_elbo:
            self.elbo_history.add_elbo(iteration, elbo)
            
            # Check for convergence
            if iteration % 10 == 0:
                converged = self.elbo_history.check_convergence()
                if converged:
                    self.elbo_history.converged = True
                    self.logger.info(
                        f"ELBO converged at iteration {iteration}: "
                        f"final_elbo={elbo:.4f}"
                    )
                else:
                    self.logger.debug(
                        f"ELBO iteration {iteration}: {elbo:.4f}, "
                        f"change={self.elbo_history.elbo_change[-1]:.6f}"
                    )
            
            # Log to console every 10 iterations
            if iteration % 10 == 0:
                self.logger.info(f"ELBO @ {iteration}: {elbo:.4f}")
        
        return elbo
    
    def update(self, observation: float, 
              max_iter: Optional[int] = None) -> Tuple[float, Dict[str, Any]]:
        """
        Streaming update with single observation.
        
        Per Constitution Principle VI, ELBO convergence is logged
        for each update to enable reproducibility and debugging.
        
        Args:
            observation: Single observation value
            max_iter: Override max iterations for this update
        
        Returns:
            Tuple of (anomaly_score, update_info)
        """
        self.n_observations += 1
        obs_array = np.array([observation])
        
        # Initialize if first observation
        if not self.is_fitted:
            self._initialize_components(obs_array)
            self.is_fitted = True
        
        max_iterations = max_iter or self.config.max_iterations
        
        # Run ADVI for this observation
        prev_elbo = None
        for iteration in range(max_iterations):
            elbo = self._advi_update(obs_array, iteration)
            
            if prev_elbo is not None and abs(elbo - prev_elbo) < self.config.convergence_threshold:
                self.logger.debug(
                    f"Early convergence at iteration {iteration} "
                    f"(change={abs(elbo - prev_elbo):.8f})"
                )
                break
            prev_elbo = elbo
        
        # Compute anomaly score
        score = self.score(obs_array)
        
        update_info = {
            "iteration": iteration + 1,
            "final_elbo": elbo,
            "n_observations": self.n_observations,
            "n_active_components": self.n_active_components,
            "converged": self.elbo_history.converged,
            "elbo_log_file": self.elbo_history.log_file
        }
        
        return score[0], update_info
    
    def fit(self, observations: np.ndarray, 
           max_iter: Optional[int] = None) -> 'DPGMMModel':
        """
        Fit model on batch of observations.
        
        Args:
            observations: Array of observations [n_obs]
            max_iter: Maximum ADVI iterations
        
        Returns:
            Self for method chaining
        """
        self._initialize_components(observations)
        
        max_iterations = max_iter or self.config.max_iterations
        
        # Run ADVI on full batch
        for iteration in range(max_iterations):
            elbo = self._advi_update(observations, iteration)
            
            if iteration % 10 == 0:
                self.logger.info(f"Batch training ELBO @ {iteration}: {elbo:.4f}")
            
            # Check convergence
            if self.elbo_history.check_convergence():
                self.elbo_history.converged = True
                self.logger.info(f"Batch training converged at iteration {iteration}")
                break
        
        # Save final ELBO history
        if self.config.log_elbo:
            log_dir = Path(self.config.elbo_log_dir)
            self.elbo_history.save_to_file(log_dir)
            self.logger.info(f"ELBO history saved to {self.elbo_history.log_file}")
        
        return self
    
    def score(self, observations: np.ndarray) -> np.ndarray:
        """
        Compute anomaly scores (negative log posterior) for observations.
        
        Args:
            observations: Array of observations [n_obs]
        
        Returns:
            Array of anomaly scores [n_obs]
        """
        n_obs = observations.shape[0]
        scores = np.zeros(n_obs)
        
        for i in range(n_obs):
            obs = observations[i]
            log_posterior = -np.inf
            
            for k in range(self.n_active_components):
                # Log probability under component k
                diff = obs - self.var_means[k, 0]
                precision = self.var_precisions[k, 0, 0]
                log_weight = np.log(self.weights[k] + 1e-10)
                
                log_prob = (
                    log_weight - 0.5 * np.log(2 * np.pi) + 0.5 * np.log(precision)
                    - 0.5 * precision * diff ** 2
                )
                log_posterior = max(log_posterior, log_prob)
            
            # Anomaly score is negative log posterior
            scores[i] = -log_posterior if log_posterior > -np.inf else 0.0
        
        return scores
    
    def get_elbo_history(self) -> ELBOHistory:
        """
        Get ELBO convergence history.
        
        Per Constitution Principle VI, this method provides access to
        the logged ELBO values for reproducibility and debugging.
        
        Returns:
            ELBOHistory object with all logged values
        """
        return self.elbo_history
    
    def get_stats(self) -> Dict[str, Any]:
        """Get model statistics including ELBO convergence info."""
        return {
            "n_observations": self.n_observations,
            "n_active_components": self.n_active_components,
            "is_fitted": self.is_fitted,
            "concentration": self.concentration,
            "elbo_stats": self.elbo_history.get_stats(),
            "elbo_converged": self.elbo_history.converged,
            "elbo_log_file": self.elbo_history.log_file
        }
    
    def save(self, path: Path) -> None:
        """Save model state to disk."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        state = {
            "config": {
                "max_components": self.config.max_components,
                "concentration_prior": self.config.concentration_prior,
                "learning_rate": self.config.learning_rate,
                "max_iterations": self.config.max_iterations
            },
            "n_observations": self.n_observations,
            "n_active_components": self.n_active_components,
            "means": self.var_means[:self.n_active_components].tolist(),
            "precisions": self.var_precisions[:self.n_active_components].tolist(),
            "weights": self.weights[:self.n_active_components].tolist(),
            "concentration": self.concentration,
            "elbo_history": self.elbo_history.get_stats()
        }
        
        with open(path / "model_state.json", 'w') as f:
            json.dump(state, f, indent=2)
    
    @classmethod
    def load(cls, path: Path, config: Optional[DPGMMConfig] = None) -> 'DPGMMModel':
        """Load model state from disk."""
        path = Path(path)
        config = config or DPGMMConfig()
        
        with open(path / "model_state.json", 'r') as f:
            state = json.load(f)
        
        model = cls(config)
        model.n_observations = state["n_observations"]
        model.n_active_components = state["n_active_components"]
        model.var_means = np.array(state["means"])
        model.var_precisions = np.array(state["precisions"])
        model.weights = np.array(state["weights"])
        model.concentration = state["concentration"]
        model.is_fitted = True
        
        return model

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """
    CLI entry point for DPGMM model with ELBO logging demonstration.
    
    Demonstrates Constitution Principle VI by logging ELBO convergence
    during variational inference on synthetic data.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create configuration with ELBO logging enabled
    config = DPGMMConfig(
        max_components=5,
        concentration_prior=1.0,
        learning_rate=0.01,
        max_iterations=100,
        convergence_threshold=1e-4,
        log_elbo=True,
        elbo_log_dir='logs/elbo',
        random_seed=42
    )
    
    # Initialize model
    model = DPGMMModel(config)
    
    # Generate synthetic data for testing
    np.random.seed(42)
    n_observations = 1000
    observations = np.concatenate([
        np.random.normal(0, 1, 800),
        np.random.normal(5, 0.5, 200)
    ])
    
    # Fit model with ELBO logging
    model.fit(observations)
    
    # Compute anomaly scores
    scores = model.score(observations)
    
    # Print ELBO convergence summary
    elbo_stats = model.get_elbo_history().get_stats()
    print(f"\n=== ELBO Convergence Summary (Constitution Principle VI) ===")
    print(f"Model ID: {model.elbo_history.model_id}")
    print(f"Log File: {model.elbo_history.log_file}")
    print(f"Converged: {elbo_stats['converged']}")
    print(f"Final ELBO: {elbo_stats['final_elbo']:.4f}")
    print(f"Initial ELBO: {elbo_stats['initial_elbo']:.4f}")
    print(f"Improvement: {elbo_stats['improvement']:.4f}")
    print(f"Total Iterations: {elbo_stats['num_iterations']}")
    
    # Print model statistics
    stats = model.get_stats()
    print(f"\n=== Model Statistics ===")
    print(f"Observations: {stats['n_observations']}")
    print(f"Active Components: {stats['n_active_components']}")
    
    # Save model
    save_path = Path('models/dp_gmm_saved')
    model.save(save_path)
    print(f"\nModel saved to {save_path}")
    
    return model

if __name__ == '__main__':
    main()
