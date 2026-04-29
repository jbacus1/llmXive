"""Implementer Agent — drives /speckit.implement (T054).

Reads the project's tasks.md, picks the next incomplete `[ ] T###`,
and either (a) writes the artifact the task describes, (b) marks the
task escalated to `human_input_needed`, or (c) requests atomization
(handled in US9). Persists progress per-task by checking off the box
in tasks.md.

Stage transitions:
  `analyzed` → `in_progress` (first task picked) →
              `research_complete` (last `[ ]` becomes `[X]`).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from llmxive.speckit.yaml_extract import parse_yaml_lenient

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.config import LEAF_TASK_BUDGET_SECONDS
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext


_TASK_RE = re.compile(
    r"^- \[(?P<status>[ Xx])\]\s+(?P<id>T\d+)\b(?P<rest>.*)$",
    re.MULTILINE,
)


class ImplementerAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.implement"

    def _feature_dir(self, ctx: SlashCommandContext) -> Path:
        candidates = sorted(ctx.project_dir.glob("specs/*/"))
        if not candidates:
            raise FileNotFoundError(f"no specs/ feature dir in {ctx.project_dir}")
        return candidates[0]

    def _next_incomplete(self, tasks_text: str) -> tuple[str, str] | None:
        for m in _TASK_RE.finditer(tasks_text):
            if m.group("status") == " ":
                return m.group("id"), m.group(0)
        return None

    def _all_complete(self, tasks_text: str) -> bool:
        return all(m.group("status") in {"X", "x"} for m in _TASK_RE.finditer(tasks_text))

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        feature_dir = self._feature_dir(ctx)
        tasks_path = feature_dir / "tasks.md"
        tasks_text = tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else ""
        next_task = self._next_incomplete(tasks_text)
        completed = [m.group("id") for m in _TASK_RE.finditer(tasks_text)
                     if m.group("status") in {"X", "x"}]
        return {
            "feature_dir": str(feature_dir),
            "tasks_path": str(tasks_path),
            "tasks_text": tasks_text,
            "next_task_id": next_task[0] if next_task else None,
            "next_task_line": next_task[1] if next_task else None,
            "completed_task_ids": completed,
            "all_complete": next_task is None and bool(completed),
        }

    def build_prompt(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
    ) -> list[ChatMessage]:
        repo = ctx.project_dir.parent.parent
        if mechanical_output.get("all_complete") or not mechanical_output.get("next_task_id"):
            # No-op prompt: the LLM is invoked but should return a no-op.
            return [
                ChatMessage(role="system", content="No incomplete tasks remain."),
                ChatMessage(role="user", content="Reply with `task_id: NONE\\nverdict: completed` only."),
            ]
        system = render_prompt(
            "agents/prompts/implementer.md",
            {
                "project_id": ctx.project_id,
                "next_task_id": mechanical_output["next_task_id"] or "",
            },
            repo_root=repo,
        )
        user = (
            f"# tasks.md\n\n{mechanical_output['tasks_text']}\n\n"
            f"# next task line\n\n{mechanical_output['next_task_line']}\n\n"
            f"# completed task ids\n{mechanical_output['completed_task_ids']}\n\n"
            f"# wall_clock_budget_seconds\n{LEAF_TASK_BUDGET_SECONDS}\n\n"
            "# Task\n\nReturn the YAML implementation report."
        )
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def _mark_task_skipped(
        self, mechanical_output: dict[str, Any], reason: str, exc: Exception | None
    ) -> None:
        """Check off the current task with a SKIPPED annotation so the
        Implementer moves to the next one instead of looping forever
        on a malformed LLM response. The annotation is preserved so a
        review pass can catch quality regressions later.
        """
        task_id = mechanical_output.get("next_task_id")
        tasks_path = mechanical_output.get("tasks_path")
        if not task_id or not tasks_path:
            return
        from pathlib import Path as _Path
        text = _Path(tasks_path).read_text(encoding="utf-8")
        # Replace `- [ ] T###` with `- [X] T### <!-- SKIPPED: reason -->`
        new_text = re.sub(
            rf"^- \[ \] ({re.escape(task_id)}\b)([^\n]*)$",
            rf"- [X] \1\2 <!-- SKIPPED: {reason}{f' ({exc!s})' if exc else ''} -->",
            text,
            count=1,
            flags=re.MULTILINE,
        )
        _Path(tasks_path).write_text(new_text, encoding="utf-8")
        print(f"[implementer] marked {task_id} SKIPPED: {reason}")

    def write_artifacts(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
        llm_response: ChatResponse,
    ) -> list[str]:
        repo = ctx.project_dir.parent.parent
        if mechanical_output.get("all_complete") or not mechanical_output.get("next_task_id"):
            return []

        try:
            doc = parse_yaml_lenient(llm_response.text)
        except yaml.YAMLError as exc:
            # Implementer responses with `contents: |` blocks are
            # frequently invalid YAML when the embedded code contains
            # docstrings, mixed indentation, or YAML-incompatible
            # constructs. Fall back to a regex-based parser that pulls
            # task_id/verdict/artifact paths/contents using markers
            # rather than YAML structure.
            doc = _regex_parse_implementer(llm_response.text)
            if doc is None:
                # Last-resort: mark this task as parse-failed and check
                # it off so the implementer moves to the next one. The
                # runlog records the failure; downstream review will
                # catch quality regressions if any.
                self._mark_task_skipped(mechanical_output, "YAML+regex parse failed", exc)
                return []
        if not isinstance(doc, dict):
            self._mark_task_skipped(mechanical_output, "non-mapping output", None)
            return []

        task_id = mechanical_output["next_task_id"]
        verdict = doc.get("verdict")
        written: list[str] = []

        if verdict == "completed":
            project_root = ctx.project_dir
            for art in doc.get("artifacts", []) or []:
                relpath = art.get("path")
                contents = art.get("contents", "")
                if not relpath:
                    continue
                # Confine all artifact writes to projects/<PROJ-ID>/.
                # The LLM occasionally produces paths like "src/" or
                # absolute paths into the repo's own source code; we
                # MUST NOT write outside the project's own tree.
                rel = relpath.lstrip("/")
                proj_prefix = f"projects/{project_root.name}/"
                if rel.startswith(proj_prefix):
                    rel = rel[len(proj_prefix):]
                target = project_root / rel
                # Reject paths that escape the project directory.
                try:
                    target.resolve().relative_to(project_root.resolve())
                except ValueError:
                    print(f"[implementer] refused out-of-project path: {relpath!r}")
                    continue
                # Skip if target is an existing directory (LLM bug).
                if target.exists() and target.is_dir():
                    print(f"[implementer] skipping directory path: {relpath!r}")
                    continue
                if not contents:
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(contents, encoding="utf-8")
                written.append(str(target.relative_to(repo)))
            # Check off the task in tasks.md.
            tasks_path = Path(mechanical_output["tasks_path"])
            text = tasks_path.read_text(encoding="utf-8")
            text = re.sub(
                rf"^- \[ \] ({re.escape(task_id)}\b)",
                r"- [X] \1",
                text,
                count=1,
                flags=re.MULTILINE,
            )
            tasks_path.write_text(text, encoding="utf-8")
            written.append(str(tasks_path.relative_to(repo)))
        elif verdict == "failed":
            escalate_marker = (
                ctx.project_dir / ".specify" / "memory" / "human_input_needed.yaml"
            )
            escalate_marker.parent.mkdir(parents=True, exist_ok=True)
            escalate_marker.write_text(
                yaml.safe_dump(
                    {
                        "reason": doc.get("failure", {}).get("reason", "unspecified"),
                        "task_id": task_id,
                    }
                ),
                encoding="utf-8",
            )
        elif verdict == "atomize":
            # Recorded for the Task-Atomizer Agent (US9) to pick up.
            atomize_dir = ctx.project_dir / "code" / ".tasks"
            atomize_dir.mkdir(parents=True, exist_ok=True)
            (atomize_dir / f"{task_id}.atomize.yaml").write_text(
                yaml.safe_dump(doc.get("atomize", {})),
                encoding="utf-8",
            )

        return written


def _regex_parse_implementer(text: str) -> dict[str, Any] | None:
    """Best-effort recovery when the LLM's YAML is malformed.

    Looks for:
      - top-level `task_id:` and `verdict:` lines
      - one or more artifact entries with `path:` and `contents: |`
        followed by an indented block (at least 2 spaces) terminated
        by EOF or a top-level `verdict:` / `task_id:` / blank-then-key
        line.

    Returns a dict shaped like the YAML success case so the caller's
    code path doesn't change. Returns None if recovery fails.
    """
    # Strip ```yaml / ``` fences if present.
    body = text.strip()
    if body.startswith("```"):
        m = re.match(r"^```(?:yaml|yml)?\s*\n(.*)\n```\s*$", body, re.DOTALL | re.IGNORECASE)
        if m:
            body = m.group(1)

    task_id_m = re.search(r"^task_id:\s*([^\s\n]+)\s*$", body, re.MULTILINE)
    verdict_m = re.search(r"^verdict:\s*(\w+)\s*$", body, re.MULTILINE)
    if not (task_id_m and verdict_m):
        return None

    out: dict[str, Any] = {
        "task_id": task_id_m.group(1),
        "verdict": verdict_m.group(1),
    }

    if out["verdict"] != "completed":
        return out

    artifacts: list[dict[str, str]] = []
    # Find every "  path: <p>\n  contents: |" pair, then read the
    # indented block until next "  path:" or end of artifacts list.
    art_re = re.compile(
        r"^\s*-\s*path:\s*(?P<path>[^\n]+)\s*\n"
        r"\s*contents:\s*\|\s*\n"
        r"(?P<block>(?:.*\n)*?)"
        r"(?=^\s*-\s*path:|\Z)",
        re.MULTILINE,
    )
    for m in art_re.finditer(body):
        path = m.group("path").strip().strip('"').strip("'")
        block = m.group("block").rstrip("\n")
        # Determine the leading indent of the block from its first
        # non-empty line, then strip that indent from every line.
        indent = None
        for ln in block.splitlines():
            if ln.strip():
                indent = len(ln) - len(ln.lstrip(" "))
                break
        if indent is None or indent == 0:
            contents = block
        else:
            stripped = []
            for ln in block.splitlines():
                if len(ln) >= indent and ln[:indent].strip() == "":
                    stripped.append(ln[indent:])
                else:
                    stripped.append(ln)
            contents = "\n".join(stripped)
        artifacts.append({"path": path, "contents": contents})

    out["artifacts"] = artifacts
    return out


__all__ = ["ImplementerAgent"]
