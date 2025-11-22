"""ai-clean package metadata."""

from __future__ import annotations

from . import planners
from .planners import plan_duplicate_blocks

__all__ = ["__version__", "plan_duplicate_blocks", "planners"]

__version__ = "0.1.0"
