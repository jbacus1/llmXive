"""Backend router (T020) — falls back through a chain on transient errors.

The agent registry declares a default backend and an ordered list of
fallback backends per agent. The router is configured per-call from
those declarations.
"""

from __future__ import annotations

from typing import Iterable

from llmxive.backends.base import (
    BaseBackend,
    BackendError,
    ChatMessage,
    ChatResponse,
    PermanentBackendError,
    TransientBackendError,
)
from llmxive.backends.dartmouth import DartmouthBackend
from llmxive.backends.huggingface import HuggingFaceBackend
from llmxive.backends.local import LocalBackend


_REGISTRY: dict[str, type[BaseBackend]] = {
    "dartmouth": DartmouthBackend,
    "huggingface": HuggingFaceBackend,
    "local": LocalBackend,
}


def make_backend(name: str) -> BaseBackend:
    cls = _REGISTRY.get(name)
    if cls is None:
        raise PermanentBackendError(f"unknown backend: {name!r}")
    return cls()  # type: ignore[call-arg]


def chat_with_fallback(
    messages: Iterable[ChatMessage],
    *,
    default_backend: str,
    fallback_backends: list[str],
    model: str,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> ChatResponse:
    """Try default backend; on TransientBackendError, walk the fallback chain.

    If `max_tokens` is None we default to 8192 — Spec Kit agents (Tasker,
    Specifier, Planner, paper-writers) frequently exceed the per-model
    silent default (often 1024) and produce truncated output otherwise.

    Retries the same backend up to 3 times on transient errors before
    falling through, so a single rate-limit blip doesn't kick the
    pipeline into HF (which usually has no token).
    """
    import time as _time

    if max_tokens is None:
        max_tokens = 8192
    chain = [default_backend, *fallback_backends]
    errors: list[str] = []
    msg_list = list(messages)
    for name in chain:
        try:
            backend = make_backend(name)
        except PermanentBackendError as exc:
            errors.append(f"{name}(init): {exc}")
            continue
        # Retry transient errors on the same backend before falling through.
        for attempt in range(3):
            if attempt:
                _time.sleep(2.0 * attempt)
            try:
                return backend.chat(
                    msg_list,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            except TransientBackendError as exc:
                errors.append(f"{name}(transient attempt {attempt + 1}): {exc}")
                if attempt == 2:
                    break  # done retrying this backend, fall through
                continue
            except PermanentBackendError as exc:
                errors.append(f"{name}(permanent): {exc}")
                break  # don't retry permanent failures, fall through
    raise BackendError(
        "every backend in chain "
        + repr(chain)
        + " failed; errors: "
        + " | ".join(errors)
    )


__all__ = ["chat_with_fallback", "make_backend"]
