"""Analyzer orchestrator that coordinates individual analyzers."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Sequence

from ai_clean.analyzers.docstrings import find_docstring_gaps
from ai_clean.analyzers.duplicate import find_duplicate_blocks
from ai_clean.analyzers.organize import propose_organize_groups
from ai_clean.analyzers.structure import find_structure_issues
from ai_clean.config import load_config
from ai_clean.models import Finding, FindingLocation

LOGGER = logging.getLogger(__name__)


AnalyzerFn = Callable[[Path, object], Sequence[Finding]]


def analyze_repo(root: Path, config_path: Path | None = None) -> list[Finding]:
    """Run all analyzers for ``root`` and return a deduplicated finding list."""

    root = root.resolve()
    config = load_config(config_path)
    analyzers: list[tuple[str, AnalyzerFn, object]] = [
        ("duplicate", find_duplicate_blocks, config.analyzers.duplicate),
        ("structure", find_structure_issues, config.analyzers.structure),
        ("docstrings", find_docstring_gaps, config.analyzers.docstring),
        ("organize", propose_organize_groups, config.analyzers.organize),
    ]

    findings_by_id: dict[str, Finding] = {}
    errors: list[dict[str, str]] = []
    for name, func, settings in analyzers:
        try:
            new_findings = func(root, settings)
        except (
            Exception
        ) as exc:  # pragma: no cover - exercised via CLI/orchestrator tests
            message = f"{name} analyzer failed: {exc}"
            LOGGER.warning(message)
            errors.append({"analyzer": name, "error": str(exc)})
            continue
        _merge_findings(findings_by_id, new_findings)

    findings = sorted(
        findings_by_id.values(), key=lambda item: (item.category, item.id)
    )

    if errors:
        findings = _annotate_errors(findings, errors)

    return findings


def _merge_findings(existing: dict[str, Finding], new: Sequence[Finding]) -> None:
    for finding in new:
        if finding.id not in existing:
            existing[finding.id] = finding
            continue
        current = existing[finding.id]
        merged_locations = _merge_locations(current.locations, finding.locations)
        merged_metadata = _merge_metadata(current.metadata, finding.metadata)
        existing[finding.id] = current.model_copy(
            update={"locations": merged_locations, "metadata": merged_metadata}
        )


def _merge_locations(
    existing: Sequence[FindingLocation], new: Sequence[FindingLocation]
) -> list[FindingLocation]:
    location_map: dict[tuple[str, int, int], FindingLocation] = {
        (loc.path.as_posix(), loc.start_line, loc.end_line): loc for loc in existing
    }
    for loc in new:
        key = (loc.path.as_posix(), loc.start_line, loc.end_line)
        if key not in location_map:
            location_map[key] = loc
    sorted_keys = sorted(
        location_map.keys(), key=lambda item: (item[0], item[1], item[2])
    )
    return [location_map[key] for key in sorted_keys]


def _merge_metadata(
    existing: dict[str, Any], incoming: dict[str, Any]
) -> dict[str, Any]:
    merged = dict(existing)
    for key, value in incoming.items():
        if key not in merged:
            merged[key] = value
            continue
        if merged[key] == value:
            continue
        if isinstance(merged[key], list) and isinstance(value, list):
            merged[key] = merged[key] + [
                item for item in value if item not in merged[key]
            ]
        else:
            merged[key] = merged[key]
    return merged


def _annotate_errors(
    findings: list[Finding], errors: list[dict[str, str]]
) -> list[Finding]:
    if findings:
        first = findings[0]
        metadata = dict(first.metadata)
        metadata["analyzer_errors"] = errors
        findings[0] = first.model_copy(update={"metadata": metadata})
        return findings

    return [
        Finding(
            id="analyzer-errors",
            category="advanced_cleanup",
            description="One or more analyzers failed",
            locations=[],
            metadata={"analyzer_errors": errors},
        )
    ]


__all__ = ["analyze_repo", "_merge_findings"]
