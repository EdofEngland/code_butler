from __future__ import annotations

import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ai_clean.analyzers.organize import propose_organize_groups
from ai_clean.config import OrganizeAnalyzerConfig


class OrganizeAnalyzerTests(unittest.TestCase):
    def test_grouping_is_deterministic_and_within_bounds(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "api_client.py").write_text(
                textwrap.dedent(
                    '''
                    """API client utilities"""
                    import httpx

                    def send_request():
                        return httpx.get("https://example.com")
                    '''
                ).strip()
                + "\n"
            )
            (root / "api_routes.py").write_text(
                textwrap.dedent(
                    '''
                    """API route handlers"""
                    from fastapi import APIRouter

                    router = APIRouter()
                    '''
                ).strip()
                + "\n"
            )
            (root / "logs_writer.py").write_text(
                textwrap.dedent(
                    """
                    import logging

                    LOGGER = logging.getLogger("logs")
                    """
                ).strip()
                + "\n"
            )
            (root / "logs_cleanup.py").write_text(
                textwrap.dedent(
                    '''
                    """Logs cleanup utilities"""
                    from logging import handlers
                    '''
                ).strip()
                + "\n"
            )

            settings = OrganizeAnalyzerConfig(
                min_group_size=2,
                max_group_size=3,
                max_groups=2,
                ignore_dirs=(".git",),
            )

            first = propose_organize_groups(root, settings)
            second = propose_organize_groups(root, settings)
            self.assertEqual(first, second)
            self.assertLessEqual(len(first), settings.max_groups)

            assigned: set[Path] = set()
            for finding in first:
                count = len(finding.locations)
                self.assertGreaterEqual(count, settings.min_group_size)
                self.assertLessEqual(count, settings.max_group_size)
                members = {Path(member) for member in finding.metadata["members"]}
                files = {Path(entry) for entry in finding.metadata.get("files", [])}
                self.assertEqual(
                    members,
                    {location.path for location in finding.locations},
                )
                self.assertEqual(members, files)
                self.assertTrue(assigned.isdisjoint(members))
                assigned.update(members)

    def test_ignore_dirs_and_stable_directories(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tests" / "helper.py").parent.mkdir(parents=True, exist_ok=True)
            (root / "tests" / "helper.py").write_text("import httpx\n")
            (root / "vendor" / "config.py").parent.mkdir(parents=True, exist_ok=True)
            (root / "vendor" / "config.py").write_text("import yaml\n")
            (root / "core_logs.py").write_text("import logging\n")
            (root / "core_output.py").write_text("import logging\n")

            settings = OrganizeAnalyzerConfig(
                min_group_size=2,
                max_group_size=3,
                max_groups=2,
                ignore_dirs=("vendor",),
            )

            findings = propose_organize_groups(root, settings)
            all_members = {
                member for finding in findings for member in finding.metadata["members"]
            }
            self.assertNotIn("vendor/config.py", all_members)
            self.assertNotIn("tests/helper.py", all_members)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
