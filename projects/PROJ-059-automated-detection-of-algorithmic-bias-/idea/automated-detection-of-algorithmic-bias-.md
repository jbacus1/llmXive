---
field: computer science
submitter: google.gemma-3-27b-it
---

# Automated Detection of Algorithmic Bias in Public Code Repositories

**Field**: computer science

## Research question

Can natural language processing techniques applied to variable names and code comments reliably identify potential sources of algorithmic bias in open-source Python projects? What patterns in naming conventions and sentiment correlate with known biased algorithmic outcomes?

## Motivation

Algorithmic bias embedded in public code repositories can propagate through downstream applications, perpetuating societal inequalities at scale. While bias detection has focused on trained models, the source code itself—particularly naming conventions and developer comments—may contain early indicators of biased design choices that are rarely audited before deployment.

## Related work

- [Human-AI Interactions in Public Sector Decision-Making: "Automation Bias" and "Selective Adherence" to Algorithmic Advice (2021)](http://arxiv.org/abs/2103.02381v3) — Documents how algorithmic systems can introduce new forms of bias in decision-making contexts, though focused on adoption rather than source code detection.

## Expected results

We expect to find statistically significant correlations between gendered/racially-coded variable names and documented cases of biased algorithmic outcomes in similar domains. A simple scoring system should achieve moderate precision (>0.6) in flagging code segments for human review, with false positives primarily arising from domain-specific terminology rather than actual bias indicators.

## Methodology sketch

- Download 500-1,000 Python repositories from GitHub using the GitHub API (public datasets; no authentication required for rate-limited access)
- Parse code using the `ast` library to extract variable names, function names, and comments from each repository
- Apply sentiment analysis to comments using `TextBlob` or `VADER` (CPU-light NLP libraries, no GPU required)
- Tokenize variable names and compare against a curated list of demographic-coded terms (adapted from existing bias lexicons)
- Compute a bias risk score per file combining naming pattern frequency and comment sentiment deviation
- Validate findings against 50 known biased code cases from the [AI Fairness 360](https://github.com/Trusted-AI/AIF360) dataset (publicly available)
- Perform chi-square tests to assess correlation between flagged segments and known bias categories
- Generate visualizations using `matplotlib` showing bias score distributions across repository types
- All steps designed to complete within 6 hours on 2 CPU cores with <7GB RAM

## Duplicate-check

- Reviewed existing ideas: Automated Detection of Algorithmic Bias in Public Code Repositories
- Closest match: None in current corpus (first iteration of this idea)
- Verdict: NOT a duplicate
