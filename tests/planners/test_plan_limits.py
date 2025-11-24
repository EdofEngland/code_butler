from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

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
    plan_advanced_cleanup,
    plan_docstring_fix,
    plan_duplicate_blocks,
    plan_long_function,
)
from ai_clean.planners.limits import (
    PlanLimitError,
    split_plans_to_limits,
    summarize_plan_size,
    validate_plan_limits,
)


def _make_config(plan_limits: PlanLimitsConfig | None = None) -> AiCleanConfig:
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
    limits = plan_limits or PlanLimitsConfig(
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
        tests=TestsConfig(default_command="pytest -q"),
        plan_limits=limits,
        analyzers=analyzers,
        metadata_root=metadata_root,
        plans_dir=metadata_root / "plans",
        specs_dir=metadata_root / "specs",
        results_dir=metadata_root / "results",
    )


def _advanced_finding(
    start_line: int = 12,
    end_line: int = 18,
    metadata_override: dict[str, Any] | None = None,
) -> Finding:
    metadata: dict[str, object] = {
        "target_path": "src/service.py",
        "start_line": start_line,
        "end_line": end_line,
        "change_type": "simplify_conditional",
        "prompt_hash": "hash-123",
        "codex_model": "gpt-4o-mini",
        "test_command": "pytest src/service.py",
        "description": "Simplify conditional and reuse helper",
    }
    if metadata_override:
        metadata.update(metadata_override)
    return Finding(
        id="adv-abc123",
        category="advanced_cleanup",
        description="Simplify conditional and reuse helper",
        locations=[
            FindingLocation(
                path=Path("src/service.py"), start_line=start_line, end_line=end_line
            )
        ],
        metadata=metadata,
    )


def _docstring_finding() -> Finding:
    return Finding(
        id="doc-1",
        category="missing_docstring",
        description="Missing docstring",
        locations=[
            FindingLocation(path=Path("src/service.py"), start_line=10, end_line=30)
        ],
        metadata={
            "symbol_type": "function",
            "qualified_name": "pkg.module.process_data",
            "symbol_name": "process_data",
            "docstring_preview": "",
            "lines_of_code": 42,
        },
    )


def _long_function_finding() -> Finding:
    return Finding(
        id="fn-1",
        category="long_function",
        description="Long function",
        locations=[
            FindingLocation(path=Path("src/module.py"), start_line=30, end_line=90)
        ],
        metadata={"qualified_name": "app.module.process_data", "line_count": 120},
    )


class TestPlanLimitHelpers:
    def test_summarize_plan_size_for_advanced_plan(self) -> None:
        plan = plan_advanced_cleanup(_advanced_finding(), _make_config())[0]
        summary = summarize_plan_size(plan)
        assert summary.file_paths == ("src/service.py",)
        assert summary.changed_lines == plan.metadata["line_span"]

    def test_summarize_plan_size_for_structure_and_docstring(self) -> None:
        config = _make_config()
        long_plan = plan_long_function(_long_function_finding(), config)[0]
        doc_plan = plan_docstring_fix(_docstring_finding(), config)[0]

        long_summary = summarize_plan_size(long_plan)
        doc_summary = summarize_plan_size(doc_plan)

        assert long_summary.file_paths == ("src/module.py",)
        assert long_summary.changed_lines == 61
        assert doc_summary.file_paths == ("src/service.py",)
        assert doc_summary.changed_lines == 21

    def test_duplicate_helper_counts_occurrence_files(self) -> None:
        config = _make_config()
        finding = Finding(
            id="dup-1",
            category="duplicate_block",
            description="Duplicate across files",
            locations=[
                FindingLocation(path=Path("src/foo/a.py"), start_line=10, end_line=20),
                FindingLocation(path=Path("src/foo/b.py"), start_line=30, end_line=40),
            ],
            metadata={},
        )
        plan = plan_duplicate_blocks([finding], config)[0]
        summary = summarize_plan_size(plan)

        assert set(summary.file_paths) == {
            "src/foo/a.py",
            "src/foo/b.py",
            "src/foo/helpers.py",
        }

        with pytest.raises(PlanLimitError):
            validate_plan_limits(plan, config.plan_limits)

        # Duplicate helper plans still need size summaries, but file caps
        # are intentionally bypassed to allow multi-file replacements.
        summary = validate_plan_limits(
            plan, config.plan_limits, enforce_file_count=False
        )
        assert summary.file_count == 3

    def test_validate_plan_limits_rejects_overages(self) -> None:
        tight_limits = PlanLimitsConfig(
            max_files_per_plan=1, max_changed_lines_per_plan=10
        )
        over_line_plan = CleanupPlan(
            id="over-lines",
            finding_id="f-1",
            title="Over cap",
            intent="Intent",
            steps=["step"],
            constraints=["constraint"],
            tests_to_run=["pytest -q"],
            metadata={"target_file": "src/app.py", "line_span": 20},
        )
        with pytest.raises(PlanLimitError):
            validate_plan_limits(over_line_plan, tight_limits)

        multi_file_plan = over_line_plan.model_copy(
            update={"id": "multi", "metadata": {"target_files": ["a.py", "b.py"]}}
        )
        with pytest.raises(PlanLimitError):
            validate_plan_limits(multi_file_plan, tight_limits)

    def test_split_plans_to_limits_clones_per_file(self) -> None:
        plan_limits = PlanLimitsConfig(
            max_files_per_plan=1, max_changed_lines_per_plan=50
        )
        multi_plan = CleanupPlan(
            id="combined",
            finding_id="f-1",
            title="Combined plan",
            intent="Intent",
            steps=["step"],
            constraints=["constraint"],
            tests_to_run=["pytest -q"],
            metadata={
                "target_files": ["src/a.py", "src/b.py"],
                "line_span": 8,
            },
        )

        split = split_plans_to_limits([multi_plan], plan_limits)
        assert [plan.id for plan in split] == ["combined-split-1", "combined-split-2"]
        for plan in split:
            assert plan.metadata.get("split_from_plan") == "combined"
            assert plan.metadata.get("split_total") == 2
            validate_plan_limits(plan, plan_limits)
