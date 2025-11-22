from __future__ import annotations

import unittest
from pathlib import Path

from ai_clean.config import (
    AdvancedAnalyzerConfig,
    AiCleanConfig,
    AnalyzersConfig,
    DocstringAnalyzerConfig,
    DuplicateAnalyzerConfig,
    ExecutorConfig,
    GitConfig,
    OrganizeAnalyzerConfig,
    ReviewConfig,
    SpecBackendConfig,
    StructureAnalyzerConfig,
    TestsConfig,
)
from ai_clean.models import Finding, FindingLocation
from ai_clean.planners import plan_large_file, plan_long_function
from ai_clean.planners.structure import ClusteredTargets, _cluster_module_targets


def _make_config(default_command: str = "pytest -q") -> AiCleanConfig:
    analyzers = AnalyzersConfig(
        duplicate=DuplicateAnalyzerConfig(
            window_size=3,
            min_occurrences=2,
            ignore_dirs=(".git",),
        ),
        structure=StructureAnalyzerConfig(
            max_file_lines=400,
            max_function_lines=60,
            ignore_dirs=(".git",),
        ),
        docstring=DocstringAnalyzerConfig(
            min_docstring_length=32,
            min_symbol_lines=5,
            weak_markers=("todo",),
            important_symbols_only=True,
            ignore_dirs=(".git",),
        ),
        organize=OrganizeAnalyzerConfig(
            min_group_size=2,
            max_group_size=5,
            max_groups=3,
            ignore_dirs=(".git",),
        ),
        advanced=AdvancedAnalyzerConfig(
            max_files=1,
            max_suggestions=1,
            prompt_template="",
            codex_model="gpt-4o-mini",
            temperature=0.1,
            ignore_dirs=(".git",),
        ),
    )
    return AiCleanConfig(
        spec_backend=SpecBackendConfig(
            type="butler",
            default_batch_group="default",
            specs_dir=Path(".ai-clean/specs"),
        ),
        executor=ExecutorConfig(
            type="codex_shell",
            binary="codex",
            apply_args=("apply",),
            results_dir=Path(".ai-clean/results"),
        ),
        review=ReviewConfig(type="codex_review", mode="summaries"),
        git=GitConfig(base_branch="main", refactor_branch="refactor/ai-clean"),
        tests=TestsConfig(default_command=default_command),
        analyzers=analyzers,
        metadata_root=Path(".ai-clean"),
        plans_dir=Path(".ai-clean/plans"),
        specs_dir=Path(".ai-clean/specs"),
        results_dir=Path(".ai-clean/results"),
    )


def _make_finding(
    finding_id: str,
    *,
    category: str,
    spans: list[tuple[int, int]],
    metadata: dict[str, object],
) -> Finding:
    locations = [
        FindingLocation(path=Path("src/module.py"), start_line=start, end_line=end)
        for start, end in spans
    ]
    return Finding(
        id=finding_id,
        category=category,
        description=f"{category} finding",
        locations=locations,
        metadata=dict(metadata),
    )


class StructurePlannerTests(unittest.TestCase):
    def test_plan_large_file_builds_split_plan(self) -> None:
        finding = _make_finding(
            "lf-alpha",
            category="large_file",
            spans=[(5, 80), (120, 200)],
            metadata={
                "line_count": 500,
                "threshold": 400,
                "test_command": "pytest src/module.py",
            },
        )
        plan = plan_large_file(finding, _make_config())[0]
        self.assertEqual(plan.id, "lf-alpha-split")
        self.assertEqual(plan.tests_to_run, ["pytest src/module.py"])
        self.assertIn("re-export", "".join(plan.constraints))
        module_paths = [
            entry["module_path"] for entry in plan.metadata["module_targets"]
        ]
        self.assertEqual(module_paths, ["src/module_1.py", "src/module_2.py"])
        self.assertIn("src/module_1.py", plan.steps[1])
        self.assertIn("src/module.py", plan.steps[0])
        self.assertEqual(plan.metadata["line_count"], 500)
        self.assertFalse(plan.metadata["leftover_segments"])

    def test_cluster_module_targets_surfaces_leftovers(self) -> None:
        locations = [
            FindingLocation(
                path=Path("src/module.py"), start_line=start, end_line=start + 10
            )
            for start in (1, 40, 80, 160)
        ]
        cluster = _cluster_module_targets(locations, max_modules=3)
        self.assertIsInstance(cluster, ClusteredTargets)
        self.assertEqual(
            [path.as_posix() for path in cluster.primary_modules],
            ["src/module_1.py", "src/module_2.py", "src/module_3.py"],
        )
        self.assertEqual(len(cluster.leftover_segments), 1)
        self.assertEqual(cluster.leftover_segments[0].start_line, 160)

        finding = _make_finding(
            "lf-beta",
            category="large_file",
            spans=[(1, 40), (41, 80), (81, 120), (121, 160)],
            metadata={"line_count": 480, "threshold": 400},
        )
        plan = plan_large_file(finding, _make_config())[0]
        self.assertTrue(plan.metadata["leftover_segments"])
        self.assertTrue(plan.metadata["follow_up_required"])

    def test_plan_long_function_references_line_span(self) -> None:
        segments = [
            {"start_line": 30, "end_line": 44, "label": "loop"},
            {"start_line": 45, "end_line": 60, "label": "cleanup"},
        ]
        finding = _make_finding(
            "lfn-alpha",
            category="long_function",
            spans=[(30, 90)],
            metadata={
                "qualified_name": "app.module.process_data",
                "line_count": 120,
                "segments": segments,
            },
        )
        plan = plan_long_function(finding, _make_config())[0]
        self.assertEqual(plan.id, "lfn-alpha-helpers")
        self.assertEqual(plan.tests_to_run, ["pytest -q"])
        self.assertIn("process_data", plan.title)
        self.assertIn("src/module.py:30-90", plan.steps[0])
        self.assertIn("process_data_", plan.steps[1])
        self.assertIn("src/module.py", plan.steps[2])
        self.assertEqual(plan.metadata["helper_prefix"], "process_data")
        self.assertEqual(plan.metadata["scope"], "single_function")
        self.assertEqual(plan.metadata["segments"], segments)

    def test_plan_large_file_missing_metadata_raises(self) -> None:
        finding = _make_finding(
            "lf-gamma",
            category="large_file",
            spans=[(1, 40)],
            metadata={"threshold": 400},
        )
        with self.assertRaisesRegex(ValueError, "line_count"):
            plan_large_file(finding, _make_config())

    def test_plan_large_file_requires_locations(self) -> None:
        finding = Finding(
            id="lf-empty",
            category="large_file",
            description="missing locations",
            locations=[],
            metadata={"line_count": 500, "threshold": 400},
        )
        with self.assertRaisesRegex(ValueError, "at least one location"):
            plan_large_file(finding, _make_config())

    def test_plan_long_function_requires_single_location(self) -> None:
        finding = _make_finding(
            "lfn-beta",
            category="long_function",
            spans=[(10, 40), (41, 80)],
            metadata={"qualified_name": "app.view.render", "line_count": 120},
        )
        with self.assertRaisesRegex(ValueError, "exactly one location"):
            plan_long_function(finding, _make_config())

    def test_plan_long_function_missing_metadata_raises(self) -> None:
        finding = _make_finding(
            "lfn-gamma",
            category="long_function",
            spans=[(5, 30)],
            metadata={"line_count": 120},
        )
        with self.assertRaisesRegex(ValueError, "qualified_name"):
            plan_long_function(finding, _make_config())

    def test_missing_test_command_raises(self) -> None:
        finding = _make_finding(
            "lf-delta",
            category="large_file",
            spans=[(5, 20)],
            metadata={"line_count": 120, "threshold": 60},
        )
        with self.assertRaisesRegex(ValueError, "test command"):
            plan_large_file(finding, _make_config(default_command=""))

        long_finding = _make_finding(
            "lfn-delta",
            category="long_function",
            spans=[(10, 50)],
            metadata={"qualified_name": "pkg.module.call", "line_count": 70},
        )
        with self.assertRaisesRegex(ValueError, "test command"):
            plan_long_function(long_finding, _make_config(default_command=""))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
