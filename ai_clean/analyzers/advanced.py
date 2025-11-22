"""Codex-powered advanced cleanup analyzer."""

from __future__ import annotations

import json
import logging
from collections import Counter
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from typing import Iterable, Sequence

from ai_clean.config import AiCleanConfig
from ai_clean.interfaces import CodexPromptRunner, PromptAttachment
from ai_clean.models import Finding, FindingLocation

LOGGER = logging.getLogger(__name__)
_GUARDRAIL_SENTENCE = "Suggest small, local cleanup changes only; no API redesigns."
_DISALLOWED_CHANGE_TYPES = {
    "refactor_architecture",
    "refactor architecture",
    "rewrite_module",
    "rewrite module",
}
_MAX_SNIPPET_LINES = 40
_SNIPPET_CONTEXT = 3


@dataclass(frozen=True)
class _Candidate:
    path: Path
    content: str
    span: tuple[int, int] | None
    finding: Finding


@dataclass(frozen=True)
class _Suggestion:
    description: str
    path: Path
    start_line: int
    end_line: int
    change_type: str
    raw_payload: dict[str, object]


def collect_advanced_cleanup_ideas(
    root: Path,
    existing_findings: Sequence[Finding],
    config: AiCleanConfig,
    runner: CodexPromptRunner,
) -> list[Finding]:
    advanced_config = config.analyzers.advanced
    root = root.resolve()
    candidates = _select_candidate_files(
        root,
        existing_findings,
        advanced_config.max_files,
        advanced_config.ignore_dirs,
    )
    if not candidates:
        LOGGER.info("Advanced analyzer summary: selected_files=0 accepted=0 dropped=0")
        return []

    findings_summary = _summarize_findings(candidates)
    snippets_block = _render_snippets(candidates)
    prompt = advanced_config.prompt_template.format(
        findings=findings_summary,
        snippets=snippets_block,
    )
    if _GUARDRAIL_SENTENCE not in prompt:
        prompt = f"{_GUARDRAIL_SENTENCE}\n\n{prompt}"
    prompt_hash = sha1(prompt.encode("utf-8")).hexdigest()

    attachments = [
        PromptAttachment(
            path=(root / candidate.path).resolve(), content=candidate.content
        )
        for candidate in candidates
    ]

    raw_response = runner.run(prompt, attachments)
    suggestions = _decode_suggestions(raw_response)

    allowed_rel = {candidate.path.as_posix() for candidate in candidates}
    allowed_abs = {
        (root / candidate.path).resolve().as_posix() for candidate in candidates
    }

    findings: list[Finding] = []
    dropped: list[dict[str, str]] = []
    for suggestion_payload in suggestions:
        normalized = _normalize_suggestion(suggestion_payload)
        if normalized is None:
            dropped.append(
                {"reason": "invalid_format", "suggestion": str(suggestion_payload)}
            )
            continue

        path_str = normalized.path.as_posix()
        abs_path_str = (root / normalized.path).resolve().as_posix()
        if path_str not in allowed_rel and abs_path_str not in allowed_abs:
            dropped.append(
                {"reason": "path_not_selected", "suggestion": str(suggestion_payload)}
            )
            continue

        normalized_change_type = normalized.change_type.strip().lower()
        normalized_change_type_slug = normalized_change_type.replace(" ", "_")
        if (
            normalized_change_type in _DISALLOWED_CHANGE_TYPES
            or normalized_change_type_slug in _DISALLOWED_CHANGE_TYPES
        ):
            dropped.append(
                {
                    "reason": "disallowed_change_type",
                    "suggestion": str(suggestion_payload),
                }
            )
            continue

        if len(findings) >= advanced_config.max_suggestions:
            dropped.append(
                {"reason": "max_suggestions", "suggestion": str(suggestion_payload)}
            )
            continue

        finding_id = _build_finding_id(path_str, normalized.description)
        location = FindingLocation(
            path=normalized.path,
            start_line=normalized.start_line,
            end_line=normalized.end_line,
        )
        metadata = {
            "change_type": normalized.change_type,
            "codex_model": advanced_config.codex_model,
            "prompt_hash": prompt_hash,
            "raw_response": raw_response,
            "target_path": path_str,
            "start_line": normalized.start_line,
            "end_line": normalized.end_line,
            "codex_payload": normalized.raw_payload,
        }
        findings.append(
            Finding(
                id=finding_id,
                category="advanced_cleanup",
                description=normalized.description,
                locations=[location],
                metadata=metadata,
            )
        )

    summary_metadata = {
        "selected_files": len(candidates),
        "accepted_suggestions": len(findings),
        "dropped_suggestions": len(dropped),
        "dropped_reason_counts": (
            dict(Counter(entry["reason"] for entry in dropped)) if dropped else {}
        ),
    }
    if dropped:
        LOGGER.info(
            "Advanced analyzer summary: selected_files=%s accepted=%s dropped=%s",
            len(candidates),
            len(findings),
            len(dropped),
        )
    else:
        LOGGER.info(
            "Advanced analyzer summary: selected_files=%s accepted=%s dropped=0",
            len(candidates),
            len(findings),
        )

    if not findings:
        return []

    enriched: list[Finding] = []
    for finding in findings:
        metadata = dict(finding.metadata)
        metadata["analyzer_summary"] = summary_metadata
        if dropped:
            metadata["dropped_suggestions"] = dropped
        enriched.append(finding.model_copy(update={"metadata": metadata}))

    return enriched


def _select_candidate_files(
    root: Path,
    findings: Sequence[Finding],
    max_files: int,
    ignore_dirs: Iterable[str],
) -> list[_Candidate]:
    ignore_set = set(ignore_dirs)
    selected: list[_Candidate] = []
    seen: set[Path] = set()
    for finding in sorted(findings, key=lambda f: (f.category, f.id)):
        for location in finding.locations:
            rel_path = location.path
            if rel_path in seen:
                continue
            if _is_ignored(rel_path, ignore_set):
                continue
            abs_path = (root / rel_path).resolve()
            if not abs_path.exists() or not abs_path.is_file():
                continue
            span = _normalize_span(location.start_line, location.end_line)
            content = abs_path.read_text(encoding="utf-8", errors="ignore")
            selected.append(
                _Candidate(path=rel_path, content=content, span=span, finding=finding)
            )
            seen.add(rel_path)
            if len(selected) >= max_files:
                return selected
    return selected


def _summarize_findings(candidates: Sequence[_Candidate]) -> str:
    lines: list[str] = []
    for candidate in candidates:
        rel_path = candidate.path.as_posix()
        finding = candidate.finding
        if candidate.span:
            start, end = candidate.span
            lines.append(
                f"- {finding.category} {finding.id}: {finding.description} "
                f"({rel_path}:{start}-{end})"
            )
        else:
            lines.append(
                f"- {finding.category} {finding.id}: {finding.description} "
                f"({rel_path})"
            )
    return "\n".join(lines) if lines else "- No prior findings"


def _render_snippets(candidates: Sequence[_Candidate]) -> str:
    blocks: list[str] = []
    for candidate in candidates:
        rel_path = candidate.path.as_posix()
        snippet = _extract_snippet(candidate.content, candidate.span)
        blocks.append(f"### {rel_path}\n{snippet.strip()}\n")
    return "\n".join(blocks)


def _extract_snippet(content: str, span: tuple[int, int] | None) -> str:
    lines = content.splitlines()
    if not lines:
        return ""
    if span:
        start = max(span[0] - _SNIPPET_CONTEXT, 1)
        end = min(span[1] + _SNIPPET_CONTEXT, len(lines))
    else:
        start = 1
        end = min(len(lines), _MAX_SNIPPET_LINES)
    snippet_lines = lines[start - 1 : end]
    if len(snippet_lines) > _MAX_SNIPPET_LINES:
        snippet_lines = snippet_lines[:_MAX_SNIPPET_LINES]
        snippet_lines.append("...")
    return "\n".join(snippet_lines)


def _build_finding_id(path: str, description: str) -> str:
    digest = sha1(f"{path}:{description}".encode("utf-8")).hexdigest()[:8]
    return f"adv-{digest}"


def _normalize_suggestion(payload: dict[str, object]) -> _Suggestion | None:
    required = ("description", "path", "start_line", "end_line", "change_type")
    if not isinstance(payload, dict):
        return None
    for key in required:
        if key not in payload:
            return None
    description = str(payload["description"]).strip()
    path_value = payload["path"]
    if not description or not isinstance(path_value, (str, Path)):
        return None
    path = Path(path_value)
    try:
        start_line = int(payload["start_line"])
        end_line = int(payload["end_line"])
    except (TypeError, ValueError):
        return None
    if start_line <= 0 or end_line <= 0 or end_line < start_line:
        return None
    change_type = str(payload["change_type"]).strip()
    if not change_type:
        return None
    return _Suggestion(
        description=description,
        path=Path(path.as_posix()),
        start_line=start_line,
        end_line=end_line,
        change_type=change_type,
        raw_payload=payload,
    )


def _is_ignored(path: Path, ignore_dirs: Iterable[str]) -> bool:
    return any(part in ignore_dirs for part in path.parts)


def _normalize_span(start_line: int, end_line: int) -> tuple[int, int] | None:
    if start_line <= 0 or end_line <= 0 or end_line < start_line:
        return None
    return (start_line, end_line)


def _decode_suggestions(raw_response: str) -> list[dict[str, object]]:
    try:
        payload = json.loads(raw_response)
    except (TypeError, json.JSONDecodeError) as exc:
        LOGGER.warning("Failed to decode Codex response: %s", exc)
        return []
    if not isinstance(payload, list):
        LOGGER.warning("Codex response must be a JSON array")
        return []
    return payload


__all__ = ["collect_advanced_cleanup_ideas"]
