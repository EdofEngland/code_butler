"""Planner orchestrator that routes findings to specific planner helpers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, Sequence

if TYPE_CHECKING:
    from ai_clean.config import AiCleanConfig
from ai_clean.models import CleanupPlan, Finding, FindingLocation
from ai_clean.planners.advanced import plan_advanced_cleanup
from ai_clean.planners.docstrings import plan_docstring_fix
from ai_clean.planners.duplicate import _chunk_occurrences, plan_duplicate_block
from ai_clean.planners.organize import plan_file_moves
from ai_clean.planners.structure import (
    plan_large_file_split,
    plan_long_function_helper,
)
from ai_clean.storage import save_plan as storage_save_plan

PlannerFunc = Callable[[Finding, int], CleanupPlan]


class PlannerError(ValueError):
    """Raised when a finding cannot be converted into a plan."""


def plan_from_finding(
    finding: Finding,
    *,
    chunk_index: int = 0,
    config: "AiCleanConfig | None" = None,
) -> CleanupPlan:
    """Return a persisted CleanupPlan for the given finding."""
    planner = _resolve_planner(finding.category)
    plan = planner(finding, chunk_index)
    plan = CleanupPlan.from_dict(plan.to_dict())
    if not plan.id:
        plan.id = _generate_plan_id(finding, chunk_index)

    if config:
        stored_path = storage_save_plan(plan, plans_dir=config.plans_dir)
        plan.metadata["stored_at"] = stored_path.as_posix()

    return plan


def _resolve_planner(category: str) -> PlannerFunc:
    planners: Dict[str, PlannerFunc] = {
        "duplicate_block": _plan_duplicate_chunk,
        "large_file": lambda finding, _: plan_large_file_split(finding),
        "long_function": lambda finding, _: plan_long_function_helper(finding),
        "missing_docstring": lambda finding, _: plan_docstring_fix(finding),
        "weak_docstring": lambda finding, _: plan_docstring_fix(finding),
        "organize_candidate": lambda finding, _: plan_file_moves(finding),
        "advanced_cleanup": lambda finding, _: plan_advanced_cleanup(finding),
    }
    planner = planners.get(category)
    if planner is None:
        raise PlannerError(f"No planner registered for category '{category}'.")
    return planner


def _plan_duplicate_chunk(finding: Finding, chunk_index: int) -> CleanupPlan:
    occurrences = _extract_occurrences(finding)
    batches = _chunk_occurrences(occurrences)
    if not batches:
        raise PlannerError("duplicate_block finding is missing occurrence data.")
    if chunk_index < 0 or chunk_index >= len(batches):
        raise PlannerError(
            f"chunk_index {chunk_index} out of range for {len(batches)} batches."
        )

    plan = plan_duplicate_block(finding, occurrence_batch=batches[chunk_index])
    plan.metadata.setdefault("duplicate_batches", len(batches))
    plan.metadata.setdefault("duplicate_chunk_index", chunk_index)
    return plan


def _extract_occurrences(finding: Finding) -> Sequence[Dict[str, object]]:
    metadata_occurrences = finding.metadata.get("occurrences")
    if isinstance(metadata_occurrences, Sequence) and not isinstance(
        metadata_occurrences, (str, bytes)
    ):
        return list(metadata_occurrences)
    return [
        {
            "path": location.path,
            "start_line": location.start_line,
            "end_line": location.end_line,
        }
        for location in finding.locations
    ]


def _generate_plan_id(finding: Finding, chunk_index: int) -> str:
    """Create a deterministic kebab-case plan id."""
    category = (finding.category or "plan").lower().replace("_", "-")
    if finding.locations:
        primary_loc = finding.locations[0]
    else:
        primary_loc = FindingLocation(
            path=finding.id or "unknown", start_line=1, end_line=1
        )
    path_part = Path(primary_loc.path).with_suffix("").as_posix()
    path_token = path_part.replace("/", "-").replace("_", "-").lower()
    base = f"{category}-{path_token}".strip("-")
    base = base or category
    if chunk_index:
        base = f"{base}-chunk-{chunk_index}"
    return base


__all__ = ["plan_from_finding", "PlannerError"]
