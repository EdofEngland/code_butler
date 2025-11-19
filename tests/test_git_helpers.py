from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

from ai_clean.git_helpers import GitError, ensure_on_refactor_branch, get_diff_stat


class GitHelpersTests(unittest.TestCase):
    @mock.patch("ai_clean.git_helpers._run_git")
    def test_ensure_on_refactor_branch_noop(self, run_git: mock.MagicMock) -> None:
        run_git.return_value = SimpleNamespace(stdout="refactor\n")
        ensure_on_refactor_branch("main", "refactor")
        run_git.assert_called_once_with(["rev-parse", "--abbrev-ref", "HEAD"])

    @mock.patch("ai_clean.git_helpers._run_git")
    def test_ensure_on_refactor_branch_creates_branch(
        self, run_git: mock.MagicMock
    ) -> None:
        outputs = [
            SimpleNamespace(stdout="main\n"),  # rev-parse current branch
            SimpleNamespace(stdout=""),  # fetch
            GitError("missing branch"),  # rev-parse refactor -> fail
            SimpleNamespace(stdout=""),  # branch
            SimpleNamespace(stdout=""),  # checkout
            SimpleNamespace(stdout=""),  # merge
        ]

        def _side_effect(args):
            result = outputs.pop(0)
            if isinstance(result, GitError):
                raise result
            return result

        run_git.side_effect = _side_effect
        ensure_on_refactor_branch("main", "refactor")

    @mock.patch("ai_clean.git_helpers._run_git")
    def test_get_diff_stat_combines_outputs(self, run_git: mock.MagicMock) -> None:
        run_git.side_effect = [
            SimpleNamespace(stdout=" file_a.py | 2 +-\n"),
            SimpleNamespace(stdout=" file_b.py | 1 +\n"),
        ]
        text = get_diff_stat()
        self.assertTrue(text.startswith("Changes:"))
        self.assertIn("file_a.py", text)
        self.assertIn("file_b.py", text)

    @mock.patch("ai_clean.git_helpers._run_git", side_effect=GitError("failure"))
    def test_get_diff_stat_raises_on_git_error(self, run_git: mock.MagicMock) -> None:
        with self.assertRaises(GitError):
            get_diff_stat()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
