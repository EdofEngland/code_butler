from __future__ import annotations

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ai_clean import cli
from ai_clean.models import CleanupPlan, ExecutionResult, Finding, FindingLocation


class AnnotateCliTests(unittest.TestCase):
    def test_creates_plans_for_missing_docstrings(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            config_path = root / "ai-clean.toml"
            config_path.write_text(_basic_config(), encoding="utf-8")
            (root / "alpha.py").write_text(
                "def first():\n    return 1\n", encoding="utf-8"
            )

            stdout = StringIO()
            stderr = StringIO()
            with (
                redirect_stdout(stdout),
                redirect_stderr(stderr),
                patch("builtins.input", side_effect=["a", "s"]),
            ):
                exit_code = cli.main(
                    ["annotate", "--root", str(root), "--config", str(config_path)]
                )

            self.assertEqual(exit_code, 0)
            plan_dir = root / ".ai-clean" / "plans"
            self.assertTrue(plan_dir.exists())
            plan_files = sorted(plan_dir.glob("*.json"))
            self.assertGreaterEqual(len(plan_files), 2)
            self.assertIn("Plan created", stdout.getvalue())

    def test_apply_now_uses_apply_plan(self) -> None:
        finding_missing = _make_finding("missing_docstring", "alpha.py", "first")
        finding_weak = _make_finding("weak_docstring", "alpha.py", "second")
        findings = [finding_missing, finding_weak]
        plans: dict[str, CleanupPlan] = {
            finding_missing.id: _make_plan("plan-one"),
            finding_weak.id: _make_plan("plan-two"),
        }

        def _fake_plan_from_finding(finding: Finding, _: object) -> list[CleanupPlan]:
            return [plans[finding.id]]

        def _fake_apply_plan(
            _: Path, __: Path | None, plan_id: str
        ) -> tuple[ExecutionResult, str]:
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

        with (
            TemporaryDirectory() as tmp,
            patch("ai_clean.cli.find_docstring_gaps", return_value=findings),
            patch(
                "ai_clean.cli.plan_from_finding", side_effect=_fake_plan_from_finding
            ),
            patch(
                "ai_clean.cli.apply_plan", side_effect=_fake_apply_plan
            ) as mock_apply,
        ):
            root = Path(tmp)
            config_path = root / "ai-clean.toml"
            config_path.write_text(_basic_config(), encoding="utf-8")

            stdout = StringIO()
            with (
                redirect_stdout(stdout),
                patch("builtins.input", side_effect=["a", "a"]),
            ):
                exit_code = cli.main(
                    [
                        "annotate",
                        "--root",
                        str(root),
                        "--config",
                        str(config_path),
                        "--mode",
                        "all",
                    ]
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(mock_apply.call_count, 2)
        self.assertIn("Planned 2 docstring(s); applied 2 plan(s).", stdout.getvalue())


def _make_finding(category: str, path: str, symbol_name: str) -> Finding:
    return Finding(
        id=f"{category}-{symbol_name}",
        category=category,
        description=f"{category} finding",
        locations=[FindingLocation(path=Path(path), start_line=1, end_line=2)],
        metadata={
            "symbol_type": "function",
            "symbol_name": symbol_name,
            "qualified_name": symbol_name,
            "docstring_preview": "",
            "lines_of_code": 10,
        },
    )


def _make_plan(plan_id: str) -> CleanupPlan:
    return CleanupPlan(
        id=plan_id,
        finding_id="finding-1",
        title="Docstring plan",
        intent="Fix docstring",
        steps=["step one"],
        constraints=["stay focused"],
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
