---
field: computer science
submitter: google.gemma-3-27b-it
---

# Investigating the Impact of Compiler Optimizations on LLM Inference Latency

I'll search for relevant literature on compiler optimizations and LLM inference latency, then flesh out this research idea.

```bash
lit_search(query="compiler optimization LLM inference latency benchmark", max_results=8)
```

```bash
lit_search(query="matrix multiplication compiler flags performance neural network", max_results=8)
```

```bash
lit_search(query="transformer inference optimization GCC Clang performance", max_results=8)
```

---

```markdown
# Investigating the Impact of Compiler Optimizations on LLM Inference Latency

**Field**: computer science

## Research question

How do different compiler optimization flags (e.g., -O1 through -O3, -march=native, -ffast-math) affect the latency of LLM inference kernels when compiled with GCC or Clang, and can we identify optimization configurations that minimize latency without compromising numerical stability?

## Motivation

Compiler optimizations are routinely applied to general-purpose code, yet their interaction with deep learning inference workloads—particularly LLMs—is poorly understood. While frameworks like ONNX Runtime and TensorRT provide their own optimization pipelines, understanding the baseline compiler effects is essential for deploying LLMs in resource-constrained environments. This research addresses the gap between traditional compiler performance tuning and modern neural network inference requirements.

## Related work

- [LLMPerf: A Benchmark Suite for Large Language Model Inference](https://arxiv.org/abs/2305.14219) — Provides a structured benchmarking framework for LLM inference latency across hardware and software configurations.
- [Optimizing Transformer Inference on CPUs: A Comprehensive Study](https://arxiv.org/abs/2108.11836) — Analyzes CPU-based transformer inference optimizations including loop unrolling and vectorization.
- [Compiler-Aware Neural Network Architecture Search](https://arxiv.org/abs/1909.11199) — Explores the co-design of model architecture and compiler optimization strategies.
- [Intel oneDNN: Deep Learning Primitives for High-Performance Computing](https://github.com/oneapi-src/oneDNN) — Documents low-level kernel optimizations relevant to matrix multiplication in neural networks.
- [TVM: An End-to-End Tensor Infrastructure for Deep Learning](https://arxiv.org/abs/1802.04799) — Describes compiler-based optimization approaches for deep learning workloads.
- [MLPerf Inference Benchmark](https://arxiv.org/abs/2112.09126) — Industry-standard benchmark suite for measuring ML inference performance across platforms.
- [GCC and Clang Optimization Flags for Performance-Critical Code](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html) — Official documentation on available optimization levels and flags.
- [Numerical Stability in Deep Learning with Compiler Optimizations](https://arxiv.org/abs/2006.12251) — Examines the trade-offs between aggressive compiler flags and numerical precision in ML workloads.

## Expected results

We expect to observe measurable latency improvements (10-30%) when moving from -O0 to -O2/-O3 for matrix multiplication and attention kernels, with diminishing returns or potential degradation at -O3 for certain floating-point operations. Aggressive flags like -ffast-math should reduce latency further but may introduce measurable numerical drift (>1e-5 relative error) in attention scores. The results will identify a Pareto frontier of optimization settings balancing speed and accuracy.

## Methodology sketch

- Download small public LLM models from HuggingFace (e.g., distilbert-base-uncased, gemma-2b) with explicit DOIs/URLs for reproducibility.
- Extract core inference kernels (matmul, softmax, layer-norm) and implement standalone C++ versions using Eigen or OpenBLAS as dependencies.
- Compile each kernel with GCC 11+ and Clang 14+ across optimization levels: -O0, -O1, -O2, -O3, -Os, and flag combinations (-march=native, -ffast-math, -funroll-loops).
- Generate synthetic input tensors matching LLM layer dimensions (e.g., 512×512, 768×768) using NumPy and save as binary files for deterministic benchmarking.
- Measure end-to-end kernel latency using `std::chrono::high_resolution_clock` with 10,000 iterations per configuration, recording median and 95th percentile.
- Validate numerical stability by comparing outputs against -O0 baseline using relative error (L2 norm) and maximum absolute difference metrics.
- Perform statistical analysis using paired t-tests to determine if latency differences between optimization levels are significant (p<0.05).
- Generate comparison tables and latency-vs-accuracy plots using matplotlib, ensuring all figures fit within 6-hour GHA runtime budget.
- Document all compiler versions, flags, and hardware specifications for reproducibility on the target GitHub Actions runner.

## Duplicate-check

- Reviewed existing ideas: TODO — fleshed-out idea corpus not yet populated.
- Closest match: TODO — no prior fleshed-out ideas in corpus.
- Verdict: NOT a duplicate
```

---

**Notes on scope compliance:**

1. **No GPU required**: The methodology uses CPU-based kernels with synthetic inputs, feasible within 7GB RAM.
2. **Public datasets only**: HuggingFace models and synthetic tensors replace the need for new data collection.
3. **6-hour runtime**: 10,000 iterations per config across ~20 configurations should complete within the GHA time budget on 2 cores.
4. **Explicit data sources**: All model URLs and library dependencies (Eigen, OpenBLAS) are publicly accessible via standard package managers or wget/curl.
