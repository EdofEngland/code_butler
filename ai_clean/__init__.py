"""ai-clean package metadata."""

from __future__ import annotations

from . import planners
from .planners import plan_duplicate_blocks
from .plans import load_plan, save_plan

__all__ = [
    "__version__",
    "plan_duplicate_blocks",
    "planners",
    "save_plan",
    "load_plan",
]

__version__ = "0.1.0"
