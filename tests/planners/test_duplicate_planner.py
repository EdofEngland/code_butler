from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from ai_clean.config import (
    AdvancedAnalyzerConfig,
    AiCleanConfig,
    AnalyzersConfig,
    DocstringAnalyzerConfig,
    DuplicateAnalyzerConfig,
    ExecutorConfig,
    GitConfig,
    OrganizeAnalyzerConfig,
    PlanLimitsConfig,
    ReviewConfig,
    SpecBackendConfig,
    StructureAnalyzerConfig,
    TestsConfig,
)
from ai_clean.models import Finding, FindingLocation
from ai_clean.planners import plan_duplicate_blocks


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
    plan_limits = PlanLimitsConfig(
        max_files_per_plan=1,
        max_changed_lines_per_plan=200,
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
        plan_limits=plan_limits,
        analyzers=analyzers,
        metadata_root=Path(".ai-clean"),
        plans_dir=Path(".ai-clean/plans"),
        specs_dir=Path(".ai-clean/specs"),
        results_dir=Path(".ai-clean/results"),
    )


def _make_location(path: str, start: int, end: int) -> FindingLocation:
    return FindingLocation(path=Path(path), start_line=start, end_line=end)


def _make_finding(
    finding_id: str,
    spans: list[tuple[str, int, int]],
    *,
    description: str = "Found duplicate windows",
    metadata: dict[str, object] | None = None,
) -> Finding:
    return Finding(
        id=finding_id,
        category="duplicate_block",
        description=description,
        locations=[_make_location(*span) for span in spans],
        metadata=dict(metadata or {}),
    )


class DuplicatePlannerTests(unittest.TestCase):
    def test_single_file_duplicate_creates_one_plan(self) -> None:
        finding = _make_finding(
            "dup-alpha",
            [
                ("src/app.py", 10, 14),
                ("src/app.py", 30, 34),
            ],
            metadata={"test_command": "pytest src/app.py"},
        )
        plans = plan_duplicate_blocks([finding], _make_config())
        self.assertEqual(len(plans), 1)
        plan = plans[0]
        self.assertEqual(plan.id, "dup-alpha-helper-1")
        self.assertEqual(plan.tests_to_run, ["pytest src/app.py"])
        self.assertEqual(plan.metadata["helper_path"], "src/app.py")
        self.assertEqual(len(plan.steps), 4)
        self.assertIn("Decide the", plan.steps[0])
        self.assertIn("Create helper", plan.steps[1])
        self.assertIn("Replace lines", plan.steps[2])
        self.assertEqual(
            plan.metadata["occurrences"],
            [
                {"path": "src/app.py", "start_line": 10, "end_line": 14},
                {"path": "src/app.py", "start_line": 30, "end_line": 34},
            ],
        )

    def test_multifile_duplicates_split_into_multiple_plans(self) -> None:
        finding = _make_finding(
            "dup-beta",
            [
                ("src/foo/a.py", 5, 9),
                ("src/foo/b.py", 15, 19),
                ("src/foo/c.py", 25, 29),
                ("src/foo/d.py", 35, 39),
                ("src/foo/e.py", 45, 49),
            ],
        )
        plans = plan_duplicate_blocks([finding], _make_config())
        self.assertEqual(len(plans), 2)
        helper_paths = {plan.metadata["helper_path"] for plan in plans}
        self.assertEqual(helper_paths, {"src/foo/helpers.py"})
        self.assertEqual(len(plans[0].metadata["occurrences"]), 3)
        self.assertEqual(len(plans[1].metadata["occurrences"]), 2)
        self.assertLess(
            plans[0].metadata["occurrences"][0]["start_line"],
            plans[1].metadata["occurrences"][0]["start_line"],
        )

    def test_fallback_to_first_path_when_no_shared_parent(self) -> None:
        finding = _make_finding(
            "dup-gamma",
            [
                ("alpha/file_a.py", 1, 5),
                ("beta/file_b.py", 2, 6),
            ],
        )
        plan = plan_duplicate_blocks([finding], _make_config())[0]
        self.assertEqual(plan.metadata["helper_path"], "alpha/file_a.py")

    def test_occurrence_ordering_is_deterministic(self) -> None:
        finding = _make_finding(
            "dup-delta",
            [
                ("src/zeta.py", 20, 22),
                ("src/alpha.py", 1, 3),
                ("src/alpha.py", 5, 7),
            ],
        )
        plan = plan_duplicate_blocks([finding], _make_config())[0]
        ordered_paths = [entry["path"] for entry in plan.metadata["occurrences"]]
        self.assertEqual(ordered_paths, ["src/alpha.py", "src/alpha.py", "src/zeta.py"])

    def test_plans_sorted_by_helper_path(self) -> None:
        first = _make_finding("dup-epsilon", [("src/zeta/foo.py", 1, 3)])
        second = _make_finding("dup-theta", [("src/alpha/bar.py", 4, 6)])
        plans = plan_duplicate_blocks([first, second], _make_config())
        self.assertEqual(
            [plan.finding_id for plan in plans], ["dup-theta", "dup-epsilon"]
        )

    def test_missing_test_command_raises(self) -> None:
        finding = _make_finding("dup-eta", [("src/app.py", 1, 4)])
        with self.assertRaises(ValueError):
            plan_duplicate_blocks([finding], _make_config(default_command=""))

    def test_helper_path_mismatch_raises(self) -> None:
        finding = _make_finding("dup-theta", [("src/app.py", 1, 3)])
        fake_clone = finding.model_copy(
            update={
                "metadata": {"_helper_path": "src/wrong.py", "_plan_chunk_index": 1},
            }
        )
        with patch(
            "ai_clean.planners.duplicate._group_duplicates",
            return_value={("src/app.py", "dup-theta"): [fake_clone]},
        ):
            with self.assertRaises(ValueError):
                plan_duplicate_blocks([finding], _make_config())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
