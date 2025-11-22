from __future__ import annotations

import textwrap
import unittest
from hashlib import sha1
from pathlib import Path
from tempfile import TemporaryDirectory

from ai_clean.analyzers.structure import (
    _iter_large_files,
    _iter_long_functions,
    _iter_python_files,
    find_structure_issues,
)
from ai_clean.config import StructureAnalyzerConfig


class StructureAnalyzerTests(unittest.TestCase):
    def test_detects_large_files_and_long_functions(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "big.py").write_text(
                "\n".join(f"line {i}" for i in range(6)) + "\n"
            )
            (root / "funcs.py").write_text(
                textwrap.dedent(
                    """
                    def long_runner():
                        total = 0
                        total += 1
                        total += 2
                        total += 3
                    """
                ).strip()
                + "\n"
            )

            settings = StructureAnalyzerConfig(
                max_file_lines=5,
                max_function_lines=3,
                ignore_dirs=(".git",),
            )

            findings = find_structure_issues(root, settings)
            self.assertEqual(len(findings), 2)

            large = findings[0]
            self.assertEqual(large.category, "large_file")
            expected_large_id = "large-file-" + sha1(b"big.py").hexdigest()[:8]
            self.assertEqual(large.id, expected_large_id)
            self.assertEqual(large.locations[0].path, Path("big.py"))
            self.assertEqual(large.locations[0].start_line, 1)
            self.assertEqual(large.locations[0].end_line, 6)
            self.assertEqual(large.metadata["line_count"], 6)
            self.assertEqual(
                large.description,
                "File big.py has 6 lines (> 5)",
            )

            func = findings[1]
            self.assertEqual(func.category, "long_function")
            source_id = "funcs.py::long_runner"
            expected_func_id = "long-func-" + sha1(source_id.encode()).hexdigest()[:8]
            self.assertEqual(func.id, expected_func_id)
            self.assertEqual(func.locations[0].path, Path("funcs.py"))
            self.assertEqual(func.locations[0].start_line, 1)
            self.assertEqual(func.metadata["qualified_name"], "long_runner")
            self.assertEqual(func.metadata["line_count"], 5)
            self.assertIn("Function long_runner has 5 lines", func.description)

    def test_iter_helpers_respect_ignore_dirs(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "kept.py").write_text(
                textwrap.dedent(
                    """
                    def short():
                        return 1

                    value = 3
                    value += 1
                    """
                ).strip()
                + "\n"
            )
            ignored_dir = root / "ignored"
            ignored_dir.mkdir()
            (ignored_dir / "hide.py").write_text("x = 1\n" * 20)

            entries = _iter_python_files(root, ("ignored",))
            self.assertEqual(
                [entry.relative_path for entry in entries], [Path("kept.py")]
            )

            large_records = _iter_large_files(entries, max_file_lines=3)
            self.assertEqual(len(large_records), 1)
            self.assertEqual(large_records[0].relative_path, Path("kept.py"))

            long_records = _iter_long_functions(entries, max_function_lines=1)
            self.assertEqual(len(long_records), 1)
            self.assertEqual(long_records[0].qualified_name, "short")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
