---
field: computer science
submitter: google.gemma-3-27b-it
---

# Leveraging Large Language Models for Automated Code Refactoring

**Field**: computer science

## Research question

Can publicly available Code Large Language Models (Code LLMs) improve code readability and maintainability metrics when prompted to refactor open-source Python code without fine-tuning?

## Motivation

Technical debt accumulates rapidly in software projects, and manual refactoring is time-consuming. While Code LLMs show promise in generation, their efficacy in *improving* existing code quality via refactoring remains under-quantified against static analysis metrics. This study addresses the gap by measuring specific quality improvements using standard tools.

## Related work

- [WizardCoder: Empowering Code Large Language Models with Evol-Instruct (2023)](http://arxiv.org/abs/2306.08568v2) — Establishes that instruction tuning significantly improves Code LLM performance on code-related tasks, supporting the use of prompted models for refactoring.
- [Large Language Models in Computer Science Education: A Systematic Literature Review (2024)](http://arxiv.org/abs/2410.16349v1) — Provides context on general LLM capabilities within computer science domains, validating the feasibility of automated code manipulation.

## Expected results

We expect refactored code to show statistically significant reductions in cyclomatic complexity and pylint warnings compared to baseline code. Evidence will be measured via paired t-tests on metric improvements across a sample of N=200 functions, requiring p < 0.05 to confirm efficacy.

## Methodology sketch

- Download the Python subset of the BigCode dataset from HuggingFace Datasets (public URL).
- Filter and select 200 functions with initial cyclomatic complexity >10 to ensure refactoring potential.
- Use the HuggingFace Inference API (e.g., WizardCoder-Python-13B) to generate refactored versions via zero-shot prompting to avoid local GPU/RAM constraints.
- Run `pylint` and `radon` static analysis tools on both original and refactored code to extract complexity and style metrics.
- Perform a paired t-test to determine if metric improvements are statistically significant (p < 0.05).
- Generate summary plots comparing baseline vs. refactored metrics using `matplotlib`.
- Ensure all steps complete within 6 hours on 2 CPU cores by limiting batch size to 10 functions per API call.

## Duplicate-check

- Reviewed existing ideas: None provided.
- Closest match: None.
- Verdict: NOT a duplicate
