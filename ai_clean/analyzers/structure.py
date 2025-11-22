"""Structure analyzer detecting large files and long functions."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from typing import Iterable

from ai_clean.config import StructureAnalyzerConfig
from ai_clean.models import Finding, FindingLocation


@dataclass(frozen=True)
class _FileEntry:
    absolute_path: Path
    relative_path: Path


@dataclass(frozen=True)
class _LargeFileRecord:
    relative_path: Path
    line_count: int


@dataclass(frozen=True)
class _LongFunctionRecord:
    relative_path: Path
    qualified_name: str
    start_line: int
    end_line: int
    line_count: int


def find_structure_issues(
    root: Path, settings: StructureAnalyzerConfig
) -> list[Finding]:
    """Return structure findings for the provided ``root`` path."""

    file_entries = _iter_python_files(root, settings.ignore_dirs)
    if not file_entries:
        return []

    large_files = _iter_large_files(
        file_entries, max_file_lines=settings.max_file_lines
    )
    long_functions = _iter_long_functions(
        file_entries, max_function_lines=settings.max_function_lines
    )

    findings: list[Finding] = []
    for record in large_files:
        identifier = _hash_id("large-file", record.relative_path.as_posix())
        description = (
            f"File {record.relative_path.as_posix()} has {record.line_count} lines (> "
            f"{settings.max_file_lines})"
        )
        finding = Finding(
            id=identifier,
            category="large_file",
            description=description,
            locations=[
                FindingLocation(
                    path=record.relative_path,
                    start_line=1,
                    end_line=record.line_count,
                )
            ],
            metadata={
                "line_count": record.line_count,
                "threshold": settings.max_file_lines,
            },
        )
        findings.append(finding)

    for record in long_functions:
        source_id = f"{record.relative_path.as_posix()}::{record.qualified_name}"
        identifier = _hash_id("long-func", source_id)
        description = (
            f"Function {record.qualified_name} has {record.line_count} lines (> "
            f"{settings.max_function_lines})"
        )
        finding = Finding(
            id=identifier,
            category="long_function",
            description=description,
            locations=[
                FindingLocation(
                    path=record.relative_path,
                    start_line=record.start_line,
                    end_line=record.end_line,
                )
            ],
            metadata={
                "line_count": record.line_count,
                "threshold": settings.max_function_lines,
                "qualified_name": record.qualified_name,
            },
        )
        findings.append(finding)

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


def _iter_large_files(
    file_entries: Iterable[_FileEntry], *, max_file_lines: int
) -> list[_LargeFileRecord]:
    records: list[_LargeFileRecord] = []
    for entry in file_entries:
        contents = entry.absolute_path.read_text(encoding="utf-8", errors="ignore")
        line_count = len(contents.splitlines())
        if line_count > max_file_lines:
            records.append(
                _LargeFileRecord(
                    relative_path=entry.relative_path, line_count=line_count
                )
            )

    records.sort(key=lambda record: record.relative_path.as_posix())
    return records


def _iter_long_functions(
    file_entries: Iterable[_FileEntry], *, max_function_lines: int
) -> list[_LongFunctionRecord]:
    records: list[_LongFunctionRecord] = []
    for entry in file_entries:
        source = entry.absolute_path.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(
                source, filename=str(entry.relative_path), type_comments=True
            )
        except SyntaxError:
            continue
        collector = _FunctionCollector(entry.relative_path, max_function_lines)
        collector.visit(tree)
        records.extend(collector.results)

    records.sort(
        key=lambda record: (
            record.relative_path.as_posix(),
            record.start_line,
            record.qualified_name,
        )
    )
    return records


class _FunctionCollector(ast.NodeVisitor):
    def __init__(self, relative_path: Path, max_length: int) -> None:
        self._relative_path = relative_path
        self._max_length = max_length
        self._stack: list[str] = []
        self.results: list[_LongFunctionRecord] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._maybe_record(node, node.name)
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._maybe_record(node, node.name)
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def _maybe_record(self, node: ast.AST, name: str) -> None:
        start = getattr(node, "lineno", None)
        if start is None:
            return
        end = getattr(node, "end_lineno", None) or start
        length = end - start + 1
        if length <= self._max_length:
            return
        qualified_name = ".".join(self._stack + [name]) if self._stack else name
        self.results.append(
            _LongFunctionRecord(
                relative_path=self._relative_path,
                qualified_name=qualified_name,
                start_line=start,
                end_line=end,
                line_count=length,
            )
        )


def _hash_id(prefix: str, value: str) -> str:
    digest = sha1(value.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{digest}"
