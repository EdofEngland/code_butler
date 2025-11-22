"""Planner entrypoints for ai-clean."""

from __future__ import annotations

# Advanced planner stays opt-in—see ai_clean.planners.advanced docstring for guardrails.
from .advanced import plan_advanced_cleanup
from .docstrings import plan_docstring_fix
from .duplicate import plan_duplicate_blocks
from .orchestrator import generate_plan_id, plan_from_finding, write_plan_to_disk
from .organize import plan_organize_candidate
from .structure import plan_large_file, plan_long_function

# Keep this sorted so future planners are easy to locate.
__all__ = [
    "generate_plan_id",
    "plan_advanced_cleanup",
    "plan_docstring_fix",
    "plan_duplicate_blocks",
    "plan_from_finding",
    "plan_large_file",
    "plan_long_function",
    "plan_organize_candidate",
    "write_plan_to_disk",
]
