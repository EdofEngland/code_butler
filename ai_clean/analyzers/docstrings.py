"""Docstring analyzer for missing or weak documentation."""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from ai_clean.models import Finding, FindingLocation

DEFAULT_SKIP_DIRS: Tuple[str, ...] = (
    ".venv",
    "venv",
    "env",
    ".ai-clean",
    "build",
    "dist",
    "site-packages",
    "__pycache__",
)
DEFAULT_MIN_SYMBOL_LINES = 0
TRIVIAL_DOCSTRING_LENGTH = 10


@dataclass
class SymbolDocInfo:
    name: str
    kind: str  # "function" or "class"
    start: int
    end: int
    docstring: str | None


def analyze_docstrings(
    root: Path | str,
    *,
    min_symbol_lines: int = DEFAULT_MIN_SYMBOL_LINES,
    skip_dirs: Sequence[str] = DEFAULT_SKIP_DIRS,
) -> List[Finding]:
    """Analyze Python files for missing or weak docstrings."""
    root = Path(root)
    findings: List[Finding] = []

    for file_path in _iter_python_files(root, skip_dirs):
        rel_path = file_path.relative_to(root).as_posix()
        source = file_path.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        module_doc = ast.get_docstring(tree, clean=True)
        if module_doc is None or module_doc.strip() == "":
            findings.append(
                Finding(
                    id=f"{rel_path}:module-doc",
                    category="missing_docstring",
                    description="Module is missing a docstring.",
                    locations=[
                        FindingLocation(path=rel_path, start_line=1, end_line=1)
                    ],
                    metadata={"symbol": rel_path, "kind": "module"},
                )
            )

        for symbol in _iter_public_symbols(tree):
            if (
                min_symbol_lines > 0
                and (symbol.end - symbol.start + 1) < min_symbol_lines
            ):
                continue

            doc = symbol.docstring.strip() if symbol.docstring else ""
            if not doc:
                category = "missing_docstring"
                description = (
                    f"{symbol.kind.title()} '{symbol.name}' is missing a docstring."
                )
            elif len(doc) < TRIVIAL_DOCSTRING_LENGTH:
                category = "weak_docstring"
                description = (
                    f"{symbol.kind.title()} '{symbol.name}' has a trivial docstring."
                )
            else:
                continue

            findings.append(
                Finding(
                    id=f"{rel_path}:{symbol.kind}:{symbol.name}:{symbol.start}",
                    category=category,
                    description=description,
                    locations=[
                        FindingLocation(
                            path=rel_path, start_line=symbol.start, end_line=symbol.end
                        )
                    ],
                    metadata={
                        "symbol": symbol.name,
                        "kind": symbol.kind,
                    },
                )
            )

    return findings


def _iter_python_files(root: Path, skip_dirs: Sequence[str]) -> Iterable[Path]:
    skip_set = set(skip_dirs)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_set and not _is_env_dir(d)]
        for filename in filenames:
            if filename.endswith(".py"):
                yield Path(dirpath) / filename


def _is_env_dir(name: str) -> bool:
    lower = name.lower()
    return lower.startswith(".venv") or lower in {"venv", "env"}


def _iter_public_symbols(tree: ast.AST) -> Iterable[SymbolDocInfo]:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            kind = "function"
        elif isinstance(node, ast.ClassDef):
            name = node.name
            kind = "class"
        else:
            continue

        if name.startswith("_"):
            continue

        start = getattr(node, "lineno", 1)
        end = getattr(node, "end_lineno", start)
        docstring = ast.get_docstring(node, clean=True)
        yield SymbolDocInfo(
            name=name, kind=kind, start=start, end=end, docstring=docstring
        )
