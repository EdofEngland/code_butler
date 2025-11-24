"""Concern taxonomy and helpers for CleanupPlan validation."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Iterable, Sequence

from ai_clean.models import CleanupPlan


class Concern(str, Enum):
    """Single-concern categories enforced for every CleanupPlan."""

    HELPER_EXTRACTION = (
        "helper_extraction"  # Extract a shared helper and replace occurrences.
    )
    FILE_SPLIT = (
        "file_split"  # Split a large file into smaller modules while preserving API.
    )
    FILE_GROUP_MOVE = (
        "file_group_move"  # Move a small, related group of files into a folder.
    )
    DOCSTRING_BATCH = "docstring_batch"  # Add or improve docstrings for a small scope.
    ADVANCED_CLEANUP = (
        "advanced_cleanup"  # Apply a single Codex-suggested micro change.
    )


class ConcernError(ValueError):
    """Raised when plan concerns are missing, mixed, or invalid."""

    def __init__(self, message: str, *, concerns: Iterable[Concern] | None = None):
        self.concerns = tuple(concerns or ())
        super().__init__(message)


_DOCSTRING_KEYS = {"docstring_type", "qualified_name", "symbol_name"}
_HELPER_KEYS = {"helper_path", "occurrences"}
_FILE_SPLIT_KEYS = {"module_targets", "module_cluster_state"}
_FILE_GROUP_KEYS = {"target_directory", "topic"}
_ADVANCED_KEYS = {"change_type", "prompt_hash", "codex_model"}
_CONCERN_HINTS = {
    Concern.DOCSTRING_BATCH: _DOCSTRING_KEYS,
    Concern.HELPER_EXTRACTION: _HELPER_KEYS,
    Concern.FILE_SPLIT: _FILE_SPLIT_KEYS,
    Concern.FILE_GROUP_MOVE: _FILE_GROUP_KEYS,
    Concern.ADVANCED_CLEANUP: _ADVANCED_KEYS,
}


def classify_plan_concern(plan: CleanupPlan) -> Concern:
    """Return the single Concern for a plan or raise ConcernError."""

    concerns = _detect_concerns(plan)
    if not concerns:
        raise ConcernError(f"Unable to determine concern for plan {plan.id}")
    if len(concerns) > 1:
        raise ConcernError(
            f"Plan {plan.id} mixes multiple concerns: "
            f"{', '.join(sorted(concern.value for concern in concerns))}",
            concerns=concerns,
        )
    concern = next(iter(concerns))
    _ensure_concern_recorded(plan, concern)
    return concern


def classify_plan_group(plans: Sequence[CleanupPlan]) -> tuple[Concern, ...]:
    """Classify all plans and return the ordered set of concerns."""

    concerns: list[Concern] = []
    for plan in plans:
        concern = classify_plan_concern(plan)
        if concern not in concerns:
            concerns.append(concern)
    return tuple(concerns)


def validate_plan_concerns(
    plans: Sequence[CleanupPlan], *, require_shared_concern: bool = True
) -> None:
    """Ensure plans share a single concern when required."""

    concerns = classify_plan_group(plans)
    if not concerns:
        raise ConcernError("No concerns detected for plan batch")
    if require_shared_concern and len(concerns) > 1:
        raise ConcernError(
            "Plan batch mixes concerns: "
            f"{', '.join(concern.value for concern in concerns)}. "
            "Split into separate batches per concern.",
            concerns=concerns,
        )


def split_plan_concerns(
    plan: CleanupPlan, *, logger: logging.Logger | None = None
) -> list[CleanupPlan]:
    """Split a mixed-concern plan into single-concern copies when possible."""

    concerns = _detect_concerns(plan)
    if len(concerns) <= 1:
        concern = next(iter(concerns)) if concerns else None
        if concern:
            _ensure_concern_recorded(plan, concern)
        return [plan]

    sorted_concerns = sorted(concerns, key=lambda c: c.value)
    total = len(sorted_concerns)
    if logger:
        logger.info(
            "Splitting plan %s by concern: detected=%s",
            plan.id,
            [concern.value for concern in sorted_concerns],
        )

    split: list[CleanupPlan] = []
    for index, concern in enumerate(sorted_concerns, start=1):
        metadata = dict(plan.metadata)
        metadata["concern"] = concern.value
        metadata["plan_kind"] = concern.value
        metadata["concern_split_index"] = index
        metadata["concern_split_total"] = total
        _prune_metadata_for_concern(metadata, concern)
        split.append(
            plan.model_copy(
                update={
                    "id": f"{plan.id}-concern-{index}",
                    "metadata": metadata,
                }
            )
        )
    return split


def split_mixed_concerns(
    plans: Sequence[CleanupPlan], *, logger: logging.Logger | None = None
) -> list[CleanupPlan]:
    """Split any mixed-concern plans and flatten the results."""

    expanded: list[CleanupPlan] = []
    for plan in plans:
        expanded.extend(split_plan_concerns(plan, logger=logger))
    return expanded


def _detect_concerns(plan: CleanupPlan) -> set[Concern]:
    metadata = plan.metadata or {}
    plan_kind = str(metadata.get("plan_kind") or "").strip().lower()
    concerns: set[Concern] = set()

    if plan_kind in {
        "duplicate_block_helper",
        "long_function_helpers",
        Concern.HELPER_EXTRACTION.value,
    }:
        concerns.add(Concern.HELPER_EXTRACTION)
    if plan_kind in {"large_file_split", Concern.FILE_SPLIT.value}:
        concerns.add(Concern.FILE_SPLIT)
    if plan_kind in {"organize", Concern.FILE_GROUP_MOVE.value}:
        concerns.add(Concern.FILE_GROUP_MOVE)
    if plan_kind in {"docstring", Concern.DOCSTRING_BATCH.value}:
        concerns.add(Concern.DOCSTRING_BATCH)
    if plan_kind in {"advanced_cleanup", Concern.ADVANCED_CLEANUP.value}:
        concerns.add(Concern.ADVANCED_CLEANUP)

    keys = set(metadata.keys())
    if keys & _HELPER_KEYS:
        concerns.add(Concern.HELPER_EXTRACTION)
    if keys & _FILE_SPLIT_KEYS:
        concerns.add(Concern.FILE_SPLIT)
    if keys & _FILE_GROUP_KEYS:
        concerns.add(Concern.FILE_GROUP_MOVE)
    if keys & _DOCSTRING_KEYS:
        concerns.add(Concern.DOCSTRING_BATCH)
    if keys & _ADVANCED_KEYS:
        concerns.add(Concern.ADVANCED_CLEANUP)

    return concerns


def _prune_metadata_for_concern(metadata: dict[str, object], concern: Concern) -> None:
    for other_concern, keys in _CONCERN_HINTS.items():
        if other_concern is concern:
            continue
        for key in keys:
            metadata.pop(key, None)


def _ensure_concern_recorded(plan: CleanupPlan, concern: Concern) -> None:
    if plan.metadata.get("concern") != concern.value:
        plan.metadata["concern"] = concern.value


__all__ = [
    "Concern",
    "ConcernError",
    "classify_plan_concern",
    "classify_plan_group",
    "validate_plan_concerns",
    "split_plan_concerns",
    "split_mixed_concerns",
]
