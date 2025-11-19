"""Planner for organize_candidate findings."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence

from ai_clean.models import CleanupPlan, Finding

DEFAULT_MAX_FILES = 4

ORGANIZE_CONSTRAINTS: List[str] = [
    "Do not modify function/class bodies; only move files and update imports.",
    "Add re-export shims or __init__.py updates when moving public modules.",
    "Limit moves to the listed files; defer any extra files to follow-up plans.",
]

ORGANIZE_TESTS: List[str] = ["Run pytest or targeted import checks"]


def plan_file_moves(
    finding: Finding,
    *,
    max_files: int = DEFAULT_MAX_FILES,
) -> CleanupPlan:
    """Create a plan to move a handful of files into a destination folder."""
    if finding.category != "organize_candidate":
        raise ValueError(
            f"Unsupported category '{finding.category}'. Expected 'organize_candidate'."
        )
    if not finding.locations:
        raise ValueError("organize_candidate findings require file locations.")

    destination = _extract_destination(finding)
    all_files = [loc.path for loc in finding.locations]
    files_to_move, deferred = _enforce_max_files(all_files, max_files)

    title = f"Move {len(files_to_move)} file(s) into {destination}"
    intent = (
        f"Group related modules by moving {len(files_to_move)} file(s) into "
        f"{destination} without changing their contents."
    )
    steps = _build_steps(files_to_move, destination, deferred)
    metadata: Dict[str, object] = {
        "target_folder": destination,
        "files": files_to_move,
        "requires_reexports": bool(finding.metadata.get("requires_reexports", True)),
    }
    if deferred:
        metadata["deferred_files"] = deferred

    constrained = list(ORGANIZE_CONSTRAINTS)
    if metadata["requires_reexports"]:
        constrained.append("Ensure old import paths continue working via re-exports.")

    plan_id = _build_plan_id(finding, destination)

    plan = CleanupPlan(
        id=plan_id,
        finding_id=finding.id,
        title=title,
        intent=intent,
        steps=steps,
        constraints=constrained,
        tests_to_run=list(ORGANIZE_TESTS),
        metadata=metadata,
    )

    return plan


def _extract_destination(finding: Finding) -> str:
    destination = finding.metadata.get("destination")
    if isinstance(destination, str) and destination.strip():
        return destination.strip()
    first_path = finding.locations[0].path
    return str(Path(first_path).parent.as_posix()) + "/"


def _enforce_max_files(
    files: Sequence[str],
    max_files: int,
) -> tuple[List[str], List[str]]:
    limited = list(files[:max_files])
    deferred = list(files[max_files:])
    return limited, deferred


def _build_steps(
    files: Sequence[str],
    destination: str,
    deferred: Sequence[str],
) -> List[str]:
    file_list = ", ".join(files)
    steps = [
        (
            f"Create or verify folder `{destination}` and ensure __init__.py exists "
            "if needed."
        ),
        (
            f"Move files ({file_list}) into `{destination}` keeping package structure "
            "consistent."
        ),
        (
            "Update imports and add re-export shims (e.g., package __init__.py) so "
            "previous import paths keep working; run repo-wide search/replace."
        ),
        "Run repo-wide search/replace to update imports referencing the moved modules.",
    ]
    if deferred:
        deferred_list = ", ".join(deferred)
        steps.append(
            "Open follow-up organize tickets for deferred files: " f"{deferred_list}."
        )
    return steps


def _build_plan_id(finding: Finding, destination: str) -> str:
    sanitized = destination.strip("/").replace("/", "-")
    return f"{finding.id}-organize-{sanitized or 'folder'}"


__all__ = ["plan_file_moves"]
