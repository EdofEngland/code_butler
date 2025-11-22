"""Structure planners for large files and long functions.

The helpers in this module translate structure analyzer findings into pure
CleanupPlan instances. They stay filesystem-agnostic so ButlerSpec can manage
execution and enforcement later in the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from ai_clean.config import AiCleanConfig as ButlerConfig
from ai_clean.models import CleanupPlan, Finding, FindingLocation


@dataclass(frozen=True)
class ClusteredTargets:
    """Suggested module boundaries for a large file split.

    ``leftover_segments`` captures spans that exceeded the per-plan module cap
    so later planners can schedule follow-up work without guessing.
    """

    primary_modules: list[Path]
    leftover_segments: list[FindingLocation]


__all__ = ["plan_large_file", "plan_long_function"]


def plan_large_file(finding: Finding, config: ButlerConfig) -> list[CleanupPlan]:
    """Convert a ``large_file`` finding into a CleanupPlan."""

    if finding.category != "large_file":
        raise ValueError("plan_large_file only accepts large_file findings")
    if not finding.locations:
        raise ValueError("large_file findings require at least one location")

    sorted_locations = _sort_locations(finding.locations)
    target_path = sorted_locations[0].path
    if any(location.path != target_path for location in sorted_locations):
        raise ValueError("large_file findings must target a single file")
    line_count = finding.metadata.get("line_count")
    threshold = finding.metadata.get("threshold")
    if line_count is None or threshold is None:
        raise ValueError(
            "large_file findings require line_count and threshold metadata"
        )

    target_file = target_path.as_posix()
    start_line = min(location.start_line for location in sorted_locations)
    end_line = max(location.end_line for location in sorted_locations)
    cluster = _cluster_module_targets(sorted_locations)

    assigned_segments = sorted_locations[: len(cluster.primary_modules)]
    module_entries = [
        {
            "module_path": module_path.as_posix(),
            "source_segment": _serialize_location(segment),
        }
        for module_path, segment in zip(cluster.primary_modules, assigned_segments)
    ]

    module_targets_str = ", ".join(entry["module_path"] for entry in module_entries)
    if not module_targets_str:
        module_targets_str = target_file
    module_parent = target_path.parent.as_posix() or "."

    plan_id = f"{finding.id}-split"
    title = f"Split {target_file} into focused modules"
    intent = (
        f"Split {target_file} into 2–3 logical modules " "while preserving imports"
    )  # noqa: E501
    steps = [
        f"Analyze {target_file} (lines {start_line}-{end_line}) and group code by responsibility.",
        (
            f"Create new modules {module_targets_str} under {module_parent} "
            f"and move code from {target_file} without changing behavior."
        ),
        "Update imports, re-exports, and tests to reference the new modules "
        f"while keeping {target_file} as the public entry point.",
    ]
    constraints = [
        f"Preserve public API by re-exporting from {target_file}",
        "Do not change function/class behavior",
    ]
    test_command = finding.metadata.get("test_command") or config.tests.default_command
    if not test_command:
        raise ValueError("large_file plans require a test command")

    leftover_entries = [
        _serialize_location(location) for location in cluster.leftover_segments
    ]
    plan_metadata = dict(finding.metadata)
    plan_metadata.update(
        {
            "plan_kind": "large_file_split",
            "target_file": target_file,
            "line_count": line_count,
            "threshold": threshold,
            "module_targets": module_entries,
            "leftover_segments": leftover_entries,
            "module_cluster_state": (
                "follow_up_required" if leftover_entries else "complete"
            ),
            "start_line": start_line,
            "end_line": end_line,
            "module_target_limit": 3,
        }
    )
    if leftover_entries:
        # ButlerSpec guardrail: one plan per file; record unfinished work instead of widening scope.
        plan_metadata["follow_up_required"] = True

    plan = CleanupPlan(
        id=plan_id,
        finding_id=finding.id,
        title=title,
        intent=intent,
        steps=steps,
        constraints=constraints,
        tests_to_run=[test_command],
        metadata=plan_metadata,
    )
    return [plan]


def plan_long_function(finding: Finding, config: ButlerConfig) -> list[CleanupPlan]:
    """Convert a ``long_function`` finding into a helper extraction plan."""

    if finding.category != "long_function":
        raise ValueError("plan_long_function only accepts long_function findings")
    if len(finding.locations) != 1:
        raise ValueError("long_function findings must target exactly one location")

    location = finding.locations[0]
    target_file = location.path.as_posix()
    qualified_name = finding.metadata.get("qualified_name")
    line_count = finding.metadata.get("line_count")
    if not qualified_name or line_count is None:
        raise ValueError(
            "long_function findings require qualified_name and line_count metadata"
        )

    start_line = location.start_line
    end_line = location.end_line
    plan_id = f"{finding.id}-helpers"
    title = f"Extract helpers for {qualified_name} in {target_file}"
    intent = f"Break {qualified_name} into helpers without changing behavior"
    helper_prefix = qualified_name.split(".")[-1]
    steps = [
        (
            f"Review {qualified_name} in {target_file}:{start_line}-{end_line} "
            "and list logical blocks."
        ),
        (
            f"Extract each block into helper functions prefixed `{helper_prefix}_...` "
            f"in {target_file} while keeping arguments stable."
        ),
        (
            "Replace the original block bodies with helper calls and re-run "
            f"targeted tests covering {target_file}:{start_line}-{end_line}."
        ),
    ]
    constraints = [
        "Do not change function signature or side effects",
        f"Limit edits to {target_file}",
    ]

    test_command = (
        finding.metadata.get("test_command")
        or config.tests.default_command  # noqa: E501
    )
    if not test_command:
        raise ValueError("long_function plans require a test command")

    plan_metadata = dict(finding.metadata)
    plan_metadata.update(
        {
            "plan_kind": "long_function_helpers",
            "target_file": target_file,
            "function": qualified_name,
            "line_count": line_count,
            "start_line": start_line,
            "end_line": end_line,
            "helper_prefix": helper_prefix,
            "scope": "single_function",
        }
    )
    segments = finding.metadata.get("segments")
    if segments:
        plan_metadata["segments"] = segments

    plan = CleanupPlan(
        id=plan_id,
        finding_id=finding.id,
        title=title,
        intent=intent,
        steps=steps,
        constraints=constraints,
        tests_to_run=[test_command],
        metadata=plan_metadata,
    )
    return [plan]


def _cluster_module_targets(
    locations: Sequence[FindingLocation], *, max_modules: int = 3
) -> ClusteredTargets:
    """Suggest module targets based on ordered locations."""

    if max_modules < 1:
        raise ValueError("max_modules must be at least 1")
    if not locations:
        raise ValueError("_cluster_module_targets requires at least one location")

    sorted_locations = _sort_locations(locations)
    base_path = sorted_locations[0].path
    primary_modules: list[Path] = []
    leftover_segments: list[FindingLocation] = []
    for index, location in enumerate(sorted_locations, start=1):
        if location.path != base_path:
            raise ValueError("clustered targets must share a single source file")
        if len(primary_modules) < max_modules:
            module_name = f"{base_path.stem}_{index}{base_path.suffix}"
            primary_modules.append(base_path.with_name(module_name))
        else:
            leftover_segments.append(location)
    return ClusteredTargets(
        primary_modules=primary_modules, leftover_segments=leftover_segments
    )


def _serialize_location(location: FindingLocation) -> dict[str, object]:
    return {
        "path": location.path.as_posix(),
        "start_line": location.start_line,
        "end_line": location.end_line,
    }


def _sort_locations(locations: Sequence[FindingLocation]) -> list[FindingLocation]:
    return sorted(
        locations,
        key=lambda loc: (loc.path.as_posix(), loc.start_line, loc.end_line),
    )
