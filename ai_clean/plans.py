"""Helpers for persisting CleanupPlan objects to disk."""

from __future__ import annotations

from pathlib import Path

from ai_clean.models import CleanupPlan
from ai_clean.paths import default_metadata_root


def _plans_root(root: Path | None) -> Path:
    base = (root or default_metadata_root()).resolve()
    return base / "plans"


def save_plan(plan: CleanupPlan, root: Path | None = None) -> Path:
    """Serialize a CleanupPlan to JSON under the metadata plans directory."""

    plans_dir = _plans_root(root)
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plans_dir / f"{plan.id}.json"
    plan_path.write_text(plan.to_json())
    return plan_path


def load_plan(plan_id: str, root: Path | None = None) -> CleanupPlan:
    """Load a CleanupPlan from the metadata plans directory."""

    plan_path = _plans_root(root) / f"{plan_id}.json"
    if not plan_path.is_file():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")
    return CleanupPlan.from_json(plan_path.read_text())


__all__ = ["save_plan", "load_plan"]
