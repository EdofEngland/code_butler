"""Shared executor-backend protocol for ai-clean apply flows.

Backends are lightweight coordinators that tell the CLI whether the apply step
should be handled automatically (run local commands/tests) or manually (surface
instructions for Codex or other tooling). Automatic backends must ensure the
existing CodeExecutor flow runs, while manual backends simply return guidance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Protocol, runtime_checkable

BackendStatus = Literal["manual", "automatic"]


@dataclass
class BackendApplyResult:
    """Structured response from ExecutorBackend.apply."""

    status: BackendStatus
    instructions: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tests_supported: bool = False


@runtime_checkable
class ExecutorBackend(Protocol):
    """Backend that bridges plan/spec generation with execution environments."""

    def plan(self, plan_id: str) -> Dict[str, Any] | None:
        """Optional hook for future planning metadata."""

    def apply(self, change_id: str, spec_path: str) -> BackendApplyResult:
        """Return backend instructions/status for the generated OpenSpec."""


__all__ = ["BackendApplyResult", "ExecutorBackend", "BackendStatus"]
