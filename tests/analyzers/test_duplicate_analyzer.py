from __future__ import annotations

import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ai_clean.analyzers import find_duplicate_blocks
from ai_clean.config import DuplicateAnalyzerConfig


def _write_file(root: Path, relative: str, contents: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(contents).strip() + "\n")
    return path


class DuplicateAnalyzerTests(unittest.TestCase):
    def test_detects_duplicates_with_deterministic_output(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            snippet = """
            def shared_block():
                total = 1
                return total
            """
            _write_file(root, "alpha.py", snippet)
            _write_file(root, "beta.py", snippet)

            settings = DuplicateAnalyzerConfig(
                window_size=3,
                min_occurrences=2,
                ignore_dirs=(".git", "__pycache__"),
            )

            first_run = find_duplicate_blocks(root, settings)
            second_run = find_duplicate_blocks(root, settings)

            self.assertEqual(first_run, second_run)
            self.assertEqual(len(first_run), 1)

            finding = first_run[0]
            self.assertEqual(finding.category, "duplicate_block")
            self.assertRegex(finding.id, r"^dup-[0-9a-f]{8}$")
            self.assertEqual(len(finding.locations), 2)
            self.assertEqual(finding.locations[0].path, Path("alpha.py"))
            self.assertEqual(finding.locations[0].start_line, 1)
            self.assertEqual(finding.locations[0].end_line, 3)
            self.assertEqual(finding.locations[1].path, Path("beta.py"))
            self.assertEqual(finding.metadata["window_size"], 3)
            self.assertTrue(
                finding.metadata["normalized_preview"].startswith("def shared_block():")
            )
            self.assertEqual(
                finding.metadata["relative_paths"],
                ["alpha.py", "beta.py"],
            )
            self.assertEqual(
                finding.description,
                "Found 2 duplicate windows starting with 'def shared_block():'",
            )

    def test_ignore_dirs_prevents_duplicates_from_ignored_paths(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            snippet = """
            value = 1
            print(value)
            """
            _write_file(root, "main.py", snippet)
            _write_file(root, "ignored/skip.py", snippet)

            allow_settings = DuplicateAnalyzerConfig(
                window_size=2,
                min_occurrences=2,
                ignore_dirs=(".git",),
            )
            baseline = find_duplicate_blocks(root, allow_settings)
            self.assertEqual(len(baseline), 1)

            filtered_settings = DuplicateAnalyzerConfig(
                window_size=2,
                min_occurrences=2,
                ignore_dirs=(".git", "ignored"),
            )
            filtered = find_duplicate_blocks(root, filtered_settings)
            self.assertEqual(filtered, [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
