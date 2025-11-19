"""Planner for duplicate_block findings."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Sequence

from ai_clean.models import CleanupPlan, Finding, FindingLocation

DEFAULT_MAX_OCCURRENCES_PER_PLAN = 3

OccurrenceDict = Dict[str, Any]

_DUPLICATE_CONSTRAINTS: List[str] = [
    "Do not change any public APIs; only add internal helpers.",
    (
        "Keep the extracted helper signature identical to the duplicated logic "
        "requirements."
    ),
    "Limit edits to the listed files and line ranges.",
]

_DEFAULT_TESTS: List[str] = ["Run existing unit test suite (pytest)"]


def plan_duplicate_block(
    finding: Finding, *, occurrence_batch: Sequence[OccurrenceDict]
) -> CleanupPlan:
    """Build a CleanupPlan describing how to extract a helper for duplicates."""
    if finding.category != "duplicate_block":
        raise ValueError(
            f"Unsupported category '{finding.category}'. Expected 'duplicate_block'."
        )
    if not occurrence_batch:
        raise ValueError("occurrence_batch must include at least one occurrence.")

    locations = [_to_location(item) for item in occurrence_batch]
    helper_name = _derive_helper_name(finding, locations)
    helper_module = _derive_helper_module(locations)
    steps = _build_duplicate_steps(helper_name, helper_module, locations)
    plan_id = _derive_plan_id(finding, locations)

    metadata = {
        "helper_name": helper_name,
        "helper_module": helper_module,
        "batch_size": len(locations),
        "occurrence_paths": sorted({loc.path for loc in locations}),
        "covered_occurrences": [
            {
                "path": loc.path,
                "start_line": loc.start_line,
                "end_line": loc.end_line,
            }
            for loc in locations
        ],
    }

    title = f"Extract helper '{helper_name}' for duplicate block"
    intent = (
        f"Create {helper_name} in {helper_module} and replace "
        f"{len(locations)} duplicated block(s) with calls to it."
    )

    return CleanupPlan(
        id=plan_id,
        finding_id=finding.id,
        title=title,
        intent=intent,
        steps=steps,
        constraints=list(_DUPLICATE_CONSTRAINTS),
        tests_to_run=list(_DEFAULT_TESTS),
        metadata=metadata,
    )


def _build_duplicate_steps(
    helper_name: str, helper_module: str, locations: Sequence[FindingLocation]
) -> List[str]:
    """Return a deterministic set of steps for helper extraction."""
    location_summary = ", ".join(
        f"{loc.path}:{loc.start_line}-{loc.end_line}" for loc in locations
    )
    steps = [
        (
            f"Choose or create module `{helper_module}` to host `{helper_name}`. "
            "Document the helper purpose and import any shared dependencies."
        ),
        (
            f"Move the duplicated logic into `{helper_name}` without changing "
            "behavior. Ensure parameters cover the values referenced within the "
            "block."
        ),
        (
            "Replace each duplicated block with a call to the helper in the following "
            f"locations: {location_summary}. Run formatting after replacements."
        ),
    ]
    return steps


def _derive_helper_name(finding: Finding, locations: Sequence[FindingLocation]) -> str:
    """Suggest a helper name derived from the finding details."""
    suggested = finding.metadata.get("suggested_helper_name")
    if isinstance(suggested, str) and suggested.strip():
        return suggested.strip()

    reference = Path(locations[0].path).stem
    sanitized = reference.replace("-", "_").replace(".", "_")
    return f"{sanitized}_helper"


def _derive_helper_module(locations: Sequence[FindingLocation]) -> str:
    """Select a helper module path (defaults to the first occurrence file)."""
    representative = locations[0].path
    path_obj = Path(representative)
    parent = path_obj.parent.as_posix()
    if parent and parent != ".":
        return f"{parent}/{path_obj.stem}_helpers.py"
    return f"{path_obj.stem}_helpers.py"


def _derive_plan_id(finding: Finding, locations: Sequence[FindingLocation]) -> str:
    """Construct a deterministic plan id."""
    first = locations[0]
    path_token = Path(first.path).as_posix().replace("/", "-")
    return f"{finding.id}-helper-{path_token}-{first.start_line}"


def _to_location(occurrence: OccurrenceDict) -> FindingLocation:
    """Convert an occurrence dict into a FindingLocation."""
    path = occurrence.get("path")
    start_line = occurrence.get("start_line")
    end_line = occurrence.get("end_line", start_line)
    if path is None or start_line is None:
        raise ValueError("Each occurrence must include 'path' and 'start_line'.")

    return FindingLocation(
        path=str(path),
        start_line=int(start_line),
        end_line=int(end_line),
    )


def _chunk_occurrences(
    occurrences: Sequence[OccurrenceDict] | None,
    limit: int = DEFAULT_MAX_OCCURRENCES_PER_PLAN,
) -> List[List[OccurrenceDict]]:
    """Split occurrences into bounded batches for planning."""
    if limit <= 0:
        raise ValueError("limit must be greater than zero.")
    if not occurrences:
        return []

    batches: List[List[OccurrenceDict]] = []
    current: List[OccurrenceDict] = []
    for occurrence in occurrences:
        current.append(occurrence)
        if len(current) >= limit:
            batches.append(current)
            current = []
    if current:
        batches.append(current)
    return batches


__all__ = ["plan_duplicate_block", "_chunk_occurrences"]
