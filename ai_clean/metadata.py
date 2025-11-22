"""Helpers for ensuring ai-clean metadata directories exist."""

from __future__ import annotations

import sys
from pathlib import Path

from ai_clean.paths import default_metadata_root


def ensure_metadata_dirs(root: Path | None = None) -> Path:
    """Create metadata directories and return the resolved root path."""

    base = (root or default_metadata_root()).resolve()
    for child in ("plans", "specs", "results"):
        path = base / child
        path.mkdir(parents=True, exist_ok=True)
    print(f"[ai-clean] metadata root: {base}", file=sys.stderr)
    return base


__all__ = ["ensure_metadata_dirs"]
