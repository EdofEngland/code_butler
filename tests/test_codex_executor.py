from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from ai_clean.executors.codex import CodexExecutor


class CodexExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.spec_path = Path(self._tmp.name) / "demo.openspec.yaml"
        self.spec_path.write_text("spec", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_runs_tests_after_successful_apply(self) -> None:
        executor = CodexExecutor(
            apply_command=["echo", "{spec_path}"],
            tests_command=["pytest", "-q"],
        )

        calls: list[list[str]] = []

        def fake_run(cmd, capture_output, text, check):
            calls.append(list(cmd))
            if len(calls) == 1:
                return SimpleNamespace(
                    returncode=0,
                    stdout="apply-ok",
                    stderr="apply-warn",
                )
            return SimpleNamespace(
                returncode=0,
                stdout="tests-ok",
                stderr="",
            )

        with mock.patch(
            "ai_clean.executors.codex.subprocess.run", side_effect=fake_run
        ):
            result = executor.apply_spec(self.spec_path.as_posix())

        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][0], "echo")
        self.assertEqual(Path(calls[0][1]).resolve(), self.spec_path.resolve())
        self.assertEqual(result.tests_passed, True)
        self.assertIn("== TESTS ==", result.stdout)
        self.assertIn("tests-ok", result.stdout)
        self.assertIn("apply-warn", result.stderr)
        self.assertEqual(result.metadata["tests"]["returncode"], 0)

    def test_skips_tests_when_apply_fails(self) -> None:
        executor = CodexExecutor(
            apply_command=["echo", "{spec_path}"],
            tests_command=["pytest"],
        )

        with mock.patch(
            "ai_clean.executors.codex.subprocess.run",
            return_value=SimpleNamespace(returncode=1, stdout="", stderr="boom"),
        ):
            with mock.patch.object(executor, "_run_tests") as mocked_tests:
                result = executor.apply_spec(self.spec_path.as_posix())

        mocked_tests.assert_not_called()
        self.assertFalse(result.success)
        self.assertIsNone(result.tests_passed)
        self.assertEqual(result.metadata["tests"]["reason"], "apply_failed")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
