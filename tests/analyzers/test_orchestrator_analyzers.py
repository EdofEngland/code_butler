from __future__ import annotations

import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ai_clean.analyzers.orchestrator import _merge_findings, analyze_repo
from ai_clean.models import Finding, FindingLocation


class OrchestratorTests(unittest.TestCase):
    def test_merge_findings_deduplicates_by_id(self) -> None:
        first = Finding(
            id="dup-1234",
            category="duplicate_block",
            description="first",
            locations=[FindingLocation(path=Path("a.py"), start_line=1, end_line=2)],
            metadata={"sources": ["first"]},
        )
        second = Finding(
            id="dup-1234",
            category="duplicate_block",
            description="second",
            locations=[
                FindingLocation(path=Path("a.py"), start_line=1, end_line=2),
                FindingLocation(path=Path("b.py"), start_line=3, end_line=4),
            ],
            metadata={"sources": ["second"]},
        )

        store: dict[str, Finding] = {first.id: first}
        _merge_findings(store, [second])

        merged = store[first.id]
        self.assertEqual(merged.description, "first")
        self.assertEqual(
            [
                (loc.path.as_posix(), loc.start_line, loc.end_line)
                for loc in merged.locations
            ],
            [("a.py", 1, 2), ("b.py", 3, 4)],
        )
        self.assertEqual(merged.metadata["sources"], ["first", "second"])

    def test_analyze_repo_runs_analyzers(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            config_path = Path(tmp) / "ai-clean.toml"
            config_path.write_text(_minimal_config(), encoding="utf-8")

            (root / "dup_a.py").write_text(
                "value = 1\nresult = value\n", encoding="utf-8"
            )
            (root / "dup_b.py").write_text(
                "value = 1\nresult = value\n", encoding="utf-8"
            )

            big_contents = "\n".join(f"line_{i}" for i in range(10)) + "\n"
            (root / "big_file.py").write_text(big_contents, encoding="utf-8")

            (root / "doc_target.py").write_text(
                "def func():\n    return 1\n", encoding="utf-8"
            )

            (root / "api_alpha.py").write_text(
                '"""API handler"""\nimport httpx\n', encoding="utf-8"
            )
            (root / "api_beta.py").write_text(
                '"""API worker"""\nimport httpx\n', encoding="utf-8"
            )

            findings = analyze_repo(root, config_path)

            categories = {finding.category for finding in findings}
            self.assertTrue(
                {"duplicate_block", "missing_docstring"}.issubset(categories)
            )
            self.assertEqual(
                findings, sorted(findings, key=lambda f: (f.category, f.id))
            )

    def test_analyze_repo_continues_after_failure(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = Path(tmp) / "ai-clean.toml"
            config_path.write_text(_minimal_config(), encoding="utf-8")
            (root / "doc_target.py").write_text(
                "def func():\n    return 1\n", encoding="utf-8"
            )

            with patch(
                "ai_clean.analyzers.orchestrator.find_duplicate_blocks",
                side_effect=RuntimeError("boom"),
            ):
                findings = analyze_repo(root, config_path)

        self.assertGreaterEqual(len(findings), 1)
        self.assertIn("analyzer_errors", findings[0].metadata)


def _minimal_config() -> str:
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
        max_file_lines = 3
        max_function_lines = 3
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
