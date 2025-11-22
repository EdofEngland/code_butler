"""Execution interfaces for applying ButlerSpec plans.

These Protocols connect CLI commands to executor implementations as described in
the Phase 1 system sketch. Keep runtime dependencies minimal and avoid Codex
imports here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, List, Protocol

from .types import StructuredReview

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from ai_clean.models import CleanupPlan, ExecutionResult


class CodeExecutor(Protocol):
    """Apply a single ButlerSpec located at the provided path."""

    def apply_spec(self, spec_path: Path) -> "ExecutionResult": ...


class BatchRunner(Protocol):
    """Apply all specs in a directory that belong to a specific batch group."""

    def apply_batch(
        self, spec_dir: Path, batch_group: str
    ) -> List["ExecutionResult"]: ...


class ReviewExecutor(Protocol):
    """Produce a structured review for a plan/diff/result tuple."""

    def review_change(
        self,
        plan: "CleanupPlan",
        diff: str,
        exec_result: "ExecutionResult",
    ) -> StructuredReview: ...


@dataclass
class ReviewContext:
    """Bundle plan, diff, and execution output for review helpers."""

    plan: "CleanupPlan"
    diff: str
    exec_result: "ExecutionResult"


__all__ = [
    "BatchRunner",
    "CodeExecutor",
    "ReviewContext",
    "ReviewExecutor",
]
