"""Analyzer entrypoints exposed by ai-clean."""

from .advanced import collect_advanced_cleanup_ideas
from .docstrings import find_docstring_gaps
from .duplicate import find_duplicate_blocks
from .orchestrator import analyze_repo
from .organize import propose_organize_groups
from .structure import find_structure_issues

__all__ = [
    "analyze_repo",
    "collect_advanced_cleanup_ideas",
    "find_docstring_gaps",
    "find_duplicate_blocks",
    "find_structure_issues",
    "propose_organize_groups",
]
