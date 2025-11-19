"""Helpers for persisting CleanupPlans to disk."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ai_clean.models import CleanupPlan

DEFAULT_PLANS_DIR = Path(".ai-clean/plans")
_SANITIZE_TABLE = str.maketrans({"/": "-", "\\": "-", ":": "-"})


def _slugify_plan_id(plan_id: str) -> str:
    """Return a filesystem-safe slug for the given plan id."""
    text = (plan_id or "plan").strip() or "plan"
    text = text.translate(_SANITIZE_TABLE)
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", text)
    text = text.strip("-") or "plan"
    return text


def _resolve_plans_dir(plans_dir: Path | str | None) -> Path:
    if plans_dir is None:
        directory = DEFAULT_PLANS_DIR
    else:
        directory = Path(plans_dir)
    return directory


def save_plan(
    plan: CleanupPlan,
    *,
    plans_dir: Path | str | None = None,
) -> Path:
    """Persist the plan JSON into the configured plans directory."""
    if not plan.id:
        raise ValueError("CleanupPlan.id must be set before saving.")

    directory = _resolve_plans_dir(plans_dir)
    directory.mkdir(parents=True, exist_ok=True)

    slug = _slugify_plan_id(plan.id)
    path = directory / f"{slug}.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(plan.to_dict(), handle, indent=2, sort_keys=True)
    return path


def load_plan(
    plan_id: str,
    *,
    plans_dir: Path | str | None = None,
) -> CleanupPlan:
    """Load a persisted plan from disk and return the reconstructed object."""
    if not plan_id:
        raise ValueError("plan_id is required to load a plan.")

    directory = _resolve_plans_dir(plans_dir)
    slug = _slugify_plan_id(plan_id)
    path = directory / f"{slug}.json"
    with path.open("r", encoding="utf-8") as handle:
        payload: Any = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError(f"Plan file {path} does not contain a JSON object.")

    try:
        return CleanupPlan.from_dict(payload)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"Plan file {path} is invalid or missing required fields."
        ) from exc


__all__ = ["save_plan", "load_plan"]
