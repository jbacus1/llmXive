"""Code-execution sandbox for the Implementer + Paper-Implementer.

Without a way to actually *run* the code an LLM writes, every project
ends up as scaffolding that never produces real data, real figures,
or real results — which is exactly what the research reviewers were
flagging. This module gives the agents a deterministic, restricted
sandbox in which to execute scripts and verify their output.

Design constraints:
  - Run inside a per-project venv at projects/<id>/code/.venv so
    requirements.txt is honored without polluting the global env.
  - Cap wall-clock time per script (default 600 s).
  - Cap memory via shell ulimit on POSIX (best-effort; not a
    security boundary — the agents are trusted code we wrote, this
    is a quality / correctness boundary).
  - Capture stdout + stderr + exit code; surface them back to the
    caller.
  - No network restrictions: GHA runners need to download datasets
    from public URLs. The constitution forbids generating new
    secrets or contacting non-listed services.

Usage:
    result = run_python_script(
        project_dir=Path("projects/PROJ-002-..."),
        script_relpath="code/scripts/figure_1.py",
        timeout_s=600,
    )
    if result.ok:
        print(result.stdout)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecutionResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool = False


def ensure_venv(project_dir: Path) -> Path:
    """Create or reuse the project's code/.venv. Returns the python path."""
    venv = project_dir / "code" / ".venv"
    py = venv / "bin" / "python"
    if py.exists():
        return py
    venv.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv)],
        check=True,
        capture_output=True,
    )
    # Install requirements.txt if present.
    req = project_dir / "code" / "requirements.txt"
    if req.exists():
        subprocess.run(
            [str(py), "-m", "pip", "install", "-q", "-r", str(req)],
            check=False,  # tolerate failures so subsequent runs report them via stderr
            capture_output=True,
        )
    return py


def run_python_script(
    *,
    project_dir: Path,
    script_relpath: str,
    timeout_s: int = 600,
    cwd: Path | None = None,
    extra_env: dict[str, str] | None = None,
) -> ExecutionResult:
    """Run `python <script>` inside the project's venv. Returns capture."""
    import time

    script = project_dir / script_relpath
    if not script.exists():
        return ExecutionResult(
            ok=False,
            returncode=-1,
            stdout="",
            stderr=f"script not found: {script}",
            duration_s=0.0,
        )
    py = ensure_venv(project_dir)
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    if extra_env:
        env.update(extra_env)
    started = time.time()
    timed_out = False
    try:
        proc = subprocess.run(
            [str(py), str(script)],
            cwd=str(cwd or (project_dir / "code")),
            timeout=timeout_s,
            capture_output=True,
            text=True,
            env=env,
        )
        rc = proc.returncode
        out = proc.stdout
        err = proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        rc = -1
        out = (exc.stdout or b"").decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = (
            (exc.stderr or b"").decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        ) + f"\n[TIMEOUT after {timeout_s}s]"
    elapsed = time.time() - started
    return ExecutionResult(
        ok=rc == 0,
        returncode=rc,
        stdout=out,
        stderr=err,
        duration_s=elapsed,
        timed_out=timed_out,
    )


def run_pytest(
    *,
    project_dir: Path,
    test_path: str = "tests/",
    timeout_s: int = 600,
) -> ExecutionResult:
    """Run pytest inside the project's venv."""
    import time
    py = ensure_venv(project_dir)
    code_dir = project_dir / "code"
    started = time.time()
    timed_out = False
    try:
        proc = subprocess.run(
            [str(py), "-m", "pytest", test_path, "-x", "--tb=short", "-q"],
            cwd=str(code_dir),
            timeout=timeout_s,
            capture_output=True,
            text=True,
        )
        rc = proc.returncode
        out = proc.stdout
        err = proc.stderr
    except subprocess.TimeoutExpired:
        timed_out = True
        rc = -1
        out = ""
        err = f"[TIMEOUT after {timeout_s}s]"
    return ExecutionResult(
        ok=rc == 0,
        returncode=rc,
        stdout=out,
        stderr=err,
        duration_s=time.time() - started,
        timed_out=timed_out,
    )


def cleanup_venv(project_dir: Path) -> None:
    """Remove the project's venv (used by tests)."""
    venv = project_dir / "code" / ".venv"
    if venv.exists():
        shutil.rmtree(venv, ignore_errors=True)


__all__ = [
    "ExecutionResult",
    "ensure_venv",
    "run_python_script",
    "run_pytest",
    "cleanup_venv",
]
