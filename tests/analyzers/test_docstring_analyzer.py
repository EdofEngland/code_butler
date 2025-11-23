from __future__ import annotations

import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ai_clean.analyzers import find_docstring_gaps
from ai_clean.config import DocstringAnalyzerConfig


class DocstringAnalyzerTests(unittest.TestCase):
    def test_detects_missing_and_weak_docstrings(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "alpha.py").write_text(
                textwrap.dedent(
                    '''
                    def missing_func():
                        return 1

                    def weak_marker():
                        """TODO: write documentation"""
                        return 2

                    class PublicClass:
                        def method(self):
                            return True
                    '''
                ).strip()
                + "\n"
            )

            settings = DocstringAnalyzerConfig(
                min_docstring_length=12,
                min_symbol_lines=1,
                weak_markers=("todo",),
                important_symbols_only=False,
                ignore_dirs=(".git",),
            )

            first = find_docstring_gaps(root, settings)
            second = find_docstring_gaps(root, settings)
            self.assertEqual(first, second)
            self.assertGreaterEqual(len(first), 4)

            module_finding = first[0]
            self.assertEqual(module_finding.category, "missing_docstring")
            self.assertEqual(module_finding.locations[0].path, Path("alpha.py"))
            self.assertEqual(module_finding.locations[0].start_line, 1)

            categories = [finding.category for finding in first]
            self.assertIn("weak_docstring", categories)

            weak_finding = next(f for f in first if f.category == "weak_docstring")
            self.assertIn("weak_marker", weak_finding.description)
            self.assertEqual(weak_finding.metadata["symbol_type"], "function")
            self.assertEqual(weak_finding.metadata["symbol_name"], "weak_marker")
            self.assertTrue(
                weak_finding.metadata["docstring_preview"].startswith("TODO")
            )

    def test_min_symbol_lines_respected_when_enabled(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "beta.py").write_text(
                textwrap.dedent(
                    """
                    def compact():
                        return 1
                    """
                ).strip()
                + "\n"
            )

            strict_settings = DocstringAnalyzerConfig(
                min_docstring_length=8,
                min_symbol_lines=5,
                weak_markers=("todo",),
                important_symbols_only=True,
                ignore_dirs=(".git",),
            )
            strict_findings = find_docstring_gaps(root, strict_settings)
            self.assertEqual(len(strict_findings), 1)
            self.assertEqual(strict_findings[0].metadata["symbol_type"], "module")

            relaxed_settings = DocstringAnalyzerConfig(
                min_docstring_length=8,
                min_symbol_lines=5,
                weak_markers=("todo",),
                important_symbols_only=False,
                ignore_dirs=(".git",),
            )
            findings = find_docstring_gaps(root, relaxed_settings)
            self.assertEqual(len(findings), 2)
            self.assertEqual(
                [f.metadata["symbol_type"] for f in findings],
                ["module", "function"],
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
