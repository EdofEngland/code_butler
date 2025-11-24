from __future__ import annotations

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ai_clean import cli
from ai_clean.models import ExecutionResult


class ApplyManualExitCodeTests(unittest.TestCase):
    def test_apply_command_returns_success_when_manual_execution_required(self) -> None:
        result = ExecutionResult(
            spec_id="plan-1-spec",
            plan_id="plan-1",
            success=False,
            tests_passed=None,
            stdout="Manual execution required",
            stderr="",
            git_diff=None,
            metadata={
                "manual_execution_required": True,
                "slash_command": "codex /butler-exec /tmp/spec",
            },
        )

        with (
            TemporaryDirectory() as tmp,
            patch(
                "ai_clean.cli.apply_plan", return_value=(result, "/tmp/spec")
            ) as mock_apply,
        ):
            stdout = StringIO()
            stderr = StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = cli.main(["apply", "plan-1", "--root", tmp])

        self.assertEqual(exit_code, 0)
        mock_apply.assert_called_once()
        self.assertIn("Run in Codex:", stdout.getvalue())
        self.assertNotIn("Failed to", stderr.getvalue())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
