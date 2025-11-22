"""Duplicate code analyzer used by `/analyze`."""

from __future__ import annotations

import textwrap
from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from typing import Iterable, Sequence

from ai_clean.config import DuplicateAnalyzerConfig
from ai_clean.models import Finding, FindingLocation


@dataclass(frozen=True)
class _Window:
    normalized_text: str
    relative_path: Path
    start_line: int
    end_line: int


def find_duplicate_blocks(
    root: Path, settings: DuplicateAnalyzerConfig
) -> list[Finding]:
    """Scan ``root`` for duplicate windows of Python code."""

    file_entries = _iter_python_files(root, settings.ignore_dirs)
    window_records: list[_Window] = []
    for absolute_path, relative_path in file_entries:
        window_records.extend(
            _build_windows(absolute_path, relative_path, settings.window_size)
        )

    window_records.sort(
        key=lambda item: (
            item.normalized_text,
            item.relative_path.as_posix(),
            item.start_line,
        )
    )

    grouped: dict[str, list[_Window]] = defaultdict(list)
    for window in window_records:
        grouped[window.normalized_text].append(window)

    findings: list[Finding] = []
    for normalized_text, windows in grouped.items():
        if len(windows) < settings.min_occurrences:
            continue

        sorted_windows = sorted(
            windows,
            key=lambda entry: (
                entry.relative_path.as_posix(),
                entry.start_line,
            ),
        )
        preview = _preview_line(normalized_text)
        finding_id = f"dup-{sha1(normalized_text.encode('utf-8')).hexdigest()[:8]}"
        relative_paths = [entry.relative_path.as_posix() for entry in sorted_windows]
        locations = [
            FindingLocation(
                path=entry.relative_path,
                start_line=entry.start_line,
                end_line=entry.end_line,
            )
            for entry in sorted_windows
        ]
        description = (
            f"Found {len(sorted_windows)} duplicate windows starting with '{preview}'"
        )
        metadata = {
            "window_size": settings.window_size,
            "normalized_preview": normalized_text,
            "relative_paths": relative_paths,
        }
        findings.append(
            Finding(
                id=finding_id,
                category="duplicate_block",
                description=description,
                locations=locations,
                metadata=metadata,
            )
        )

    findings.sort(key=lambda finding: (finding.category, finding.id))
    return findings


def _iter_python_files(
    root: Path, ignore_dirs: Iterable[str]
) -> list[tuple[Path, Path]]:
    if not root.exists():
        return []

    ignored = {name for name in ignore_dirs}
    discovered: list[tuple[Path, Path]] = []
    for candidate in root.rglob("*.py"):
        try:
            relative = candidate.relative_to(root)
        except ValueError:  # pragma: no cover - defensive
            continue
        if any(part in ignored for part in relative.parts[:-1]):
            continue
        discovered.append((candidate, relative))

    discovered.sort(key=lambda item: item[1].as_posix())
    return discovered


def _build_windows(path: Path, relative: Path, window_size: int) -> list[_Window]:
    contents = path.read_text(encoding="utf-8", errors="ignore")
    lines = contents.splitlines()
    if window_size <= 0 or len(lines) < window_size:
        return []

    windows: list[_Window] = []
    for start_index in range(0, len(lines) - window_size + 1):
        block = lines[start_index : start_index + window_size]
        if _is_comment_only(block):
            continue
        normalized = textwrap.dedent("\n".join(block)).rstrip()
        if not normalized.strip():
            continue
        windows.append(
            _Window(
                normalized_text=normalized,
                relative_path=relative,
                start_line=start_index + 1,
                end_line=start_index + window_size,
            )
        )
    return windows


def _is_comment_only(lines: Sequence[str]) -> bool:
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith("#"):
            return False
    return True


def _preview_line(normalized_text: str) -> str:
    for line in normalized_text.splitlines():
        candidate = line.strip()
        if candidate:
            preview = candidate
            break
    else:
        preview = normalized_text.strip()

    if not preview:
        preview = "<blank>"
    if len(preview) > 60:
        preview = f"{preview[:57]}..."
    return preview
