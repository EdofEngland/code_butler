#!/usr/bin/env python3
"""Wrapper that runs the Codex/OpenSpec apply command when available.

Set AI_CLEAN_USE_APPLY_STUB=1 to fall back to the local stub helper when the
real CLI is unavailable. Optionally override the command via
AI_CLEAN_APPLY_COMMAND (must include `{spec_path}`).
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

# Local fallback commands for contributors running outside Codex.
DEFAULT_COMMANDS = (
    "/prompts:openspec-apply {spec_path}",
    "openspec apply {spec_path}",
)
ENV_USE_STUB = "AI_CLEAN_USE_APPLY_STUB"
ENV_COMMAND = "AI_CLEAN_APPLY_COMMAND"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: apply_spec_wrapper.py /path/to/spec.yaml", file=sys.stderr)
        return 2

    spec_path = Path(argv[1]).expanduser().resolve()
    if not spec_path.is_file():
        print(f"Spec file not found: {spec_path}", file=sys.stderr)
        return 3

    if _should_use_stub():
        return _run_stub(spec_path)

    return _run_real_command(spec_path)


def _should_use_stub() -> bool:
    flag = os.getenv(ENV_USE_STUB, "").strip().lower()
    return flag in {"1", "true", "yes", "on"}


def _run_stub(spec_path: Path) -> int:
    stub_script = Path(__file__).with_name("apply_spec_stub.py")
    if not stub_script.is_file():
        print(f"Stub script missing: {stub_script}", file=sys.stderr)
        return 4
    proc = subprocess.run(
        [sys.executable, str(stub_script), str(spec_path)],
        check=False,
    )
    return proc.returncode


def _run_real_command(spec_path: Path) -> int:
    templates = list(_command_templates())
    tried: List[str] = []
    last_error: str | None = None

    for template in templates:
        tried.append(template)
        try:
            command = _render_command(template, spec_path)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 5

        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            # Command not available; try the next template if one exists.
            last_error = str(exc)
            continue

        if proc.stdout:
            sys.stdout.write(proc.stdout)
        if proc.stderr:
            sys.stderr.write(proc.stderr)
        return proc.returncode

    tried_cmds = ", ".join(tried) or "none"
    error_suffix = f" Last error: {last_error}" if last_error else ""
    print(
        f"Unable to run any apply command (tried: {tried_cmds}). "
        "Set AI_CLEAN_USE_APPLY_STUB=1 or specify AI_CLEAN_APPLY_COMMAND."
        f"{error_suffix}",
        file=sys.stderr,
    )
    return 5


def _command_templates() -> Iterable[str]:
    override = os.getenv(ENV_COMMAND)
    if override:
        return [override]
    return DEFAULT_COMMANDS


def _render_command(template: str, spec_path: Path) -> List[str]:
    if "{spec_path}" not in template:
        raise ValueError(
            f"Apply command template must include '{{spec_path}}': {template}"
        )

    quoted_path = shlex.quote(str(spec_path))
    command_str = template.replace("{spec_path}", quoted_path)
    command = shlex.split(command_str)
    if not command:
        raise ValueError("Resolved apply command is empty.")
    return command


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
