---
field: computer science
submitter: google.gemma-3-27b-it
---

# Leveraging LLMs for Automated Test Case Generation from Natural Language Requirements

**Field**: computer science

## Research question

Can large language models (LLMs) generate executable unit tests from natural language software requirements that achieve comparable code coverage to manually written tests?

## Motivation

Manual test case creation is a significant bottleneck in software engineering, often consuming 30-50% of development effort. While LLMs show promise in code generation, their specific efficacy in translating natural language requirements into passing tests remains under-evaluated on constrained hardware. This project addresses the gap between requirements engineering and automated testing by validating LLM performance within realistic resource limits.

## Related work

- [CiRA: An Open-Source Python Package for Automated Generation of Test Case Descriptions from Natural Language Requirements (2023)](http://arxiv.org/abs/2310.08234v1) — Directly addresses deriving acceptance tests from natural language requirements, providing a baseline for comparison.
- [A Comprehensive Review of State-of-the-Art Methods for Java Code Generation from Natural Language Text (2023)](http://arxiv.org/abs/2306.06371v1) — Establishes the state-of-the-art for generating code artifacts from text, relevant to test case generation.
- [Natural Language Processing for Requirements Traceability (2024)](http://arxiv.org/abs/2405.10845v1) — Discusses linking software artifacts to requirements, supporting the traceability aspect of generated tests.
- [GPT-4 Technical Report (2023)](https://doi.org/10.4230/lipics.cosit.2024.11) — Highlights inherent stochasticity in LLMs, which poses challenges for deterministic test generation.
- [A Review on Large Language Models: Architectures, Applications, Taxonomies, Open Issues and Challenges (2024)](https://doi.org/10.1109/access.2024.3365742) — Provides general context on LLM capabilities and limitations in NLP tasks.

## Expected results

We expect LLMs to generate syntactically valid tests that achieve 40-60% of the code coverage of manual baseline tests. Failure to reach this threshold would indicate the need for prompt engineering or model fine-tuning. Evidence will be confirmed via statistical comparison of coverage metrics across a held-out test set.

## Methodology sketch

- **Data Acquisition**: Download the Defects4J dataset (publicly available via GitHub) containing buggy Java projects with associated test suites.
- **Requirement Extraction**: Use existing issue tracker data from the projects to extract natural language requirement descriptions linked to specific bugs/fixes.
- **Model Selection**: Load a quantized 2.7B parameter model (e.g., Phi-2) using `llama.cpp` on CPU to fit within 7GB RAM constraints.
- **Generation**: Prompt the model with extracted requirements to generate JUnit test code snippets.
- **Execution**: Compile and execute generated tests against the project source code using Maven/Gradle within the GitHub Actions runner.
- **Measurement**: Calculate code coverage using JaCoCo to compare generated tests against the baseline manual tests.
- **Analysis**: Perform a paired t-test on coverage percentages between LLM-generated and manual tests to determine statistical significance.
- **Optimization**: Iterate prompts based on initial failure rates, limited to 50 samples to ensure execution completes within 6 hours.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: N/A (No corpus provided).
- Verdict: NOT a duplicate
