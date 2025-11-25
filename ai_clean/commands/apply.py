"""Helpers for applying a single CleanupPlan via ButlerSpec."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from ai_clean.config import load_config
from ai_clean.factories import SpecBackendHandle, get_spec_backend
from ai_clean.git import ensure_on_refactor_branch
from ai_clean.metadata import resolve_metadata_paths
from ai_clean.models import CleanupPlan
from ai_clean.planners.limits import PlanLimitError, validate_plan_limits
from ai_clean.plans import load_plan
from ai_clean.spec_backends import ButlerSpecBackend


def _load_plan_by_id(plan_id: str, root: Path | None = None) -> CleanupPlan:
    return load_plan(plan_id, root=root)


def apply_plan(root: Path, config_path: Path | None, plan_id: str) -> Tuple[str, str]:
    """Apply a single plan by ID and return the spec id and spec path."""

    config = load_config(config_path)
    _, plans_dir, specs_dir, _ = resolve_metadata_paths(root, config)

    plan = _load_plan_by_id(plan_id, root=plans_dir.parent)
    try:
        validate_plan_limits(plan, config.plan_limits)
    except PlanLimitError as exc:
        raise ValueError(str(exc)) from exc

    ensure_on_refactor_branch(config.git.base_branch, config.git.refactor_branch)
    backend_handle: SpecBackendHandle = get_spec_backend(config)
    backend = backend_handle.backend
    if not isinstance(backend, ButlerSpecBackend):
        raise ValueError("Only ButlerSpec backend is supported for apply.")

    try:
        spec = backend.plan_to_spec(plan)
        spec_path = backend.write_spec(spec, directory=specs_dir)
    except ValueError as exc:
        raise ValueError(f"ButlerSpec validation failed: {exc}") from exc

    return spec.id, str(spec_path.resolve())


__all__ = ["apply_plan"]
