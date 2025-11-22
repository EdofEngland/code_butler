"""Advanced cleanup planner helpers.

This module turns Codex-suggested ``advanced_cleanup`` findings into ButlerSpec
plans without touching the filesystem. It enforces narrow scopes so Butler can
apply the change safely later in the pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_clean.config import AiCleanConfig as ButlerConfig
from ai_clean.models import CleanupPlan, Finding

_MAX_LINE_SPAN = 25

__all__ = ["plan_advanced_cleanup"]


def plan_advanced_cleanup(finding: Finding, config: ButlerConfig) -> list[CleanupPlan]:
    """Translate a Codex suggestion into a CleanupPlan."""

    if finding.category != "advanced_cleanup":
        raise ValueError("plan_advanced_cleanup only accepts advanced_cleanup findings")
    if len(finding.locations) != 1:
        raise ValueError("advanced_cleanup findings must include exactly one location")

    metadata = dict(finding.metadata)
    suggestions_value = metadata.get("suggestions")
    if (
        isinstance(suggestions_value, list)
        and len([entry for entry in suggestions_value if entry]) > 1
    ):
        raise ValueError(
            "advanced_cleanup findings must contain a single Codex suggestion; "
            "split suggestions into separate findings"
        )
    elif suggestions_value and not isinstance(suggestions_value, list):
        raise ValueError("advanced_cleanup suggestions metadata must be a list")

    (
        target_file,
        start_line,
        end_line,
        line_span,
        change_type,
        prompt_hash,
        codex_model,
        description,
    ) = _validate_metadata(finding, metadata, line_span_limit=_MAX_LINE_SPAN)

    test_command = (metadata.get("test_command") or "").strip()
    if not test_command:
        test_command = config.tests.default_command.strip()
    if not test_command:
        raise ValueError("advanced_cleanup plans require a test command")

    plan_id = f"{finding.id}-plan"
    title = f"{change_type.capitalize()} in {target_file}"
    intent = (
        f"Apply Codex-suggested {change_type} limited to lines "
        f"{start_line}-{end_line} of {target_file}"
    )
    steps = _build_steps(
        target_file=target_file,
        start_line=start_line,
        end_line=end_line,
        prompt_hash=prompt_hash,
        description=description,
        test_command=test_command,
    )
    constraints = [
        f"Limit edits to {target_file}:{start_line}-{end_line}",
        "Do not introduce unrelated refactors or API changes",
        "Keep coding style consistent with existing file",
    ]
    optional_followups = metadata.get("optional_followups")  # noqa: E501
    if not optional_followups:
        optional_followups = metadata.get("follow_up_actions")
    if isinstance(optional_followups, list):
        # Encode optional follow-ups as constraints instead of new steps to prevent scope creep.
        extra_constraints = []
        for entry in optional_followups:
            stripped = str(entry).strip()
            if stripped:
                extra_constraints.append(stripped)
        if extra_constraints:
            constraints.extend(extra_constraints)

    plan_metadata = dict(metadata)
    plan_metadata.update(
        {
            "plan_kind": "advanced_cleanup",
            "target_file": target_file,
            "start_line": start_line,
            "end_line": end_line,
            "line_span": line_span,
            "line_span_limit": _MAX_LINE_SPAN,
            "change_type": change_type,
            "prompt_hash": prompt_hash,
            "codex_model": codex_model,
        }
    )
    plan_metadata.setdefault("needs_manual_verification", False)

    plan = CleanupPlan(
        id=plan_id,
        finding_id=finding.id,
        title=title,
        intent=intent,
        steps=steps,
        constraints=constraints,
        tests_to_run=[test_command],
        metadata=plan_metadata,
    )
    return [plan]


def _validate_metadata(
    finding: Finding,
    metadata: dict[str, Any],
    *,
    line_span_limit: int,
) -> tuple[str, int, int, int, str, str, str, str]:
    required_fields = (
        "target_path",
        "start_line",
        "end_line",
        "change_type",
        "prompt_hash",
        "codex_model",
    )
    missing = [key for key in required_fields if metadata.get(key) is None]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"advanced_cleanup finding is missing metadata: {joined}")

    location = finding.locations[0]
    target_path_value = metadata["target_path"]
    target_path_text = str(target_path_value).strip()
    if not target_path_text:
        raise ValueError("target_path must be a non-empty path string")
    target_file = Path(target_path_text).as_posix()
    if location.path.as_posix() != target_file:
        raise ValueError(
            "advanced_cleanup findings must reference a single target file"
        )

    start_line = metadata["start_line"]
    end_line = metadata["end_line"]
    if not isinstance(start_line, int) or not isinstance(end_line, int):
        raise ValueError("start_line and end_line must be integers")
    if start_line < 1 or end_line < 1:
        raise ValueError("start_line and end_line must be positive")
    if start_line >= end_line:
        raise ValueError("start_line must be less than end_line")
    if location.start_line != start_line or location.end_line != end_line:
        raise ValueError("location span does not match metadata span")
    line_span = end_line - start_line + 1
    if line_span > line_span_limit:
        raise ValueError(
            "advanced_cleanup plan exceeds allowed span "
            f"({line_span}>{line_span_limit})"
        )

    change_type = str(metadata["change_type"]).strip()
    prompt_hash = str(metadata["prompt_hash"]).strip()
    codex_model = str(metadata["codex_model"]).strip()
    if not change_type or not prompt_hash or not codex_model:
        raise ValueError(
            "change_type, prompt_hash, and codex_model must all be present"
        )

    description = str(metadata.get("description") or finding.description).strip()

    return (
        target_file,
        start_line,
        end_line,
        line_span,
        change_type,
        prompt_hash,
        codex_model,
        description,
    )


def _build_steps(
    *,
    target_file: str,
    start_line: int,
    end_line: int,
    prompt_hash: str,
    description: str,
    test_command: str,
) -> list[str]:
    snippet_reference = f"{target_file}:{start_line}-{end_line}"
    # ButlerSpec guardrail: keep exactly three steps so Codex instructions remain concise.
    return [
        (
            f"Review the Codex suggestion (prompt hash {prompt_hash}, {description}) "
            "and confirm the change still applies to "
            f"{snippet_reference}."
        ),
        (
            f"Implement the described change strictly within {snippet_reference}, "
            "referencing the snippet in metadata."
        ),
        (
            f"Run `{test_command}` and verify no "
            "unrelated files changed after applying "
            "the update."  # noqa: E501
        ),
    ]
