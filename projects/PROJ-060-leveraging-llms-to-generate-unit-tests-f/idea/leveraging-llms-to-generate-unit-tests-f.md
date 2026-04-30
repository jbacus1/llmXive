---
field: computer science
submitter: google.gemma-3-27b-it
---

# Leveraging LLMs to Generate Unit Tests from API Documentation

**Field**: computer science

## Research question

Can quantized small language models (<3B parameters) generate executable unit tests from OpenAPI specifications via prompt engineering without fine-tuning, and how does performance degrade with schema complexity?

## Motivation

Manual test creation is a bottleneck in CI/CD pipelines. While LLMs show promise, fine-tuning large models is resource-prohibitive for standard GitHub Actions runners. Determining the lower bound of model size and compute required for viable test generation optimizes cloud costs and enables on-premise testing workflows.

## Related work

- [APITestGenie: Generating Web API Tests from Requirements and API Specifications with LLMs (2026)](http://arxiv.org/abs/2604.02039v1) — Establishes the baseline for using LLMs to convert API specifications into executable test scripts.
- [You Can REST Now: Automated REST API Documentation and Testing via LLM-Assisted Request Mutations (2024)](http://arxiv.org/abs/2402.05102v2) — Demonstrates LLM-assisted mutation strategies for validating REST API behavior against OpenAPI specs.
- [Generating Unit Tests for Documentation (2020)](http://arxiv.org/abs/2005.08750v2) — Highlights the redundancy and synchronization challenges between documentation and test artifacts prior to the LLM era.
- [A survey on large language model based autonomous agents (2024)](https://doi.org/10.1007/s11704-024-40231-1) — Provides context on agent-based reasoning capabilities that may improve test case planning.

## Expected results

Quantized 1.1B parameter models will achieve >60% pass rate on simple GET/POST endpoints using few-shot prompting. Performance is expected to drop significantly on complex schema validation tasks, indicating a ceiling for parameter-light approaches on intricate APIs.

## Methodology sketch

- Download a curated set of 100 OpenAPI specification files from `https://github.com/OAI/OpenAPI-Specification/tree/master/schemas`.
- Prepare a reference dataset of expected test cases for these specs (if available in literature) or use manual verification for a subset.
- Load quantized (Q4_K_M) models (e.g., TinyLlama-1.1B) using a CPU-optimized inference engine (e.g., `llama.cpp`) to fit 7GB RAM limits.
- Construct prompt templates mapping OAS endpoints to Python `pytest` syntax with few-shot examples.
- Generate test scripts for all 100 endpoints within a single 6-hour GHA job window.
- Execute generated tests in a sandboxed Docker container with stubbed API responses.
- Record pass/fail status, code coverage, and hallucination rate (invalid endpoints).
- Perform an independent samples t-test comparing pass rates across different prompt complexity levels.

## Duplicate-check

- Reviewed existing ideas: None provided in corpus.
- Closest match: N/A (no prior ideas in context).
- Verdict: NOT a duplicate
