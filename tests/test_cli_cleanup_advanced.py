from __future__ import annotations

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from ai_clean import cli


class CleanupAdvancedCliTests(unittest.TestCase):
    def test_command_is_disabled_and_does_not_invoke_runner(self) -> None:
        with TemporaryDirectory() as tmp:
            findings_json = Path(tmp) / "findings.json"
            findings_json.write_text("[]", encoding="utf-8")
            stdout = StringIO()
            stderr = StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = cli.main(
                    [
                        "cleanup-advanced",
                        "--root",
                        tmp,
                        "--findings-json",
                        str(findings_json),
                    ]
                )

        self.assertEqual(exit_code, 1)
        self.assertEqual("", stdout.getvalue().strip())
        stderr_output = stderr.getvalue()
        self.assertIn("Advanced cleanup is disabled", stderr_output)
        self.assertIn("/cleanup-advanced", stderr_output)
        self.assertIn(str(findings_json.resolve()), stderr_output)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
