from __future__ import annotations

import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from ai_clean import cli
from ai_clean.models import ExecutionResult
from ai_clean.results import save_execution_result


def _write_config(root: Path) -> Path:
    meta = root / ".ai-clean"
    config_path = root / "ai-clean.toml"
    config_text = f"""
[spec_backend]
type = "butler"
default_batch_group = "default"
specs_dir = "{(meta / "specs").as_posix()}"

[executor]
type = "codex_shell"
binary = "codex"
apply_args = ["apply"]
results_dir = "{(meta / "results").as_posix()}"

[review]
type = "codex_review"
mode = "summarize"

[git]
base_branch = "main"
refactor_branch = "refactor/ai-clean"

[tests]
default_command = "pytest -q"

[plan_limits]
max_files_per_plan = 1
max_changed_lines_per_plan = 200

[analyzers.duplicate]
window_size = 5
min_occurrences = 2
ignore_dirs = [".git"]

[analyzers.structure]
max_file_lines = 400
max_function_lines = 60
ignore_dirs = [".git"]

[analyzers.docstring]
min_docstring_length = 10
min_symbol_lines = 1
weak_markers = ["TODO"]
important_symbols_only = false
ignore_dirs = [".git"]

[analyzers.organize]
min_group_size = 2
max_group_size = 3
max_groups = 2
ignore_dirs = [".git"]

[analyzers.advanced]
max_files = 3
max_suggestions = 5
prompt_template = "tmpl"
codex_model = "gpt"
temperature = 0.0
ignore_dirs = [".git"]

[metadata]
root = "{meta.as_posix()}"
plans_dir = "{(meta / "plans").as_posix()}"
specs_dir = "{(meta / "specs").as_posix()}"
results_dir = "{(meta / "results").as_posix()}"
"""
    config_path.write_text(config_text.strip() + "\n", encoding="utf-8")
    return config_path


def _sample_diff() -> str:
    return "\n".join(
        [
            "diff --git a/foo.py b/foo.py",
            "--- a/foo.py",
            "+++ b/foo.py",
            "@@",
            "-old",
            "+new",
        ]
    )


class IngestCliTests(unittest.TestCase):
    def test_ingest_updates_execution_result_and_clears_manual_flag(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = _write_config(root)
            results_dir = root / ".ai-clean" / "results"
            base_result = ExecutionResult(
                spec_id="spec-1",
                plan_id="plan-1",
                success=False,
                tests_passed=None,
                stdout="manual",
                stderr="",
                git_diff=None,
                metadata={"manual_execution_required": True},
            )
            save_execution_result(base_result, results_dir)

            artifact_path = root / "artifact.json"
            artifact = {
                "plan_id": "plan-1",
                "diff": _sample_diff(),
                "stdout": "applied",
                "stderr": "",
                "tests": {
                    "status": "ran",
                    "command": "pytest -q",
                    "exit_code": 0,
                    "stdout": "",
                    "stderr": "",
                },
            }
            artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

            stdout = StringIO()
            stderr = StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = cli.main(
                    [
                        "ingest",
                        "--plan-id",
                        "plan-1",
                        "--artifact",
                        str(artifact_path),
                        "--root",
                        str(root),
                        "--config",
                        str(config_path),
                    ]
                )

            self.assertEqual(exit_code, 0)
            updated = ExecutionResult.from_json(
                (results_dir / "plan-1.json").read_text(encoding="utf-8")
            )
            self.assertTrue(updated.success)
            self.assertTrue(updated.tests_passed)
            self.assertFalse(updated.metadata.get("manual_execution_required"))
            self.assertIn("diff --git", updated.git_diff or "")
            self.assertIn("Tests status: ran", stdout.getvalue())
            self.assertEqual("", stderr.getvalue().strip())

    def test_ingest_rejects_mismatched_plan_and_keeps_original_result(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = _write_config(root)
            results_dir = root / ".ai-clean" / "results"
            base_result = ExecutionResult(
                spec_id="spec-1",
                plan_id="plan-1",
                success=False,
                tests_passed=None,
                stdout="manual",
                stderr="",
                git_diff=None,
                metadata={"manual_execution_required": True},
            )
            save_execution_result(base_result, results_dir)

            artifact_path = root / "artifact.json"
            artifact_path.write_text(
                json.dumps(
                    {
                        "plan_id": "other",
                        "diff": _sample_diff(),
                        "stdout": "applied",
                        "stderr": "",
                        "tests": {
                            "status": "ran",
                            "command": "pytest -q",
                            "exit_code": 0,
                            "stdout": "",
                            "stderr": "",
                        },
                    }
                ),
                encoding="utf-8",
            )

            stdout = StringIO()
            stderr = StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = cli.main(
                    [
                        "ingest",
                        "--plan-id",
                        "plan-1",
                        "--artifact",
                        str(artifact_path),
                        "--root",
                        str(root),
                        "--config",
                        str(config_path),
                    ]
                )

            self.assertEqual(exit_code, 1)
            # Original result remains unchanged.
            unchanged = ExecutionResult.from_json(
                (results_dir / "plan-1.json").read_text(encoding="utf-8")
            )
            self.assertTrue(unchanged.metadata.get("manual_execution_required"))
            self.assertIn("plan_id", stderr.getvalue())

    def test_ingest_updates_findings_when_flag_enabled(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = _write_config(root)
            results_dir = root / ".ai-clean" / "results"
            base_result = ExecutionResult(
                spec_id="spec-1",
                plan_id="plan-1",
                success=False,
                tests_passed=None,
                stdout="manual",
                stderr="",
                git_diff=None,
                metadata={"manual_execution_required": True},
            )
            save_execution_result(base_result, results_dir)

            artifact_path = root / "artifact.json"
            artifact_path.write_text(
                json.dumps(
                    {
                        "plan_id": "plan-1",
                        "diff": _sample_diff(),
                        "stdout": "applied",
                        "stderr": "",
                        "tests": {
                            "status": "ran",
                            "command": "pytest -q",
                            "exit_code": 0,
                            "stdout": "",
                            "stderr": "",
                        },
                        "suggestions": [
                            {
                                "description": "Tighten helper",
                                "path": "src/app.py",
                                "start_line": 10,
                                "end_line": 12,
                                "change_type": "refine_function",
                                "model": "gpt-4o-mini",
                                "prompt_hash": "abc",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            findings_path = root / ".ai-clean" / "findings.json"

            stdout = StringIO()
            stderr = StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = cli.main(
                    [
                        "ingest",
                        "--plan-id",
                        "plan-1",
                        "--artifact",
                        str(artifact_path),
                        "--root",
                        str(root),
                        "--config",
                        str(config_path),
                        "--update-findings",
                        "--findings-json",
                        str(findings_path),
                    ]
                )

            self.assertEqual(exit_code, 0)
            stored = json.loads(findings_path.read_text(encoding="utf-8"))
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored[0]["category"], "advanced_cleanup")
            meta = stored[0]["metadata"]
            self.assertEqual(meta["target_path"], "src/app.py")
            self.assertEqual(meta["start_line"], 10)
            self.assertEqual(meta["end_line"], 12)
            self.assertEqual(meta["codex_model"], "gpt-4o-mini")
            self.assertEqual(meta["change_type"], "refine_function")

    def test_ingest_resolves_paths_relative_to_root(self) -> None:
        with TemporaryDirectory() as tmp, TemporaryDirectory() as other_cwd:
            root = Path(tmp)
            config_path = _write_config(root)
            results_dir = root / ".ai-clean" / "results"
            base_result = ExecutionResult(
                spec_id="spec-1",
                plan_id="plan-1",
                success=False,
                tests_passed=None,
                stdout="manual",
                stderr="",
                git_diff=None,
                metadata={"manual_execution_required": True},
            )
            save_execution_result(base_result, results_dir)

            artifact_rel = Path(".ai-clean/results/plan-1.codex.json")
            artifact_path = root / artifact_rel
            artifact_path.write_text(
                json.dumps(
                    {
                        "plan_id": "plan-1",
                        "diff": _sample_diff(),
                        "stdout": "applied",
                        "stderr": "",
                        "tests": {
                            "status": "ran",
                            "command": "pytest -q",
                            "exit_code": 0,
                            "stdout": "",
                            "stderr": "",
                        },
                    }
                ),
                encoding="utf-8",
            )

            stdout = StringIO()
            stderr = StringIO()
            prev_cwd = Path.cwd()
            os.chdir(other_cwd)
            try:
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = cli.main(
                        [
                            "ingest",
                            "--plan-id",
                            "plan-1",
                            "--artifact",
                            artifact_rel.as_posix(),
                            "--root",
                            str(root),
                            "--config",
                            str(config_path),
                        ]
                    )
            finally:
                os.chdir(prev_cwd)

            self.assertEqual(exit_code, 0)
            updated = ExecutionResult.from_json(
                (results_dir / "plan-1.json").read_text(encoding="utf-8")
            )
            self.assertTrue(updated.success)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
