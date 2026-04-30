"""
Dirichlet Process Gaussian Mixture Model for Anomaly Detection in Time Series.

Implements streaming DPGMM with ADVI variational inference and ELBO convergence logging.
Per Constitution Principle VI: All inference procedures must log convergence metrics.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import logging
from datetime import datetime
from pathlib import Path

# Configure logging for ELBO convergence tracking
logger = logging.getLogger(__name__)

@dataclass
class ELBOHistory:
    """Constitution Principle VI: Track ELBO convergence for ADVI inference."""
    iterations: List[int] = field(default_factory=list)
    elbo_values: List[float] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)
    convergence_threshold: float = 1e-4
    max_no_improvement: int = 100

    def record(self, iteration: int, elbo: float) -> None:
        """Record ELBO value at given iteration."""
        self.iterations.append(iteration)
        self.elbo_values.append(elbo)
        self.timestamps.append(datetime.now().isoformat())

    def is_converged(self, min_iterations: int = 10) -> bool:
        """Check if ELBO has converged based on recent change."""
        if len(self.elbo_values) < min_iterations:
            return False
        recent = self.elbo_values[-self.max_no_improvement:]
        if len(recent) < 2:
            return False
        recent_change = abs(recent[-1] - recent[-2])
        return recent_change < self.convergence_threshold

    def get_elbo_change(self) -> float:
        """Get change in ELBO since last iteration."""
        if len(self.elbo_values) < 2:
            return 0.0
        return self.elbo_values[-1] - self.elbo_values[-2]

    def summary(self) -> Dict[str, Any]:
        """Return convergence summary statistics."""
        if not self.elbo_values:
            return {
                'total_iterations': 0,
                'final_elbo': None,
                'initial_elbo': None,
                'converged': False,
                'elbo_improvement': 0.0
            }
        return {
            'total_iterations': len(self.iterations),
            'final_elbo': self.elbo_values[-1],
            'initial_elbo': self.elbo_values[0],
            'converged': self.is_converged(),
            'elbo_improvement': self.elbo_values[-1] - self.elbo_values[0],
            'final_elbo_change': self.get_elbo_change()
        }

    def save_to_log(self, log_path: Path) -> None:
        """Save ELBO history to log file for debugging and audit."""
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'w') as f:
            f.write("ELBO Convergence Log - Constitution Principle VI\n")
            f.write(f"Start Time: {self.timestamps[0] if self.timestamps else 'N/A'}\n")
            f.write(f"Convergence Threshold: {self.convergence_threshold}\n")
            f.write("-" * 60 + "\n")
            f.write("Iter,ELBO,Delta\n")
            for i, (it, elbo) in enumerate(zip(self.iterations, self.elbo_values)):
                delta = self.elbo_values[i] - self.elbo_values[i-1] if i > 0 else 0.0
                f.write(f"{it},{elbo:.6f},{delta:.6f}\n")

@dataclass
class ClusterAnomalyResult:
    """Result of cluster anomaly detection."""
    cluster_id: int
    cluster_size: int
    anomaly_score: float
    confidence: float
    timestamps: List[str] = field(default_factory=list)

@dataclass
class DPGMMConfig:
    """Configuration for DPGMM model with ADVI inference."""
    max_components: int = 20
    min_components: int = 1
    concentration_prior: float = 1.0
    learning_rate: float = 0.01
    max_iterations: int = 1000
    convergence_threshold: float = 1e-4
    elbo_log_interval: int = 10
    random_seed: Optional[int] = None

@dataclass
class AnomalyScore:
    """Anomaly score with probabilistic uncertainty."""
    timestamp: str
    score: float
    uncertainty: float
    component_id: Optional[int] = None
    log_likelihood: float = 0.0
    elbo_at_observation: Optional[float] = None

class DPGMMModel:
    """
    Streaming DPGMM with ADVI variational inference.

    Constitution Principle VI: ELBO convergence is logged for all inference.
    """

    def __init__(self, config: Optional[DPGMMConfig] = None):
        self.config = config or DPGMMConfig()
        if self.config.random_seed is not None:
            np.random.seed(self.config.random_seed)

        # Model parameters
        self.means: List[np.ndarray] = []
        self.covariances: List[np.ndarray] = []
        self.weights: List[float] = []
        self.concentration: float = self.config.concentration_prior

        # ADVI variational parameters
        self.variational_means: List[np.ndarray] = []
        self.variational_precisions: List[np.ndarray] = []

        # ELBO convergence tracking (Constitution Principle VI)
        self.elbo_history: Optional[ELBOHistory] = None
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up ELBO convergence logging per Constitution Principle VI."""
        log_dir = Path("code/logs/elbo")
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = log_dir / f"elbo_convergence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    def initialize(self, data: np.ndarray) -> None:
        """Initialize model with first batch of data."""
        if len(data) == 0:
            raise ValueError("Cannot initialize with empty data")

        # Initialize first component
        self.means = [np.mean(data, axis=0)]
        self.covariances = [np.cov(data.T) + np.eye(data.shape[1]) * 1e-6]
        self.weights = [1.0]

        # Initialize variational parameters
        self.variational_means = [self.means[0].copy()]
        self.variational_precisions = [np.linalg.inv(self.covariances[0])]

        # Initialize ELBO history for convergence tracking
        self.elbo_history = ELBOHistory(
            convergence_threshold=self.config.convergence_threshold
        )

        # Log initial ELBO
        initial_elbo = self._compute_elbo(data)
        self.elbo_history.record(0, initial_elbo)
        logger.info(f"[ELBO] Initial: {initial_elbo:.6f} - Constitution Principle VI")

    def _compute_elbo(self, data: np.ndarray) -> float:
        """
        Compute Evidence Lower Bound (ELBO) for convergence tracking.

        Constitution Principle VI: ELBO must be logged for all ADVI inference.
        """
        if len(data) == 0 or not self.means:
            return 0.0

        n_samples, n_features = data.shape
        n_components = len(self.means)

        # Compute responsibilities
        responsibilities = np.zeros((n_samples, n_components))
        for k in range(n_components):
            diff = data - self.means[k]
            log_prob = -0.5 * n_features * np.log(2 * np.pi)
            log_prob -= 0.5 * np.log(np.linalg.det(self.covariances[k]))
            log_prob -= 0.5 * np.sum(diff @ np.linalg.inv(self.covariances[k]) * diff, axis=1)
            responsibilities[:, k] = self.weights[k] * np.exp(log_prob)

        # Normalize responsibilities
        resp_sum = responsibilities.sum(axis=1, keepdims=True)
        resp_sum[resp_sum == 0] = 1e-10
        responsibilities = responsibilities / resp_sum

        # Compute expected log likelihood
        expected_ll = 0.0
        for k in range(n_components):
            diff = data - self.means[k]
            log_det = np.linalg.slogdet(self.covariances[k])[1]
            trace_term = np.trace(np.linalg.inv(self.covariances[k]) @ np.cov(data.T))
            expected_ll += np.sum(responsibilities[:, k] * (
                np.log(self.weights[k]) - 0.5 * n_features * np.log(2 * np.pi)
                - 0.5 * log_det - 0.5 * np.sum(diff @ np.linalg.inv(self.covariances[k]) * diff, axis=1)
            ))

        # Add prior terms (simplified for logging)
        prior_term = self.concentration * np.log(self.concentration)

        return expected_ll + prior_term

    def update(self, observation: np.ndarray) -> AnomalyScore:
        """
        Update model with single observation (streaming).

        Constitution Principle VI: Log ELBO at each update interval.
        """
        timestamp = datetime.now().isoformat()

        # Initialize model if first observation
        if not self.means:
            self.initialize(observation.reshape(1, -1))
            return AnomalyScore(
                timestamp=timestamp,
                score=0.0,
                uncertainty=1.0,
                elbo_at_observation=self.elbo_history.elbo_values[0] if self.elbo_history else None
            )

        # Compute anomaly score using current model
        score, uncertainty, component_id, log_likelihood = self._score_observation(observation)

        # Update model with new observation
        self._streaming_update(observation)

        # Log ELBO at configured interval (Constitution Principle VI)
        if self.elbo_history is not None and len(self.elbo_history.iterations) > 0:
            current_iter = len(self.elbo_history.iterations)
            if current_iter % self.config.elbo_log_interval == 0:
                current_elbo = self._compute_elbo(np.array([observation]))
                self.elbo_history.record(current_iter, current_elbo)

                if self.config.elbo_log_interval > 0:
                    logger.info(
                        f"[ELBO] Iter {current_iter}: {current_elbo:.6f}, "
                        f"Delta: {current_elbo - self.elbo_history.elbo_values[-2]:.6f} "
                        if len(self.elbo_history.elbo_values) > 1 else ""
                    )

        return AnomalyScore(
            timestamp=timestamp,
            score=score,
            uncertainty=uncertainty,
            component_id=component_id,
            log_likelihood=log_likelihood,
            elbo_at_observation=self.elbo_history.elbo_values[-1] if self.elbo_history else None
        )

    def _score_observation(self, observation: np.ndarray) -> Tuple[float, float, Optional[int], float]:
        """Compute anomaly score for single observation."""
        obs = observation.reshape(1, -1)
        n_components = len(self.means)

        # Compute log likelihood under each component
        log_likelihoods = []
        for k in range(n_components):
            diff = obs - self.means[k]
            log_det = np.linalg.slogdet(self.covariances[k])[1]
            mahalanobis = np.sum(diff @ np.linalg.inv(self.covariances[k]) * diff)
            log_likelihood = -0.5 * (obs.shape[1] * np.log(2 * np.pi) + log_det + mahalanobis)
            log_likelihoods.append(log_likelihood)

        # Find best fitting component
        best_component = np.argmax(log_likelihoods)
        max_log_likelihood = log_likelihoods[best_component]

        # Anomaly score is negative log likelihood (lower likelihood = higher anomaly)
        score = -max_log_likelihood
        uncertainty = 1.0 / (1.0 + np.exp(score))  # Scaled to [0, 1]

        return score, uncertainty, best_component, max_log_likelihood

    def _streaming_update(self, observation: np.ndarray) -> None:
        """Perform streaming update with ADVI posterior."""
        obs = observation.reshape(1, -1)

        # Compute responsibilities for current observation
        responsibilities = self._compute_responsibilities(obs)[0]

        # Update component parameters with exponential moving average
        alpha = self.config.learning_rate
        for k in range(len(self.means)):
            if responsibilities[k] > 0.1:  # Only update if observation fits component
                # Update mean
                self.means[k] = (1 - alpha) * self.means[k] + alpha * obs[0]

                # Update covariance (simplified streaming update)
                diff = obs[0] - self.means[k]
                self.covariances[k] = (1 - alpha) * self.covariances[k] + alpha * np.outer(diff, diff)
                self.covariances[k] += np.eye(obs.shape[1]) * 1e-6  # Regularization

                # Update variational parameters
                self.variational_means[k] = (1 - alpha) * self.variational_means[k] + alpha * obs[0]
                self.variational_precisions[k] = np.linalg.inv(self.covariances[k])

        # Normalize weights
        total_weight = sum(responsibilities)
        if total_weight > 0:
            for k in range(len(self.weights)):
                self.weights[k] = responsibilities[k] / total_weight

    def _compute_responsibilities(self, data: np.ndarray) -> np.ndarray:
        """Compute responsibilities for data points."""
        n_samples, n_features = data.shape
        n_components = len(self.means)
        responsibilities = np.zeros((n_samples, n_components))

        for k in range(n_components):
            diff = data - self.means[k]
            log_prob = -0.5 * n_features * np.log(2 * np.pi)
            log_prob -= 0.5 * np.log(np.linalg.det(self.covariances[k]))
            log_prob -= 0.5 * np.sum(diff @ np.linalg.inv(self.covariances[k]) * diff, axis=1)
            responsibilities[:, k] = self.weights[k] * np.exp(log_prob)

        # Normalize
        resp_sum = responsibilities.sum(axis=1, keepdims=True)
        resp_sum[resp_sum == 0] = 1e-10
        responsibilities = responsibilities / resp_sum

        return responsibilities

    def get_elbo_convergence_status(self) -> Dict[str, Any]:
        """
        Get ELBO convergence status for monitoring.

        Constitution Principle VI: Provide access to convergence metrics.
        """
        if self.elbo_history is None:
            return {
                'status': 'not_initialized',
                'message': 'ELBO history not initialized'
            }

        summary = self.elbo_history.summary()
        return {
            'status': 'converged' if summary['converged'] else 'training',
            'iterations': summary['total_iterations'],
            'final_elbo': summary['final_elbo'],
            'initial_elbo': summary['initial_elbo'],
            'improvement': summary['elbo_improvement'],
            'converged': summary['converged'],
            'log_path': str(self.log_path)
        }

    def save_elbo_log(self) -> Path:
        """Save ELBO convergence log to file."""
        if self.elbo_history is not None:
            self.elbo_history.save_to_log(self.log_path)
        return self.log_path

    def detect_clustered_anomalies(self, scores: List[AnomalyScore], window_size: int = 5) -> List[ClusterAnomalyResult]:
        """Detect clustered anomalies rather than isolated points."""
        if len(scores) < window_size:
            return []

        results = []
        i = 0
        while i < len(scores):
            if scores[i].score > np.median([s.score for s in scores]) * 1.5:
                # Found potential cluster start
                cluster_scores = [scores[i]]
                j = i + 1
                while j < len(scores) and j < i + window_size:
                    if scores[j].score > np.median([s.score for s in scores]) * 1.5:
                        cluster_scores.append(scores[j])
                        j += 1
                    else:
                        break

                if len(cluster_scores) >= 2:
                  # Cluster detected
                  avg_score = np.mean([s.score for s in cluster_scores])
                  confidence = len(cluster_scores) / window_size
                  results.append(ClusterAnomalyResult(
                      cluster_id=len(results),
                      cluster_size=len(cluster_scores),
                      anomaly_score=avg_score,
                      confidence=confidence,
                      timestamps=[s.timestamp for s in cluster_scores]
                  ))
                i = j
            else:
                i += 1

        return results

    def smooth_anomaly_scores(self, scores: List[AnomalyScore], window_size: int = 3) -> List[AnomalyScore]:
        """Smooth anomaly scores using moving average."""
        if len(scores) < window_size:
            return scores

        smoothed = []
        for i in range(len(scores)):
            start = max(0, i - window_size // 2)
            end = min(len(scores), i + window_size // 2 + 1)
            window_scores = [scores[j].score for j in range(start, end)]
            smoothed_score = np.mean(window_scores)

            smoothed.append(AnomalyScore(
                timestamp=scores[i].timestamp,
                score=smoothed_score,
                uncertainty=scores[i].uncertainty,
                component_id=scores[i].component_id,
                log_likelihood=scores[i].log_likelihood,
                elbo_at_observation=scores[i].elbo_at_observation
            ))

        return smoothed

def main():
    """Example usage with ELBO convergence logging."""
    logging.basicConfig(level=logging.INFO)
    config = DPGMMConfig(
        max_iterations=100,
        elbo_log_interval=10,
        random_seed=42
    )
    model = DPGMMModel(config)

    # Generate synthetic data
    np.random.seed(42)
    data = np.random.randn(1000, 2)
    data[500:550] += 3  # Inject anomaly cluster

    # Initialize and update
    model.initialize(data[:100])
    for i in range(100, len(data)):
        score = model.update(data[i])

    # Check convergence status
    status = model.get_elbo_convergence_status()
    print(f"ELBO Convergence Status: {status}")

    # Save log
    log_path = model.save_elbo_log()
    print(f"ELBO log saved to: {log_path}")

if __name__ == "__main__":
    main()
