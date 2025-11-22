from __future__ import annotations

import json
import textwrap
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from ai_clean import cli


class AnalyzeCliTests(unittest.TestCase):
    def test_analyze_text_output(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            config = Path(tmp) / "ai-clean.toml"
            config.write_text(_basic_config(), encoding="utf-8")
            (root / "sample.py").write_text(
                "def func():\n    return 1\n", encoding="utf-8"
            )

            stdout = StringIO()
            stderr = StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = cli.main(
                    [
                        "analyze",
                        "--root",
                        str(root),
                        "--config",
                        str(config),
                    ]
                )

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("missing_docstring", output)

    def test_analyze_json_output(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = Path(tmp) / "ai-clean.toml"
            config.write_text(_basic_config(), encoding="utf-8")
            (root / "sample.py").write_text(
                "def func():\n    return 1\n", encoding="utf-8"
            )

            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = cli.main(
                    [
                        "analyze",
                        "--root",
                        str(root),
                        "--config",
                        str(config),
                        "--json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertIsInstance(payload, list)
            if payload:
                self.assertIn("category", payload[0])

    def test_analyze_uses_root_default_config(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            config = root / "ai-clean.toml"
            config.write_text(_basic_config(), encoding="utf-8")
            (root / "sample.py").write_text(
                "def func():\n    return 1\n", encoding="utf-8"
            )

            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = cli.main(
                    [
                        "analyze",
                        "--root",
                        str(root),
                    ]
                )

        self.assertEqual(exit_code, 0)
        self.assertIn("missing_docstring", stdout.getvalue())


def _basic_config() -> str:
    return (
        textwrap.dedent(
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
        """
        ).strip()
        + "\n"
    )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
