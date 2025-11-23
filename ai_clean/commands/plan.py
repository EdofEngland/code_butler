"""Helpers for creating CleanupPlan objects from findings."""

from __future__ import annotations

from pathlib import Path

from ai_clean.config import load_config
from ai_clean.metadata import resolve_metadata_paths
from ai_clean.models import CleanupPlan, Finding
from ai_clean.planners.orchestrator import plan_from_finding
from ai_clean.plans import save_plan


def run_plan_for_finding(
    root: Path, config_path: Path | None, finding: Finding
) -> list[tuple[CleanupPlan, Path]]:
    """Create and persist cleanup plans for a single finding.

    This helper is intentionally simple: it loads configuration, delegates
    to the planner orchestrator, and writes each resulting plan beneath the
    `.ai-clean/plans/` directory rooted at ``root``.
    """

    config = load_config(config_path)
    _, plans_dir, _, _ = resolve_metadata_paths(root, config)
    plans = plan_from_finding(finding, config)
    persisted: list[tuple[CleanupPlan, Path]] = []
    for plan in plans:
        plan_path = save_plan(plan, root=plans_dir.parent)
        persisted.append((plan, plan_path))
    return persisted


__all__ = ["run_plan_for_finding"]
