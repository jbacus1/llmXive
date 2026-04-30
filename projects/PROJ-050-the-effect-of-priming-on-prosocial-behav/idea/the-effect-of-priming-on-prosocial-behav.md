---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Effect of Priming on Prosocial Behavior in Online Communities

**Field**: psychology

## Research question

To what extent does the presence of prosocial cues (e.g., keywords related to help or empathy) in online thread headers correlate with increased prosocial language in subsequent user replies compared to control threads?

## Motivation

Online communities frequently struggle with toxicity, and subtle environmental cues may offer a low-cost method to improve discourse. Understanding whether natural priming effects exist in static datasets can inform platform design without requiring invasive live experiments.

## Related work

- [Priming prosocial behavior and expectations in response to the Covid-19 pandemic -- Evidence from an online experiment (2021)](http://arxiv.org/abs/2102.13538v1) — Provides evidence that information framing can shift prosocial behavior, supporting the theoretical basis for priming cues.
- [Exploring the Effects of Chatbot Anthropomorphism and Human Empathy on Human Prosocial Behavior Toward Chatbots (2025)](http://arxiv.org/abs/2506.20748v1) — Highlights how digital interfaces influence human empathy, relevant to online interaction dynamics.
- [ProsocialDialog: A Prosocial Backbone for Conversational Agents (2022)](http://arxiv.org/abs/2205.12688v2) — Defines metrics for prosocial behavior in dialogue systems, offering a framework for quantifying user replies.
- [Evolution of prosocial behavior in multilayer populations (2020)](http://arxiv.org/abs/2010.01433v2) — Discusses social dynamics in diverse networks, contextualizing behavior in multi-user online environments.

## Expected results

Threads containing explicit prosocial cues will show statistically higher sentiment scores and lower aggression metrics in reply text. This evidence would suggest that visible community norms act as effective primes for user behavior.

## Methodology sketch

- Obtain a public Reddit dataset from HuggingFace Datasets (e.g., `reddit` or `pushshift` subsets) via `wget` or Python API.
- Filter data to a specific timeframe and select 5 subreddits known for both support and general discussion.
- Identify "prime" threads containing keywords like "help", "support", or "charity" in the title; select matched control threads without these keywords.
- Limit the sample size to 10,000 comments total to ensure execution fits within 7 GB RAM and 6-hour runtime limits.
- Perform text preprocessing (tokenization, lowercasing) using Python `pandas` and `nltk` on CPU only.
- Compute sentiment and aggression scores for each comment using the VADER sentiment library (lightweight, CPU-efficient).
- Aggregate scores by thread type (prime vs. control) and calculate mean differences.
- Apply an independent samples t-test to determine if the difference in mean prosocial scores is statistically significant (p < 0.05).
- Run a linear regression controlling for thread age and comment count to isolate the priming effect.
- Generate summary plots (boxplots of sentiment scores) using `matplotlib` for the final report.

## Duplicate-check

- Reviewed existing ideas: None provided.
- Closest match: None (no corpus available for comparison).
- Verdict: NOT a duplicate
