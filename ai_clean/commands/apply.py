"""Helpers for applying a single CleanupPlan via ButlerSpec."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from ai_clean.config import load_config
from ai_clean.factories import (
    ExecutorHandle,
    SpecBackendHandle,
    get_executor,
    get_spec_backend,
)
from ai_clean.git import ensure_on_refactor_branch, get_diff_stat
from ai_clean.metadata import resolve_metadata_paths
from ai_clean.models import CleanupPlan, ExecutionResult
from ai_clean.plans import load_plan
from ai_clean.results import save_execution_result
from ai_clean.spec_backends import ButlerSpecBackend


def _load_plan_by_id(plan_id: str, root: Path | None = None) -> CleanupPlan:
    return load_plan(plan_id, root=root)


def apply_plan(
    root: Path, config_path: Path | None, plan_id: str
) -> Tuple[ExecutionResult, str]:
    """Apply a single plan by ID and return its execution result and spec path."""

    config = load_config(config_path)
    _, plans_dir, specs_dir, results_dir = resolve_metadata_paths(root, config)
    ensure_on_refactor_branch(config.git.base_branch, config.git.refactor_branch)

    plan = _load_plan_by_id(plan_id, root=plans_dir.parent)
    backend_handle: SpecBackendHandle = get_spec_backend(config)
    backend = backend_handle.backend
    if not isinstance(backend, ButlerSpecBackend):
        raise ValueError("Only ButlerSpec backend is supported for apply.")

    spec = backend.plan_to_spec(plan)
    spec_path = backend.write_spec(spec, directory=specs_dir)

    executor_handle: ExecutorHandle = get_executor(config)
    executor = executor_handle.executor
    result = executor.apply_spec(spec_path)

    diff_stat = get_diff_stat()
    if result.git_diff is None:
        result = result.model_copy(update={"git_diff": diff_stat})

    save_execution_result(result, results_dir)

    return result, str(spec_path)


__all__ = ["apply_plan"]
