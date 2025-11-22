from __future__ import annotations

import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ai_clean import cli
from ai_clean.models import Finding, FindingLocation


class CleanupAdvancedCliTests(unittest.TestCase):
    def test_text_output(self) -> None:
        sample = _sample_finding()
        with (
            TemporaryDirectory() as tmp,
            patch("ai_clean.cli.run_advanced_cleanup", return_value=[sample]),
        ):
            findings_json = Path(tmp) / "findings.json"
            findings_json.write_text("[]")
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = cli.main(
                    [
                        "cleanup-advanced",
                        "--root",
                        tmp,
                        "--findings-json",
                        str(findings_json),
                    ]
                )
        self.assertEqual(exit_code, 0)
        self.assertIn(sample.id, stdout.getvalue())

    def test_json_output(self) -> None:
        sample = _sample_finding()
        with (
            TemporaryDirectory() as tmp,
            patch("ai_clean.cli.run_advanced_cleanup", return_value=[sample]),
        ):
            findings_json = Path(tmp) / "findings.json"
            findings_json.write_text("[]")
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = cli.main(
                    [
                        "cleanup-advanced",
                        "--root",
                        tmp,
                        "--findings-json",
                        str(findings_json),
                        "--json",
                    ]
                )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload[0]["id"], sample.id)

    def test_defaults_config_to_root(self) -> None:
        with (
            TemporaryDirectory() as tmp,
            patch(
                "ai_clean.cli.run_advanced_cleanup", return_value=[]
            ) as mocked_runner,
        ):
            root = Path(tmp) / "repo"
            root.mkdir()
            (root / "ai-clean.toml").write_text("placeholder config", encoding="utf-8")
            findings_json = Path(tmp) / "findings.json"
            findings_json.write_text("[]")
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = cli.main(
                    [
                        "cleanup-advanced",
                        "--root",
                        str(root),
                        "--findings-json",
                        str(findings_json),
                    ]
                )

        self.assertEqual(exit_code, 0)
        mocked_runner.assert_called_once()
        call_args = mocked_runner.call_args[0]
        expected_root = root.resolve()
        self.assertEqual(call_args[0], expected_root)
        self.assertEqual(call_args[1], expected_root / "ai-clean.toml")


def _sample_finding() -> Finding:
    return Finding(
        id="adv-1234",
        category="advanced_cleanup",
        description="Extract constant",
        locations=[FindingLocation(path=Path("module.py"), start_line=1, end_line=2)],
        metadata={},
    )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
