"""
Anomaly Detection Service for Bayesian Nonparametric Time Series

This module implements the AnomalyDetector service that computes anomaly scores
based on the negative log posterior probability from a DPGMM model.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging

from ..models.dpgmm import DPGMMModel
from ..models.anomaly_score import AnomalyScore
from ..models.timeseries import TimeSeries
from ..models.evaluation_metrics import EvaluationMetrics
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AnomalyDetector:
    """
    Anomaly detection service using DPGMM model.
    
    Computes anomaly scores as negative log posterior probability.
    Observations with lower posterior probability (higher negative log posterior)
    are considered more anomalous.
    
    Attributes:
        model: The DPGMM model instance for inference
        threshold: Optional threshold for flagging anomalies
        config: Configuration dictionary for detector parameters
    """
    
    def __init__(
        self,
        model: DPGMMModel,
        threshold: Optional[float] = None,
        config: Optional[Dict] = None
    ):
        """
        Initialize the AnomalyDetector.
        
        Args:
            model: Pre-trained DPGMMModel instance
            threshold: Optional anomaly threshold (scores above this are anomalies)
            config: Configuration dictionary with detector parameters
        """
        self.model = model
        self.threshold = threshold
        self.config = config or {}
        logger.info(f"AnomalyDetector initialized with threshold={threshold}")
    
    def compute_log_posterior(
        self,
        observation: Union[float, np.ndarray],
        component_weights: Optional[np.ndarray] = None,
        component_means: Optional[np.ndarray] = None,
        component_variances: Optional[np.ndarray] = None
    ) -> float:
        """
        Compute the log posterior probability for a single observation.
        
        The log posterior is computed as:
        log p(x|model) = log sum_k [w_k * N(x | mu_k, sigma_k^2)]
        
        Args:
            observation: Single observation value (scalar or 1D array)
            component_weights: Optional pre-computed component weights
            component_means: Optional pre-computed component means
            component_variances: Optional pre-computed component variances
            
        Returns:
            log_posterior: Log probability of the observation under the model
        """
        # Get model parameters if not provided
        if component_weights is None:
            component_weights = self.model.get_component_weights()
        if component_means is None:
            component_means = self.model.get_component_means()
        if component_variances is None:
            component_variances = self.model.get_component_variances()
        
        # Ensure observation is numpy array
        if np.isscalar(observation):
            observation = np.array([observation])
        
        # Compute log likelihood for each component
        log_likelihoods = []
        for k in range(len(component_weights)):
            # Compute log of Gaussian PDF: -0.5 * log(2*pi*sigma^2) - 0.5 * (x-mu)^2/sigma^2
            mu = component_means[k]
            sigma_sq = component_variances[k]
            
            # Handle numerical stability - ensure minimum variance
            sigma_sq = max(sigma_sq, 1e-10)
            
            # Compute log likelihood for this component
            log_likelihood = -0.5 * np.log(2 * np.pi * sigma_sq) - \
                            0.5 * ((observation - mu) ** 2) / sigma_sq
            
            # Weight by component weight
            log_weight = np.log(max(component_weights[k], 1e-10))
            log_likelihoods.append(log_weight + log_likelihood)
        
        # Log-sum-exp trick for numerical stability
        log_likelihoods = np.array(log_likelihoods)
        max_ll = np.max(log_likelihoods)
        log_sum_exp = max_ll + np.log(np.sum(np.exp(log_likelihoods - max_ll)))
        
        return log_sum_exp
    
    def compute_anomaly_score(
        self,
        observation: Union[float, np.ndarray]
    ) -> AnomalyScore:
        """
        Compute anomaly score for a single observation.
        
        The anomaly score is the negative log posterior probability.
        Higher scores indicate more anomalous observations.
        
        Args:
            observation: Single observation value
            
        Returns:
            AnomalyScore: Named tuple with score and metadata
        """
        try:
            # Compute log posterior
            log_posterior = self.compute_log_posterior(observation)
            
            # Anomaly score is negative log posterior
            anomaly_score = -log_posterior
            
            # Determine if anomaly based on threshold
            is_anomaly = False
            if self.threshold is not None:
                is_anomaly = anomaly_score > self.threshold
            
            # Create AnomalyScore object
            score = AnomalyScore(
                value=float(anomaly_score),
                observation=float(observation) if np.isscalar(observation) else float(observation[0]),
                is_anomaly=is_anomaly,
                threshold=self.threshold,
                log_posterior=float(log_posterior)
            )
            
            logger.debug(f"Anomaly score computed: {anomaly_score:.4f}, is_anomaly: {is_anomaly}")
            
            return score
            
        except Exception as e:
            logger.error(f"Error computing anomaly score for observation {observation}: {e}")
            raise
    
    def compute_anomaly_scores_batch(
        self,
        observations: Union[List[float], np.ndarray]
    ) -> List[AnomalyScore]:
        """
        Compute anomaly scores for multiple observations.
        
        Args:
            observations: List or array of observation values
            
        Returns:
            List of AnomalyScore objects, one per observation
        """
        scores = []
        for obs in observations:
            score = self.compute_anomaly_score(obs)
            scores.append(score)
        
        logger.info(f"Computed {len(scores)} anomaly scores")
        return scores
    
    def update_and_score(
        self,
        observation: Union[float, np.ndarray],
        update_model: bool = True
    ) -> AnomalyScore:
        """
        Update the model with a new observation and compute its anomaly score.
        
        This is the streaming inference workflow:
        1. Update model posterior with new observation
        2. Compute anomaly score for the observation based on updated model
        
        Args:
            observation: New observation value
            update_model: Whether to update model before scoring
            
        Returns:
            AnomalyScore: Score for the observation
        """
        if update_model:
            # Update model with new observation
            self.model.update(observation)
            logger.debug("Model updated with new observation")
        
        # Compute anomaly score
        score = self.compute_anomaly_score(observation)
        
        return score
    
    def set_threshold(self, threshold: float) -> None:
        """
        Set the anomaly threshold.
        
        Args:
            threshold: Score threshold above which observations are flagged as anomalies
        """
        self.threshold = threshold
        logger.info(f"Anomaly threshold set to {threshold}")
    
    def get_threshold(self) -> Optional[float]:
        """
        Get the current anomaly threshold.
        
        Returns:
            Current threshold value or None if not set
        """
        return self.threshold
    
    def score_time_series(
        self,
        timeseries: TimeSeries,
        streaming: bool = True
    ) -> List[AnomalyScore]:
        """
        Score all observations in a TimeSeries object.
        
        Args:
            timeseries: TimeSeries object containing observations
            streaming: If True, update model after each observation
            
        Returns:
            List of AnomalyScore objects, one per observation
        """
        scores = []
        for obs in timeseries.observations:
            if streaming:
                score = self.update_and_score(obs, update_model=True)
            else:
                score = self.compute_anomaly_score(obs)
            scores.append(score)
        
        logger.info(f"Scored {len(scores)} observations from TimeSeries")
        return scores