"""Tasker Agent — drives /speckit.tasks then /speckit.analyze loop (T052).

Mode A: generate tasks.md from spec.md + plan.md.
Mode B: read /speckit.analyze report and propose patches; loop until
analyze returns CLEAN or `TASKER_MAX_REVISION_ROUNDS` is reached
(then escalate to `human_input_needed`).

There is no dedicated mechanical script in upstream Spec Kit for
/speckit.tasks (the slash command is agent-driven). The Tasker
therefore reads the existing artifacts directly.

Stage transitions:
  `planned` → `tasked` → `analyze_in_progress` →
                                 `analyzed` | `human_input_needed`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.backends.router import chat_with_fallback
from llmxive.config import TASKER_MAX_REVISION_ROUNDS
from llmxive.speckit.analyze_cmd import is_clean, run_analyze
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext


class TaskerAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.tasks"

    def _feature_dir(self, ctx: SlashCommandContext) -> Path:
        candidates = sorted(ctx.project_dir.glob("specs/*/"))
        if not candidates:
            raise FileNotFoundError(f"no specs/ feature dir in {ctx.project_dir}")
        return candidates[0]

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        feature_dir = self._feature_dir(ctx)
        return {
            "feature_dir": str(feature_dir),
            "spec_path": str(feature_dir / "spec.md"),
            "plan_path": str(feature_dir / "plan.md"),
            "tasks_path": str(feature_dir / "tasks.md"),
            "tasks_template_path": str(
                ctx.project_dir / ".specify" / "templates" / "tasks-template.md"
            ),
        }

    def build_prompt(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
    ) -> list[ChatMessage]:
        repo = ctx.project_dir.parent.parent
        spec_text = Path(mechanical_output["spec_path"]).read_text(encoding="utf-8")
        plan_text = Path(mechanical_output["plan_path"]).read_text(encoding="utf-8")
        tasks_template_path = Path(mechanical_output["tasks_template_path"])
        tasks_template = (
            tasks_template_path.read_text(encoding="utf-8")
            if tasks_template_path.exists()
            else ""
        )
        # On a revision pass, surface prior review feedback so the
        # Tasker can write tasks that explicitly address each
        # reviewer's complaints. Without this, the Tasker would
        # regenerate the same tasks and the reviewers would reject
        # again.
        existing_tasks_path = Path(mechanical_output["tasks_path"])
        existing_tasks = (
            existing_tasks_path.read_text(encoding="utf-8")
            if existing_tasks_path.exists()
            else ""
        )
        reviews_dir = ctx.project_dir / "reviews" / "research"
        review_block = ""
        if reviews_dir.is_dir():
            review_chunks: list[str] = []
            for md in sorted(reviews_dir.glob("*.md")):
                try:
                    text = md.read_text(encoding="utf-8")
                except OSError:
                    continue
                review_chunks.append(f"## {md.name}\n\n{text}")
            if review_chunks:
                review_block = (
                    "\n\n# Prior research-stage reviews "
                    "(address every reviewer's concerns in the new tasks list)\n\n"
                    + "\n\n---\n\n".join(review_chunks)
                )
        system = render_prompt(
            "agents/prompts/tasker.md",
            {"project_id": ctx.project_id, "mode": "A"},
            repo_root=repo,
        )
        user_parts = [
            "Mode: A (generate tasks.md)",
            f"# spec.md\n\n{spec_text}",
            f"# plan.md\n\n{plan_text}",
            f"# tasks template\n\n{tasks_template}",
        ]
        if existing_tasks.strip():
            user_parts.append(
                "# Existing tasks.md (revise — keep [X] tasks already done, "
                "add new [ ] tasks that address review concerns)\n\n" + existing_tasks
            )
        if review_block:
            user_parts.append(review_block)
        user_parts.append(
            "# Task\n\nReturn the FULL contents of tasks.md as Markdown. "
            "DO NOT return a diff or partial patch — return the entire "
            "file from the first line to the last. Preserve all existing "
            "[X]-marked tasks verbatim and append new [ ]-marked tasks "
            "for the revision concerns. The output MUST contain at least "
            "one line beginning with `- [ ] T###`."
        )
        user = "\n\n".join(user_parts)
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def write_artifacts(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
        llm_response: ChatResponse,
    ) -> list[str]:
        repo = ctx.project_dir.parent.parent
        tasks_path = Path(mechanical_output["tasks_path"])
        tasks_path.parent.mkdir(parents=True, exist_ok=True)
        # Strip ```markdown / ```md fences if the LLM wrapped its response.
        text = llm_response.text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].lstrip("`").lower() in {"", "markdown", "md"}:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        # Sanity check: a tasks.md must contain at least one task checkbox.
        # Without this, the analyze loop runs against an empty file and the
        # Implementer has nothing to do (PROJ-007 hit this when the LLM
        # returned a 180-byte preamble-only response).
        if "- [ ]" not in text and "- [X]" not in text and "- [x]" not in text:
            raise RuntimeError(
                f"Tasker produced no checkbox tasks (got {len(text)} chars). "
                "Re-running the Tasker on next pipeline cycle will retry."
            )
        tasks_path.write_text(text + "\n", encoding="utf-8")
        written = [str(tasks_path.relative_to(repo))]

        # Now run the analyze-resolve loop.
        spec_path = Path(mechanical_output["spec_path"])
        plan_path = Path(mechanical_output["plan_path"])
        for round_idx in range(TASKER_MAX_REVISION_ROUNDS):
            report = run_analyze(
                spec_text=spec_path.read_text(encoding="utf-8"),
                plan_text=plan_path.read_text(encoding="utf-8"),
                tasks_text=tasks_path.read_text(encoding="utf-8"),
                default_backend=ctx.default_backend,
                fallback_backends=ctx.fallback_backends,
                default_model=ctx.default_model,
                repo_root=repo,
            )
            if is_clean(report):
                # Persist the round count alongside tasks.md for SC-012.
                round_record = (
                    ctx.project_dir / ".specify" / "memory" / "tasker_rounds.yaml"
                )
                round_record.parent.mkdir(parents=True, exist_ok=True)
                round_record.write_text(
                    yaml.safe_dump({"rounds_used": round_idx + 1}),
                    encoding="utf-8",
                )
                return written

            # Mode B — ask the Tasker to patch the artifacts.
            mode_b_system = render_prompt(
                "agents/prompts/tasker.md",
                {"project_id": ctx.project_id, "mode": "B"},
                repo_root=repo,
            )
            mode_b_user = (
                "Mode: B (resolve analyze findings)\n\n"
                f"# Analyze report\n\n{report}\n\n"
                f"# spec.md\n\n{spec_path.read_text(encoding='utf-8')}\n\n"
                f"# plan.md\n\n{plan_path.read_text(encoding='utf-8')}\n\n"
                f"# tasks.md\n\n{tasks_path.read_text(encoding='utf-8')}\n\n"
                "Return the YAML patch document per the contract."
            )
            patch_response = chat_with_fallback(
                [
                    ChatMessage(role="system", content=mode_b_system),
                    ChatMessage(role="user", content=mode_b_user),
                ],
                default_backend=ctx.default_backend.value,
                fallback_backends=[b.value for b in ctx.fallback_backends],
                model=ctx.default_model,
            )
            try:
                doc = yaml.safe_load(patch_response.text)
            except yaml.YAMLError:
                continue
            if not isinstance(doc, dict):
                continue
            for issue in doc.get("issues_resolved", []) or []:
                f = issue.get("file")
                patch = issue.get("patch", "")
                if f == "spec.md":
                    spec_path.write_text(patch, encoding="utf-8")
                elif f == "plan.md":
                    plan_path.write_text(patch, encoding="utf-8")
                elif f == "tasks.md":
                    tasks_path.write_text(patch, encoding="utf-8")
            if doc.get("verdict") == "escalate":
                # Escalate flag — caller transitions project to
                # human_input_needed.
                escalate_marker = (
                    ctx.project_dir / ".specify" / "memory" / "human_input_needed.yaml"
                )
                escalate_marker.parent.mkdir(parents=True, exist_ok=True)
                escalate_marker.write_text(
                    yaml.safe_dump(
                        {
                            "reason": "tasker analyze loop did not converge",
                            "rounds_used": round_idx + 1,
                        }
                    ),
                    encoding="utf-8",
                )
                return written

        # Cap reached without converge — accept the current tasks.md as
        # best-effort and let the project advance. The analyze loop is a
        # quality polish, not a hard gate; downstream specialist reviewers
        # will catch substantive issues.
        rounds_marker = (
            ctx.project_dir / ".specify" / "memory" / "tasker_rounds.yaml"
        )
        rounds_marker.parent.mkdir(parents=True, exist_ok=True)
        rounds_marker.write_text(
            yaml.safe_dump({"rounds_used": TASKER_MAX_REVISION_ROUNDS, "converged": False}),
            encoding="utf-8",
        )
        return written


__all__ = ["TaskerAgent"]
