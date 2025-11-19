"""Docstring planners for missing or weak docstring findings."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from ai_clean.models import CleanupPlan, Finding, FindingLocation

ALLOWED_CATEGORIES = {"missing_docstring", "weak_docstring"}
MAX_SYMBOL_BATCH = 3

DOCSTRING_CONSTRAINTS: Tuple[str, ...] = (
    "Do not rename symbols or change their signatures; only edit docstrings.",
    "Document existing behavior and side effects factually; do not promise new work.",
    "Keep edits scoped to the referenced module or symbol(s).",
)

DOCSTRING_TESTS: List[str] = [
    "Run static docstring linters if available, otherwise run pytest"
]


def plan_docstring_fix(finding: Finding) -> CleanupPlan:
    """Create a CleanupPlan that adds or improves docstrings."""
    if finding.category not in ALLOWED_CATEGORIES:
        raise ValueError(
            f"Unsupported category '{finding.category}'. "
            f"Expected one of {sorted(ALLOWED_CATEGORIES)}."
        )

    location = _require_location(finding)
    symbol_name = _extract_symbol_name(finding)
    symbol_kind = _extract_symbol_kind(finding)
    symbol_batch, remaining = _build_symbol_batch(finding, symbol_name)

    title, intent = _build_title_intent(
        category=finding.category,
        symbol_name=symbol_name,
        symbol_kind=symbol_kind,
        path=location.path,
    )
    steps = _build_docstring_steps(location, symbol_batch, symbol_kind)

    metadata: Dict[str, object] = {
        "symbol_batch": symbol_batch,
        "docstring_category": finding.category,
        "symbol_kind": symbol_kind,
        "path": location.path,
    }
    if remaining:
        metadata["remaining_symbols"] = remaining

    plan_id = _build_plan_id(finding, location.path, symbol_name)

    return CleanupPlan(
        id=plan_id,
        finding_id=finding.id,
        title=title,
        intent=intent,
        steps=steps,
        constraints=list(DOCSTRING_CONSTRAINTS),
        tests_to_run=list(DOCSTRING_TESTS),
        metadata=metadata,
    )


def _require_location(finding: Finding) -> FindingLocation:
    if not finding.locations:
        raise ValueError("Docstring findings must include at least one location.")
    return finding.locations[0]


def _extract_symbol_name(finding: Finding) -> str:
    symbol = finding.metadata.get("symbol")
    if isinstance(symbol, str) and symbol.strip():
        return symbol.strip()
    return Path(finding.locations[0].path).stem or "module"


def _extract_symbol_kind(finding: Finding) -> str:
    kind = finding.metadata.get("kind")
    if isinstance(kind, str) and kind.strip():
        return kind.strip()
    return "module"


def _build_symbol_batch(
    finding: Finding, primary_symbol: str
) -> Tuple[List[str], List[str]]:
    metadata_batch = finding.metadata.get("symbol_batch")
    if isinstance(metadata_batch, list):
        raw_symbols = [str(sym) for sym in metadata_batch if str(sym).strip()]
    else:
        raw_symbols = []

    if primary_symbol not in raw_symbols:
        raw_symbols.insert(0, primary_symbol)

    deduped: List[str] = []
    for symbol in raw_symbols:
        cleaned = symbol.strip()
        if cleaned and cleaned not in deduped:
            deduped.append(cleaned)

    kept = deduped[:MAX_SYMBOL_BATCH]
    remaining = deduped[MAX_SYMBOL_BATCH:]
    return kept, remaining


def _build_title_intent(
    *, category: str, symbol_name: str, symbol_kind: str, path: str
) -> Tuple[str, str]:
    prefix = "Add" if category == "missing_docstring" else "Improve"
    title = f"{prefix} docstring for {symbol_kind} '{symbol_name}'"
    intent = (
        f"{prefix} a concise, factual docstring for {symbol_kind} '{symbol_name}' in "
        f"{path} without changing behavior."
    )
    return title, intent


def _build_docstring_steps(
    location: FindingLocation, symbols: Sequence[str], symbol_kind: str
) -> List[str]:
    symbol_list = ", ".join(symbols)
    span = f"{location.path}:{location.start_line}-{location.end_line}"
    return [
        (
            f"Review the implementation of {symbol_kind}(s) {symbol_list} at {span} "
            "to understand its purpose and inputs/outputs."
        ),
        (
            "Draft a concise docstring describing intent, key parameters, "
            "return values, and important side effects or invariants."
        ),
        (
            f"Insert or replace the docstring for {symbol_kind}(s) {symbol_list} at "
            f"{span}, keeping formatting consistent (triple quotes, indentation)."
        ),
    ]


def _build_plan_id(finding: Finding, path: str, symbol: str) -> str:
    sanitized_path = path.replace("/", "-")
    sanitized_symbol = symbol.replace(" ", "_")
    return f"{finding.id}-docstring-{sanitized_path}-{sanitized_symbol}"


__all__ = ["plan_docstring_fix", "DOCSTRING_CONSTRAINTS"]
