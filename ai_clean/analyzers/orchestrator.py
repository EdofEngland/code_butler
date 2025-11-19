"""Analyzer orchestrator that aggregates multiple analyzer outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable, List, Sequence, Union

from ai_clean.analyzers.docstrings import analyze_docstrings
from ai_clean.analyzers.organize import analyze_organize
from ai_clean.analyzers.structure import analyze_structure
from ai_clean.models import Finding, FindingLocation

try:  # Optional: duplicate analyzer may not exist yet.
    from ai_clean.analyzers.duplicate import analyze_duplicates
except ImportError:  # pragma: no cover - placeholder until implemented

    def analyze_duplicates(root: Path | str) -> List[Finding]:
        return []


AnalyzerFunc = Callable[[Union[Path, str]], Iterable[Finding]]


ANALYZERS: Sequence[AnalyzerFunc] = (
    analyze_duplicates,
    analyze_structure,
    analyze_docstrings,
    analyze_organize,
)


def analyze_repo(root: Path | str) -> List[Finding]:
    """Run all analyzers and return merged findings with stable IDs."""
    findings: List[Finding] = []
    for analyzer in ANALYZERS:
        for finding in analyzer(root):
            findings.append(_with_stable_id(finding))
    return findings


def _with_stable_id(finding: Finding) -> Finding:
    """Return finding with an id if missing; otherwise pass through."""
    if finding.id:
        return finding
    # Fallback: derive from category and first location path.
    path = finding.locations[0].path if finding.locations else "unknown"
    derived_id = f"{finding.category}:{path}:{len(finding.description)}"
    finding.id = derived_id
    return finding


def format_location_summary(location: FindingLocation) -> str:
    """Format a single location as path:line-line."""
    if location.start_line and location.end_line:
        return f"{location.path}:{location.start_line}-{location.end_line}"
    return location.path


__all__ = ["analyze_repo"]
