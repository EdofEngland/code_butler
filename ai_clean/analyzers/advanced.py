"""Codex-powered advanced cleanup analyzer."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, List, Sequence

from ai_clean.models import Finding, FindingLocation

DEFAULT_MAX_FILES = 5
DEFAULT_MAX_SNIPPET_LINES = 80
DEFAULT_MAX_SUGGESTIONS = 5
DEFAULT_FINDINGS_SUMMARY = 6
DEFAULT_SKIP_DIRS: tuple[str, ...] = (
    ".venv",
    "venv",
    "env",
    ".ai-clean",
    "build",
    "dist",
    "site-packages",
    "__pycache__",
)

CodexCompletion = Callable[[str], Any]


@dataclass
class ContextSnippet:
    """Represents a curated file snippet shared with the Codex prompt."""

    path: str
    start_line: int
    end_line: int
    content: str


def analyze_advanced_cleanups(
    root: Path | str,
    findings_summary: Sequence[Finding] | Sequence[dict[str, Any]] | None = None,
    *,
    codex_completion: CodexCompletion | None = None,
    max_files: int = DEFAULT_MAX_FILES,
    max_snippet_lines: int = DEFAULT_MAX_SNIPPET_LINES,
    max_suggestions: int = DEFAULT_MAX_SUGGESTIONS,
    skip_dirs: Sequence[str] = DEFAULT_SKIP_DIRS,
) -> List[Finding]:
    """Request Codex suggestions and convert them into advanced_cleanup findings."""
    root_path = Path(root)
    snippets = _curate_snippets(
        root_path,
        findings_summary=findings_summary,
        max_files=max_files,
        max_snippet_lines=max_snippet_lines,
        skip_dirs=skip_dirs,
    )
    prompt = _build_prompt(
        snippets=snippets,
        findings_summary=findings_summary,
        max_suggestions=max_suggestions,
    )

    if codex_completion is None:
        return []

    raw_response = codex_completion(prompt)
    suggestions = _parse_suggestions(raw_response, max_suggestions)
    findings: List[Finding] = []
    for index, suggestion in enumerate(suggestions, start=1):
        finding = _suggestion_to_finding(
            suggestion,
            root_path=root_path,
            fallback_index=index,
        )
        if finding:
            findings.append(finding)
    return findings


def _curate_snippets(
    root: Path,
    *,
    findings_summary: Sequence[Finding] | Sequence[dict[str, Any]] | None,
    max_files: int,
    max_snippet_lines: int,
    skip_dirs: Sequence[str],
) -> List[ContextSnippet]:
    """Select snippets informed by current findings; fall back to default files."""
    snippets: List[ContextSnippet] = []
    seen_paths: set[str] = set()

    def add_snippet(rel_path: str, preferred_start: int | None = None) -> None:
        if rel_path in seen_paths or len(snippets) >= max_files:
            return
        snippet = _load_snippet(
            root / rel_path,
            rel_path,
            preferred_start=preferred_start,
            max_lines=max_snippet_lines,
        )
        if snippet:
            snippets.append(snippet)
            seen_paths.add(rel_path)

    for loc in _iter_summary_locations(findings_summary):
        add_snippet(loc.path, preferred_start=loc.start_line)
        if len(snippets) >= max_files:
            break

    if len(snippets) >= max_files:
        return snippets

    extra_files = _iter_python_files(root, skip_dirs)
    for file_path in extra_files:
        rel_path = file_path.relative_to(root).as_posix()
        add_snippet(rel_path)
        if len(snippets) >= max_files:
            break

    return snippets


def _load_snippet(
    file_path: Path,
    rel_path: str,
    *,
    preferred_start: int | None,
    max_lines: int,
) -> ContextSnippet | None:
    try:
        lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return None

    if not lines:
        return None

    start_index = max(0, (preferred_start or 1) - 1)
    start_index = min(start_index, len(lines) - 1)
    end_index = min(len(lines), start_index + max_lines)
    snippet_lines = lines[start_index:end_index]
    if not snippet_lines:
        return None

    return ContextSnippet(
        path=rel_path,
        start_line=start_index + 1,
        end_line=end_index,
        content="\n".join(snippet_lines),
    )


def _iter_summary_locations(
    findings_summary: Sequence[Finding] | Sequence[dict[str, Any]] | None,
) -> Iterable[FindingLocation]:
    if not findings_summary:
        return ()

    def _convert(loc: Any) -> FindingLocation | None:
        try:
            return FindingLocation(
                path=str(loc["path"]),
                start_line=int(loc.get("start_line", 1)),
                end_line=int(loc.get("end_line", loc.get("start_line", 1))),
            )
        except Exception:
            return None

    collected: List[FindingLocation] = []
    for item in findings_summary:
        if isinstance(item, Finding):
            collected.extend(item.locations)
        elif isinstance(item, dict):
            locations = item.get("locations", []) or []
            for raw_location in locations:
                converted = _convert(raw_location)
                if converted:
                    collected.append(converted)
    return collected


def _iter_python_files(root: Path, skip_dirs: Sequence[str]) -> Iterable[Path]:
    skip_set = {name.lower() for name in skip_dirs}
    for dirpath, dirnames, filenames in os.walk(root):
        rel_parts = Path(dirpath).relative_to(root).parts
        dirnames[:] = [
            name
            for name in dirnames
            if name.lower() not in skip_set and not name.startswith(".")
        ]
        if any(part in (".git", "__pycache__") for part in rel_parts):
            continue
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            file_path = Path(dirpath) / filename
            yield file_path


def _build_prompt(
    snippets: Sequence[ContextSnippet],
    findings_summary: Sequence[Finding] | Sequence[dict[str, Any]] | None,
    *,
    max_suggestions: int,
) -> str:
    summary_lines = _format_findings_summary(findings_summary)
    snippet_sections = [
        "\n".join(
            [
                f"File: {snippet.path} (lines {snippet.start_line}-{snippet.end_line})",
                "```python",
                snippet.content,
                "```",
            ]
        )
        for snippet in snippets
    ]

    instructions = [
        "You are Codex reviewing a Python repository for tiny cleanups.",
        (
            "Focus on localized improvements: remove dead code, tidy imports, split "
            "overly nested logic,"
        ),
        (
            "or rename temporary variables for clarity. Avoid multi-file rewrites, "
            "framework changes,"
        ),
        "large renames, or architectural redesigns.",
        f"Return at most {max_suggestions} suggestions.",
        (
            "Each suggestion must reference a specific path and line span from the "
            "provided context."
        ),
        (
            "Respond with compact JSON: "
            '{"suggestions":[{"id":"str","title":"str","description":"str","path":"relative.py",'
            '"start_line":10,"end_line":12,"metadata":{"rationale":"..."}}]}'
        ),
    ]

    parts = [
        "\n".join(instructions),
        "Current findings summary:",
        summary_lines or "- None shared; look for obvious small wins.",
        "Context snippets:",
        (
            "\n\n".join(snippet_sections)
            if snippet_sections
            else "- No snippets available."
        ),
    ]

    return "\n\n".join(parts)


def _format_findings_summary(
    findings_summary: Sequence[Finding] | Sequence[dict[str, Any]] | None,
) -> str:
    if not findings_summary:
        return ""

    lines: List[str] = []
    for idx, finding in enumerate(findings_summary[:DEFAULT_FINDINGS_SUMMARY], start=1):
        if isinstance(finding, Finding):
            location = finding.locations[0] if finding.locations else None
            loc_str = (
                f"{location.path}:{location.start_line}-{location.end_line}"
                if location
                else "unknown"
            )
            lines.append(
                f"{idx}. [{finding.category}] {finding.description} ({loc_str})"
            )
        elif isinstance(finding, dict):
            category = finding.get("category", "unknown")
            description = finding.get("description", "").strip() or "No description"
            locations = finding.get("locations", [])
            if locations:
                first = locations[0]
                loc_str = (
                    f"{first.get('path')}:{first.get('start_line')}-"
                    f"{first.get('end_line')}"
                )
            else:
                loc_str = "unknown"
            lines.append(f"{idx}. [{category}] {description} ({loc_str})")
    return "\n".join(lines)


def _parse_suggestions(raw_response: Any, max_suggestions: int) -> List[dict[str, Any]]:
    if raw_response in (None, "", []):
        return []

    parsed: Any = raw_response
    if isinstance(raw_response, str):
        raw_response = raw_response.strip()
        if not raw_response:
            return []
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            return []

    if isinstance(parsed, dict):
        suggestions = parsed.get("suggestions") or parsed.get("ideas") or []
    elif isinstance(parsed, list):
        suggestions = parsed
    else:
        return []

    result: List[dict[str, Any]] = []
    for suggestion in suggestions:
        if isinstance(suggestion, dict):
            result.append(suggestion)
        if len(result) >= max_suggestions:
            break
    return result


def _suggestion_to_finding(
    suggestion: dict[str, Any],
    *,
    root_path: Path,
    fallback_index: int,
) -> Finding | None:
    description = suggestion.get("description") or suggestion.get("title")
    path = suggestion.get("path") or suggestion.get("file")
    start_line = suggestion.get("start_line") or suggestion.get("line")
    end_line = suggestion.get("end_line") or start_line
    if not description or not path or not start_line or not end_line:
        return None

    try:
        start_line_int = int(start_line)
        end_line_int = int(end_line)
    except (TypeError, ValueError):
        return None

    rel_path = _normalize_relative_path(path, root_path)
    metadata_raw = suggestion.get("metadata", {})
    metadata = dict(metadata_raw) if isinstance(metadata_raw, dict) else {}
    metadata.setdefault("title", suggestion.get("title", "Advanced cleanup"))
    metadata["advisory"] = True
    metadata.setdefault("source", "advanced_analyzer")

    finding_id = (
        suggestion.get("id")
        or f"advanced_cleanup:{rel_path}:{start_line_int}:{fallback_index}"
    )

    return Finding(
        id=str(finding_id),
        category="advanced_cleanup",
        description=str(description),
        locations=[
            FindingLocation(
                path=rel_path, start_line=start_line_int, end_line=end_line_int
            )
        ],
        metadata=metadata,
    )


def _normalize_relative_path(path_value: Any, root_path: Path) -> str:
    try:
        path_obj = Path(str(path_value))
    except Exception:
        return str(path_value)

    if not path_obj.is_absolute():
        return path_obj.as_posix()

    try:
        return path_obj.relative_to(root_path).as_posix()
    except ValueError:
        return path_obj.name


__all__ = ["analyze_advanced_cleanups"]
