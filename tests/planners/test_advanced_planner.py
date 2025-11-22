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
from ai_clean.planners import plan_advanced_cleanup


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
    *,
    start_line: int = 12,
    end_line: int = 18,
    metadata_override: dict[str, object] | None = None,
    description: str = "Simplify conditional and reuse helper",
) -> Finding:
    metadata: dict[str, object] = {
        "target_path": "src/service.py",
        "start_line": start_line,
        "end_line": end_line,
        "change_type": "simplify_conditional",
        "prompt_hash": "hash-123",
        "codex_model": "gpt-4o-mini",
        "test_command": "pytest src/service.py",
        "description": description,
    }
    if metadata_override:
        metadata.update(metadata_override)
    return Finding(
        id="adv-abc123",
        category="advanced_cleanup",
        description=description,
        locations=[
            FindingLocation(
                path=Path("src/service.py"), start_line=start_line, end_line=end_line
            )
        ],
        metadata=metadata,
    )


class AdvancedPlannerTests(unittest.TestCase):
    def test_plan_advanced_cleanup_generates_expected_plan(self) -> None:
        finding = _make_finding()
        plan = plan_advanced_cleanup(finding, _make_config())[0]
        self.assertTrue(plan.id.endswith("-plan"))
        self.assertIn("Simplify_conditional", plan.title)
        self.assertIn("src/service.py", plan.title)
        self.assertIn("simplify_conditional", plan.intent)
        self.assertIn("src/service.py", plan.intent)
        snippet_str = "src/service.py:12-18"
        self.assertIn(snippet_str, plan.steps[0])
        self.assertIn(snippet_str, plan.steps[1])
        self.assertIn("pytest src/service.py", plan.steps[2])
        self.assertEqual(plan.tests_to_run, ["pytest src/service.py"])
        self.assertEqual(plan.constraints[0], "Limit edits to src/service.py:12-18")
        metadata = plan.metadata
        self.assertEqual(metadata["plan_kind"], "advanced_cleanup")
        self.assertEqual(metadata["target_file"], "src/service.py")
        self.assertEqual(metadata["line_span"], 7)
        self.assertEqual(metadata["prompt_hash"], "hash-123")
        self.assertEqual(metadata["codex_model"], "gpt-4o-mini")

    def test_plan_advanced_cleanup_uses_default_test_command(self) -> None:
        finding = _make_finding(metadata_override={"test_command": ""})
        plan = plan_advanced_cleanup(finding, _make_config())[0]
        self.assertEqual(plan.tests_to_run, ["pytest -q"])

    def test_optional_followups_become_constraints(self) -> None:
        finding = _make_finding(
            metadata_override={
                "optional_followups": ["Review related logging after change"]
            }
        )
        plan = plan_advanced_cleanup(finding, _make_config())[0]
        self.assertIn("Review related logging after change", plan.constraints[-1])

    def test_missing_metadata_raises_value_error(self) -> None:
        finding = _make_finding(metadata_override={"target_path": None})
        with self.assertRaisesRegex(ValueError, "target_path"):
            plan_advanced_cleanup(finding, _make_config())

    def test_multiple_locations_rejected(self) -> None:
        finding = _make_finding()
        finding.locations.append(
            FindingLocation(path=Path("src/service.py"), start_line=30, end_line=34)
        )
        with self.assertRaisesRegex(ValueError, "exactly one location"):
            plan_advanced_cleanup(finding, _make_config())

    def test_invalid_span_rejected(self) -> None:
        finding = _make_finding(start_line=8, end_line=8)
        with self.assertRaisesRegex(ValueError, "less than end_line"):
            plan_advanced_cleanup(finding, _make_config())

    def test_span_longer_than_limit_rejected(self) -> None:
        finding = _make_finding(start_line=1, end_line=40)
        with self.assertRaisesRegex(ValueError, "exceeds allowed span"):
            plan_advanced_cleanup(finding, _make_config())

    def test_missing_test_command_and_default_raises(self) -> None:
        finding = _make_finding(metadata_override={"test_command": ""})
        config = _make_config(default_command="")
        with self.assertRaisesRegex(ValueError, "test command"):
            plan_advanced_cleanup(finding, config)

    def test_multiple_suggestions_raise_error(self) -> None:
        finding = _make_finding(
            metadata_override={
                "suggestions": [
                    {"target_path": "src/service.py"},
                    {"target_path": "src/service.py"},
                ]
            }
        )
        with self.assertRaisesRegex(ValueError, "single Codex suggestion"):
            plan_advanced_cleanup(finding, _make_config())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
