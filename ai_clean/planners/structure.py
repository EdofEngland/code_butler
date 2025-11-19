"""Planners for large files and long functions."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence

from ai_clean.models import CleanupPlan, Finding, FindingLocation

KEEP_PUBLIC_API = (
    "Preserve public APIs by re-exporting moved symbols from the original module."
)
LIMIT_TO_LOCAL_SCOPE = (
    "Keep changes local to the targeted file/function; avoid cross-package edits."
)
AVOID_SIGNATURE_CHANGES = (
    "Do not change function signatures; extracted helpers must preserve inputs/outputs."
)

DEFAULT_STRUCTURE_TESTS: List[str] = ["pytest"]


def plan_large_file_split(finding: Finding, *, max_modules: int = 3) -> CleanupPlan:
    """Create a CleanupPlan for splitting a large file into smaller modules."""
    if finding.category != "large_file":
        raise ValueError(
            f"Unsupported category '{finding.category}'. Expected 'large_file'."
        )
    location = _require_location(finding)
    line_count = _get_line_count(finding, location)

    estimated_sections = _estimate_sections(line_count)
    proposed_modules = _suggest_module_names(location.path, estimated_sections)

    target_modules = proposed_modules[:max_modules]
    truncated_modules = proposed_modules[max_modules:]

    plan_id = _build_plan_id(finding, suffix="split")
    steps = _build_large_file_steps(location.path, line_count, target_modules)
    constraints = [
        KEEP_PUBLIC_API,
        LIMIT_TO_LOCAL_SCOPE,
        "Re-export moved symbols from the original module to keep imports stable.",
    ]

    metadata: Dict[str, object] = {
        "line_count": line_count,
        "target_modules": target_modules,
        "estimated_sections": estimated_sections,
    }
    if truncated_modules:
        metadata["omitted_sections"] = truncated_modules

    return CleanupPlan(
        id=plan_id,
        finding_id=finding.id,
        title=f"Split {location.path} into {len(target_modules)} modules",
        intent=(
            f"Move cohesive parts of {location.path} (~{line_count} lines) into "
            f"{len(target_modules)} focused modules while keeping public APIs intact."
        ),
        steps=steps,
        constraints=constraints,
        tests_to_run=list(DEFAULT_STRUCTURE_TESTS),
        metadata=metadata,
    )


def plan_long_function_helper(finding: Finding, *, max_helpers: int = 2) -> CleanupPlan:
    """Create a CleanupPlan for extracting helpers from a long function."""
    if finding.category != "long_function":
        raise ValueError(
            f"Unsupported category '{finding.category}'. Expected 'long_function'."
        )
    location = _require_location(finding)
    function_name = _extract_function_name(finding, location)
    span_lines = location.end_line - location.start_line + 1

    estimated_helpers = _estimate_helpers(span_lines)
    helper_candidates = _suggest_helper_names(function_name, estimated_helpers)
    target_helpers = helper_candidates[:max_helpers]
    omitted_helpers = helper_candidates[max_helpers:]

    plan_id = _build_plan_id(finding, suffix="helpers")
    steps = _build_long_function_steps(
        location.path, function_name, target_helpers, location
    )
    constraints = [
        LIMIT_TO_LOCAL_SCOPE,
        AVOID_SIGNATURE_CHANGES,
        "Place new helpers next to the original function within the same module.",
    ]

    metadata: Dict[str, object] = {
        "function_name": function_name,
        "function_span": span_lines,
        "helper_candidates": target_helpers,
    }
    if omitted_helpers:
        metadata["omitted_sections"] = omitted_helpers

    return CleanupPlan(
        id=plan_id,
        finding_id=finding.id,
        title=f"Extract helpers from {function_name}",
        intent=(
            f"Break {function_name} ({span_lines} lines) into small helpers to reduce "
            "complexity while keeping behavior the same."
        ),
        steps=steps,
        constraints=constraints,
        tests_to_run=list(DEFAULT_STRUCTURE_TESTS),
        metadata=metadata,
    )


def _require_location(finding: Finding) -> FindingLocation:
    if not finding.locations:
        raise ValueError("Finding must include at least one location.")
    return finding.locations[0]


def _get_line_count(finding: Finding, location: FindingLocation) -> int:
    metadata_line_count = finding.metadata.get("line_count")
    if metadata_line_count is not None:
        try:
            return int(metadata_line_count)
        except (TypeError, ValueError):
            pass
    return location.end_line - location.start_line + 1


def _estimate_sections(line_count: int) -> int:
    if line_count <= 0:
        return 2
    return max(2, min(5, line_count // 200 + 1))


def _estimate_helpers(span_lines: int) -> int:
    if span_lines <= 0:
        return 1
    return max(1, min(4, span_lines // 80 + 1))


def _suggest_module_names(path: str, count: int) -> List[str]:
    base = Path(path).stem or "module"
    return [f"{base}_part_{idx + 1}" for idx in range(max(count, 1))]


def _suggest_helper_names(function_name: str, count: int) -> List[str]:
    base = function_name or "function"
    safe_base = base.replace(" ", "_")
    return [f"{safe_base}_helper_{idx + 1}" for idx in range(max(count, 1))]


def _build_large_file_steps(
    path: str, line_count: int, modules: Sequence[str]
) -> List[str]:
    module_list = ", ".join(modules)
    return [
        (
            f"Review {path} (~{line_count} lines) and group top-level "
            "classes/functions into "
            f"{len(modules)} cohorts mapped to: {module_list}."
        ),
        (
            f"Create the new modules ({module_list}) and move the grouped code "
            "into each file while keeping internal imports consistent."
        ),
        (
            "Update the original file to import or re-export moved symbols "
            "so existing callers keep working, then run formatting/lint."
        ),
    ]


def _build_long_function_steps(
    path: str,
    function_name: str,
    helpers: Sequence[str],
    location: FindingLocation,
) -> List[str]:
    helper_list = ", ".join(helpers)
    return [
        (
            f"Review {function_name} in "
            f"{path}:{location.start_line}-{location.end_line} "
            f"to identify {len(helpers)} logical blocks to extract."
        ),
        (
            f"Implement helpers ({helper_list}) next to {function_name}, "
            "copying the logic verbatim and passing only needed parameters."
        ),
        (
            "Replace each extracted block with helper calls and keep the "
            f"public signature of {function_name} unchanged; run formatting/tests."
        ),
    ]


def _build_plan_id(finding: Finding, suffix: str) -> str:
    base = finding.id or "structure"
    return f"{base}-{suffix}"


def _extract_function_name(finding: Finding, location: FindingLocation) -> str:
    metadata_function = finding.metadata.get("function")
    if isinstance(metadata_function, str) and metadata_function.strip():
        return metadata_function.strip()
    return Path(location.path).stem or "function"


__all__ = ["plan_large_file_split", "plan_long_function_helper"]
