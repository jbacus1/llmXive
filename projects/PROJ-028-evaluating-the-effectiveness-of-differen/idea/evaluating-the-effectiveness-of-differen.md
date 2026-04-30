---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Effectiveness of Different Prompting Strategies for Code Generation

**Field**: computer science

## Research question

Which prompting strategy (zero-shot, few-shot, or chain-of-thought) yields the highest pass@k score for resource-constrained open-source models on standard code generation benchmarks?

## Motivation

While large language models show promise in coding, their performance varies significantly based on prompt engineering, especially when deployed on edge or serverless environments with limited compute. This research addresses the gap in empirical evidence regarding optimal prompting techniques for smaller, publicly available models where fine-tuning is infeasible.

## Related work

- [Introducing HALC: A general pipeline for finding optimal prompting strategies for automated coding with LLMs in the computational social sciences (2025)](http://arxiv.org/abs/2507.21831v1) — Establishes a pipeline for comparing prompting strategies in automated coding tasks.
- [Execution-based Evaluation for Data Science Code Generation Models (2022)](http://arxiv.org/abs/2211.09374v1) — Proposes execution-based metrics as a robust measure for code generation quality.
- [Opinion Paper: “So what if ChatGPT wrote it?” Multidisciplinary perspectives on opportunities, challenges and implications of generative conversational AI for research, practice and policy (2023)](https://doi.org/10.1016/j.ijinfomgt.2023.102642) — Discusses broader implications and challenges of generative AI in research contexts.

## Expected results

Chain-of-thought prompting is expected to yield statistically higher pass@k rates compared to zero-shot baselines for models under 1B parameters. Evidence will be confirmed if the difference in mean pass rates exceeds 5% with p < 0.05 across 3 random seeds.

## Methodology sketch

- **Data Acquisition**: Download the MBPP dataset from HuggingFace (`google-research-datasets/mbpp`) using `datasets.load_dataset` (no new data collection).
- **Model Selection**: Load `Salesforce/codegen-350M-mono` from HuggingFace to ensure inference fits within 7 GB RAM on CPU.
- **Prompt Engineering**: Implement three prompt templates: Zero-shot, Few-shot (3 examples), and Chain-of-Thought.
- **Generation**: Run inference on the test subset (approx. 500 tasks) using CPU-only execution, limiting batch size to 1 to manage memory.
- **Execution Environment**: Use `docker` or `subprocess` with strict timeouts (10s per task) to execute generated code against provided unit tests.
- **Metrics**: Calculate pass@1 and pass@10 scores based on test suite execution success.
- **Statistical Analysis**: Perform paired t-tests comparing pass rates across prompting strategies.
- **Resource Monitoring**: Log peak RAM usage and total runtime to verify adherence to GitHub Actions constraints (≤ 6h, ≤ 7 GB).

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: N/A (no corpus available).
- Verdict: NOT a duplicate
