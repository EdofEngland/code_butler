from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import ai_clean.planners.orchestrator as orchestrator
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
from ai_clean.models import CleanupPlan, Finding, FindingLocation
from ai_clean.planners import (
    generate_plan_id,
    plan_from_finding,
    write_plan_to_disk,
)


def _make_config(
    default_command: str = "pytest -q",
    plans_dir: Path | None = None,
) -> AiCleanConfig:
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
    metadata_root = Path(".ai-clean")
    default_plans_dir = plans_dir or metadata_root / "plans"
    return AiCleanConfig(
        spec_backend=SpecBackendConfig(
            type="butler",
            default_batch_group="default",
            specs_dir=metadata_root / "specs",
        ),
        executor=ExecutorConfig(
            type="codex_shell",
            binary="codex",
            apply_args=("apply",),
            results_dir=metadata_root / "results",
        ),
        review=ReviewConfig(type="codex_review", mode="summaries"),
        git=GitConfig(base_branch="main", refactor_branch="refactor/ai-clean"),
        tests=TestsConfig(default_command=default_command),
        analyzers=analyzers,
        metadata_root=metadata_root,
        plans_dir=default_plans_dir,
        specs_dir=metadata_root / "specs",
        results_dir=metadata_root / "results",
    )


def _make_generic_finding(category: str, *, allow_unknown: bool = False) -> Finding:
    payload = {
        "id": f"{category}-id",
        "category": category,
        "description": f"{category} finding",
        "locations": [
            FindingLocation(path=Path("src/file.py"), start_line=1, end_line=5)
        ],
        "metadata": {},
    }
    if allow_unknown:
        return Finding.model_construct(**payload)
    return Finding(**payload)


def _make_doc_finding(category: str = "missing_docstring") -> Finding:
    metadata: dict[str, object] = {
        "symbol_type": "function",
        "qualified_name": "pkg.module.process_data",
        "symbol_name": "process_data",
        "docstring_preview": "" if category == "missing_docstring" else "Old text",
        "lines_of_code": 42,
    }
    return Finding(
        id=f"{category}-123",
        category=category,
        description=f"{category} finding",
        locations=[
            FindingLocation(path=Path("src/service.py"), start_line=10, end_line=30)
        ],
        metadata=metadata,
    )


def _make_plan(plan_id: str) -> CleanupPlan:
    return CleanupPlan(
        id=plan_id,
        finding_id="f-1",
        title="Sample",
        intent="Do something",
        steps=["step"],
        constraints=["constraint"],
        tests_to_run=["pytest -q"],
        metadata={},
    )


class PlannerOrchestratorTests(unittest.TestCase):
    def test_generate_plan_id_normalizes_and_validates(self) -> None:
        plan_id = generate_plan_id(" Finding--XYZ ", " Doc-Update ")
        self.assertEqual(plan_id, "finding-xyz-doc-update")

    def test_generate_plan_id_rejects_invalid_suffix(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid plan ID suffix"):
            generate_plan_id("abc123", "Bad Suffix!")

    def test_dispatch_routes_each_category(self) -> None:
        config = _make_config()
        cases = [
            ("duplicate_block", "ai_clean.planners.orchestrator._plan_duplicate_block"),
            ("large_file", "ai_clean.planners.orchestrator.plan_large_file"),
            ("long_function", "ai_clean.planners.orchestrator.plan_long_function"),
            ("missing_docstring", "ai_clean.planners.orchestrator.plan_docstring_fix"),
            ("weak_docstring", "ai_clean.planners.orchestrator.plan_docstring_fix"),
            (
                "organize_candidate",
                "ai_clean.planners.orchestrator.plan_organize_candidate",
            ),
            (
                "advanced_cleanup",
                "ai_clean.planners.orchestrator.plan_advanced_cleanup",
            ),
        ]
        for category, target in cases:
            with self.subTest(category=category):
                sentinel = [f"{category}-plan"]
                with patch(target, return_value=sentinel) as mock_helper:
                    original = orchestrator._CATEGORY_DISPATCH[category]
                    orchestrator._CATEGORY_DISPATCH[category] = mock_helper
                    finding = _make_generic_finding(category)
                    try:
                        result = plan_from_finding(finding, config)
                        self.assertIs(result, sentinel)
                        mock_helper.assert_called_once_with(finding, config)
                    finally:
                        orchestrator._CATEGORY_DISPATCH[category] = original

    @patch("ai_clean.planners.orchestrator.plan_duplicate_blocks")
    def test_duplicate_block_passthrough(self, mock_plan) -> None:
        plans = [_make_plan("one"), _make_plan("two")]
        mock_plan.return_value = plans
        config = _make_config()
        finding = _make_generic_finding("duplicate_block")
        result = plan_from_finding(finding, config)
        self.assertIs(result, plans)
        mock_plan.assert_called_once()
        args, kwargs = mock_plan.call_args
        self.assertEqual(len(args), 2)
        self.assertEqual(len(args[0]), 1)
        self.assertIs(args[0][0], finding)
        self.assertIs(args[1], config)

    def test_unknown_category(self) -> None:
        with self.assertRaisesRegex(NotImplementedError, "strange"):
            plan_from_finding(
                _make_generic_finding("strange", allow_unknown=True), _make_config()
            )

    def test_write_plan_to_disk_round_trip(self) -> None:
        with TemporaryDirectory() as tmp:
            plans_dir = Path(tmp) / ".ai-clean" / "plans"
            config = _make_config(plans_dir=plans_dir)
            finding = _make_doc_finding()
            plans = plan_from_finding(finding, config)
            self.assertTrue(plans)
            for plan in plans:
                destination = write_plan_to_disk(plan, config.plans_dir)
                self.assertEqual(destination, config.plans_dir / f"{plan.id}.json")
                self.assertEqual(
                    destination.read_text(encoding="utf-8"),
                    plan.to_json(indent=2),
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
