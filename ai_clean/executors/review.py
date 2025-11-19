"""Codex-based review executor that summarizes diffs without writing files."""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

from ai_clean.interfaces import ReviewExecutor
from ai_clean.models import CleanupPlan, ExecutionResult

CodexCompletion = Callable[[str], Any]


class CodexReviewExecutor(ReviewExecutor):
    """Invoke a Codex-style completion API to produce structured reviews."""

    def __init__(self, *, completion: CodexCompletion) -> None:
        if completion is None:
            raise ValueError("CodexReviewExecutor requires a completion callable.")
        self._completion = completion

    def review_change(
        self,
        plan: CleanupPlan,
        diff: str,
        execution_result: ExecutionResult | None,
    ) -> Dict[str, Any]:
        prompt = _build_prompt(plan, diff, execution_result)
        try:
            raw_response = self._completion(prompt)
        except Exception as exc:  # pragma: no cover - defensive
            raise RuntimeError("Review completion failed.") from exc

        structured = _parse_response(raw_response)
        structured.setdefault("summary", "")
        structured.setdefault("risks", [])
        structured.setdefault("suggested_checks", [])
        structured["metadata"] = {
            "prompt": prompt,
            "raw_response": raw_response,
        }
        return structured


def _build_prompt(
    plan: CleanupPlan,
    diff: str,
    execution_result: ExecutionResult | None,
) -> str:
    sections: List[str] = []
    sections.append("You are Codex performing a read-only code review.")
    sections.append(
        "Provide JSON with keys summary, risks (list), and suggested_checks (list)."
    )
    sections.append(f"Plan ID: {plan.id}")
    sections.append(f"Intent: {plan.intent}")
    sections.append("Steps:\n" + "\n".join(f"- {step}" for step in plan.steps))
    if plan.constraints:
        sections.append(
            "Constraints:\n"
            + "\n".join(f"- {constraint}" for constraint in plan.constraints)
        )
    tests_info = _format_execution_summary(execution_result)
    sections.append(f"Execution Summary:\n{tests_info}")
    diff_body = diff.strip() or "(diff unavailable)"
    sections.append(f"Diff:\n```diff\n{diff_body}\n```")
    sections.append(
        "Respond strictly with JSON: "
        '{"summary":"...", "risks":["..."], "suggested_checks":["..."]}'
    )
    return "\n\n".join(sections)


def _format_execution_summary(execution_result: ExecutionResult | None) -> str:
    if not execution_result:
        return "Apply/tests not yet run."
    parts = [
        f"Apply success: {execution_result.success}",
        f"Tests status: {execution_result.tests_passed}",
    ]
    tests_meta = execution_result.metadata.get("tests", {})
    if tests_meta:
        parts.append(f"Tests metadata: {tests_meta}")
    return "\n".join(parts)


def _parse_response(raw_response: Any) -> Dict[str, Any]:
    if isinstance(raw_response, dict):
        return {
            "summary": str(raw_response.get("summary", "")).strip(),
            "risks": _ensure_list(raw_response.get("risks")),
            "suggested_checks": _ensure_list(raw_response.get("suggested_checks")),
        }
    if isinstance(raw_response, str):
        stripped = raw_response.strip()
        if not stripped:
            return {"summary": "", "risks": [], "suggested_checks": []}
        try:
            return _parse_response(json.loads(stripped))
        except json.JSONDecodeError:
            # Treat malformed JSON as a plain-text summary.
            return {
                "summary": stripped,
                "risks": [],
                "suggested_checks": [],
            }
    # Unknown type; fall back to repr for summary.
    return {
        "summary": repr(raw_response),
        "risks": [],
        "suggested_checks": [],
    }


def _ensure_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value:
        return [str(value).strip()]
    return []


__all__ = ["CodexReviewExecutor"]
