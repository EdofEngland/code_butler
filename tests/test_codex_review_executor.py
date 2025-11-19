from __future__ import annotations

import unittest
from typing import Any, Dict

from ai_clean.executors.review import CodexReviewExecutor
from ai_clean.models import CleanupPlan, ExecutionResult


def _plan() -> CleanupPlan:
    return CleanupPlan(
        id="plan-1",
        finding_id="finding-1",
        title="Demo",
        intent="Improve things",
        steps=["Edit file A", "Run tests"],
        constraints=["No new deps"],
        tests_to_run=["pytest"],
    )


class CodexReviewExecutorTests(unittest.TestCase):
    def test_returns_structured_review_from_dict_response(self) -> None:
        captured_prompt: Dict[str, Any] = {}

        def fake_completion(prompt: str) -> Dict[str, Any]:
            captured_prompt["value"] = prompt
            return {
                "summary": "Looks good",
                "risks": ["Edge case"],
                "suggested_checks": ["Run lint"],
            }

        executor = CodexReviewExecutor(completion=fake_completion)
        result = executor.review_change(
            _plan(),
            diff="diff --git",
            execution_result=ExecutionResult(
                spec_id="spec",
                success=True,
                tests_passed=True,
                stdout="ok",
                stderr="",
                metadata={"tests": {"command": ["pytest"], "returncode": 0}},
            ),
        )

        self.assertIn("Plan ID: plan-1", captured_prompt["value"])
        self.assertEqual(result["summary"], "Looks good")
        self.assertEqual(result["risks"], ["Edge case"])
        self.assertEqual(result["suggested_checks"], ["Run lint"])
        self.assertIn("raw_response", result["metadata"])

    def test_fallbacks_when_response_is_not_json(self) -> None:
        executor = CodexReviewExecutor(completion=lambda prompt: "Plain text answer")
        result = executor.review_change(_plan(), diff="", execution_result=None)
        self.assertEqual(result["summary"], "Plain text answer")
        self.assertEqual(result["risks"], [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
