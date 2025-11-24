from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path

import pytest

import ai_clean.factories as factories
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
from ai_clean.factories import get_executor, get_review_executor, get_spec_backend
from ai_clean.models import CleanupPlan, ExecutionResult
from ai_clean.spec_backends import ButlerSpecBackend

TestsConfig.__test__ = False  # Prevent pytest from treating the dataclass as a test.


def _sample_config(
    backend_type: str,
    *,
    tests_command: str = "pytest -q",
    metadata_root: Path | None = None,
    executor_type: str = "codex_shell",
    review_type: str = "codex_review",
) -> AiCleanConfig:
    metadata_root = metadata_root or Path(".ai-clean")
    plans_dir = metadata_root / "plans"
    specs_dir = metadata_root / "specs"
    results_dir = metadata_root / "results"

    analyzers = AnalyzersConfig(
        duplicate=DuplicateAnalyzerConfig(
            window_size=5,
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
            max_files=3,
            max_suggestions=5,
            prompt_template="tmpl",
            codex_model="gpt",
            temperature=0.2,
            ignore_dirs=(".git",),
        ),
    )
    plan_limits = PlanLimitsConfig(
        max_files_per_plan=1,
        max_changed_lines_per_plan=200,
    )

    return AiCleanConfig(
        spec_backend=SpecBackendConfig(
            type=backend_type,
            default_batch_group="default",
            specs_dir=specs_dir,
        ),
        executor=ExecutorConfig(
            type=executor_type,
            binary="codex",
            apply_args=("apply",),
            results_dir=results_dir,
        ),
        review=ReviewConfig(type=review_type, mode="summarize"),
        git=GitConfig(base_branch="main", refactor_branch="refactor/ai-clean"),
        tests=TestsConfig(default_command=tests_command),
        plan_limits=plan_limits,
        analyzers=analyzers,
        metadata_root=metadata_root,
        plans_dir=plans_dir,
        specs_dir=specs_dir,
        results_dir=results_dir,
    )


def test_get_spec_backend_returns_butler_backend():
    config = _sample_config("butler")
    handle = get_spec_backend(config)

    assert isinstance(handle.backend, ButlerSpecBackend)
    assert handle.specs_dir == config.spec_backend.specs_dir


def test_get_spec_backend_rejects_unknown_type():
    config = _sample_config("other")

    with pytest.raises(ValueError, match="Unsupported spec backend: other"):
        get_spec_backend(config)


def test_get_spec_backend_rejects_blank_type():
    config = _sample_config("")

    with pytest.raises(ValueError, match="Unsupported spec backend: <empty>"):
        get_spec_backend(config)


def test_get_executor_valid_and_unknown_types():
    config = _sample_config("butler")
    handle = get_executor(config)

    assert isinstance(handle.executor, factories._CodexShellExecutor)
    assert handle.results_dir == config.executor.results_dir

    bad_config = _sample_config("butler", executor_type="other")
    with pytest.raises(ValueError, match="Unsupported executor type: other"):
        get_executor(bad_config)


def test_get_review_executor_valid_and_unknown_types(tmp_path, monkeypatch):
    metadata_root = tmp_path / ".ai-clean"
    config = _sample_config("butler", metadata_root=metadata_root)

    # ensure prompt runner is wired but not invoked during construction
    monkeypatch.setattr(factories, "get_codex_prompt_runner", lambda cfg: None)

    handle = get_review_executor(config)
    assert isinstance(handle.reviewer, factories._CodexReviewExecutor)
    assert handle.metadata_root == metadata_root

    bad_config = _sample_config("butler", executor_type="codex_shell", review_type="")
    with pytest.raises(ValueError, match="Unsupported review executor type: <empty>"):
        get_review_executor(bad_config)


def test_codex_shell_executor_builds_deterministic_command(monkeypatch, tmp_path):
    config = _sample_config("butler", tests_command="")
    executor = get_executor(config).executor
    spec_path = tmp_path / "spec-demo.butler.yaml"
    spec_path.write_text("id: spec-demo\nplan_id: plan-123\n")

    recorded: dict[str, object] = {}
    monkeypatch.setattr(
        factories.shutil, "which", lambda binary: f"/usr/local/bin/{binary}"
    )

    def fake_run(cmd, **kwargs):
        recorded["cmd"] = cmd
        recorded["kwargs"] = kwargs

        class Result:
            returncode = 0
            stdout = "ok"
            stderr = ""

        return Result()

    monkeypatch.setattr(factories.subprocess, "run", fake_run)

    result = executor.apply_spec(spec_path)

    expected_command = [
        "bash",
        "-lc",
        " ".join(
            shlex.quote(part)
            for part in [
                config.executor.binary,
                *config.executor.apply_args,
                str(spec_path.resolve()),
            ]
        ),
    ]
    assert recorded["cmd"] == expected_command
    kwargs = recorded["kwargs"]
    assert kwargs["cwd"] == spec_path.resolve().parent
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["check"] is False
    assert kwargs["timeout"] == factories._CodexShellExecutor._APPLY_TIMEOUT_SECONDS

    assert result.spec_id == "spec-demo"
    assert result.plan_id == "plan-123"


def test_codex_shell_executor_maps_process_output(monkeypatch, tmp_path):
    config = _sample_config("butler", tests_command="")
    executor = get_executor(config).executor
    spec_path = tmp_path / "fallback-id.butler.yaml"
    spec_path.write_text("plan_id: plan-456\n")

    monkeypatch.setattr(
        factories.shutil, "which", lambda binary: f"/usr/local/bin/{binary}"
    )

    def fake_run(cmd, **kwargs):
        class Result:
            returncode = 3
            stdout = "apply stdout"
            stderr = "apply stderr"

        return Result()

    monkeypatch.setattr(factories.subprocess, "run", fake_run)

    result = executor.apply_spec(spec_path)

    assert result.spec_id == "fallback-id"
    assert result.plan_id == "plan-456"
    assert result.success is False
    assert result.stdout == "apply stdout"
    assert result.stderr == "apply stderr"
    assert result.tests_passed is None
    assert result.git_diff is None
    assert result.metadata["exit_code"] == 3


def test_executor_runs_tests_after_successful_apply(monkeypatch, tmp_path):
    config = _sample_config("butler", tests_command="run-tests")
    executor = get_executor(config).executor
    spec_path = tmp_path / "spec-demo.butler.yaml"
    spec_path.write_text("id: spec-demo\nplan_id: plan-123\n")

    monkeypatch.setattr(
        factories.shutil, "which", lambda binary: f"/usr/local/bin/{binary}"
    )

    calls: list[tuple[str, object]] = []

    def fake_run(cmd, **kwargs):
        if isinstance(cmd, list):
            calls.append(("apply", cmd, kwargs))

            class Result:
                returncode = 0
                stdout = "apply out"
                stderr = "apply err"

            return Result()
        calls.append(("tests", cmd, kwargs))

        class TestResult:
            returncode = 0
            stdout = "test out"
            stderr = "test err"

        return TestResult()

    monkeypatch.setattr(factories.subprocess, "run", fake_run)

    result = executor.apply_spec(spec_path)

    assert [entry[0] for entry in calls] == ["apply", "tests"]
    test_call = calls[1]
    assert test_call[2]["shell"] is True
    assert test_call[2]["cwd"] == spec_path.resolve().parent
    assert result.success is True
    assert result.tests_passed is True
    assert result.stdout == "apply out"
    assert result.stderr == "apply err"
    tests_meta = result.metadata["tests"]
    assert tests_meta["status"] == "ran"
    assert tests_meta["command"] == "run-tests"
    assert tests_meta["exit_code"] == 0
    assert tests_meta["stdout"] == "test out"
    assert tests_meta["stderr"] == "test err"


def test_executor_marks_tests_failed_without_affecting_apply_success(
    monkeypatch, tmp_path
):
    config = _sample_config("butler", tests_command="run-tests")
    executor = get_executor(config).executor
    spec_path = tmp_path / "spec-demo.butler.yaml"
    spec_path.write_text("id: spec-demo\nplan_id: plan-123\n")

    monkeypatch.setattr(
        factories.shutil, "which", lambda binary: f"/usr/local/bin/{binary}"
    )

    def fake_run(cmd, **kwargs):
        if isinstance(cmd, list):

            class ApplyResult:
                returncode = 0
                stdout = "apply ok"
                stderr = "apply err"

            return ApplyResult()

        class TestResult:
            returncode = 5
            stdout = "test fail"
            stderr = "failure"

        return TestResult()

    monkeypatch.setattr(factories.subprocess, "run", fake_run)

    result = executor.apply_spec(spec_path)

    assert result.success is True
    assert result.tests_passed is False
    assert result.metadata["exit_code"] == 0
    tests_meta = result.metadata["tests"]
    assert tests_meta["status"] == "ran"
    assert tests_meta["exit_code"] == 5
    assert tests_meta["stdout"] == "test fail"
    assert tests_meta["stderr"] == "failure"
    assert result.stdout == "apply ok"
    assert result.stderr == "apply err"


def test_executor_skips_tests_when_apply_fails(monkeypatch, tmp_path):
    config = _sample_config("butler", tests_command="run-tests")
    executor = get_executor(config).executor
    spec_path = tmp_path / "spec-demo.butler.yaml"
    spec_path.write_text("id: spec-demo\nplan_id: plan-123\n")

    monkeypatch.setattr(
        factories.shutil, "which", lambda binary: f"/usr/local/bin/{binary}"
    )

    calls: list[object] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)

        class ApplyResult:
            returncode = 2
            stdout = "apply fail"
            stderr = "apply err"

        return ApplyResult()

    monkeypatch.setattr(factories.subprocess, "run", fake_run)

    result = executor.apply_spec(spec_path)

    assert len(calls) == 1  # tests not invoked
    assert result.success is False
    assert result.tests_passed is None
    tests_meta = result.metadata["tests"]
    assert tests_meta["status"] == "apply_failed"
    assert tests_meta["apply_exit_code"] == 2
    assert result.stdout == "apply fail"
    assert result.stderr == "apply err"


def test_executor_skips_tests_when_command_missing(monkeypatch, tmp_path):
    config = _sample_config("butler", tests_command=" ")
    executor = get_executor(config).executor
    spec_path = tmp_path / "spec-demo.butler.yaml"
    spec_path.write_text("id: spec-demo\nplan_id: plan-123\n")

    monkeypatch.setattr(
        factories.shutil, "which", lambda binary: f"/usr/local/bin/{binary}"
    )

    calls: list[object] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)

        class ApplyResult:
            returncode = 0
            stdout = "apply ok"
            stderr = "apply err"

        return ApplyResult()

    monkeypatch.setattr(factories.subprocess, "run", fake_run)

    result = executor.apply_spec(spec_path)

    assert len(calls) == 1
    assert result.success is True
    assert result.tests_passed is False
    assert result.metadata["tests"]["status"] == "not_configured"


def test_executor_records_missing_test_binary(monkeypatch, tmp_path):
    config = _sample_config("butler", tests_command="run-tests")
    executor = get_executor(config).executor
    spec_path = tmp_path / "spec-demo.butler.yaml"
    spec_path.write_text("id: spec-demo\nplan_id: plan-123\n")

    monkeypatch.setattr(
        factories.shutil, "which", lambda binary: f"/usr/local/bin/{binary}"
    )

    def fake_run(cmd, **kwargs):
        if isinstance(cmd, list):

            class ApplyResult:
                returncode = 0
                stdout = ""
                stderr = ""

            return ApplyResult()
        raise FileNotFoundError("run-tests missing")

    monkeypatch.setattr(factories.subprocess, "run", fake_run)

    result = executor.apply_spec(spec_path)

    assert result.success is True
    assert result.tests_passed is False
    tests_meta = result.metadata["tests"]
    assert tests_meta["status"] == "command_not_found"
    assert "missing" in tests_meta["error"]


def test_executor_records_test_timeout(monkeypatch, tmp_path):
    config = _sample_config("butler", tests_command="run-tests")
    executor = get_executor(config).executor
    spec_path = tmp_path / "spec-demo.butler.yaml"
    spec_path.write_text("id: spec-demo\nplan_id: plan-123\n")

    monkeypatch.setattr(
        factories.shutil, "which", lambda binary: f"/usr/local/bin/{binary}"
    )

    def fake_run(cmd, **kwargs):
        if isinstance(cmd, list):

            class ApplyResult:
                returncode = 0
                stdout = ""
                stderr = ""

            return ApplyResult()
        raise subprocess.TimeoutExpired(cmd="run-tests", timeout=5)

    monkeypatch.setattr(factories.subprocess, "run", fake_run)

    result = executor.apply_spec(spec_path)

    assert result.success is True
    assert result.tests_passed is False
    tests_meta = result.metadata["tests"]
    assert tests_meta["status"] == "timed_out"
    assert tests_meta["timeout_seconds"] == 5


def test_review_executor_loads_plan_and_builds_prompt(monkeypatch, tmp_path):
    metadata_root = tmp_path / ".ai-clean"
    plans_dir = metadata_root / "plans"
    plans_dir.mkdir(parents=True)

    plan = CleanupPlan(
        id="plan-1",
        finding_id="f-1",
        title="Title",
        intent="Improve docs",
        steps=["a"],
        constraints=["keep concise"],
        tests_to_run=[],
        metadata={"target_file": "file.py"},
    )
    (plans_dir / "plan-1.json").write_text(plan.to_json())

    exec_result = ExecutionResult(
        spec_id="spec-1",
        plan_id="plan-1",
        success=True,
        tests_passed=True,
        stdout="apply ok",
        stderr="",
    )

    captured_prompt: dict[str, str] = {}

    class FakeRunner:
        def run(self, prompt: str, attachments):
            captured_prompt["prompt"] = prompt
            return json.dumps(
                {
                    "summary": "Looks fine",
                    "risk_grade": "low",
                    "manual_checks": ["verify formatting"],
                }
            )

    monkeypatch.setattr(
        factories, "get_codex_prompt_runner", lambda config: FakeRunner()
    )

    config = _sample_config("butler", metadata_root=metadata_root)
    reviewer = get_review_executor(config).reviewer
    review = reviewer.review_change(None, "diff content", exec_result)

    assert "plan-1" in captured_prompt["prompt"]
    assert "diff content" in captured_prompt["prompt"]
    assert "tests_passed: True" in captured_prompt["prompt"]
    assert review["summary"] == "Looks fine"
    assert review["risk_grade"] == "low"
    assert review["manual_checks"] == ["verify formatting"]
    assert review["metadata"]["exit_code"] == 0
    assert review["metadata"]["attachments"]["plan_id"] == "plan-1"


def test_review_executor_flags_missing_exec_fields(tmp_path):
    metadata_root = tmp_path / ".ai-clean"
    config = _sample_config("butler", metadata_root=metadata_root)
    reviewer = get_review_executor(config).reviewer
    plan = CleanupPlan(
        id="plan-2",
        finding_id="f-2",
        title="Title",
        intent="Improve docs",
        steps=["a"],
        constraints=[],
        tests_to_run=[],
    )
    exec_result = ExecutionResult(
        spec_id="spec-2",
        plan_id="plan-2",
        success=True,
        tests_passed=None,
        stdout="ok",
        stderr="",
    )

    reviewer.review_change(plan, "diff", exec_result)


def test_review_executor_rejects_patchy_output(monkeypatch, tmp_path):
    metadata_root = tmp_path / ".ai-clean"
    plans_dir = metadata_root / "plans"
    plans_dir.mkdir(parents=True)
    plan = CleanupPlan(
        id="plan-3",
        finding_id="f-3",
        title="Title",
        intent="Intent",
        steps=[],
        constraints=[],
        tests_to_run=[],
    )
    (plans_dir / "plan-3.json").write_text(plan.to_json())

    exec_result = ExecutionResult(
        spec_id="spec-3",
        plan_id="plan-3",
        success=True,
        tests_passed=True,
        stdout="ok",
        stderr="",
    )

    class PatchyRunner:
        def run(self, prompt: str, attachments):
            return "```diff --git a b```"

    monkeypatch.setattr(
        factories, "get_codex_prompt_runner", lambda config: PatchyRunner()
    )

    config = _sample_config("butler", metadata_root=metadata_root)
    reviewer = get_review_executor(config).reviewer

    with pytest.raises(ValueError, match="advisory-only"):
        reviewer.review_change(None, "", exec_result)
