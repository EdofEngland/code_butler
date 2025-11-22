"""Planner for docstring-related findings.

The helpers here translate ``missing_docstring`` and ``weak_docstring`` analyzer
findings into ButlerSpec-ready ``CleanupPlan`` instances. Plans stay pure data
structures so downstream stages control execution and file edits.
"""

from __future__ import annotations

from typing import Any

from ai_clean.config import AiCleanConfig as ButlerConfig
from ai_clean.models import CleanupPlan, Finding, FindingLocation

__all__ = ["plan_docstring_fix"]

_SUPPORTED_CATEGORIES = {"missing_docstring", "weak_docstring"}


def plan_docstring_fix(finding: Finding, config: ButlerConfig) -> list[CleanupPlan]:
    """Return a CleanupPlan describing how to fix the docstring finding."""

    if finding.category not in _SUPPORTED_CATEGORIES:
        raise ValueError("plan_docstring_fix only accepts docstring findings")
    location = _single_location(finding.locations)
    path = location.path
    path_str = path.as_posix()
    metadata = _validate_metadata(finding.metadata)

    qualified_name: str = metadata["qualified_name"]
    symbol_name: str = metadata["symbol_name"]
    symbol_type: str = metadata["symbol_type"]
    preview: str = metadata["docstring_preview"]
    lines_of_code: int = metadata["lines_of_code"]
    missing_docstring = finding.category == "missing_docstring"

    plan_id = f"{finding.id}-docstring"
    title_action = "Add" if missing_docstring else "Improve"
    intent_action = "Add" if missing_docstring else "Strengthen"
    title = f"{title_action} docstring for {qualified_name}"
    intent = (
        f"{intent_action} the docstring for {qualified_name} in {path_str} "
        "without changing behavior"
    )

    start_line = location.start_line
    end_line = location.end_line
    steps = [
        (
            f"Review {qualified_name} in {path_str}:{start_line}-{end_line} "
            f"(≈{lines_of_code} LOC) to understand current behavior."
        ),
        (
            "Draft a docstring covering purpose, parameters, return value, and "
            f"edge cases for {qualified_name} in {path_str} "
            "using the provided preview/context."
        ),
        (
            f"Insert or replace the docstring directly above {qualified_name} in "
            f"{path_str}, matching indentation and style."
        ),
    ]

    if not all(path_str in step for step in steps):
        raise AssertionError("All steps must reference the target file path")

    constraints = [
        "No symbol renames or signature changes",
        "Docstring must describe existing behavior; "
        "explicitly state assumptions if unsure",
    ]

    requires_review_assistance = lines_of_code > 250
    if requires_review_assistance:
        constraints.append(
            f"Large symbol (~{lines_of_code} LOC) in {path_str} "
            "may require reviewer assistance"
        )

    test_command = finding.metadata.get("test_command") or config.tests.default_command
    if not test_command:
        raise ValueError("docstring plans require a configured test command")

    plan_metadata: dict[str, Any] = dict(finding.metadata)
    plan_metadata.update(
        {
            "plan_kind": "docstring",
            "target_file": path_str,
            "qualified_name": qualified_name,
            "symbol_name": symbol_name,
            "symbol_type": symbol_type,
            "docstring_preview": preview,
            "lines_of_code": lines_of_code,
            "docstring_type": finding.category,
            "scope": "single_module",
            "assumptions_required": not bool(preview),
        }
    )
    if requires_review_assistance:
        plan_metadata["requires_review_assistance"] = True

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


def _single_location(locations: list[FindingLocation]) -> FindingLocation:
    if len(locations) != 1:
        raise ValueError("docstring findings must include exactly one location")
    return locations[0]


def _validate_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    required = [
        "symbol_type",
        "qualified_name",
        "symbol_name",
        "docstring_preview",
        "lines_of_code",
    ]
    missing = [key for key in required if key not in metadata]
    if missing:
        formatted = ", ".join(missing)
        raise ValueError(f"docstring findings require metadata fields: {formatted}")
    lines = metadata["lines_of_code"]
    if not isinstance(lines, int) or lines < 1:
        raise ValueError("lines_of_code must be a positive integer")
    return metadata
