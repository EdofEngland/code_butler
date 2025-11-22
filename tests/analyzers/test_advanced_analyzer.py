from __future__ import annotations

import json
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Sequence

from ai_clean.analyzers.advanced import collect_advanced_cleanup_ideas
from ai_clean.config import load_config
from ai_clean.interfaces import CodexPromptRunner, PromptAttachment
from ai_clean.models import Finding, FindingLocation


class FakeRunner(CodexPromptRunner):
    def __init__(self, payload: list[dict[str, object]]) -> None:
        self.payload = payload
        self.calls: list[str] = []
        self.attachments: list[list[PromptAttachment]] = []

    def run(self, prompt: str, attachments: Sequence[PromptAttachment]) -> str:
        self.calls.append(prompt)
        self.attachments.append(list(attachments))
        return json.dumps(self.payload)


class AdvancedAnalyzerTests(unittest.TestCase):
    def test_collects_suggestions_with_guardrails(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            config_path = Path(tmp) / "ai-clean.toml"
            config_path.write_text(
                _config_text(max_files=1, max_suggestions=1), encoding="utf-8"
            )
            config = load_config(config_path)

            target_file = root / "module.py"
            target_file.write_text("value = 1\nvalue = value + 1\n", encoding="utf-8")

            findings = [
                Finding(
                    id="dup-1",
                    category="duplicate_block",
                    description="test",
                    locations=[
                        FindingLocation(
                            path=Path("module.py"), start_line=1, end_line=2
                        )
                    ],
                    metadata={},
                )
            ]

            runner = FakeRunner(
                [
                    {
                        "description": "Extract constant",
                        "path": "module.py",
                        "start_line": 1,
                        "end_line": 2,
                        "change_type": "extract_constant",
                    },
                    {
                        "description": "Second suggestion",
                        "path": "module.py",
                        "start_line": 1,
                        "end_line": 1,
                        "change_type": "extract_constant",
                    },
                ]
            )

            results = collect_advanced_cleanup_ideas(root, findings, config, runner)
            self.assertEqual(len(results), 1)
            finding = results[0]
            self.assertEqual(finding.category, "advanced_cleanup")
            metadata = finding.metadata
            self.assertEqual(metadata["change_type"], "extract_constant")
            self.assertEqual(metadata["target_path"], "module.py")
            self.assertEqual(metadata["start_line"], 1)
            self.assertEqual(metadata["end_line"], 2)
            self.assertIn("prompt_hash", metadata)
            self.assertEqual(metadata["codex_model"], "gpt-4o-mini")
            self.assertEqual(
                metadata["codex_payload"]["description"], "Extract constant"
            )
            self.assertIn("raw_response", metadata)
            self.assertIn("analyzer_summary", metadata)
            summary = metadata["analyzer_summary"]
            self.assertEqual(summary["selected_files"], 1)
            self.assertEqual(summary["accepted_suggestions"], 1)
            self.assertEqual(summary["dropped_suggestions"], 1)
            self.assertEqual(summary["dropped_reason_counts"]["max_suggestions"], 1)
            self.assertEqual(len(metadata["dropped_suggestions"]), 1)
            self.assertEqual(
                metadata["dropped_suggestions"][0]["reason"], "max_suggestions"
            )
            self.assertTrue(
                runner.calls[0].startswith(
                    "Suggest small, local cleanup changes only; no API redesigns."
                )
            )

    def test_rejects_unselected_paths(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            config_path = Path(tmp) / "ai-clean.toml"
            config_path.write_text(
                _config_text(max_files=1, max_suggestions=2), encoding="utf-8"
            )
            config = load_config(config_path)

            target_file = root / "module.py"
            target_file.write_text("value = 1\nvalue = value + 1\n", encoding="utf-8")

            findings = [
                Finding(
                    id="dup-1",
                    category="duplicate_block",
                    description="test",
                    locations=[
                        FindingLocation(
                            path=Path("module.py"), start_line=1, end_line=2
                        )
                    ],
                    metadata={},
                )
            ]

            runner = FakeRunner(
                [
                    {
                        "description": "Invalid path",
                        "path": "other.py",
                        "start_line": 1,
                        "end_line": 2,
                        "change_type": "extract_constant",
                    }
                ]
            )

            results = collect_advanced_cleanup_ideas(root, findings, config, runner)
            self.assertEqual(results, [])

    def test_rejects_disallowed_change_types(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            config_path = Path(tmp) / "ai-clean.toml"
            config_path.write_text(
                _config_text(max_files=1, max_suggestions=1), encoding="utf-8"
            )
            config = load_config(config_path)

            target_file = root / "module.py"
            target_file.write_text("value = 1\nvalue = value + 1\n", encoding="utf-8")

            findings = [
                Finding(
                    id="dup-1",
                    category="duplicate_block",
                    description="test",
                    locations=[
                        FindingLocation(
                            path=Path("module.py"), start_line=1, end_line=2
                        )
                    ],
                    metadata={},
                )
            ]

            runner = FakeRunner(
                [
                    {
                        "description": "Rewrite module",
                        "path": "module.py",
                        "start_line": 1,
                        "end_line": 2,
                        "change_type": "Refactor Architecture",
                    }
                ]
            )

            results = collect_advanced_cleanup_ideas(root, findings, config, runner)
            self.assertEqual(results, [])


def _config_text(max_files: int, max_suggestions: int) -> str:
    prompt_template_line = (
        'prompt_template = """Findings:\\n{{findings}}\\nSnippets:\\n' '{{snippets}}"""'
    )
    return (
        textwrap.dedent(
            f"""
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

        [analyzers.advanced]
        max_files = {max_files}
        max_suggestions = {max_suggestions}
        {prompt_template_line}
        codex_model = "gpt-4o-mini"
        temperature = 0.3
        ignore_dirs = [".git", "__pycache__", ".venv"]
        """
        ).strip()
        + "\n"
    )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
