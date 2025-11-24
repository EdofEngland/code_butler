from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ai_clean.commands.apply import apply_plan
from ai_clean.models import CleanupPlan, ExecutionResult


class ApplyCommandTests(unittest.TestCase):
    def test_apply_plan_records_manual_execution_and_slash_command(self) -> None:
        plan = _make_plan("plan-manual-1", intent="Touch alpha.py safely")

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "ai-clean.toml"
            config_path.write_text(_basic_config(), encoding="utf-8")

            plans_dir = root / ".ai-clean" / "plans"
            plans_dir.mkdir(parents=True, exist_ok=True)
            (plans_dir / f"{plan.id}.json").write_text(plan.to_json(), encoding="utf-8")

            with patch("ai_clean.commands.apply.ensure_on_refactor_branch"):
                result, spec_path = apply_plan(root, config_path, plan.id)

            spec_path_obj = Path(spec_path)
            self.assertTrue(spec_path_obj.is_file())
            self.assertTrue(spec_path_obj.is_absolute())
            slash_command = str(result.metadata.get("slash_command", ""))
            self.assertIn("/butler-exec", slash_command)
            self.assertIn(str(spec_path_obj), slash_command)
            self.assertIn(str(spec_path_obj), result.stdout)
            self.assertEqual(result.spec_id, f"{plan.id}-spec")
            self.assertEqual(result.plan_id, plan.id)
            self.assertFalse(result.success)
            self.assertIsNone(result.tests_passed)
            self.assertEqual(result.metadata.get("tests", {}).get("status"), "not_run")
            self.assertTrue(result.metadata.get("manual_execution_required"))

            result_path = root / ".ai-clean" / "results" / f"{plan.id}.json"
            self.assertTrue(result_path.is_file())
            stored = ExecutionResult.from_json(result_path.read_text())
            self.assertEqual(stored.metadata.get("manual_execution_required"), True)

    def test_apply_plan_aborts_when_plan_limits_exceeded(self) -> None:
        plan = _make_plan(
            "plan-too-large",
            intent="Edit alpha.py beyond limits",
            metadata={"target_file": "alpha.py", "start_line": 1, "end_line": 400},
        )

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "ai-clean.toml"
            config_path.write_text(_basic_config(), encoding="utf-8")

            plans_dir = root / ".ai-clean" / "plans"
            plans_dir.mkdir(parents=True, exist_ok=True)
            (plans_dir / f"{plan.id}.json").write_text(plan.to_json(), encoding="utf-8")

            with patch("ai_clean.commands.apply.ensure_on_refactor_branch"):
                with self.assertRaisesRegex(ValueError, "exceeds plan limits"):
                    apply_plan(root, config_path, plan.id)

            specs_dir = root / ".ai-clean" / "specs"
            self.assertFalse(
                specs_dir.exists() and any(specs_dir.glob("*.butler.yaml"))
            )
            result_path = root / ".ai-clean" / "results" / f"{plan.id}.json"
            self.assertFalse(result_path.exists())


def _make_plan(
    plan_id: str,
    *,
    intent: str,
    metadata: dict[str, object] | None = None,
) -> CleanupPlan:
    return CleanupPlan(
        id=plan_id,
        finding_id="finding-1",
        title="Plan title",
        intent=intent,
        steps=["step one"],
        constraints=["stay focused"],
        tests_to_run=["pytest -q"],
        metadata=metadata or {"target_file": "alpha.py"},
    )


def _basic_config() -> str:
    return (
        """
[spec_backend]
type = "butler"
default_batch_group = "default"

[executor]
type = "manual"
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

[plan_limits]
max_files_per_plan = 1
max_changed_lines_per_plan = 200

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

[analyzers.advanced]
max_files = 3
max_suggestions = 5
prompt_template = "Prompt"
codex_model = "gpt-4o-mini"
temperature = 0.2
ignore_dirs = [".git", "__pycache__", ".venv"]
""".strip()
        + "\n"
    )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
