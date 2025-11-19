"""Planner for advanced cleanup findings."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from ai_clean.models import CleanupPlan, Finding, FindingLocation

DEFAULT_MAX_FILES = 1
DEFAULT_MAX_LINES = 40

ADVANCED_CONSTRAINTS: List[str] = [
    "Treat this as advisory; review the suggestion carefully before committing.",
    "Do not modify APIs or behavior outside the referenced snippet.",
    "Keep changes limited to the referenced file and clipped line range.",
]

ADVANCED_TESTS: List[str] = [
    "Run focused linters/tests relevant to the affected file or snippet",
]


def plan_advanced_cleanup(
    finding: Finding,
    *,
    max_files: int = DEFAULT_MAX_FILES,
    max_lines: int = DEFAULT_MAX_LINES,
) -> CleanupPlan:
    """Create a CleanupPlan for a single advanced cleanup suggestion."""
    if finding.category != "advanced_cleanup":
        raise ValueError(
            f"Unsupported category '{finding.category}'. Expected 'advanced_cleanup'."
        )
    if not finding.locations:
        raise ValueError("advanced_cleanup findings require at least one location.")

    selected_location, deferred_files = _select_location(finding.locations, max_files)
    clipped_location, original_span = _clip_location(selected_location, max_lines)

    metadata = _build_metadata(finding, clipped_location, original_span, deferred_files)
    title, intent = _determine_title_intent(finding, metadata, clipped_location)
    steps = _build_steps(finding, metadata, clipped_location)
    plan_id = _build_plan_id(finding, clipped_location)

    return CleanupPlan(
        id=plan_id,
        finding_id=finding.id,
        title=title,
        intent=intent,
        steps=steps,
        constraints=list(ADVANCED_CONSTRAINTS),
        tests_to_run=list(ADVANCED_TESTS),
        metadata=metadata,
    )


def _select_location(
    locations: Sequence[FindingLocation], max_files: int
) -> Tuple[FindingLocation, List[str]]:
    """Select the primary file to act on and track deferred files."""
    seen_files: List[str] = []
    deferred: List[str] = []
    primary: FindingLocation | None = None

    for location in locations:
        path = location.path
        if path not in seen_files:
            seen_files.append(path)
            if len(seen_files) > max_files:
                deferred.append(path)
                continue
            if primary is None:
                primary = location
        elif primary is None:
            primary = location

    if primary is None:
        primary = locations[0]

    return primary, deferred


def _clip_location(
    location: FindingLocation, max_lines: int
) -> Tuple[FindingLocation, Dict[str, int]]:
    """Clip the target location to the configured maximum number of lines."""
    start = location.start_line
    end = location.end_line
    if max_lines > 0:
        max_end = start + max_lines - 1
        end = min(end, max_end)
    clipped = replace(location, start_line=start, end_line=end)
    original_span = {
        "path": location.path,
        "start_line": location.start_line,
        "end_line": location.end_line,
    }
    return clipped, original_span


def _build_metadata(
    finding: Finding,
    clipped_location: FindingLocation,
    original_span: Dict[str, int],
    deferred_files: Sequence[str],
) -> Dict[str, object]:
    metadata = dict(finding.metadata or {})
    metadata.update(
        {
            "advisory": True,
            "source_finding_id": finding.id,
            "clipped_span": {
                "path": clipped_location.path,
                "start_line": clipped_location.start_line,
                "end_line": clipped_location.end_line,
            },
            "original_span": original_span,
        }
    )
    if deferred_files:
        metadata["deferred_files"] = list(deferred_files)
    return metadata


def _determine_title_intent(
    finding: Finding, metadata: Dict[str, object], location: FindingLocation
) -> Tuple[str, str]:
    suggested_title = metadata.get("title")
    suggested_rationale = metadata.get("rationale")
    path_token = Path(location.path).as_posix()
    span = f"{path_token}:{location.start_line}-{location.end_line}"

    title = (
        str(suggested_title).strip()
        if isinstance(suggested_title, str) and suggested_title.strip()
        else f"Advanced cleanup for {span}"
    )
    intent = (
        str(suggested_rationale).strip()
        if isinstance(suggested_rationale, str) and suggested_rationale.strip()
        else f"Apply advisory cleanup to {span} as suggested by advanced analyzer."
    )
    return title, intent


def _build_steps(
    finding: Finding,
    metadata: Dict[str, object],
    location: FindingLocation,
) -> List[str]:
    suggestion_text = metadata.get("suggested_changes") or metadata.get("rationale")
    suggestion = (
        suggestion_text.strip()
        if isinstance(suggestion_text, str) and suggestion_text.strip()
        else finding.description
    )
    span = f"{location.path}:{location.start_line}-{location.end_line}"
    return [
        f"Review the advisory suggestion: {suggestion}",
        (
            f"Apply the suggested edits only within {span}, keeping surrounding logic "
            "intact."
        ),
        (
            "Run focused tests or lint (e.g., pytest targeting the affected module) to "
            "verify behavior."
        ),
    ]


def _build_plan_id(finding: Finding, location: FindingLocation) -> str:
    path_token = Path(location.path).as_posix().replace("/", "-")
    return f"{finding.id}-advanced-{path_token}-{location.start_line}"


__all__ = ["plan_advanced_cleanup"]
