from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ai_clean.config import (
    AiCleanConfig,
    ExecutorConfig,
    GitConfig,
    ReviewConfig,
    SpecBackendConfig,
    TestsConfig,
)
from ai_clean.models import CleanupPlan, Finding, FindingLocation
from ai_clean.planners.orchestrator import plan_from_finding


def _make_config(base_dir: Path) -> AiCleanConfig:
    return AiCleanConfig(
        spec_backend=SpecBackendConfig(type="openspec"),
        executor=ExecutorConfig(type="codex", apply_command=["echo", "{spec_path}"]),
        review=ReviewConfig(type="codex_review"),
        git=GitConfig(base_branch="main", refactor_branch="feature"),
        tests=TestsConfig(default_command="pytest -q"),
        metadata_root=base_dir,
        plans_dir=base_dir / "plans",
        specs_dir=base_dir / "specs",
        executions_dir=base_dir / "executions",
    )


class PlannerOrchestratorStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base_dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_plan_from_finding_persists_using_slugified_id(self) -> None:
        finding = Finding(
            id="src/foo.py:large_file-split",
            category="large_file",
            description="demo",
            locations=[FindingLocation(path="src/foo.py", start_line=1, end_line=2)],
        )
        plan = CleanupPlan(
            id="src/foo.py:large_file-split",
            finding_id=finding.id,
            title="demo",
            intent="intent",
            steps=["step"],
            constraints=["constraint"],
            tests_to_run=["pytest"],
        )

        config = _make_config(self.base_dir)

        with mock.patch(
            "ai_clean.planners.orchestrator._resolve_planner",
            return_value=lambda *_: plan,
        ):
            result = plan_from_finding(finding, config=config)

        expected_path = config.plans_dir / "src-foo.py-large_file-split.json"
        self.assertTrue(expected_path.exists())
        self.assertEqual(result.metadata["stored_at"], expected_path.as_posix())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
