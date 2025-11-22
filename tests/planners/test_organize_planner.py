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
from ai_clean.models import Finding
from ai_clean.planners import plan_organize_candidate
from ai_clean.planners.organize import _derive_target_folder


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
    files: list[str] | None = None,
    topic: str = "Payments Services",
    metadata_override: dict[str, object] | None = None,
    finding_id: str = "organize-sample",
) -> Finding:
    metadata: dict[str, object] = {
        "topic": topic,
        "files": files or ["src/payments/card.py"],
    }
    if metadata_override:
        metadata.update(metadata_override)
    return Finding(
        id=finding_id,
        category="organize_candidate",
        description="Organize related files",
        locations=[],
        metadata=metadata,
    )


class OrganizePlannerTests(unittest.TestCase):
    def test_plan_generation_creates_per_file_plans(self) -> None:
        files = ["src/payments/card.py", "src/payments/bank.py"]
        finding = _make_finding(
            files=files,
            metadata_override={"test_command": "pytest src/payments"},
            finding_id="organize-alpha",
        )
        plans = plan_organize_candidate(finding, _make_config())
        self.assertEqual(len(plans), 2)

        target_dir = "src/payments/payments-services"
        for index, plan in enumerate(plans):
            self.assertEqual(plan.id, f"organize-alpha-move-{index + 1}")
            self.assertEqual(plan.tests_to_run, ["pytest src/payments"])
            self.assertIn("Payments Services", plan.intent)
            current_file = files[index]
            self.assertIn(current_file, plan.title)
            for step in plan.steps:
                self.assertIn(current_file.split("/")[-1], step)
            self.assertIn(
                "No changes inside function/class bodies", " ".join(plan.constraints)
            )
            metadata = plan.metadata
            self.assertEqual(metadata["file"], current_file)
            self.assertEqual(metadata["target_directory"], target_dir)
            self.assertEqual(metadata["split_index"], index)
            self.assertEqual(metadata["batch_size"], len(files))
            self.assertEqual(metadata["members"], files)
            self.assertFalse(metadata["requires_reexports"])

    def test_public_entry_point_requires_reexports(self) -> None:
        finding = _make_finding(
            files=["src/payments/__init__.py"],
            metadata_override={"test_command": "pytest"},
        )
        plan = plan_organize_candidate(finding, _make_config())[0]
        self.assertTrue(plan.metadata["requires_reexports"])
        self.assertIn("re-exports", " ".join(plan.constraints))

    def test_derive_target_folder_slugifies_topic(self) -> None:
        files = [Path("src/payments/card.py"), Path("src/payments/forms/bank.py")]
        info = _derive_target_folder(files, "Core Services")
        self.assertEqual(info.path, Path("src/payments/core-services"))
        self.assertFalse(info.requires_reexports)

    def test_derive_target_folder_rejects_deep_topics(self) -> None:
        files = [Path("src/payments/card.py")]
        with self.assertRaisesRegex(ValueError, "too deep"):
            _derive_target_folder(files, "Payments/Bank/Files")

    def test_disjoint_parents_raise_errors(self) -> None:
        files = ["src/payments/card.py", "tests/payments/test_card.py"]
        finding = _make_finding(
            files=files, metadata_override={"test_command": "pytest"}
        )
        with self.assertRaisesRegex(ValueError, "disjoint"):
            plan_organize_candidate(finding, _make_config())

    def test_missing_topic_or_files_raise_errors(self) -> None:
        missing_topic = _make_finding(
            topic="", metadata_override={"test_command": "pytest"}
        )
        with self.assertRaisesRegex(ValueError, "topic"):
            plan_organize_candidate(missing_topic, _make_config())

        missing_files = _make_finding(
            metadata_override={"files": [], "test_command": "pytest"},
        )
        with self.assertRaisesRegex(ValueError, "files"):
            plan_organize_candidate(missing_files, _make_config())

    def test_file_limit_guard(self) -> None:
        files = [f"src/payments/file_{index}.py" for index in range(6)]
        finding = _make_finding(
            files=files, metadata_override={"test_command": "pytest"}
        )
        with self.assertRaisesRegex(ValueError, "at most"):
            plan_organize_candidate(finding, _make_config())

    def test_missing_test_command_raises(self) -> None:
        finding = _make_finding(files=["src/payments/card.py"])
        with self.assertRaisesRegex(ValueError, "test command"):
            plan_organize_candidate(finding, _make_config(default_command=""))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
