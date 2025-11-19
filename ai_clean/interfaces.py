"""Plugin interfaces for ai-clean.

These interfaces stay tool-agnostic (no Codex/OpenSpec naming) and depend
only on standard library typing plus core models.
"""

from __future__ import annotations

from typing import Protocol, Union

from .models import CleanupPlan, ExecutionResult, SpecChange


class SpecBackend(Protocol):
    """Backend that converts plans into specs and writes them to disk."""

    def plan_to_spec(self, plan: CleanupPlan) -> SpecChange:
        """Convert a CleanupPlan into a SpecChange payload."""

    def write_spec(self, spec: SpecChange, directory: str) -> str:
        """Persist the spec in the target directory and return the file path."""


class CodeExecutor(Protocol):
    """Executor that applies a spec file and reports results."""

    def apply_spec(self, spec_path: str) -> ExecutionResult:
        """Apply the spec at the given path and return an execution result."""


class ReviewExecutor(Protocol):
    """Review-only executor that summarizes a change and risks."""

    def review_change(
        self,
        plan: CleanupPlan,
        diff: str,
        execution_result: Union[ExecutionResult, None],
    ) -> Union[str, dict]:
        """Return a review summary (text or structured) for the given change."""


__all__ = ["SpecBackend", "CodeExecutor", "ReviewExecutor"]
