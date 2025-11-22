"""Docstring analyzer used by `/annotate`.

This module intentionally keeps the implementation simple: it skips directories
listed in the analyzer config, ignores private symbols (names starting with `_`),
and only performs presence/length/marker heuristics. Content quality/stylistic
checks are out of scope for this phase.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from typing import Iterable

from ai_clean.config import DocstringAnalyzerConfig
from ai_clean.models import Finding, FindingLocation


@dataclass(frozen=True)
class _FileEntry:
    absolute_path: Path
    relative_path: Path


@dataclass(frozen=True)
class _SymbolRecord:
    qualified_name: str
    symbol_type: str
    start_line: int
    end_line: int
    lines_of_code: int
    docstring: str | None


def find_docstring_gaps(root: Path, settings: DocstringAnalyzerConfig) -> list[Finding]:
    """Return docstring-related findings for the provided root."""

    file_entries = _iter_python_files(root, settings.ignore_dirs)
    findings: list[Finding] = []
    for entry in file_entries:
        source = entry.absolute_path.read_text(encoding="utf-8", errors="ignore")
        lines = source.splitlines() or [""]
        try:
            tree = ast.parse(
                source, filename=str(entry.relative_path), type_comments=True
            )
        except SyntaxError:
            continue

        module_doc = ast.get_docstring(tree, clean=True)
        if module_doc is None or not module_doc.strip():
            findings.append(
                _build_finding(
                    category="missing_docstring",
                    relative_path=entry.relative_path,
                    qualified_name="<module>",
                    description=(
                        "Module "
                        f"{entry.relative_path.as_posix()} is missing a docstring"
                    ),
                    start_line=1,
                    end_line=1,
                    symbol_type="module",
                    docstring_preview="",
                    lines_of_code=len(lines),
                )
            )

        collector = _DocstringCollector()
        collector.visit(tree)
        records = sorted(
            collector.results,
            key=lambda record: (record.start_line, record.qualified_name),
        )

        for record in records:
            if (
                settings.important_symbols_only
                and record.lines_of_code < settings.min_symbol_lines
            ):
                continue
            classification = _classify_docstring(record.docstring, settings)
            if classification is None:
                continue
            category, reason = classification
            preview = _preview_docstring(record.docstring)
            description = (
                f"{record.symbol_type.capitalize()} {record.qualified_name} in "
                f"{entry.relative_path.as_posix()} {reason}"
            )
            findings.append(
                _build_finding(
                    category=category,
                    relative_path=entry.relative_path,
                    qualified_name=record.qualified_name,
                    description=description,
                    start_line=record.start_line,
                    end_line=record.end_line,
                    symbol_type=record.symbol_type,
                    docstring_preview=preview,
                    lines_of_code=record.lines_of_code,
                )
            )

    return findings


def _iter_python_files(root: Path, ignore_dirs: Iterable[str]) -> list[_FileEntry]:
    if not root.exists():
        return []

    ignored = set(ignore_dirs)
    entries: list[_FileEntry] = []
    for candidate in root.rglob("*.py"):
        try:
            relative = candidate.relative_to(root)
        except ValueError:  # pragma: no cover - defensive
            continue
        if any(part in ignored for part in relative.parts[:-1]):
            continue
        entries.append(_FileEntry(absolute_path=candidate, relative_path=relative))

    entries.sort(key=lambda entry: entry.relative_path.as_posix())
    return entries


class _DocstringCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self._stack: list[str] = []
        self.results: list[_SymbolRecord] = []

    def visit_ClassDef(
        self, node: ast.ClassDef
    ) -> None:  # pragma: no cover - exercised via analyzer tests
        self._record_symbol(node, node.name, "class")
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def visit_FunctionDef(
        self, node: ast.FunctionDef
    ) -> None:  # pragma: no cover - exercised via analyzer tests
        self._record_symbol(node, node.name, "function")
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def visit_AsyncFunctionDef(
        self, node: ast.AsyncFunctionDef
    ) -> None:  # pragma: no cover - exercised via analyzer tests
        self._record_symbol(node, node.name, "async_function")
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def _record_symbol(self, node: ast.AST, name: str, symbol_type: str) -> None:
        qualified_parts = self._stack + [name]
        if any(part.startswith("_") for part in qualified_parts):
            return
        start = getattr(node, "lineno", None)
        if start is None:
            return
        end = getattr(node, "end_lineno", None) or start
        lines_of_code = end - start + 1
        docstring = ast.get_docstring(node, clean=True)
        self.results.append(
            _SymbolRecord(
                qualified_name=".".join(qualified_parts),
                symbol_type=symbol_type,
                start_line=start,
                end_line=end,
                lines_of_code=lines_of_code,
                docstring=docstring,
            )
        )


def _classify_docstring(
    docstring: str | None, settings: DocstringAnalyzerConfig
) -> tuple[str, str] | None:
    if docstring is None:
        return ("missing_docstring", "is missing a docstring")
    normalized = docstring.strip()
    if not normalized:
        return ("missing_docstring", "has an empty docstring")

    if len(normalized) < settings.min_docstring_length:
        return (
            "weak_docstring",
            (
                "has a short docstring "
                f"({len(normalized)} chars < {settings.min_docstring_length})"
            ),
        )

    lowered = normalized.lower()
    if any(marker in lowered for marker in settings.weak_markers):
        return ("weak_docstring", "contains a weak docstring marker")

    return None


def _preview_docstring(docstring: str | None) -> str:
    if not docstring:
        return ""
    first_line = docstring.strip().splitlines()[0].strip()
    if len(first_line) > 80:
        return f"{first_line[:77]}..."
    return first_line


def _build_finding(
    *,
    category: str,
    relative_path: Path,
    qualified_name: str,
    description: str,
    start_line: int,
    end_line: int,
    symbol_type: str,
    docstring_preview: str,
    lines_of_code: int,
) -> Finding:
    identifier = _doc_identifier(category, relative_path, qualified_name)
    return Finding(
        id=identifier,
        category=category,
        description=description,
        locations=[
            FindingLocation(
                path=relative_path,
                start_line=start_line,
                end_line=end_line,
            )
        ],
        metadata={
            "symbol_type": symbol_type,
            "docstring_preview": docstring_preview,
            "lines_of_code": lines_of_code,
            "qualified_name": qualified_name,
        },
    )


def _doc_identifier(category: str, relative_path: Path, qualified_name: str) -> str:
    token = f"{relative_path.as_posix()}:{qualified_name}"
    digest = sha1(token.encode("utf-8")).hexdigest()[:8]
    return f"doc-{category}-{digest}"
