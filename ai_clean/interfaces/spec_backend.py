"""Contracts for translating CleanupPlans to ButlerSpec files.

Keep this module dependency-free—Codex implementations belong in separate
packages. The goal is to honor the Phase 1 system sketch hand-offs without
pulling in executor logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from ai_clean.models import ButlerSpec, CleanupPlan


@runtime_checkable
class SpecBackend(Protocol):
    """Backend responsible for generating and persisting ButlerSpec files."""

    def plan_to_spec(self, plan: "CleanupPlan") -> "ButlerSpec":
        """Convert a CleanupPlan into a ButlerSpec without side effects."""

    def write_spec(self, spec: "ButlerSpec", directory: Path) -> Path:
        """Persist the ButlerSpec under the provided directory and return the path."""


class BaseSpecBackend(ABC):
    """Fallback base class for implementers that prefer inheritance."""

    @abstractmethod
    def plan_to_spec(
        self, plan: "CleanupPlan"
    ) -> "ButlerSpec":  # pragma: no cover - abstract
        raise NotImplementedError

    def write_spec(self, spec: "ButlerSpec", directory: Path) -> Path:
        spec_path = directory / f"{spec.id}.yaml"
        directory.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(spec.to_yaml())
        return spec_path


__all__ = ["SpecBackend", "BaseSpecBackend"]
