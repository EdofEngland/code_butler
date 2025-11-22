"""Validation helpers for ButlerSpec backends.

Shared guards live here so `ButlerSpecBackend` can enforce the contract
documented in `docs/butlerspec_plan.md#phase-4-1`.
"""

from __future__ import annotations

from json import dumps as json_dumps
from pathlib import Path
from typing import Any, Mapping, Sequence

PLAN_METADATA_LIMIT = 32 * 1024
_MAX_TEXT_ENTRIES = 25
_TARGET_KEY = "target_file"


def normalize_text_array(
    values: Sequence[str], *, section_name: str = "entries"
) -> list[str]:
    """Return trimmed, deterministic text arrays per canonical plan rules.

    Empty strings are dropped, relative ordering is preserved, and arrays with
    more than 25 entries raise ValueError so oversized plans are rejected before
    ButlerSpec generation. Section names use the anchors from
    `docs/butlerspec_plan.md#canonical-plan-json`.
    """

    cleaned: list[str] = []
    for value in values:
        trimmed = value.strip()
        if trimmed:
            cleaned.append(trimmed)
    if len(cleaned) > _MAX_TEXT_ENTRIES:
        raise ValueError(
            f"CleanupPlan {section_name} may not exceed {_MAX_TEXT_ENTRIES} entries"
        )
    return cleaned


def ensure_single_target(metadata: Mapping[str, Any]) -> str:
    """Return the canonical target_file per
    docs/butlerspec_plan.md#governance-and-error-catalog."""

    raw_target = metadata.get(_TARGET_KEY)
    if not isinstance(raw_target, str) or not raw_target.strip():
        raise ValueError("ButlerSpec plans must declare exactly one target_file")
    normalized = raw_target.strip()

    conflicting_keys = [
        key
        for key in metadata
        if key != _TARGET_KEY and "target_file" in key and metadata.get(key)
    ]
    if conflicting_keys:
        raise ValueError("ButlerSpec plans must not declare multiple target files")
    return normalized


def assert_metadata_size(metadata: Mapping[str, Any]) -> None:
    """Enforce the 32 KB metadata ceiling in
    docs/butlerspec_plan.md#canonical-plan-json."""

    encoded = json_dumps(metadata, default=str).encode("utf-8")
    if len(encoded) > PLAN_METADATA_LIMIT:
        raise ValueError("ButlerSpec metadata exceeds the 32 KB limit")


def assert_intent_matches_target(intent: str, target_file: str) -> None:
    """Ensure intent text references the normalized target_file per
    docs/butlerspec_plan.md#governance-and-error-catalog."""

    lowered_intent = intent.strip().lower()
    normalized_target = target_file.strip()

    candidates = {
        normalized_target.lower(),
        Path(normalized_target).name.lower(),
    }
    if not lowered_intent or not any(
        candidate and candidate in lowered_intent for candidate in candidates
    ):
        raise ValueError(
            f"CleanupPlan intent must describe work in target_file '{target_file}'"
        )


__all__ = [
    "PLAN_METADATA_LIMIT",
    "assert_intent_matches_target",
    "assert_metadata_size",
    "ensure_single_target",
    "normalize_text_array",
]
