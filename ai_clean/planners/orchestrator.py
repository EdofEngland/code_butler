"""Planning orchestrator utilities and helpers."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Callable, ClassVar

from ai_clean.config import AiCleanConfig as ButlerConfig
from ai_clean.models import CleanupPlan, Finding
from ai_clean.planners.concerns import (
    split_mixed_concerns,
    validate_plan_concerns,
)
from ai_clean.planners.limits import (
    split_plans_to_limits,
    validate_plan_limits,
)
from ai_clean.planners.scope_guard import validate_scope

from .advanced import plan_advanced_cleanup
from .docstrings import plan_docstring_fix
from .duplicate import plan_duplicate_blocks
from .organize import plan_organize_candidate
from .structure import plan_large_file, plan_long_function

PlannerCallable = Callable[[Finding, ButlerConfig], list[CleanupPlan]]

LOGGER = logging.getLogger(__name__)

_PLAN_ID_PATTERN = re.compile(r"^[a-z0-9-]+$")
_DASH_RE = re.compile(r"-+")

__all__: ClassVar[list[str]] = [
    "generate_plan_id",
    "write_plan_to_disk",
    "plan_from_finding",
]


def generate_plan_id(finding_id: str, suffix: str) -> str:
    """Return a deterministic `<finding-id>-<suffix>` identifier.

    The helper normalizes both segments (trim + lowercase), collapses
    consecutive dashes, and validates the final identifier to guarantee stable
    filenames.

    >>> generate_plan_id("Finding-123", "Doc")
    'finding-123-doc'
    """

    normalized_suffix = suffix.strip().lower()
    if not normalized_suffix:
        raise ValueError("invalid plan ID suffix: empty")
    if not _PLAN_ID_PATTERN.fullmatch(normalized_suffix):
        raise ValueError(f"invalid plan ID suffix: {suffix!r}")

    normalized_finding_id = finding_id.strip().lower()
    if not normalized_finding_id:
        raise ValueError("finding_id must not be empty")

    combined = f"{normalized_finding_id}-{normalized_suffix}"
    combined = _DASH_RE.sub("-", combined)

    if not _PLAN_ID_PATTERN.fullmatch(combined):
        raise ValueError(f"invalid plan ID: {combined!r}")

    return combined


def write_plan_to_disk(plan: CleanupPlan, base_dir: Path) -> Path:
    """Persist a CleanupPlan as JSON inside ``base_dir``."""

    destination = base_dir / f"{plan.id}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(plan.to_json(indent=2), encoding="utf-8")
    return destination


def _plan_duplicate_block(finding: Finding, config: ButlerConfig) -> list[CleanupPlan]:
    return plan_duplicate_blocks([finding], config)


_CATEGORY_DISPATCH: dict[str, PlannerCallable] = {
    "advanced_cleanup": plan_advanced_cleanup,
    "duplicate_block": _plan_duplicate_block,
    "large_file": plan_large_file,
    "long_function": plan_long_function,
    "missing_docstring": plan_docstring_fix,
    "organize_candidate": plan_organize_candidate,
    "weak_docstring": plan_docstring_fix,
}
_SPLITTABLE_CATEGORIES = {
    "advanced_cleanup",
    "large_file",
    "long_function",
    "organize_candidate",
}
_FILE_LIMIT_EXEMPT_CATEGORIES = {"duplicate_block"}


def plan_from_finding(finding: Finding, config: ButlerConfig) -> list[CleanupPlan]:
    """Dispatch a finding to the correct planner helper."""

    planner = _CATEGORY_DISPATCH.get(finding.category)
    if planner is None:
        raise NotImplementedError(f"Unsupported finding category: {finding.category}")
    plans = planner(finding, config)
    processed = (
        split_plans_to_limits(plans, config.plan_limits, logger=LOGGER)
        if finding.category in _SPLITTABLE_CATEGORIES
        else plans
    )
    processed = split_mixed_concerns(processed, logger=LOGGER)
    validate_plan_concerns(processed)
    validate_scope(processed, logger=LOGGER)
    for plan in processed:
        validate_plan_limits(
            plan,
            config.plan_limits,
            enforce_file_count=finding.category not in _FILE_LIMIT_EXEMPT_CATEGORIES,
        )
    return processed
