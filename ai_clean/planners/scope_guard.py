"""Scope guardrails preventing global renames or API overhauls."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Sequence

from ai_clean.models import CleanupPlan

LOGGER = logging.getLogger(__name__)


class ForbiddenChange(str, Enum):
    """Non-V0 operations that must be blocked."""

    PUBLIC_API_RENAME = "public_api_rename"
    SIGNATURE_CHANGE = "signature_change"
    GLOBAL_RENAME = "global_rename"
    MULTI_MODULE_REDESIGN = "multi_module_redesign"
    SUBSYSTEM_RESTRUCTURE = "subsystem_restructure"


@dataclass(frozen=True)
class ScopeViolation:
    """Evidence describing why a plan violates scope guardrails."""

    change: ForbiddenChange
    evidence: str


class ScopeGuardError(ValueError):
    """Raised when a plan triggers forbidden scope changes."""

    def __init__(self, violations: Iterable[ScopeViolation]):
        violations = tuple(violations)
        self.violations = violations
        joined = ", ".join(f"{v.change.value}: {v.evidence}" for v in violations)
        super().__init__(
            f"Plan blocked by scope guard: {joined}. "
            "Split the work or open a separate redesign phase."
        )


_RENAME_KEYWORDS = {"rename", "rebrand", "retitle"}
_PUBLIC_KEYWORDS = {"api", "public", "export", "interface"}
_SIGNATURE_KEYWORDS = {
    "change signature",
    "update signature",
    "modify signature",
    "add parameter",
    "remove parameter",
    "rename parameter",
    "change parameters",
    "alter parameters",
}
_REWRITE_KEYWORDS = {"overhaul", "rewrite", "redesign", "re-architect"}
_SUBSYSTEM_KEYWORDS = {"subsystem", "system-wide", "global change"}
_GLOBAL_RENAME_HINTS = {
    "across",
    "everywhere",
    "all files",
    "all modules",
    "project-wide",
    "codebase",
    "global",
}


def detect_forbidden_changes(plan: CleanupPlan) -> list[ScopeViolation]:
    """Return any scope violations detected for a plan."""

    metadata = plan.metadata or {}
    natural_blocks = [
        plan.title,
        plan.intent,
        " ".join(plan.steps),
        " ".join(plan.constraints),
        " ".join(plan.tests_to_run),
    ]
    haystack = " ".join(natural_blocks).lower()
    metadata_haystack = " ".join(
        f"{key}:{value}" for key, value in metadata.items()
    ).lower()
    combined_haystack = f"{haystack} {metadata_haystack}".strip()
    violations: list[ScopeViolation] = []

    if _contains_any(combined_haystack, _REWRITE_KEYWORDS, ignore_negated=True):
        violations.append(
            ScopeViolation(
                change=ForbiddenChange.MULTI_MODULE_REDESIGN,
                evidence="mentions redesign/overhaul",
            )
        )

    if _contains_any(combined_haystack, _SUBSYSTEM_KEYWORDS, ignore_negated=True):
        violations.append(
            ScopeViolation(
                change=ForbiddenChange.SUBSYSTEM_RESTRUCTURE,
                evidence="mentions subsystem/global change",
            )
        )

    if _contains_any(combined_haystack, _SIGNATURE_KEYWORDS, ignore_negated=True):
        violations.append(
            ScopeViolation(
                change=ForbiddenChange.SIGNATURE_CHANGE,
                evidence="suggests signature/parameter changes",
            )
        )

    if _contains_any(haystack, _RENAME_KEYWORDS, ignore_negated=True):
        target_paths = _extract_target_paths(metadata)
        public_rename = _contains_any(haystack, _PUBLIC_KEYWORDS, ignore_negated=True)
        global_hint = _contains_any(haystack, _GLOBAL_RENAME_HINTS, ignore_negated=True)
        if public_rename:
            change = ForbiddenChange.PUBLIC_API_RENAME
        elif global_hint or len(target_paths) > 1:
            change = ForbiddenChange.GLOBAL_RENAME
        else:
            change = None
        if change:
            violations.append(
                ScopeViolation(change=change, evidence="contains rename intent")
            )

    return violations


def summarize_forbidden_changes(plans: Sequence[CleanupPlan]) -> list[ScopeViolation]:
    """Aggregate violations across a batch of plans."""

    violations: list[ScopeViolation] = []
    for plan in plans:
        violations.extend(detect_forbidden_changes(plan))
    return violations


def validate_scope(
    plans: Sequence[CleanupPlan], *, logger: logging.Logger | None = None
) -> None:
    """Raise ScopeGuardError when any plan triggers forbidden changes."""

    violations = summarize_forbidden_changes(plans)
    if not violations:
        return
    if logger:
        logger.warning(
            "Scope guard blocked plan batch: %s",
            [f"{v.change.value}:{v.evidence}" for v in violations],
        )
    raise ScopeGuardError(violations)


def _contains_any(
    text: str, keywords: Iterable[str], *, ignore_negated: bool = False
) -> bool:
    normalized = text.lower()
    for keyword in keywords:
        if keyword in normalized:
            if ignore_negated and _is_negated(normalized, keyword):
                continue
            return True
    return False


def _is_negated(text: str, keyword: str) -> bool:
    markers = ("no ", "do not ", "avoid ", "without ", "never ")
    start = text.find(keyword)
    if start == -1:
        return False
    window_start = max(0, start - 10)
    window = text[window_start:start]
    return any(marker in window for marker in markers)


def _extract_target_paths(metadata: object) -> set[str]:
    if not isinstance(metadata, dict):
        return set()

    paths: set[str] = set()

    def _add(value: object) -> None:
        if value is None:
            return
        if isinstance(value, (str, Path)):
            text = str(value).strip()
            if text:
                paths.add(text)
            return
        if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
            for entry in value:
                _add(entry)

    for field in ("target_file", "target_path", "file", "helper_path"):
        _add(metadata.get(field))
    for field in ("target_files", "target_paths"):
        _add(metadata.get(field))

    occurrences_value = metadata.get("occurrences")
    if isinstance(occurrences_value, Iterable) and not isinstance(
        occurrences_value, (str, bytes, bytearray)
    ):
        for entry in occurrences_value:
            if isinstance(entry, dict):
                _add(entry.get("path"))

    return paths


__all__ = [
    "ForbiddenChange",
    "ScopeGuardError",
    "ScopeViolation",
    "detect_forbidden_changes",
    "summarize_forbidden_changes",
    "validate_scope",
]
