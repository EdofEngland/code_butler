"""Filesystem helpers shared across ai-clean modules."""

from __future__ import annotations

from pathlib import Path


def default_metadata_root() -> Path:
    """Return the root directory for all ai-clean metadata."""

    return Path(".ai-clean")


def default_plan_path(plan_id: str) -> Path:
    """Return the default on-disk location for a serialized CleanupPlan."""

    return default_metadata_root() / "plans" / f"{plan_id}.json"


def default_spec_path(spec_id: str) -> Path:
    """Return the default on-disk location for a ButlerSpec YAML file."""

    return default_metadata_root() / "specs" / f"{spec_id}.yaml"


def default_result_path(plan_id: str) -> Path:
    """Return the default path for ExecutionResult logs."""

    return default_metadata_root() / "results" / f"{plan_id}.json"


__all__ = [
    "default_metadata_root",
    "default_plan_path",
    "default_result_path",
    "default_spec_path",
]
