"""Structure analyzer for large files and long functions."""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from ai_clean.models import Finding, FindingLocation

DEFAULT_LARGE_FILE_THRESHOLD = 400
DEFAULT_LONG_FUNCTION_THRESHOLD = 60
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


def analyze_structure(
    root: Path | str,
    *,
    large_file_threshold: int = DEFAULT_LARGE_FILE_THRESHOLD,
    long_function_threshold: int = DEFAULT_LONG_FUNCTION_THRESHOLD,
    skip_dirs: Sequence[str] = DEFAULT_SKIP_DIRS,
) -> List[Finding]:
    """Analyze a repository for large files and long functions."""
    root = Path(root)
    findings: List[Finding] = []

    for file_path in _iter_python_files(root, skip_dirs):
        rel_path = file_path.relative_to(root).as_posix()
        lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        file_line_count = len(lines)

        if file_line_count >= large_file_threshold:
            findings.append(
                Finding(
                    id=f"{rel_path}:large_file",
                    category="large_file",
                    description=(
                        f"File has {file_line_count} lines "
                        f"(threshold {large_file_threshold})."
                    ),
                    locations=[
                        FindingLocation(
                            path=rel_path, start_line=1, end_line=file_line_count
                        )
                    ],
                    metadata={"line_count": file_line_count},
                )
            )

        # Parse functions and measure spans.
        for func_name, start, end in _iter_function_spans(file_path):
            span_len = end - start + 1
            if span_len >= long_function_threshold:
                findings.append(
                    Finding(
                        id=f"{rel_path}:{func_name}:{start}",
                        category="long_function",
                        description=(
                            f"Function '{func_name}' spans {span_len} lines "
                            f"(threshold {long_function_threshold})."
                        ),
                        locations=[
                            FindingLocation(
                                path=rel_path, start_line=start, end_line=end
                            )
                        ],
                        metadata={
                            "function": func_name,
                            "line_span": span_len,
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


def _iter_function_spans(file_path: Path) -> Iterable[Tuple[str, int, int]]:
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                yield node.name, int(node.lineno), int(node.end_lineno)
