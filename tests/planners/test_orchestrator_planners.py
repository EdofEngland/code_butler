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
    PlanLimitsConfig,
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
from ai_clean.planners.concerns import ConcernError
from ai_clean.planners.limits import PlanLimitError
from ai_clean.planners.scope_guard import ScopeGuardError


def _make_config(
    default_command: str = "pytest -q",
    plans_dir: Path | None = None,
    plan_limits: PlanLimitsConfig | None = None,
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
    plan_limits = plan_limits or PlanLimitsConfig(
        max_files_per_plan=1,
        max_changed_lines_per_plan=200,
    )
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
        plan_limits=plan_limits,
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


def _make_plan(
    plan_id: str,
    metadata: dict[str, object] | None = None,
    *,
    plan_kind: str | None = None,
) -> CleanupPlan:
    combined_metadata: dict[str, object] = {}
    if plan_kind:
        combined_metadata["plan_kind"] = plan_kind
    combined_metadata.update(metadata or {})
    return CleanupPlan(
        id=plan_id,
        finding_id="f-1",
        title="Sample",
        intent="Do something",
        steps=["step"],
        constraints=["constraint"],
        tests_to_run=["pytest -q"],
        metadata=combined_metadata,
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
            (
                "duplicate_block",
                "ai_clean.planners.orchestrator._plan_duplicate_block",
                "duplicate_block_helper",
            ),
            (
                "large_file",
                "ai_clean.planners.orchestrator.plan_large_file",
                "large_file_split",
            ),
            (
                "long_function",
                "ai_clean.planners.orchestrator.plan_long_function",
                "long_function_helpers",
            ),
            (
                "missing_docstring",
                "ai_clean.planners.orchestrator.plan_docstring_fix",
                "docstring",
            ),
            (
                "weak_docstring",
                "ai_clean.planners.orchestrator.plan_docstring_fix",
                "docstring",
            ),
            (
                "organize_candidate",
                "ai_clean.planners.orchestrator.plan_organize_candidate",
                "organize",
            ),
            (
                "advanced_cleanup",
                "ai_clean.planners.orchestrator.plan_advanced_cleanup",
                "advanced_cleanup",
            ),
        ]
        for category, target, plan_kind in cases:
            with self.subTest(category=category):
                sentinel = [
                    _make_plan(
                        f"{category}-plan",
                        metadata={"target_file": "src/file.py", "line_span": 1},
                        plan_kind=plan_kind,
                    )
                ]
                with patch(target, return_value=sentinel) as mock_helper:
                    original = orchestrator._CATEGORY_DISPATCH[category]
                    orchestrator._CATEGORY_DISPATCH[category] = mock_helper
                    finding = _make_generic_finding(category)
                    try:
                        result = plan_from_finding(finding, config)
                        self.assertEqual(len(result), len(sentinel))
                        self.assertIs(result[0], sentinel[0])
                        mock_helper.assert_called_once_with(finding, config)
                    finally:
                        orchestrator._CATEGORY_DISPATCH[category] = original

    @patch("ai_clean.planners.orchestrator.plan_duplicate_blocks")
    def test_duplicate_block_passthrough(self, mock_plan) -> None:
        plans = [
            _make_plan("one", plan_kind="duplicate_block_helper"),
            _make_plan("two", plan_kind="duplicate_block_helper"),
        ]
        mock_plan.return_value = plans
        config = _make_config()
        finding = _make_generic_finding("duplicate_block")
        result = plan_from_finding(finding, config)
        self.assertEqual(result, plans)
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

    def test_plan_from_finding_allows_multi_file_duplicate_helper(self) -> None:
        config = _make_config()
        multi_plan = _make_plan("multi").model_copy(
            update={
                "metadata": {
                    "target_files": ["src/a.py", "src/b.py"],
                    "plan_kind": "duplicate_block_helper",
                    "helper_path": "src/helpers.py",
                    "occurrences": [
                        {"path": "src/a.py", "start_line": 1, "end_line": 3},
                        {"path": "src/b.py", "start_line": 10, "end_line": 12},
                    ],
                }
            }
        )

        def _multi_file_planner(finding: Finding, _: object) -> list[CleanupPlan]:
            return [multi_plan]

        original = orchestrator._CATEGORY_DISPATCH["duplicate_block"]
        orchestrator._CATEGORY_DISPATCH["duplicate_block"] = _multi_file_planner
        try:
            plans = plan_from_finding(_make_generic_finding("duplicate_block"), config)
        finally:
            orchestrator._CATEGORY_DISPATCH["duplicate_block"] = original

        self.assertEqual([plan.id for plan in plans], ["multi"])

    def test_plan_from_finding_rejects_multi_file_non_duplicate_plan(self) -> None:
        config = _make_config()
        multi_plan = _make_plan("multi").model_copy(
            update={
                "metadata": {
                    "target_files": ["src/a.py", "src/b.py"],
                    "plan_kind": "docstring",
                }
            }
        )

        def _multi_file_planner(finding: Finding, _: object) -> list[CleanupPlan]:
            return [multi_plan]

        original = orchestrator._CATEGORY_DISPATCH["missing_docstring"]
        orchestrator._CATEGORY_DISPATCH["missing_docstring"] = _multi_file_planner
        try:
            with self.assertRaises(PlanLimitError):
                plan_from_finding(_make_doc_finding(), config)
        finally:
            orchestrator._CATEGORY_DISPATCH["missing_docstring"] = original

    def test_plan_from_finding_rejects_over_line_cap(self) -> None:
        tight_limits = PlanLimitsConfig(
            max_files_per_plan=1, max_changed_lines_per_plan=5
        )
        config = _make_config(plan_limits=tight_limits)
        with self.assertRaises(PlanLimitError):
            plan_from_finding(_make_doc_finding(), config)

    def test_plan_from_finding_rejects_scope_guard(self) -> None:
        config = _make_config()

        def _rename_planner(finding: Finding, _: object) -> list[CleanupPlan]:
            return [
                _make_plan(
                    "rename-api",
                    plan_kind="advanced_cleanup",
                    metadata={
                        "target_file": "src/api.py",
                        "line_span": 3,
                    },
                ).model_copy(
                    update={
                        "title": "Rename public API",
                        "intent": "Rename public API method",
                        "steps": ["Rename public API function"],
                    }
                )
            ]

        original = orchestrator._CATEGORY_DISPATCH["advanced_cleanup"]
        orchestrator._CATEGORY_DISPATCH["advanced_cleanup"] = _rename_planner
        try:
            with self.assertRaises(ScopeGuardError):
                plan_from_finding(_make_generic_finding("advanced_cleanup"), config)
        finally:
            orchestrator._CATEGORY_DISPATCH["advanced_cleanup"] = original

    def test_plan_from_finding_splits_multi_file_outputs(self) -> None:
        config = _make_config()
        base_plan = _make_plan("split-me").model_copy(
            update={
                "metadata": {
                    "target_files": ["src/a.py", "src/b.py"],
                    "line_span": 4,
                    "plan_kind": "organize",
                }
            }
        )

        def _split_planner(finding: Finding, _: object) -> list[CleanupPlan]:
            return [base_plan]

        original = orchestrator._CATEGORY_DISPATCH["organize_candidate"]
        orchestrator._CATEGORY_DISPATCH["organize_candidate"] = _split_planner
        try:
            plans = plan_from_finding(
                _make_generic_finding("organize_candidate"), config
            )
        finally:
            orchestrator._CATEGORY_DISPATCH["organize_candidate"] = original

        self.assertEqual(
            sorted(plan.id for plan in plans),
            ["split-me-split-1", "split-me-split-2"],
        )
        for plan in plans:
            self.assertEqual(plan.metadata.get("split_from_plan"), "split-me")
            self.assertEqual(plan.metadata.get("split_total"), 2)
            self.assertIn(plan.metadata.get("split_index"), {1, 2})
            self.assertIn(plan.metadata.get("target_file"), {"src/a.py", "src/b.py"})

    def test_plan_from_finding_tags_concern(self) -> None:
        config = _make_config()
        plan = plan_from_finding(_make_doc_finding(), config)[0]
        self.assertEqual(plan.metadata.get("concern"), "docstring_batch")

    def test_plan_from_finding_rejects_mixed_concerns(self) -> None:
        config = _make_config()
        helper_plan = _make_plan(
            "helper",
            metadata={"target_file": "src/a.py"},
            plan_kind="duplicate_block_helper",
        )
        doc_plan = _make_plan(
            "doc",
            metadata={"target_file": "src/a.py", "docstring_type": "missing"},
            plan_kind="docstring",
        )

        def _multi_planner(finding: Finding, _: object) -> list[CleanupPlan]:
            return [helper_plan, doc_plan]

        original = orchestrator._CATEGORY_DISPATCH["advanced_cleanup"]
        orchestrator._CATEGORY_DISPATCH["advanced_cleanup"] = _multi_planner
        try:
            with self.assertRaises(ConcernError):
                plan_from_finding(_make_generic_finding("advanced_cleanup"), config)
        finally:
            orchestrator._CATEGORY_DISPATCH["advanced_cleanup"] = original


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
