from __future__ import annotations

import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ai_clean import cli
from ai_clean.models import CleanupPlan, ExecutionResult, Finding, FindingLocation


class OrganizeCliTests(unittest.TestCase):
    def test_creates_plans_and_saves(self) -> None:
        finding = _make_finding(
            "organize-api-01",
            topic="api",
            members=["api_client.py", "api_routes.py"],
        )
        plan = _make_plan("plan-organize-1")

        with TemporaryDirectory() as tmp:
            with (
                patch("ai_clean.cli.propose_organize_groups", return_value=[finding]),
                patch(
                    "ai_clean.cli.plan_from_finding", return_value=[plan]
                ) as mock_plan,
            ):
                root = Path(tmp)
                config_path = root / "ai-clean.toml"
                config_path.write_text(_basic_config(), encoding="utf-8")

                stdout = StringIO()
                with (
                    redirect_stdout(stdout),
                    patch("builtins.input", side_effect=["1", "s"]),
                ):
                    exit_code = cli.main(
                        ["organize", "--root", str(root), "--config", str(config_path)]
                    )

                self.assertEqual(exit_code, 0)
                # The CLI should inject the files alias for the planner.
                planned_finding = mock_plan.call_args[0][0]
                self.assertIn("files", planned_finding.metadata)
                plan_path = root / ".ai-clean" / "plans" / f"{plan.id}.json"
                self.assertTrue(plan_path.exists())
                self.assertIn("Plan created", stdout.getvalue())

    def test_apply_now_calls_apply_plan(self) -> None:
        finding = _make_finding(
            "organize-logs-01",
            topic="logs",
            members=["logs_writer.py", "logs_cleanup.py"],
        )
        plan = _make_plan("plan-organize-apply")

        def _fake_apply(root: Path, __: Path | None, plan_id: str):
            return (
                ExecutionResult(
                    spec_id=f"spec-{plan_id}",
                    plan_id=plan_id,
                    success=True,
                    tests_passed=True,
                    stdout="",
                    stderr="",
                    git_diff="",
                ),
                f"specs/{plan_id}.yaml",
            )

        with TemporaryDirectory() as tmp:
            with (
                patch("ai_clean.cli.propose_organize_groups", return_value=[finding]),
                patch("ai_clean.cli.plan_from_finding", return_value=[plan]),
                patch("ai_clean.cli.apply_plan", side_effect=_fake_apply) as mock_apply,
            ):
                root = Path(tmp)
                config_path = root / "ai-clean.toml"
                config_path.write_text(_basic_config(), encoding="utf-8")

                stdout = StringIO()
                with (
                    redirect_stdout(stdout),
                    patch("builtins.input", side_effect=["1", "a"]),
                ):
                    exit_code = cli.main(
                        ["organize", "--root", str(root), "--config", str(config_path)]
                    )

                self.assertEqual(exit_code, 0)
                self.assertEqual(mock_apply.call_count, 1)
                apply_args = mock_apply.call_args[0]
                self.assertTrue(str(apply_args[0]).endswith(".ai-clean"))
                self.assertIn("applied 1 plan", stdout.getvalue())


def _make_finding(finding_id: str, *, topic: str, members: list[str]) -> Finding:
    return Finding(
        id=finding_id,
        category="organize_candidate",
        description="Group related files",
        locations=[FindingLocation(path=Path(members[0]), start_line=1, end_line=1)],
        metadata={"topic": topic, "members": members},
    )


def _make_plan(plan_id: str) -> CleanupPlan:
    return CleanupPlan(
        id=plan_id,
        finding_id="finding-1",
        title="Organize plan",
        intent="Move files",
        steps=["step one"],
        constraints=["keep changes focused"],
        tests_to_run=["pytest -q"],
        metadata={"target_directory": "api/"},
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
