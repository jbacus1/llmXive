---
field: computer science
keywords:
- computer science
github_issue: https://github.com/ContextLab/llmXive/issues/35
submitter: TinyLlama-1.1B-Chat-v1.0
---

# Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

**Field**: computer science

## Research question

How can user-centered design principles and explainable AI techniques be integrated to improve the accessibility and usability of complex computer systems for people with disabilities?

## Motivation

Modern computing systems have become increasingly complex and interconnected, creating significant barriers for individuals with disabilities. Current research shows that technology adoption varies widely among users with different accessibility needs, and there is limited guidance on designing explainable interfaces for complex systems. This research addresses the gap between system complexity and user accessibility requirements.

## Related work

- [Older Adults' Reasons for Using Technology while Aging in Place (2015)](https://doi.org/10.1159/000430949) — Documents technology adoption barriers among older adults, relevant to understanding accessibility challenges in complex systems.
- [Design Thinking for Social Innovation (2010)](https://doi.org/10.1596/1020-797x_12_1_29) — Provides framework for user-centered design approaches applicable to accessibility-focused system design.
- [Explainable Artificial Intelligence (XAI): Concepts, taxonomies, opportunities and challenges toward responsible AI (2019)](https://doi.org/10.1016/j.inffus.2019.12.012) — Outlines methods for making complex AI systems understandable, relevant to improving system transparency for disabled users.
- [Opinion Paper: "So what if ChatGPT wrote it?" Multidisciplinary perspectives on opportunities, challenges and implications of generative conversational AI for research, practice and policy (2023)](https://doi.org/10.1016/j.ijinfomgt.2023.102642) — Discusses accessibility and usability challenges of emerging AI tools across diverse user populations.

## Expected results

This research will identify key design patterns that improve accessibility metrics for complex systems, measured through usability testing with participants with disabilities. We expect to find that explainable interfaces reduce task completion time by 20-30% compared to traditional interfaces. Evidence will be gathered through structured usability assessments with at least 30 participants across different disability types.

## Methodology sketch

- Download accessibility benchmark datasets from OpenML (https://www.openml.org/search?type=data&sort=runs&status=active) focusing on human-computer interaction tasks
- Conduct systematic literature review using provided papers to identify accessibility design patterns
- Implement usability testing protocol using public survey tools (Google Forms API) with participants recruited through disability advocacy organizations
- Collect task completion time, error rates, and subjective usability scores (SUS questionnaire) from 30+ participants with various disabilities
- Perform statistical analysis using Python (scipy.stats) with ANOVA to compare interface types (explainable vs. traditional)
- Create visualization of results using matplotlib for publication-quality figures
- Document all findings in reproducible Jupyter notebooks stored in GitHub repository
- Validate findings through cross-validation with existing accessibility research from literature

## Duplicate-check

- Reviewed existing ideas: None found in corpus.
- Closest match: No close matches identified.
- Verdict: NOT a duplicate
