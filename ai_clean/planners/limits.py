"""Utilities for enforcing plan size limits."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from ai_clean.config import PlanLimitsConfig
from ai_clean.models import CleanupPlan

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PlanSizeSummary:
    """File and line-span summary for a CleanupPlan."""

    plan_id: str
    file_paths: tuple[str, ...]
    changed_lines: int

    @property
    def file_count(self) -> int:
        return len(self.file_paths)


class PlanLimitError(ValueError):
    """Raised when a plan exceeds configured size guardrails."""

    def __init__(
        self,
        plan_id: str,
        summary: PlanSizeSummary,
        limits: PlanLimitsConfig,
        *,
        reason: str,
    ) -> None:
        self.plan_id = plan_id
        self.summary = summary
        self.limits = limits
        self.reason = reason
        message = (
            f"Plan {plan_id} exceeds plan limits ({reason}): "
            f"files={summary.file_count}/{limits.max_files_per_plan}, "
            f"changed_lines={summary.changed_lines}/"
            f"{limits.max_changed_lines_per_plan}. "
            "Split into separate plans."
        )
        super().__init__(message)


def summarize_plan_size(plan: CleanupPlan) -> PlanSizeSummary:
    """Return a normalized file + changed-line summary for a plan."""

    file_paths = tuple(dict.fromkeys(_collect_target_paths(plan.metadata)))
    changed_lines = _estimate_changed_lines(plan.metadata)
    return PlanSizeSummary(plan.id, file_paths, changed_lines)


def validate_plan_limits(
    plan: CleanupPlan,
    limits: PlanLimitsConfig,
    *,
    enforce_file_count: bool = True,
) -> PlanSizeSummary:
    """Validate a plan against configured limits."""

    summary = summarize_plan_size(plan)
    if enforce_file_count and summary.file_count > limits.max_files_per_plan:
        LOGGER.warning(
            "Plan %s rejected: files=%s limit=%s changed_lines=%s limit=%s",
            plan.id,
            summary.file_count,
            limits.max_files_per_plan,
            summary.changed_lines,
            limits.max_changed_lines_per_plan,
        )
        raise PlanLimitError(
            plan.id, summary, limits, reason="max_files_per_plan exceeded"
        )
    if summary.changed_lines > limits.max_changed_lines_per_plan:
        LOGGER.warning(
            "Plan %s rejected: files=%s limit=%s changed_lines=%s limit=%s",
            plan.id,
            summary.file_count,
            limits.max_files_per_plan,
            summary.changed_lines,
            limits.max_changed_lines_per_plan,
        )
        raise PlanLimitError(
            plan.id, summary, limits, reason="max_changed_lines_per_plan exceeded"
        )
    return summary


def split_plans_to_limits(
    plans: Sequence[CleanupPlan],
    limits: PlanLimitsConfig,
    *,
    logger: logging.Logger | None = None,
) -> list[CleanupPlan]:
    """Split multi-file plans into single-file plans when limits allow."""

    expanded: list[CleanupPlan] = []
    for plan in plans:
        summary = summarize_plan_size(plan)
        if summary.file_count <= limits.max_files_per_plan or not summary.file_paths:
            expanded.append(plan)
            continue

        split_plans: list[CleanupPlan] = []
        for index, path in enumerate(summary.file_paths, start=1):
            updated_metadata = dict(plan.metadata)
            updated_metadata["target_file"] = path
            if "target_path" in updated_metadata:
                updated_metadata["target_path"] = path
            if "target_files" in updated_metadata:
                updated_metadata["target_files"] = [path]
            if "target_paths" in updated_metadata:
                updated_metadata["target_paths"] = [path]
            if "file" in updated_metadata:
                updated_metadata["file"] = path
            updated_metadata.setdefault("split_from_plan", plan.id)
            updated_metadata["split_index"] = index
            updated_metadata["split_total"] = summary.file_count

            split_plans.append(
                plan.model_copy(
                    update={
                        "id": f"{plan.id}-split-{index}",
                        "metadata": updated_metadata,
                    }
                )
            )

        if logger:
            after = [summarize_plan_size(candidate) for candidate in split_plans]
            logger.info(
                "Split plan %s due to plan limits: before files=%s lines=%s; after=%s",
                plan.id,
                summary.file_count,
                summary.changed_lines,
                [
                    {
                        "plan_id": candidate.plan_id,
                        "files": candidate.file_count,
                        "lines": candidate.changed_lines,
                    }
                    for candidate in after
                ],
            )
        expanded.extend(split_plans)
    return expanded


def _collect_target_paths(metadata: Any) -> list[str]:
    if not isinstance(metadata, dict):
        return []
    paths: list[str] = []
    direct_fields = (
        "target_file",
        "target_path",
        "file",
        "target_files",
        "target_paths",
    )
    for key in direct_fields:
        paths.extend(_normalize_path_entries(metadata.get(key)))

    paths.extend(_normalize_path_entries(metadata.get("helper_path")))

    occurrences_value = metadata.get("occurrences")
    if isinstance(occurrences_value, Iterable) and not isinstance(
        occurrences_value, (str, bytes, bytearray, Path)
    ):
        for entry in occurrences_value:
            if isinstance(entry, dict):
                paths.extend(_normalize_path_entries(entry.get("path")))
    return paths


def _normalize_path_entries(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, Path)):
        text = str(value).strip()
        return [Path(text).as_posix()] if text else []
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        normalized: list[str] = []
        for entry in value:
            normalized.extend(_normalize_path_entries(entry))
        return normalized
    return []


def _estimate_changed_lines(metadata: Any) -> int:
    if not isinstance(metadata, dict):
        return 0

    line_span = _coerce_positive_int(metadata.get("line_span"))
    if line_span is not None:
        return line_span

    start_line = _coerce_positive_int(metadata.get("start_line"))
    end_line = _coerce_positive_int(metadata.get("end_line"))
    if start_line is not None and end_line is not None and end_line >= start_line:
        return end_line - start_line + 1

    occurrences_value = metadata.get("occurrences")
    if isinstance(occurrences_value, Iterable):
        occurrences_total = 0
        for entry in occurrences_value:
            if not isinstance(entry, dict):
                continue
            start = _coerce_positive_int(entry.get("start_line"))
            end = _coerce_positive_int(entry.get("end_line"))
            if start is not None and end is not None and end >= start:
                occurrences_total += end - start + 1
        if occurrences_total:
            return occurrences_total

    lines_of_code = _coerce_positive_int(metadata.get("lines_of_code"))
    if lines_of_code is not None:
        return lines_of_code

    line_count = _coerce_positive_int(metadata.get("line_count"))
    if line_count is not None:
        return line_count

    return 0


def _coerce_positive_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


__all__ = [
    "PlanLimitError",
    "PlanSizeSummary",
    "split_plans_to_limits",
    "summarize_plan_size",
    "validate_plan_limits",
]
