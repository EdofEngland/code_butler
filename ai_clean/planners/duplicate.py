"""Convert duplicate analyzer findings into deterministic CleanupPlans.

The duplicate planner translates pure analyzer output into ButlerSpec-ready
CleanupPlan objects. It groups duplicate windows by the helper location they
should share, selects the helper path deterministically, and emits small plans
that describe how to extract a helper and replace each occurrence. Planners do
not touch the filesystem; they only reshape metadata for downstream stages.
"""

from __future__ import annotations

import collections
import itertools
from pathlib import Path
from typing import Sequence, TypeAlias

from ai_clean.config import AiCleanConfig as ButlerConfig
from ai_clean.models import CleanupPlan, Finding, FindingLocation

HelperKey: TypeAlias = tuple[str, str]
_MAX_OCCURRENCES_PER_PLAN = 3

__all__ = ["plan_duplicate_blocks"]


def plan_duplicate_blocks(
    findings: Sequence[Finding], config: ButlerConfig
) -> list[CleanupPlan]:
    """Plan helper extractions for duplicate-block findings.

    The planner keeps each plan focused on a single helper location, trims each
    plan to at most ``_MAX_OCCURRENCES_PER_PLAN`` duplicate windows, and returns
    a list of pure CleanupPlan models sorted by helper path and first occurrence
    line. Serialization and Codex execution happen in later pipeline stages.
    """

    helper_groups = _group_duplicates(findings)
    plans: list[CleanupPlan] = []
    for (helper_path_str, _), group in helper_groups.items():
        helper_path = Path(helper_path_str)
        # Guardrail: if metadata drifted, refuse to mix helper targets.
        for finding in group:
            recorded = finding.metadata.get("_helper_path")
            if recorded and recorded != helper_path_str:
                raise ValueError(
                    "Finding helper path does not match group helper target"
                )
        plan = _build_plan(group, helper_path, config)
        plans.append(plan)

    # Preserve deterministic ordering so reviewers can apply plans sequentially.
    plans.sort(key=_plan_sort_key)
    return plans


def _group_duplicates(findings: Sequence[Finding]) -> dict[HelperKey, list[Finding]]:
    """Group findings by helper target while splitting oversize chunks.

    Each group key encodes ``(helper_path, finding_id or finding_id-suffix)`` so
    identical inputs always produce the same grouping order. Groups never exceed
    ``_MAX_OCCURRENCES_PER_PLAN`` occurrences; extra windows spill into new
    helper keys with predictable ``"-2"`` style suffixes. The invariant is that
    every finding in a group points at the same helper target.
    """

    ordered: dict[HelperKey, list[Finding]] = collections.OrderedDict()
    prepared: list[tuple[Path, list[FindingLocation], Finding]] = []
    for finding in findings:
        if finding.category != "duplicate_block":
            raise ValueError(
                "plan_duplicate_blocks only accepts duplicate_block findings"
            )
        if not finding.locations:
            raise ValueError("duplicate_block findings require at least one location")
        sorted_locations = _sort_locations(finding.locations)
        helper_path = _select_helper_path(sorted_locations)
        prepared.append((helper_path, sorted_locations, finding))

    prepared.sort(
        key=lambda item: (
            item[0].as_posix(),
            item[1][0].path.as_posix(),
            item[1][0].start_line,
            item[2].id,
        )
    )

    for helper_path, locations, finding in prepared:
        for index, chunk in enumerate(
            _chunk_locations(locations, _MAX_OCCURRENCES_PER_PLAN), start=1
        ):
            label = finding.id if index == 1 else f"{finding.id}-{index}"
            key: HelperKey = (helper_path.as_posix(), label)
            metadata = dict(finding.metadata)
            metadata["_plan_chunk_index"] = index
            metadata["_helper_path"] = helper_path.as_posix()
            chunk_finding = finding.model_copy(
                update={"locations": chunk, "metadata": metadata}
            )
            ordered.setdefault(key, []).append(chunk_finding)
    return ordered


def _select_helper_path(locations: Sequence[FindingLocation]) -> Path:
    """Choose where the helper should live based on duplicate occurrences.

    Default placement is the module containing the first occurrence. When
    duplicates span multiple modules, the helper moves to the deepest common
    parent package and lives inside ``helpers.py`` so later phases can keep the
    extraction local. If no shared parent exists, the first occurrence path wins.
    The helper path is serialized via ``Path.as_posix`` to avoid OS-specific
    separators. Later configuration work may override this heuristic.
    """

    if not locations:
        raise ValueError("_select_helper_path requires at least one location")
    sorted_locations = _sort_locations(locations)
    first_path = sorted_locations[0].path
    if all(loc.path == first_path for loc in sorted_locations):
        return first_path

    shared_parents = set(_meaningful_parents(first_path))
    for location in sorted_locations[1:]:
        shared_parents &= set(_meaningful_parents(location.path))
        if not shared_parents:
            return first_path

    target_parent = max(shared_parents, key=lambda path: len(path.parts))
    return target_parent / "helpers.py"


def _meaningful_parents(path: Path) -> tuple[Path, ...]:
    return tuple(parent for parent in path.parents if parent.parts)


def _sort_locations(locations: Sequence[FindingLocation]) -> list[FindingLocation]:
    return sorted(
        locations,
        key=lambda loc: (loc.path.as_posix(), loc.start_line, loc.end_line),
    )


def _chunk_locations(
    locations: Sequence[FindingLocation], chunk_size: int
) -> list[list[FindingLocation]]:
    iterator = iter(locations)
    chunks: list[list[FindingLocation]] = []
    while True:
        batch = list(itertools.islice(iterator, chunk_size))
        if not batch:
            break
        chunks.append(batch)
    return chunks


def _build_plan(
    group: list[Finding], helper_path: Path, config: ButlerConfig
) -> CleanupPlan:
    """Construct a CleanupPlan for the provided helper chunk.

    Plan identifiers follow ``{finding_id}-helper-{index}``, where ``index`` is
    the 1-based chunk counter recorded in the finding metadata.
    """

    if not group:
        raise ValueError("cannot build plan for empty finding group")

    metadata = dict(group[0].metadata)
    chunk_index = int(metadata.pop("_plan_chunk_index", 1))
    metadata.pop("_helper_path", None)
    helper_path_str = helper_path.as_posix()
    helper_name = helper_path.stem or "helper"
    occurrences = [
        loc for finding in group for loc in _sort_locations(finding.locations)
    ]
    if not occurrences:
        raise ValueError("duplicate_block plans require at least one occurrence")

    plan_id = f"{group[0].id}-helper-{chunk_index}"
    finding_description = group[0].description
    summary = ", ".join(
        f"{loc.path.as_posix()}:{loc.start_line}-{loc.end_line}" for loc in occurrences
    )
    steps = [
        (
            f"Decide the {helper_name} helper signature covering {summary} "
            "so inputs and return values stay consistent."
        ),
        (
            f"Create helper `{helper_name}` inside {helper_path_str} with a"
            " focused docstring and naming derived from the helper path."
        ),
    ]
    for location in occurrences:
        steps.append(
            (
                f"Replace lines {location.start_line}-{location.end_line} in "
                f"{location.path.as_posix()} with a call to `{helper_name}`."
            )
        )

    test_command = group[0].metadata.get("test_command") or config.tests.default_command
    if not test_command:
        raise ValueError("duplicate_block plans require a configured test command")

    constraints = [
        f"Do not change public APIs in {helper_path_str}",
        f"Keep helper pure in {helper_path_str}; no global state or behavior changes",
    ]

    plan_metadata = dict(metadata)
    plan_metadata.update(
        {
            "plan_kind": "duplicate_block_helper",
            "helper_path": helper_path_str,
            "occurrences": [
                {
                    "path": loc.path.as_posix(),
                    "start_line": loc.start_line,
                    "end_line": loc.end_line,
                }
                for loc in occurrences
            ],
            "source_findings": [finding.id for finding in group],
            "plan_chunk_index": chunk_index,
        }
    )

    intent = (
        f"Create shared helper at {helper_path_str} and replace duplicates "
        f"from: {finding_description}"
    )

    return CleanupPlan(
        id=plan_id,
        finding_id=group[0].id,
        title=f"Extract helper into {helper_path.name}",
        intent=intent,
        steps=steps,
        constraints=constraints,
        tests_to_run=[test_command],
        metadata=plan_metadata,
    )


def _plan_sort_key(plan: CleanupPlan) -> tuple[str, int]:
    helper_path = plan.metadata.get("helper_path", "")
    occurrences = plan.metadata.get("occurrences") or []
    first_line = 0
    if occurrences:
        first_line = int(occurrences[0].get("start_line", 0))
    return helper_path, first_line
