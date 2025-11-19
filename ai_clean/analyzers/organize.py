"""Organize-seed analyzer to suggest small file grouping candidates."""

from __future__ import annotations

import ast
import os
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Iterable, List, Sequence, Tuple

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
MIN_GROUP_SIZE = 2
MAX_GROUP_SIZE = 5


def analyze_organize(
    root: Path | str,
    *,
    skip_dirs: Sequence[str] = DEFAULT_SKIP_DIRS,
    min_group_size: int = MIN_GROUP_SIZE,
    max_group_size: int = MAX_GROUP_SIZE,
) -> List[Finding]:
    """Suggest organize_candidate findings based on simple topic grouping."""
    root = Path(root)
    groups: DefaultDict[str, List[Path]] = defaultdict(list)

    for file_path in _iter_files(root, skip_dirs):
        topic = _infer_topic(file_path)
        if topic:
            groups[topic].append(file_path)

    findings: List[Finding] = []
    for topic, files in groups.items():
        if not (min_group_size <= len(files) <= max_group_size):
            continue
        # Propose moving into a folder named after the topic.
        first_file = files[0]
        dest_folder = first_file.parent / topic if topic else first_file.parent
        locations = [
            FindingLocation(path=str(f.relative_to(root)), start_line=1, end_line=1)
            for f in files
        ]
        finding_id = f"organize:{topic}:{len(findings)}"
        description = (
            f"Organize {len(files)} file(s) into "
            f"'{dest_folder.as_posix()}/' based on topic '{topic or 'general'}'."
        )
        findings.append(
            Finding(
                id=finding_id,
                category="organize_candidate",
                description=description,
                locations=locations,
                metadata={
                    "topic": topic,
                    "destination": dest_folder.as_posix() + "/",
                    "files": [loc.path for loc in locations],
                },
            )
        )

    return findings


def _iter_files(root: Path, skip_dirs: Sequence[str]) -> Iterable[Path]:
    skip_set = set(skip_dirs)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_set and not _is_env_dir(d)]
        for filename in filenames:
            if filename.endswith(".py"):
                yield Path(dirpath) / filename


def _is_env_dir(name: str) -> bool:
    lower = name.lower()
    return lower.startswith(".venv") or lower in {"venv", "env"}


def _infer_topic(path: Path) -> str:
    # Use filename stem tokens, top imports, or module docstring as signals.
    stem_tokens = [tok for tok in path.stem.replace("_", "-").split("-") if tok]
    topic = stem_tokens[0] if stem_tokens else ""

    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return topic

    imports = _collect_top_imports(tree)
    if imports:
        topic = topic or imports[0]

    doc = ast.get_docstring(tree, clean=True)
    if doc:
        words = doc.split()
        if words:
            first_word = words[0].strip(".,:")
            if first_word:
                topic = topic or first_word.lower()

    return topic


def _collect_top_imports(tree: ast.AST) -> List[str]:
    top_imports: List[str] = []
    for node in tree.body if hasattr(tree, "body") else []:
        if isinstance(node, ast.Import) and node.names:
            top_imports.append(node.names[0].name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            top_imports.append(node.module.split(".")[0])
    return top_imports
