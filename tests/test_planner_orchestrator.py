from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ai_clean.config import (
    AiCleanConfig,
    ExecutorBackendConfig,
    ExecutorConfig,
    GitConfig,
    ReviewConfig,
    SpecBackendConfig,
    TestsConfig,
)
from ai_clean.models import CleanupPlan, Finding, FindingLocation
from ai_clean.planners.orchestrator import PlannerError, plan_from_finding


def _make_config(base_dir: Path) -> AiCleanConfig:
    return AiCleanConfig(
        spec_backend=SpecBackendConfig(type="openspec"),
        executor=ExecutorConfig(type="codex", apply_command=["echo", "{spec_path}"]),
        executor_backend=ExecutorBackendConfig(
            type="codex",
            command_prefix="/openspec-apply",
            prompt_hint="/prompts:openspec-apply",
        ),
        review=ReviewConfig(type="codex_review"),
        git=GitConfig(base_branch="main", refactor_branch="feature"),
        tests=TestsConfig(default_command="pytest -q"),
        metadata_root=base_dir,
        plans_dir=base_dir / "plans",
        specs_dir=base_dir / "specs",
        executions_dir=base_dir / "executions",
        max_plan_files=5,
        max_plan_lines=400,
        allow_global_rename=False,
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

    def test_plan_from_finding_enforces_file_limit(self) -> None:
        finding = Finding(
            id="multi-files",
            category="missing_docstring",
            description="multi",
            locations=[
                FindingLocation(path="pkg/a.py", start_line=1, end_line=5),
                FindingLocation(path="pkg/b.py", start_line=1, end_line=5),
            ],
        )
        config = _make_config(self.base_dir)
        config.max_plan_files = 1

        with self.assertRaises(PlannerError):
            plan_from_finding(finding, config=config)

    def test_plan_from_finding_enforces_line_limit(self) -> None:
        finding = Finding(
            id="too-large",
            category="missing_docstring",
            description="multi",
            locations=[
                FindingLocation(path="pkg/a.py", start_line=1, end_line=500),
            ],
        )
        config = _make_config(self.base_dir)
        config.max_plan_lines = 10

        with self.assertRaises(PlannerError):
            plan_from_finding(finding, config=config)

    def test_plan_from_finding_requires_single_concern_for_docstrings(self) -> None:
        finding = Finding(
            id="doc-many",
            category="missing_docstring",
            description="multi",
            locations=[
                FindingLocation(path="pkg/a.py", start_line=1, end_line=2),
                FindingLocation(path="pkg/b.py", start_line=3, end_line=4),
            ],
        )
        config = _make_config(self.base_dir)
        config.max_plan_files = 5

        with self.assertRaises(PlannerError):
            plan_from_finding(finding, config=config)

    def test_plan_from_finding_blocks_global_rename_when_disabled(self) -> None:
        finding = Finding(
            id="adv-rename",
            category="advanced_cleanup",
            description="rename",
            locations=[FindingLocation(path="pkg/a.py", start_line=1, end_line=2)],
        )
        plan = CleanupPlan(
            id="renamer",
            finding_id=finding.id,
            title="Rename API",
            intent="Rename Foo to Bar",
            steps=["Rename Foo class to Bar across modules."],
            constraints=[],
            tests_to_run=[],
        )
        config = _make_config(self.base_dir)

        with mock.patch(
            "ai_clean.planners.orchestrator._resolve_planner",
            return_value=lambda *_: plan,
        ):
            with self.assertRaises(PlannerError):
                plan_from_finding(finding, config=config)

    def test_plan_limits_use_plan_metadata_for_duplicates(self) -> None:
        finding = Finding(
            id="dup-many",
            category="duplicate_block",
            description="dup",
            locations=[
                FindingLocation(path="pkg/a.py", start_line=1, end_line=2),
                FindingLocation(path="pkg/b.py", start_line=3, end_line=4),
                FindingLocation(path="pkg/c.py", start_line=5, end_line=6),
            ],
        )
        plan = CleanupPlan(
            id="dup-plan",
            finding_id=finding.id,
            title="dup",
            intent="dup",
            steps=[],
            constraints=[],
            tests_to_run=[],
            metadata={
                "covered_occurrences": [
                    {"path": "pkg/a.py", "start_line": 1, "end_line": 2},
                ]
            },
        )
        config = _make_config(self.base_dir)
        config.max_plan_files = 1

        with mock.patch(
            "ai_clean.planners.orchestrator._resolve_planner",
            return_value=lambda *_: plan,
        ):
            result = plan_from_finding(finding, config=config)

        self.assertEqual(result.id, "dup-plan")

    def test_plan_limits_fail_when_metadata_exceeds_limit(self) -> None:
        finding = Finding(
            id="dup-many",
            category="duplicate_block",
            description="dup",
            locations=[
                FindingLocation(path="pkg/a.py", start_line=1, end_line=2),
                FindingLocation(path="pkg/b.py", start_line=3, end_line=4),
            ],
        )
        plan = CleanupPlan(
            id="dup-plan",
            finding_id=finding.id,
            title="dup",
            intent="dup",
            steps=[],
            constraints=[],
            tests_to_run=[],
            metadata={
                "covered_occurrences": [
                    {"path": "pkg/a.py", "start_line": 1, "end_line": 2},
                    {"path": "pkg/b.py", "start_line": 3, "end_line": 4},
                ]
            },
        )
        config = _make_config(self.base_dir)
        config.max_plan_files = 1

        with mock.patch(
            "ai_clean.planners.orchestrator._resolve_planner",
            return_value=lambda *_: plan,
        ):
            with self.assertRaises(PlannerError):
                plan_from_finding(finding, config=config)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
