from __future__ import annotations

import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ai_clean.config import load_config
from ai_clean.factories import get_executor, get_review_executor, get_spec_backend


def _write_config(path: Path) -> None:
    contents = textwrap.dedent(
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
        window_size = 5
        min_occurrences = 2
        ignore_dirs = [".git", "__pycache__", ".venv"]

        [analyzers.structure]
        max_file_lines = 400
        max_function_lines = 60
        ignore_dirs = [".git", "__pycache__", ".venv"]

        [analyzers.docstring]
        min_docstring_length = 32
        min_symbol_lines = 5
        weak_markers = ["TODO", "fixme"]
        important_symbols_only = true
        ignore_dirs = [".git", "__pycache__", ".venv"]

        [analyzers.organize]
        min_group_size = 2
        max_group_size = 4
        max_groups = 3
        ignore_dirs = [".git", "__pycache__", ".venv"]

        [analyzers.advanced]
        max_files = 2
        max_suggestions = 4
        prompt_template = "Findings:\\n{findings}\\nSnippets:\\n{snippets}"
        codex_model = "gpt-4o-mini"
        temperature = 0.3
        ignore_dirs = [".git", "__pycache__", ".venv"]
        """
    ).strip()
    path.write_text(contents + "\n")


class ConfigLoaderTests(unittest.TestCase):
    def test_load_config_happy_path(self) -> None:
        with TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "ai-clean.toml"
            _write_config(cfg_path)
            config = load_config(cfg_path)
            self.assertEqual(config.spec_backend.type, "butler")
            self.assertTrue(config.specs_dir.is_absolute())

            spec_handle = get_spec_backend(config)
            self.assertEqual(spec_handle.specs_dir, config.spec_backend.specs_dir)
            self.assertRaises(
                NotImplementedError, spec_handle.backend.plan_to_spec, object()
            )

            executor_handle = get_executor(config)
            self.assertEqual(executor_handle.results_dir, config.executor.results_dir)
            self.assertRaises(
                NotImplementedError,
                executor_handle.executor.apply_spec,
                Path("spec.yaml"),
            )

            review_handle = get_review_executor(config)
            self.assertEqual(review_handle.metadata_root, config.metadata_root)
            self.assertRaises(
                NotImplementedError,
                review_handle.reviewer.review_change,
                object(),
                "diff",
                object(),
            )

            duplicate_cfg = config.analyzers.duplicate
            self.assertEqual(duplicate_cfg.window_size, 5)
            self.assertEqual(duplicate_cfg.min_occurrences, 2)
            self.assertEqual(
                duplicate_cfg.ignore_dirs,
                (".git", "__pycache__", ".venv"),
            )

            structure_cfg = config.analyzers.structure
            self.assertEqual(structure_cfg.max_file_lines, 400)
            self.assertEqual(structure_cfg.max_function_lines, 60)
            self.assertEqual(
                structure_cfg.ignore_dirs,
                (".git", "__pycache__", ".venv"),
            )

            doc_cfg = config.analyzers.docstring
            self.assertEqual(doc_cfg.min_docstring_length, 32)
            self.assertEqual(doc_cfg.min_symbol_lines, 5)
            self.assertEqual(doc_cfg.weak_markers, ("todo", "fixme"))
            self.assertTrue(doc_cfg.important_symbols_only)
            self.assertEqual(doc_cfg.ignore_dirs, (".git", "__pycache__", ".venv"))

            organize_cfg = config.analyzers.organize
            self.assertEqual(organize_cfg.min_group_size, 2)
            self.assertEqual(organize_cfg.max_group_size, 4)
            self.assertEqual(organize_cfg.max_groups, 3)
            self.assertEqual(organize_cfg.ignore_dirs, (".git", "__pycache__", ".venv"))

            advanced_cfg = config.analyzers.advanced
            self.assertEqual(advanced_cfg.max_files, 2)
            self.assertEqual(advanced_cfg.max_suggestions, 4)
            self.assertEqual(
                advanced_cfg.prompt_template,
                "Findings:\n{findings}\nSnippets:\n{snippets}",
            )
            self.assertEqual(advanced_cfg.codex_model, "gpt-4o-mini")
            self.assertAlmostEqual(advanced_cfg.temperature, 0.3)
            self.assertEqual(advanced_cfg.ignore_dirs, (".git", "__pycache__", ".venv"))

    def test_missing_section_raises(self) -> None:
        with TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "ai-clean.toml"
            cfg_path.write_text(
                textwrap.dedent(
                    """
                    [spec_backend]
                    type = "butler"

                    [executor]
                    type = "codex_shell"
                    binary = "codex"
                    apply_args = ["apply"]
                    """
                ).strip()
            )
            with self.assertRaises(ValueError):
                load_config(cfg_path)

    def test_unsupported_type(self) -> None:
        with TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "ai-clean.toml"
            _write_config(cfg_path)
            data = cfg_path.read_text().replace('type = "butler"', 'type = "custom"', 1)
            cfg_path.write_text(data)
            with self.assertRaises(ValueError):
                load_config(cfg_path)

    def test_duplicate_threshold_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "ai-clean.toml"
            _write_config(cfg_path)
            base_text = cfg_path.read_text()

            cfg_path.write_text(base_text.replace("window_size = 5", "window_size = 0"))
            with self.assertRaisesRegex(ValueError, "window_size"):
                load_config(cfg_path)

            cfg_path.write_text(
                base_text.replace("min_occurrences = 2", "min_occurrences = 1")
            )
            with self.assertRaisesRegex(ValueError, "min_occurrences"):
                load_config(cfg_path)

    def test_duplicate_ignore_dirs_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "ai-clean.toml"
            _write_config(cfg_path)
            bad_text = cfg_path.read_text().replace(
                'ignore_dirs = [".git", "__pycache__", ".venv"]',
                'ignore_dirs = [".git", ""]',
            )
            cfg_path.write_text(bad_text)
            with self.assertRaisesRegex(ValueError, "ignore_dirs"):
                load_config(cfg_path)

    def test_structure_threshold_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "ai-clean.toml"
            _write_config(cfg_path)
            data = cfg_path.read_text()

            cfg_path.write_text(
                data.replace("max_file_lines = 400", "max_file_lines = 0")
            )
            with self.assertRaisesRegex(ValueError, "max_file_lines"):
                load_config(cfg_path)

            cfg_path.write_text(
                data.replace("max_function_lines = 60", "max_function_lines = -1")
            )
            with self.assertRaisesRegex(ValueError, "max_function_lines"):
                load_config(cfg_path)

    def test_structure_ignore_dirs_merge_and_validation(self) -> None:
        template = textwrap.dedent(
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
            window_size = 5
            min_occurrences = 2
            ignore_dirs = [".git", "__pycache__", ".venv"]

            [analyzers.structure]
            max_file_lines = 400
            max_function_lines = 60
            ignore_dirs = {ignore_dirs}
            """
        ).strip()

        with TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "ai-clean.toml"
            cfg_path.write_text(
                template.format(ignore_dirs='["build", "custom"]') + "\n"
            )
            config = load_config(cfg_path)
            self.assertEqual(
                config.analyzers.structure.ignore_dirs,
                (".git", "__pycache__", ".venv", "build", "custom"),
            )

            cfg_path.write_text(template.format(ignore_dirs='["", "tmp"]') + "\n")
            with self.assertRaisesRegex(ValueError, "ignore_dirs"):
                load_config(cfg_path)

    def test_docstring_threshold_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "ai-clean.toml"
            _write_config(cfg_path)
            base = cfg_path.read_text()

            cfg_path.write_text(
                base.replace(
                    "min_docstring_length = 32",
                    "min_docstring_length = 0",
                )
            )
            with self.assertRaisesRegex(ValueError, "min_docstring_length"):
                load_config(cfg_path)

            cfg_path.write_text(
                base.replace(
                    "min_symbol_lines = 5",
                    "min_symbol_lines = 0",
                )
            )
            with self.assertRaisesRegex(ValueError, "min_symbol_lines"):
                load_config(cfg_path)

    def test_docstring_weak_markers_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "ai-clean.toml"
            _write_config(cfg_path)
            bad = cfg_path.read_text().replace(
                'weak_markers = ["TODO", "fixme"]',
                'weak_markers = ["", " "]',
            )
            cfg_path.write_text(bad)
            with self.assertRaisesRegex(ValueError, "weak_markers"):
                load_config(cfg_path)

    def test_docstring_ignore_dirs_validation(self) -> None:
        template = textwrap.dedent(
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
            window_size = 5
            min_occurrences = 2
            ignore_dirs = [".git", "__pycache__", ".venv"]

            [analyzers.structure]
            max_file_lines = 400
            max_function_lines = 60
            ignore_dirs = [".git", "__pycache__", ".venv"]

            [analyzers.docstring]
            min_docstring_length = 32
            min_symbol_lines = 5
            weak_markers = ["TODO", "fixme"]
            important_symbols_only = true
            ignore_dirs = {ignore_dirs}
            """
        ).strip()

        with TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "ai-clean.toml"
            cfg_path.write_text(
                template.format(ignore_dirs='[".git", "__pycache__", ".venv"]') + "\n"
            )
            load_config(cfg_path)

            cfg_path.write_text(template.format(ignore_dirs='["", "tmp"]') + "\n")
            with self.assertRaisesRegex(ValueError, "ignore_dirs"):
                load_config(cfg_path)

    def test_docstring_important_symbols_flag(self) -> None:
        template = textwrap.dedent(
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
            window_size = 5
            min_occurrences = 2
            ignore_dirs = [".git", "__pycache__", ".venv"]

            [analyzers.structure]
            max_file_lines = 400
            max_function_lines = 60
            ignore_dirs = [".git", "__pycache__", ".venv"]

            [analyzers.docstring]
            min_docstring_length = 32
            min_symbol_lines = 5
            weak_markers = ["TODO", "fixme"]
            important_symbols_only = {flag}
            ignore_dirs = [".git", "__pycache__", ".venv"]
            """
        ).strip()

        with TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "ai-clean.toml"
            cfg_path.write_text(template.format(flag="true") + "\n")
            self.assertTrue(
                load_config(cfg_path).analyzers.docstring.important_symbols_only
            )

            cfg_path.write_text(template.format(flag="false") + "\n")
            self.assertFalse(
                load_config(cfg_path).analyzers.docstring.important_symbols_only
            )

    def test_organize_threshold_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "ai-clean.toml"
            _write_config(cfg_path)
            baseline = cfg_path.read_text()

            cfg_path.write_text(
                baseline.replace("min_group_size = 2", "min_group_size = 1")
            )
            with self.assertRaisesRegex(ValueError, "min_group_size"):
                load_config(cfg_path)

            cfg_path.write_text(
                baseline.replace("max_group_size = 4", "max_group_size = 1")
            )
            with self.assertRaisesRegex(ValueError, "max_group_size"):
                load_config(cfg_path)

            cfg_path.write_text(
                baseline.replace("max_group_size = 4", "max_group_size = 6")
            )
            with self.assertRaisesRegex(ValueError, "max_group_size"):
                load_config(cfg_path)

            cfg_path.write_text(baseline.replace("max_groups = 3", "max_groups = 0"))
            with self.assertRaisesRegex(ValueError, "max_groups"):
                load_config(cfg_path)

    def test_organize_ignore_dirs_validation(self) -> None:
        template = textwrap.dedent(
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
            window_size = 5
            min_occurrences = 2
            ignore_dirs = [".git", "__pycache__", ".venv"]

            [analyzers.structure]
            max_file_lines = 400
            max_function_lines = 60
            ignore_dirs = [".git", "__pycache__", ".venv"]

            [analyzers.docstring]
            min_docstring_length = 32
            min_symbol_lines = 5
            weak_markers = ["TODO", "fixme"]
            important_symbols_only = true
            ignore_dirs = [".git", "__pycache__", ".venv"]

            [analyzers.organize]
            min_group_size = 2
            max_group_size = 4
            max_groups = 3
            ignore_dirs = {ignore_dirs}
            """
        ).strip()

        with TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "ai-clean.toml"
            cfg_path.write_text(
                template.format(ignore_dirs='[".git", "__pycache__", ".venv"]') + "\n"
            )
            load_config(cfg_path)

            cfg_path.write_text(template.format(ignore_dirs='["", "tmp"]') + "\n")
            with self.assertRaisesRegex(ValueError, "ignore_dirs"):
                load_config(cfg_path)

    def test_advanced_config_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "ai-clean.toml"
            _write_config(cfg_path)
            base = cfg_path.read_text()

            cfg_path.write_text(base.replace("max_files = 2", "max_files = 0"))
            with self.assertRaisesRegex(ValueError, "max_files"):
                load_config(cfg_path)

            cfg_path.write_text(
                base.replace("max_suggestions = 4", "max_suggestions = 0")
            )
            with self.assertRaisesRegex(ValueError, "max_suggestions"):
                load_config(cfg_path)

            bad_prompt = (
                'prompt_template = "Findings:\\n{findings}\\nSnippets:\\n{snippets}"'
            )
            cfg_path.write_text(base.replace(bad_prompt, 'prompt_template = ""'))
            with self.assertRaisesRegex(ValueError, "prompt_template"):
                load_config(cfg_path)

            cfg_path.write_text(
                base.replace('codex_model = "gpt-4o-mini"', 'codex_model = ""')
            )
            with self.assertRaisesRegex(ValueError, "codex_model"):
                load_config(cfg_path)

            cfg_path.write_text(base.replace("temperature = 0.3", "temperature = 0"))
            with self.assertRaisesRegex(ValueError, "temperature"):
                load_config(cfg_path)

    def test_advanced_ignore_dirs_validation(self) -> None:
        template = textwrap.dedent(
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
            window_size = 5
            min_occurrences = 2
            ignore_dirs = [".git", "__pycache__", ".venv"]

            [analyzers.structure]
            max_file_lines = 400
            max_function_lines = 60
            ignore_dirs = [".git", "__pycache__", ".venv"]

            [analyzers.docstring]
            min_docstring_length = 32
            min_symbol_lines = 5
            weak_markers = ["TODO", "fixme"]
            important_symbols_only = true
            ignore_dirs = [".git", "__pycache__", ".venv"]

            [analyzers.organize]
            min_group_size = 2
            max_group_size = 4
            max_groups = 3
            ignore_dirs = [".git", "__pycache__", ".venv"]

            [analyzers.advanced]
            max_files = 2
            max_suggestions = 4
            prompt_template = "Findings:\\n{{findings}}\\nSnippets:\\n{{snippets}}"
            codex_model = "gpt-4o-mini"
            temperature = 0.3
            ignore_dirs = {ignore_dirs}
            """
        ).strip()

        with TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "ai-clean.toml"
            cfg_path.write_text(
                template.format(ignore_dirs='[".git", "__pycache__", ".venv"]') + "\n"
            )
            load_config(cfg_path)

            cfg_path.write_text(template.format(ignore_dirs='["", "tmp"]') + "\n")
            with self.assertRaisesRegex(ValueError, "ignore_dirs"):
                load_config(cfg_path)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
