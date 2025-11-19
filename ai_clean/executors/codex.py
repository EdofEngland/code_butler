"""Codex-backed executor that applies specs and optionally runs tests."""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence

from ai_clean.interfaces import CodeExecutor
from ai_clean.models import ExecutionResult


@dataclass
class _CommandCapture:
    command: List[str]
    returncode: int
    stdout: str
    stderr: str


class CodexExecutor(CodeExecutor):
    """Execute specs via configured shell commands and capture results."""

    def __init__(
        self,
        *,
        apply_command: Sequence[str],
        tests_command: Sequence[str] | str | None = None,
    ) -> None:
        self._apply_command = _normalize_apply_command(apply_command)
        self._tests_command = _normalize_optional_command(tests_command)

    def apply_spec(self, spec_path: str) -> ExecutionResult:
        target = Path(spec_path).expanduser().resolve()
        if not target.is_file():
            raise FileNotFoundError(f"Spec file not found: {target}")

        apply_cmd = self._render_apply_command(target)
        apply_proc = subprocess.run(
            apply_cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        success = apply_proc.returncode == 0
        stdout = (apply_proc.stdout or "").strip()
        stderr = (apply_proc.stderr or "").strip()
        metadata: Dict[str, Any] = {
            "apply": {
                "command": apply_cmd,
                "returncode": apply_proc.returncode,
            }
        }

        tests_passed: bool | None = None
        if success and self._tests_command:
            test_capture = self._run_tests()
            metadata["tests"] = {
                "command": test_capture.command,
                "returncode": test_capture.returncode,
            }
            stdout = _append_section(stdout, "== TESTS ==", test_capture.stdout)
            stderr = _append_section(stderr, "== TESTS ==", test_capture.stderr)
            tests_passed = test_capture.returncode == 0
        elif success:
            metadata["tests"] = {"skipped": True, "reason": "tests_disabled"}
        else:
            metadata["tests"] = {"skipped": True, "reason": "apply_failed"}

        return ExecutionResult(
            spec_id=target.stem,
            success=success,
            tests_passed=tests_passed,
            stdout=stdout,
            stderr=stderr,
            metadata=metadata,
        )

    def _render_apply_command(self, spec_path: Path) -> List[str]:
        rendered: List[str] = []
        replaced = False
        spec_token = spec_path.as_posix()
        for token in self._apply_command:
            new_token = token.replace("{spec_path}", spec_token)
            if new_token != token:
                replaced = True
            rendered.append(new_token)
        if not replaced:
            raise ValueError(
                "apply_command must include '{spec_path}' so the spec path can be "
                "passed"
            )
        return rendered

    def _run_tests(self) -> _CommandCapture:
        if not self._tests_command:
            return _CommandCapture(command=[], returncode=0, stdout="", stderr="")

        proc = subprocess.run(
            self._tests_command,
            capture_output=True,
            text=True,
            check=False,
        )
        return _CommandCapture(
            command=list(self._tests_command),
            returncode=proc.returncode,
            stdout=(proc.stdout or "").strip(),
            stderr=(proc.stderr or "").strip(),
        )


def _append_section(base: str, heading: str, section: str) -> str:
    section = (section or "").strip()
    parts: List[str] = []
    if base.strip():
        parts.append(base.strip())
    if section:
        parts.append(f"{heading}\n{section}")
    return "\n\n".join(parts).strip()


def _normalize_apply_command(command: Sequence[str]) -> List[str]:
    tokens = [str(part) for part in command if str(part).strip()]
    if not tokens:
        raise ValueError("apply_command must include at least one token.")
    if not any("{spec_path}" in token for token in tokens):
        raise ValueError("apply_command must include '{spec_path}' placeholder.")
    return tokens


def _normalize_optional_command(
    command: Sequence[str] | str | None,
) -> List[str] | None:
    if command is None:
        return None
    if isinstance(command, str):
        tokens = shlex.split(command)
    else:
        tokens = [str(part) for part in command if str(part).strip()]
    return tokens or None


__all__ = ["CodexExecutor"]
