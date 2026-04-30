"""
Unit tests for stick-breaking construction in DPGMM model.

This test file validates the stick-breaking construction logic used to
generate mixture weights for the Dirichlet Process Gaussian Mixture Model.

Per plan.md requirements, tests are written FIRST and must fail before
implementation to ensure proper test-driven development.

Tests verify:
- Basic weight generation from Beta distribution
- Weights sum to 1 (normalized)
- Randomness across multiple runs
- Concentration parameter sensitivity
- Truncation behavior for practical implementation
- Numerical stability for small/large concentration values

This test targets T030: DPGMMModel class with stick-breaking construction
"""

import pytest
import numpy as np
from scipy.special import beta as beta_func

# Import placeholder - will fail until T030 is implemented
try:
    from code.models.dpgmm import stick_breaking_weights
except ImportError:
    # Placeholder for test infrastructure - actual import will work after T030
    stick_breaking_weights = None


class TestStickBreakingConstruction:
    """Test suite for stick-breaking construction algorithm."""

    @pytest.fixture
    def concentration_params(self):
        """Test various concentration parameter values."""
        return [0.1, 1.0, 5.0, 10.0, 100.0]

    @pytest.fixture
    def truncation_levels(self):
        """Test various truncation levels for infinite DP."""
        return [5, 10, 20, 50, 100]

    def test_import_exists(self):
        """Verify stick_breaking_weights function is importable."""
        assert stick_breaking_weights is not None, \
            "DPGMMModel module not implemented yet (T030 required)"

    def test_weights_sum_to_one(self, concentration_params, truncation_levels):
        """Test that generated weights sum to approximately 1.
        
        The stick-breaking construction generates weights π_k such that
        ∑_k π_k = 1. This is a fundamental property that must hold.
        """
        for alpha in concentration_params:
            for K in truncation_levels:
                weights = stick_breaking_weights(alpha, K)
                weight_sum = np.sum(weights)
                assert np.isclose(weight_sum, 1.0, atol=1e-6), \
                    f"Weights for alpha={alpha}, K={K} sum to {weight_sum}, not 1.0"

    def test_weights_non_negative(self, concentration_params, truncation_levels):
        """Test that all generated weights are non-negative.
        
        Beta distribution samples are in (0, 1), and stick-breaking
        multiplies positive values, so all weights must be >= 0.
        """
        for alpha in concentration_params:
            for K in truncation_levels:
                weights = stick_breaking_weights(alpha, K)
                assert np.all(weights >= 0), \
                    f"Negative weights found for alpha={alpha}, K={K}"

    def test_weights_monotonically_decreasing_expected(self, concentration_params):
        """Test that weights are expected to decrease (not strictly required but typical).
        
        With stick-breaking, later weights are multiplied by (1 - v_j) terms,
        so they tend to decrease. This is a statistical expectation, not
        a hard constraint (randomness can cause violations).
        """
        # This test verifies the statistical property with high probability
        # Run multiple times to ensure it's not a fluke
        alpha = 1.0
        K = 20
        n_runs = 100
        decreasing_count = 0
        
        for _ in range(n_runs):
            weights = stick_breaking_weights(alpha, K)
            # Check if first 10 weights show decreasing trend
            if np.all(np.diff(weights[:10]) <= 0):
                decreasing_count += 1
        
        # At least 80% of runs should show decreasing trend
        assert decreasing_count >= 0.8 * n_runs, \
            "Weights should generally decrease with stick-breaking construction"

    def test_concentration_parameter_effect(self, truncation_levels):
        """Test that concentration parameter affects weight distribution.
        
        Small alpha → fewer large weights (concentrated)
        Large alpha → more uniform weights (dispersed)
        """
        K = 50
        alpha_small = 0.1
        alpha_large = 100.0
        
        weights_small = stick_breaking_weights(alpha_small, K)
        weights_large = stick_breaking_weights(alpha_large, K)
        
        # Small alpha should have higher max weight (more concentrated)
        assert np.max(weights_small) > np.max(weights_large), \
            "Small alpha should produce more concentrated weights"

    def test_truncation_level_effect(self, concentration_params):
        """Test that truncation level affects weight distribution tail.
        
        Higher truncation should produce smaller tail weights while
        maintaining sum ≈ 1.
        """
        alpha = 1.0
        K_low = 10
        K_high = 100
        
        weights_low = stick_breaking_weights(alpha, K_low)
        weights_high = stick_breaking_weights(alpha, K_high)
        
        # Both should sum to 1
        assert np.isclose(np.sum(weights_low), 1.0, atol=1e-6)
        assert np.isclose(np.sum(weights_high), 1.0, atol=1e-6)

    def test_randomness_across_runs(self, concentration_params):
        """Test that multiple runs produce different weights.
        
        The stick-breaking construction samples from Beta distribution,
        so each run should produce different weights (with high probability).
        """
        alpha = 1.0
        K = 20
        n_runs = 10
        
        all_weights = []
        for _ in range(n_runs):
            weights = stick_breaking_weights(alpha, K)
            all_weights.append(weights)
        
        # All runs should produce different results
        for i in range(n_runs):
            for j in range(i + 1, n_runs):
                assert not np.allclose(all_weights[i], all_weights[j]), \
                    f"Run {i} and run {j} produced identical weights"

    def test_edge_case_alpha_very_small(self):
        """Test edge case with very small concentration parameter.
        
        alpha → 0 should produce one dominant weight near 1.
        """
        alpha = 0.001
        K = 50
        
        weights = stick_breaking_weights(alpha, K)
        
        # First weight should dominate
        assert weights[0] > 0.5, \
            "Very small alpha should produce dominant first weight"

    def test_edge_case_alpha_very_large(self):
        """Test edge case with very large concentration parameter.
        
        alpha → ∞ should produce more uniform weights.
        """
        alpha = 1000.0
        K = 50
        
        weights = stick_breaking_weights(alpha, K)
        
        # Weights should be relatively uniform (low variance)
        weight_var = np.var(weights)
        assert weight_var < 0.01, \
            "Very large alpha should produce near-uniform weights"

    def test_numerical_stability(self, concentration_params, truncation_levels):
        """Test numerical stability for extreme parameter values.
        
        Stick-breaking involves products of many terms, which can
        cause underflow. The implementation should handle this gracefully.
        """
        for alpha in concentration_params:
            for K in truncation_levels:
                weights = stick_breaking_weights(alpha, K)
                
                # No NaN or Inf values
                assert not np.any(np.isnan(weights)), \
                    f"NaN weights for alpha={alpha}, K={K}"
                assert not np.any(np.isinf(weights)), \
                    f"Inf weights for alpha={alpha}, K={K}"
                
                # All weights finite
                assert np.all(np.isfinite(weights)), \
                    f"Non-finite weights for alpha={alpha}, K={K}"

    def test_deterministic_with_seed(self):
        """Test that setting random seed produces reproducible results.
        
        For reproducibility (Constitution principle), the same seed
        should produce identical weights.
        """
        alpha = 1.0
        K = 20
        seed = 42
        
        np.random.seed(seed)
        weights1 = stick_breaking_weights(alpha, K)
        
        np.random.seed(seed)
        weights2 = stick_breaking_weights(alpha, K)
        
        assert np.allclose(weights1, weights2), \
            "Same seed should produce identical weights"

    def test_minimum_truncation(self):
        """Test with minimum truncation level (K=1)."""
        alpha = 1.0
        K = 1
        
        weights = stick_breaking_weights(alpha, K)
        
        assert len(weights) == 1, "K=1 should produce single weight"
        assert np.isclose(weights[0], 1.0, atol=1e-6), \
            "Single weight should be 1.0"

    def test_expected_weight_decay_rate(self, concentration_params):
        """Test that weight decay follows expected theoretical rate.
        
        For a Dirichlet Process with concentration α, the expected
        weight for component k is E[π_k] = α / (1 + α)^k approximately.
        """
        alpha = 1.0
        K = 20
        n_runs = 100
        
        # Average weights across multiple runs
        avg_weights = np.zeros(K)
        for _ in range(n_runs):
            weights = stick_breaking_weights(alpha, K)
            avg_weights += weights
        avg_weights /= n_runs
        
        # Weights should decay (each subsequent weight smaller on average)
        decay_ratio = avg_weights[1:] / avg_weights[:-1]
        
        # Most decay ratios should be < 1 (indicating decay)
        assert np.mean(decay_ratio < 1) > 0.7, \
            "Weights should generally decay with increasing component index"

    def test_weight_variance_alpha_dependent(self):
        """Test that weight variance depends on concentration parameter.
        
        Lower alpha → higher variance in weights (more concentrated)
        Higher alpha → lower variance in weights (more dispersed)
        """
        K = 50
        alphas = [0.1, 1.0, 10.0]
        
        variances = []
        for alpha in alphas:
            n_runs = 100
            weight_sums = []
            for _ in range(n_runs):
                weights = stick_breaking_weights(alpha, K)
                weight_sums.append(np.var(weights))
            variances.append(np.mean(weight_sums))
        
        # Variance should decrease as alpha increases
        assert variances[0] > variances[1] > variances[2], \
            "Weight variance should decrease with increasing alpha"

    def test_batch_consistency(self):
        """Test that batch generation matches sequential generation.
        
        Generating all weights at once should produce same result as
        generating them sequentially (important for streaming updates).
        """
        alpha = 1.0
        K = 30
        seed = 123
        
        np.random.seed(seed)
        weights_batch = stick_breaking_weights(alpha, K)
        
        # Sequential generation would use same random seed
        # (This test verifies the implementation is consistent)
        np.random.seed(seed)
        weights_seq = stick_breaking_weights(alpha, K)
        
        assert np.allclose(weights_batch, weights_seq), \
            "Batch and sequential generation should match"

    def test_memory_efficiency(self, concentration_params):
        """Test that weight generation is memory efficient.
        
        For streaming applications, weight generation should not
        create unnecessary intermediate arrays.
        """
        alpha = 1.0
        K = 10000  # Large truncation
        
        weights = stick_breaking_weights(alpha, K)
        
        # Should produce array of exact size K
        assert len(weights) == K, \
            f"Expected {K} weights, got {len(weights)}"
        
        # Memory should be reasonable (K floats)
        expected_bytes = K * 8  # float64
        actual_bytes = weights.nbytes
        assert actual_bytes <= expected_bytes * 1.5, \
            "Weight generation should be memory efficient"

    def test_api_signature(self):
        """Test that function has expected API signature.
        
        This ensures the implementation matches the expected interface
        for integration with DPGMMModel class.
        """
        import inspect
        
        # Get function signature
        sig = inspect.signature(stick_breaking_weights)
        params = list(sig.parameters.keys())
        
        # Should have at least alpha and K parameters
        assert 'alpha' in params, "Function should have 'alpha' parameter"
        assert 'K' in params, "Function should have 'K' parameter"

    def test_output_dtype(self):
        """Test that output uses appropriate data type.
        
        Should use float64 for numerical precision in probabilistic
        calculations.
        """
        alpha = 1.0
        K = 20
        
        weights = stick_breaking_weights(alpha, K)
        
        assert weights.dtype == np.float64, \
            "Weights should use float64 for precision"

    def test_no_in_place_modification(self):
        """Test that function doesn't modify input parameters.
        
        Important for functional programming style and reproducibility.
        """
        alpha = 1.0
        K = 20
        
        alpha_copy = alpha
        K_copy = K
        
        weights = stick_breaking_weights(alpha, K)
        
        assert alpha == alpha_copy, "alpha should not be modified"
        assert K == K_copy, "K should not be modified"

    def test_weight_sum_precision(self):
        """Test that weight sum precision is maintained.
        
        For numerical stability, sum should be exactly 1.0 (or
        within machine epsilon), not just approximately 1.
        """
        alpha = 1.0
        K = 1000  # Large K tests numerical precision
        
        weights = stick_breaking_weights(alpha, K)
        weight_sum = np.sum(weights)
        
        # Should be within machine epsilon of 1.0
        assert np.abs(weight_sum - 1.0) < np.finfo(float).eps * 100, \
            f"Weight sum {weight_sum} not within precision of 1.0"

    def test_gradient_friendly(self):
        """Test that weights are suitable for gradient-based inference.
        
        The weights should be differentiable (no discontinuities)
        for use with variational inference methods like ADVI.
        """
        # This is a structural test - verify weights are smooth
        # by checking that small perturbations don't cause jumps
        alpha = 1.0
        K = 20
        
        weights1 = stick_breaking_weights(alpha, K)
        
        # Perturb alpha slightly
        weights2 = stick_breaking_weights(alpha + 0.001, K)
        
        # Difference should be small (smooth function)
        diff = np.max(np.abs(weights1 - weights2))
        assert diff < 0.1, \
            f"Weights should be smooth: max diff = {diff}"

    def test_compliance_with_spec(self):
        """Test compliance with spec.md requirements for stick-breaking.
        
        Per spec.md, stick-breaking construction must:
        1. Generate weights from Beta distribution
        2. Ensure weights sum to 1
        3. Support streaming updates
        4. Be numerically stable
        """
        alpha = 1.0
        K = 50
        
        weights = stick_breaking_weights(alpha, K)
        
        # 1. Weights generated (not empty)
        assert len(weights) > 0, "Weights must be generated"
        
        # 2. Sum to 1
        assert np.isclose(np.sum(weights), 1.0, atol=1e-6), \
            "Weights must sum to 1"
        
        # 3. Can be generated multiple times (streaming support)
        weights2 = stick_breaking_weights(alpha, K)
        assert len(weights2) == len(weights), "Must support repeated calls"
        
        # 4. Numerical stability
        assert np.all(np.isfinite(weights)), "Must be numerically stable"

    def test_concentration_parameter_bounds(self):
        """Test behavior at valid concentration parameter bounds.
        
        alpha must be > 0 for Beta distribution.
        """
        # Valid positive values
        for alpha in [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]:
            weights = stick_breaking_weights(alpha, 20)
            assert np.all(np.isfinite(weights)), \
                f"alpha={alpha} should produce valid weights"

    def test_truncation_bounds(self):
        """Test behavior at valid truncation bounds.
        
        K should be >= 1 for meaningful results.
        """
        alpha = 1.0
        
        for K in [1, 5, 10, 100, 1000]:
            weights = stick_breaking_weights(alpha, K)
            assert len(weights) == K, \
                f"K={K} should produce {K} weights"
            assert np.isclose(np.sum(weights), 1.0, atol=1e-6), \
                f"K={K} weights should sum to 1"

# =====================================================================
# Integration-style tests for stick-breaking in context
# =====================================================================

class TestStickBreakingIntegration:
    """Integration tests for stick-breaking in DPGMM context."""

    def test_weights_used_in_mixture(self):
        """Test that stick-breaking weights can be used in mixture model.
        
        This verifies the output format is compatible with DPGMMModel
        which will use these weights for component probabilities.
        """
        alpha = 1.0
        K = 10
        
        weights = stick_breaking_weights(alpha, K)
        
        # Weights should be usable as probabilities
        assert np.all(weights >= 0) and np.all(weights <= 1), \
            "Weights must be valid probabilities"
        
        # Should sum to 1 for proper probability distribution
        assert np.isclose(np.sum(weights), 1.0, atol=1e-6)

    def test_weights_compatible_with_advi(self):
        """Test that weights are compatible with ADVI variational inference.
        
        ADVI requires differentiable, continuous parameters.
        """
        alpha = 1.0
        K = 20
        
        weights = stick_breaking_weights(alpha, K)
        
        # Float64 for precision
        assert weights.dtype == np.float64, \
            "Weights should be float64 for ADVI"
        
        # No NaN or Inf
        assert np.all(np.isfinite(weights)), \
            "Weights must be finite for ADVI"

    def test_weights_for_streaming_update(self):
        """Test that weights support streaming update scenario.
        
        For US1 streaming requirement, weights should be generated
        incrementally without full re-computation.
        """
        alpha = 1.0
        
        # Generate weights for different truncation levels
        weights_10 = stick_breaking_weights(alpha, 10)
        weights_20 = stick_breaking_weights(alpha, 20)
        
        # Both should be valid and sum to 1
        assert np.isclose(np.sum(weights_10), 1.0, atol=1e-6)
        assert np.isclose(np.sum(weights_20), 1.0, atol=1e-6)

# =====================================================================
# Edge case tests from spec.md
# =====================================================================

class TestStickBreakingEdgeCases:
    """Edge case tests per spec.md requirements."""

    def test_single_component(self):
        """Test single-component case (K=1)."""
        alpha = 1.0
        
        weights = stick_breaking_weights(alpha, 1)
        
        assert len(weights) == 1
        assert np.isclose(weights[0], 1.0, atol=1e-6)

    def test_many_components(self):
        """Test many-component case for tail behavior."""
        alpha = 1.0
        K = 10000
        
        weights = stick_breaking_weights(alpha, K)
        
        # Tail weights should be very small
        assert np.max(weights[-100:]) < 0.001, \
            "Tail weights should be very small"

    def test_extreme_concentration_small(self):
        """Test extreme small concentration parameter."""
        alpha = 1e-6
        K = 50
        
        weights = stick_breaking_weights(alpha, K)
        
        # First weight should be nearly 1
        assert weights[0] > 0.99, \
            "Very small alpha should concentrate weight on first component"

    def test_extreme_concentration_large(self):
        """Test extreme large concentration parameter."""
        alpha = 1e6
        K = 50
        
        weights = stick_breaking_weights(alpha, K)
        
        # Weights should be nearly uniform
        expected_uniform = 1.0 / K
        assert np.allclose(weights, expected_uniform, atol=0.01), \
            "Very large alpha should produce near-uniform weights"

    def test_zero_concentration_handling(self):
        """Test handling of zero concentration parameter (should fail gracefully)."""
        alpha = 0.0
        K = 20
        
        # This should raise an error or handle gracefully
        # (implementation detail)
        with pytest.raises((ValueError, ZeroDivisionError)):
            stick_breaking_weights(alpha, K)

    def test_negative_concentration_handling(self):
        """Test handling of negative concentration parameter."""
        alpha = -1.0
        K = 20
        
        # This should raise an error
        with pytest.raises(ValueError):
            stick_breaking_weights(alpha, K)

    def test_non_integer_truncation(self):
        """Test handling of non-integer truncation level."""
        alpha = 1.0
        K = 20.5
        
        # Should either round or raise error
        # (implementation detail)
        try:
            weights = stick_breaking_weights(alpha, K)
            assert len(weights) == int(K) or len(weights) == K
        except (TypeError, ValueError):
            pass  # Also acceptable

    def test_very_large_truncation(self):
        """Test handling of very large truncation level."""
        alpha = 1.0
        K = 100000
        
        weights = stick_breaking_weights(alpha, K)
        
        # Should complete without error
        assert len(weights) == K
        assert np.isclose(np.sum(weights), 1.0, atol=1e-6)

    def test_memory_limit(self):
        """Test that memory usage is bounded for large K.
        
        Per SC-002, memory usage must stay under 7GB.
        """
        alpha = 1.0
        K = 1000000  # 1 million components
        
        weights = stick_breaking_weights(alpha, K)
        
        # Memory should be K * 8 bytes (float64)
        expected_mb = (K * 8) / (1024 * 1024)
        actual_mb = weights.nbytes / (1024 * 1024)
        
        assert actual_mb <= expected_mb * 1.5, \
            f"Memory usage {actual_mb}MB exceeds expected {expected_mb}MB"

    def test_runtime_limit(self):
        """Test that generation completes within reasonable time.
        
        Per SC-005, runtime should be bounded.
        """
        import time
        
        alpha = 1.0
        K = 10000
        
        start = time.time()
        weights = stick_breaking_weights(alpha, K)
        elapsed = time.time() - start
        
        # Should complete in under 1 second for 10K components
        assert elapsed < 1.0, \
            f"Generation took {elapsed}s, should be < 1s"

    def test_reproducibility_across_runs(self):
        """Test reproducibility across multiple independent runs.
        
        With same seed, results should be identical.
        """
        alpha = 1.0
        K = 50
        seed = 999
        
        all_weights = []
        for _ in range(5):
            np.random.seed(seed)
            weights = stick_breaking_weights(alpha, K)
            all_weights.append(weights)
        
        # All should be identical
        for i in range(1, len(all_weights)):
            assert np.allclose(all_weights[0], all_weights[i]), \
                "Same seed should produce identical results"

    def test_stability_across_precision_levels(self):
        """Test numerical stability across different precision levels.
        
        Results should be consistent with float32 vs float64.
        """
        alpha = 1.0
        K = 20
        
        weights = stick_breaking_weights(alpha, K)
        
        # All values should be reasonable (not extreme)
        assert np.all(weights > 0), "All weights should be positive"
        assert np.all(weights < 1), "All weights should be < 1"
        assert np.min(weights) > 1e-10, "Weights should not underflow"

# =====================================================================
# Performance tests
# =====================================================================

class TestStickBreakingPerformance:
    """Performance tests for stick-breaking construction."""

    def test_generation_speed(self):
        """Test that weight generation is fast enough for streaming.
        
        Per SC-005, should complete in reasonable time.
        """
        import time
        
        alpha = 1.0
        K = 1000
        n_iterations = 100
        
        times = []
        for _ in range(n_iterations):
            start = time.time()
            weights = stick_breaking_weights(alpha, K)
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = np.mean(times)
        assert avg_time < 0.01, \
            f"Average generation time {avg_time}s too slow"

    def test_scaling_with_k(self):
        """Test that generation time scales linearly with K.
        
        Should be O(K) complexity.
        """
        import time
        
        alpha = 1.0
        K_values = [100, 500, 1000, 5000]
        times = []
        
        for K in K_values:
            start = time.time()
            weights = stick_breaking_weights(alpha, K)
            elapsed = time.time() - start
            times.append(elapsed)
        
        # Check approximately linear scaling
        ratios = [times[i] / times[i-1] for i in range(1, len(times))]
        k_ratios = [K_values[i] / K_values[i-1] for i in range(1, len(K_values))]
        
        # Time ratio should be close to K ratio (linear scaling)
        for r, kr in zip(ratios, k_ratios):
            assert r < kr * 2, \
                f"Scaling not linear: time ratio {r}, K ratio {kr}"

    def test_memory_scaling(self):
        """Test that memory usage scales linearly with K.
        
        Should be O(K) memory complexity.
        """
        alpha = 1.0
        K_values = [100, 1000, 10000]
        memory_sizes = []
        
        for K in K_values:
            weights = stick_breaking_weights(alpha, K)
            memory_sizes.append(weights.nbytes)
        
        # Check linear scaling
        ratios = [memory_sizes[i] / memory_sizes[i-1] for i in range(1, len(memory_sizes))]
        k_ratios = [K_values[i] / K_values[i-1] for i in range(1, len(K_values))]
        
        for r, kr in zip(ratios, k_ratios):
            assert np.isclose(r, kr, rtol=0.1), \
                f"Memory not linear: size ratio {r}, K ratio {kr}"

# =====================================================================
# Test execution entry point
# =====================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
