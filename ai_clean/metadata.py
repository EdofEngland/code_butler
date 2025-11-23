"""Helpers for ensuring ai-clean metadata directories exist."""

from __future__ import annotations

import sys
from pathlib import Path

from ai_clean.config import AiCleanConfig
from ai_clean.paths import (
    default_metadata_root,
    default_plan_path,
    default_result_path,
    default_spec_path,
)


def ensure_metadata_dirs(root: Path | None = None) -> Path:
    """Create metadata directories and return the resolved root path."""

    base = (root or default_metadata_root()).resolve()
    for child in ("plans", "specs", "results"):
        path = base / child
        path.mkdir(parents=True, exist_ok=True)
    print(f"[ai-clean] metadata root: {base}", file=sys.stderr)
    return base


__all__ = ["ensure_metadata_dirs", "resolve_metadata_paths"]


def resolve_metadata_paths(
    root: Path, config: AiCleanConfig
) -> tuple[Path, Path, Path, Path]:
    """Return metadata directories adjusted to the CLI root."""

    root_base = root.parent if root.name == default_metadata_root().name else root

    metadata_root = config.metadata_root
    default_meta_root = default_metadata_root().resolve()
    if metadata_root == default_meta_root:
        metadata_root = (root_base / default_metadata_root()).resolve()

    plans_dir = config.plans_dir
    default_plan_dir = default_plan_path("__plan__").resolve().parent
    if plans_dir == default_plan_dir:
        plans_dir = (metadata_root / "plans").resolve()

    specs_dir = config.specs_dir
    default_specs_dir = default_spec_path("__spec__").resolve().parent
    if specs_dir == default_specs_dir:
        specs_dir = (metadata_root / "specs").resolve()

    results_dir = config.results_dir
    default_results_dir = default_result_path("__plan__").resolve().parent
    if results_dir == default_results_dir:
        results_dir = (metadata_root / "results").resolve()

    return metadata_root, plans_dir, specs_dir, results_dir
