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
    PlanLimitsConfig,
    ReviewConfig,
    SpecBackendConfig,
    StructureAnalyzerConfig,
    TestsConfig,
)
from ai_clean.models import Finding, FindingLocation
from ai_clean.planners import plan_docstring_fix


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


def _make_location(
    start_line: int, end_line: int, path: str = "src/sample.py"
) -> FindingLocation:
    return FindingLocation(path=Path(path), start_line=start_line, end_line=end_line)


def _make_doc_finding(
    category: str,
    *,
    metadata_override: dict[str, object] | None = None,
    start_line: int = 10,
    end_line: int = 40,
) -> Finding:
    base_metadata: dict[str, object] = {
        "symbol_type": "function",
        "qualified_name": "pkg.module.process_data",
        "symbol_name": "process_data",
        "docstring_preview": "" if category == "missing_docstring" else "Old text",
        "lines_of_code": 42,
    }
    if metadata_override:
        base_metadata.update(metadata_override)
    return Finding(
        id=f"{category}-abc123",
        category=category,
        description=f"{category} finding",
        locations=[_make_location(start_line, end_line)],
        metadata=base_metadata,
    )


class DocstringPlannerTests(unittest.TestCase):
    def test_missing_docstring_plan_contains_expected_metadata(self) -> None:
        finding = _make_doc_finding("missing_docstring")
        plan_list = plan_docstring_fix(finding, _make_config())
        self.assertEqual(len(plan_list), 1)
        plan = plan_list[0]
        self.assertTrue(plan.id.endswith("-docstring"))
        self.assertIn("Add docstring", plan.title)
        self.assertIn("Add the docstring", plan.intent)
        self.assertEqual(plan.tests_to_run, ["pytest -q"])
        for step in plan.steps:
            self.assertIn("src/sample.py", step)
        constraint_text = " ".join(plan.constraints)
        self.assertIn("No symbol renames or signature changes", constraint_text)
        metadata = plan.metadata
        self.assertEqual(metadata["plan_kind"], "docstring")
        self.assertEqual(metadata["docstring_type"], "missing_docstring")
        self.assertEqual(metadata["target_file"], "src/sample.py")
        self.assertTrue(metadata["assumptions_required"])
        self.assertEqual(metadata["symbol_name"], "process_data")

    def test_weak_docstring_plan_uses_improve_language(self) -> None:
        finding = _make_doc_finding("weak_docstring")
        plan = plan_docstring_fix(finding, _make_config())[0]
        self.assertIn("Improve docstring", plan.title)
        self.assertIn("Strengthen the docstring", plan.intent)
        self.assertFalse(plan.metadata["assumptions_required"])
        self.assertEqual(plan.metadata["docstring_type"], "weak_docstring")

    def test_large_symbol_sets_review_flag_and_constraint(self) -> None:
        finding = _make_doc_finding(
            "weak_docstring",
            metadata_override={"lines_of_code": 400},
        )
        plan = plan_docstring_fix(finding, _make_config())[0]
        self.assertTrue(plan.metadata["requires_review_assistance"])
        self.assertIn("reviewer assistance", " ".join(plan.constraints))

    def test_missing_metadata_raises_error(self) -> None:
        finding = _make_doc_finding("weak_docstring")
        finding.metadata.pop("symbol_name")
        with self.assertRaisesRegex(ValueError, "symbol_name"):
            plan_docstring_fix(finding, _make_config())

    def test_missing_location_raises(self) -> None:
        finding = _make_doc_finding("missing_docstring")
        finding.locations.clear()
        with self.assertRaisesRegex(ValueError, "exactly one location"):
            plan_docstring_fix(finding, _make_config())

    def test_multiple_locations_raises(self) -> None:
        finding = _make_doc_finding("missing_docstring")
        finding.locations.append(_make_location(50, 60, path="src/other.py"))
        with self.assertRaisesRegex(ValueError, "exactly one location"):
            plan_docstring_fix(finding, _make_config())

    def test_missing_test_command_raises(self) -> None:
        finding = _make_doc_finding("weak_docstring")
        with self.assertRaisesRegex(ValueError, "test command"):
            plan_docstring_fix(finding, _make_config(default_command=""))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
