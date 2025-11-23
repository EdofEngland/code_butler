"""Organize analyzer that suggests grouping related files.

The analyzer is intentionally conservative: it only suggests a grouping when
multiple files share strong, unambiguous signals (filename tokens, shared
imports, or module docstring keywords). Private files, vendor/test directories,
and ambiguous topics are skipped to avoid noisy findings.
"""

from __future__ import annotations

import ast
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ai_clean.config import OrganizeAnalyzerConfig
from ai_clean.models import Finding, FindingLocation

_STOPWORDS = {
    "",
    "the",
    "and",
    "for",
    "with",
    "test",
    "tests",
    "init",
    "module",
    "file",
    "main",
    "common",
    "utils",
    "utility",
}
_STABLE_DIRECTORIES = {"tests", "migrations"}
_TOKEN_PATTERN = re.compile(r"[^a-zA-Z0-9]+")


@dataclass(frozen=True)
class _FileEntry:
    absolute_path: Path
    relative_path: Path


def propose_organize_groups(
    root: Path, settings: OrganizeAnalyzerConfig
) -> list[Finding]:
    """Emit organize candidates based on shared topics."""

    entries = _iter_python_files(root, settings.ignore_dirs)
    topic_members: dict[str, list[Path]] = defaultdict(list)
    for entry in entries:
        topic = _infer_topic(entry.absolute_path, entry.relative_path)
        if topic is None:
            continue
        topic_members[topic].append(entry.relative_path)

    for members in topic_members.values():
        members.sort(key=lambda path: path.as_posix())

    candidates = [
        (topic, members)
        for topic, members in topic_members.items()
        if settings.min_group_size <= len(members) <= settings.max_group_size
    ]
    candidates.sort(key=lambda item: (-len(item[1]), item[0]))

    claimed: set[Path] = set()
    findings: list[Finding] = []
    for index, (topic, members) in enumerate(candidates, start=1):
        available = [member for member in members if member not in claimed]
        if len(available) < settings.min_group_size:
            continue
        available = available[: settings.max_group_size]
        for member in available:
            claimed.add(member)

        finding_id = f"organize-{topic}-{index:02d}"
        description = f'Consider regrouping {len(available)} files under "{topic}/"'
        locations = [
            FindingLocation(path=member, start_line=1, end_line=1)
            for member in available
        ]
        metadata = {
            "topic": topic,
            "members": [member.as_posix() for member in available],
            "files": [member.as_posix() for member in available],
        }
        findings.append(
            Finding(
                id=finding_id,
                category="organize_candidate",
                description=description,
                locations=locations,
                metadata=metadata,
            )
        )
        if len(findings) >= settings.max_groups:
            break

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
        if relative.parts and relative.parts[0] in _STABLE_DIRECTORIES:
            continue
        entries.append(_FileEntry(absolute_path=candidate, relative_path=relative))

    entries.sort(key=lambda entry: entry.relative_path.as_posix())
    return entries


def _infer_topic(absolute_path: Path, relative_path: Path) -> str | None:
    try:
        source = absolute_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:  # pragma: no cover - filesystem issues
        return None

    try:
        tree = ast.parse(source, filename=str(relative_path), type_comments=True)
    except SyntaxError:
        return None

    filename_tokens = _tokenize(relative_path.stem)
    import_tokens = _collect_import_tokens(tree)
    doc_tokens = _tokenize(ast.get_docstring(tree, clean=True) or "")

    signals = [
        token_set
        for token_set in (filename_tokens, import_tokens, doc_tokens)
        if token_set
    ]
    if not signals:
        return None

    scores: Counter[str] = Counter()
    for token_set in signals:
        for token in token_set:
            scores[token] += 1

    max_score = max(scores.values())
    best_tokens = sorted(token for token, score in scores.items() if score == max_score)
    if len(best_tokens) != 1:
        return None
    return best_tokens[0]


def _collect_import_tokens(tree: ast.AST) -> set[str]:
    if not isinstance(tree, ast.Module):
        return set()

    tokens: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                first = alias.name.split(".")[0]
                normalized = _normalize_token(first)
                if normalized:
                    tokens.add(normalized)
        elif isinstance(node, ast.ImportFrom):
            module = node.module.split(".")[0] if node.module else None
            if module:
                normalized = _normalize_token(module)
                if normalized:
                    tokens.add(normalized)
    return {token for token in tokens if token not in _STOPWORDS}


def _tokenize(text: str) -> set[str]:
    if not text:
        return set()
    raw_tokens = _TOKEN_PATTERN.split(text.lower())
    tokens = {token for token in raw_tokens if token and token not in _STOPWORDS}
    return tokens


def _normalize_token(token: str) -> str:
    cleaned = _TOKEN_PATTERN.sub("", token.lower())
    return cleaned
