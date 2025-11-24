from __future__ import annotations

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ai_clean import cli
from ai_clean.factories import ReviewExecutorHandle
from ai_clean.models import CleanupPlan, ExecutionResult
from ai_clean.plans import save_plan


class StubReviewer:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def review_change(self, plan, diff, exec_result, *, plan_id=None):
        self.calls.append((plan, diff, exec_result, plan_id))
        return {
            "summary": "Reviewed change",
            "risk_grade": "low",
            "manual_checks": ["Run smoke tests"],
            "constraints": ["Constraints respected"],
        }


class ChangesReviewCliTests(unittest.TestCase):
    def test_runs_review_with_all_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata_root = root / ".ai-clean"

            plan = _make_plan()
            save_plan(plan, root=metadata_root)

            spec_path = metadata_root / "specs" / f"{plan.id}-spec.butler.yaml"
            spec_path.parent.mkdir(parents=True, exist_ok=True)
            spec_path.write_text(
                "id: plan-123-spec\nplan_id: plan-123\n", encoding="utf-8"
            )

            exec_result = ExecutionResult(
                spec_id="plan-123-spec",
                plan_id=plan.id,
                success=True,
                tests_passed=True,
                stdout="ok",
                stderr="",
                git_diff="diff --stat",
                metadata={
                    "tests": {
                        "status": "ran",
                        "command": "pytest -q",
                        "exit_code": 0,
                        "stdout": "ok",
                        "stderr": "",
                    }
                },
            )
            result_path = metadata_root / "results" / f"{plan.id}.json"
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_text(exec_result.to_json(), encoding="utf-8")

            reviewer = StubReviewer()
            handle = ReviewExecutorHandle(
                reviewer=reviewer, metadata_root=metadata_root
            )

            config_path = root / "ai-clean.toml"
            config_path.write_text(_basic_config(), encoding="utf-8")

            stdout = StringIO()
            with (
                redirect_stdout(stdout),
                patch("ai_clean.cli.get_review_executor", return_value=handle),
            ):
                exit_code = cli.main(
                    [
                        "changes-review",
                        plan.id,
                        "--root",
                        str(root),
                        "--config",
                        str(config_path),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(len(reviewer.calls), 1)
            _, diff_text, _, called_plan_id = reviewer.calls[0]
            self.assertEqual(called_plan_id, plan.id)
            self.assertIn("ButlerSpec:", diff_text)
            output = stdout.getvalue()
            self.assertIn("Summary of Changes:", output)
            self.assertIn("Risk Assessment:", output)
            self.assertIn("Manual QA Suggestions:", output)
            self.assertIn("Constraint Validation Notes:", output)
            self.assertIn("Run smoke tests", output)

    def test_missing_plan_fails_fast(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "ai-clean.toml"
            config_path.write_text(_basic_config(), encoding="utf-8")

            stdout = StringIO()
            stderr = StringIO()
            with (
                redirect_stdout(stdout),
                redirect_stderr(stderr),
                patch("ai_clean.cli.get_review_executor") as mocked_executor,
            ):
                exit_code = cli.main(
                    [
                        "changes-review",
                        "unknown-plan",
                        "--root",
                        str(root),
                        "--config",
                        str(config_path),
                    ]
                )
            self.assertNotEqual(exit_code, 0)
            self.assertIn("CleanupPlan not found", stderr.getvalue())
            mocked_executor.assert_not_called()

    def test_missing_execution_result_is_reported(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata_root = root / ".ai-clean"

            plan = _make_plan()
            save_plan(plan, root=metadata_root)

            spec_path = metadata_root / "specs" / f"{plan.id}-spec.butler.yaml"
            spec_path.parent.mkdir(parents=True, exist_ok=True)
            spec_path.write_text(
                "id: plan-123-spec\nplan_id: plan-123\n", encoding="utf-8"
            )

            reviewer = StubReviewer()
            handle = ReviewExecutorHandle(
                reviewer=reviewer, metadata_root=metadata_root
            )

            config_path = root / "ai-clean.toml"
            config_path.write_text(_basic_config(), encoding="utf-8")

            stdout = StringIO()
            with (
                redirect_stdout(stdout),
                patch("ai_clean.cli.get_review_executor", return_value=handle),
            ):
                exit_code = cli.main(
                    [
                        "changes-review",
                        plan.id,
                        "--root",
                        str(root),
                        "--config",
                        str(config_path),
                    ]
                )

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("ExecutionResult not found", output)
            self.assertEqual(len(reviewer.calls), 1)


def _make_plan() -> CleanupPlan:
    return CleanupPlan(
        id="plan-123",
        finding_id="finding-1",
        title="Docstring plan",
        intent="Improve docs",
        steps=["add docs"],
        constraints=["keep behavior"],
        tests_to_run=["pytest -q"],
        metadata={"target_file": "alpha.py"},
    )


def _basic_config() -> str:
    return (
        """
[spec_backend]
type = "butler"
default_batch_group = "default"

[executor]
type = "codex_shell"
binary = "codex"
apply_args = ["apply"]

[review]
type = "codex_review"
mode = "summarize-and-risk"

[git]
base_branch = "main"
refactor_branch = "refactor/ai-clean"

[tests]
default_command = "pytest -q"

[analyzers.duplicate]
window_size = 2
min_occurrences = 2
ignore_dirs = [".git", "__pycache__", ".venv"]

[analyzers.structure]
max_file_lines = 10
max_function_lines = 10
ignore_dirs = [".git", "__pycache__", ".venv"]

[analyzers.docstring]
min_docstring_length = 10
min_symbol_lines = 1
weak_markers = ["TODO"]
important_symbols_only = false
ignore_dirs = [".git", "__pycache__", ".venv"]

[analyzers.organize]
min_group_size = 2
max_group_size = 3
max_groups = 2
ignore_dirs = [".git", "__pycache__", ".venv"]
""".strip()
        + "\n"
    )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
