"""Repo-external integrations (GitHub Issues, Cloudflare Worker, etc.).

Lightweight, dependency-free helpers. Each function is a thin wrapper
around `gh` CLI invocations; we shell out rather than pull in PyGithub
to keep the dependency tree small (Constitution Principle IV — Free First).
"""
