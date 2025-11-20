#!/usr/bin/env python3
"""Wrapper that prefers the real `openspec apply` command.

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

DEFAULT_COMMAND = "openspec apply {spec_path}"
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
    template = os.getenv(ENV_COMMAND, DEFAULT_COMMAND)
    if "{spec_path}" not in template:
        print(
            f"{ENV_COMMAND} must include '{{spec_path}}' placeholder: {template}",
            file=sys.stderr,
        )
        return 5

    quoted_path = shlex.quote(str(spec_path))
    command_str = template.replace("{spec_path}", quoted_path)
    command = shlex.split(command_str)
    if not command:
        print("Resolved apply command is empty.", file=sys.stderr)
        return 5

    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)

    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
