"""Codex executor backend that emits /openspec-apply instructions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .backends import BackendApplyResult, ExecutorBackend


@dataclass
class CodexExecutorBackend(ExecutorBackend):
    """Backend that instructs operators to run /openspec-apply manually."""

    command_prefix: str = "/openspec-apply"
    prompt_hint: str | None = "/prompts:openspec-apply"

    def plan(self, plan_id: str) -> Dict[str, str] | None:  # pragma: no cover - stub
        return None

    def apply(self, change_id: str, spec_path: str) -> BackendApplyResult:
        prefix = self.command_prefix.strip() or "/openspec-apply"
        hint = (self.prompt_hint or "").strip()

        primary_command = f"{prefix} {change_id}"
        instructions = (
            f"In Codex, run `{primary_command}` to apply the OpenSpec change."
        )
        if hint:
            instructions = (
                f"{instructions} If prompts commands are configured, run "
                f"`{hint} {change_id}`."
            )
        instructions = f"{instructions} (Spec path: {spec_path})"

        metadata = {
            "backend": "codex",
            "command_prefix": prefix,
        }
        if hint:
            metadata["prompt_hint"] = hint

        return BackendApplyResult(
            status="manual",
            instructions=instructions,
            metadata=metadata,
            tests_supported=False,
        )


__all__ = ["CodexExecutorBackend"]
