"""Tests for the ai-clean apply CLI command."""

from __future__ import annotations

from types import SimpleNamespace
from typing import List

import pytest

from ai_clean import cli
from ai_clean.models import CleanupPlan, ExecutionResult, SpecChange


def _make_plan(plan_id: str) -> CleanupPlan:
    return CleanupPlan(
        id=plan_id,
        finding_id="finding-1",
        title="Sample Plan",
        intent="Do work",
        steps=["step 1"],
        constraints=["stay safe"],
        tests_to_run=["pytest"],
        metadata={},
    )


def _make_config(tmp_path) -> SimpleNamespace:
    return SimpleNamespace(
        git=SimpleNamespace(base_branch="main", refactor_branch="feat"),
        plans_dir=tmp_path / "plans",
        specs_dir=tmp_path / "specs",
        executions_dir=tmp_path / "executions",
        tests=SimpleNamespace(default_command="pytest"),
        spec_backend=SimpleNamespace(type="openspec"),
        executor=SimpleNamespace(type="codex", apply_command=["apply {spec_path}"]),
    )


def test_apply_command_runs_full_flow(
    monkeypatch: pytest.MonkeyPatch, capsys, tmp_path
) -> None:
    plan = _make_plan("plan-123")
    config = _make_config(tmp_path)
    saved_results: List[tuple] = []

    class FakeBackend:
        def __init__(self) -> None:
            self.plan_to_spec_called = False

        def plan_to_spec(self, provided_plan: CleanupPlan) -> SpecChange:
            assert provided_plan is plan
            self.plan_to_spec_called = True
            return SpecChange(id="spec-1", backend_type="openspec", payload={})

        def write_spec(self, spec: SpecChange, directory: str) -> str:
            assert self.plan_to_spec_called
            return f"{directory}/spec.yaml"

    class FakeExecutor:
        def apply_spec(self, spec_path: str) -> ExecutionResult:
            assert spec_path.endswith("spec.yaml")
            return ExecutionResult(
                spec_id="spec-1",
                success=True,
                tests_passed=True,
                stdout="apply ok",
                stderr="",
                metadata={},
            )

    monkeypatch.setattr(cli, "load_config", lambda: config)
    monkeypatch.setattr(cli, "ensure_on_refactor_branch", lambda base, ref: None)
    monkeypatch.setattr(cli, "load_plan", lambda plan_id, plans_dir=None: plan)
    monkeypatch.setattr(cli, "build_spec_backend", lambda cfg: FakeBackend())
    monkeypatch.setattr(cli, "build_code_executor", lambda cfg: FakeExecutor())

    def fake_save_execution_result(result, plan_id, executions_dir=None):
        saved_results.append((plan_id, executions_dir))
        return tmp_path / "executions" / f"{plan_id}.json"

    monkeypatch.setattr(cli, "save_execution_result", fake_save_execution_result)
    monkeypatch.setattr(cli, "get_diff_stat", lambda: "Changes:\n 1 files changed")

    exit_code = cli.main(
        ["apply", "plan-123", "--spec-dir", str(tmp_path / "custom-specs")]
    )

    assert exit_code == 0
    assert saved_results == [("plan-123", config.executions_dir)]
    output = capsys.readouterr().out
    assert "Spec written to:" in output
    assert "Apply success: yes" in output
    assert "Tests: passed" in output
    assert "Changes:" in output
    assert "Execution result stored at:" in output


def test_apply_command_handles_missing_plan(
    monkeypatch: pytest.MonkeyPatch, capsys, tmp_path
) -> None:
    config = _make_config(tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda: config)
    monkeypatch.setattr(cli, "ensure_on_refactor_branch", lambda base, ref: None)

    def fake_load_plan(plan_id, plans_dir=None):
        raise FileNotFoundError("not found")

    monkeypatch.setattr(cli, "load_plan", fake_load_plan)

    exit_code = cli.main(["apply", "missing-plan"])

    assert exit_code == 2
    assert "Failed to load plan 'missing-plan'" in capsys.readouterr().out


def test_apply_command_can_skip_tests(
    monkeypatch: pytest.MonkeyPatch, capsys, tmp_path
) -> None:
    plan = _make_plan("plan-xyz")
    config = _make_config(tmp_path)

    class FakeBackend:
        def plan_to_spec(self, provided_plan: CleanupPlan) -> SpecChange:
            return SpecChange(id="spec-2", backend_type="openspec", payload={})

        def write_spec(self, spec: SpecChange, directory: str) -> str:
            return f"{directory}/spec.yaml"

    class FakeExecutor:
        def apply_spec(self, spec_path: str) -> ExecutionResult:
            return ExecutionResult(
                spec_id="spec-2",
                success=True,
                tests_passed=None,
                stdout="done",
                stderr="",
                metadata={},
            )

    def fake_build_code_executor(passed_config):
        assert passed_config.tests.default_command == ""
        return FakeExecutor()

    monkeypatch.setattr(cli, "load_config", lambda: config)
    monkeypatch.setattr(cli, "ensure_on_refactor_branch", lambda base, ref: None)
    monkeypatch.setattr(cli, "load_plan", lambda plan_id, plans_dir=None: plan)
    monkeypatch.setattr(cli, "build_spec_backend", lambda cfg: FakeBackend())
    monkeypatch.setattr(cli, "build_code_executor", fake_build_code_executor)
    monkeypatch.setattr(cli, "save_execution_result", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "get_diff_stat", lambda: "Changes:\n none")

    exit_code = cli.main(["apply", "plan-xyz", "--skip-tests"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Tests: skipped (--skip-tests)" in output
    assert "Execution result stored at:" in output


def test_apply_command_reports_test_failure(
    monkeypatch: pytest.MonkeyPatch, capsys, tmp_path
) -> None:
    plan = _make_plan("plan-tests")
    config = _make_config(tmp_path)

    class FakeBackend:
        def plan_to_spec(self, provided_plan: CleanupPlan) -> SpecChange:
            return SpecChange(id="spec-3", backend_type="openspec", payload={})

        def write_spec(self, spec: SpecChange, directory: str) -> str:
            return f"{directory}/spec.yaml"

    class FakeExecutor:
        def apply_spec(self, spec_path: str) -> ExecutionResult:
            return ExecutionResult(
                spec_id="spec-3",
                success=True,
                tests_passed=False,
                stdout="apply",
                stderr="",
                metadata={
                    "tests": {
                        "command": ["pytest"],
                        "returncode": 1,
                        "stdout": "",
                        "stderr": "boom",
                    },
                    "apply": {
                        "command": ["apply"],
                        "returncode": 0,
                        "stdout": "",
                        "stderr": "",
                    },
                },
            )

    monkeypatch.setattr(cli, "load_config", lambda: config)
    monkeypatch.setattr(cli, "ensure_on_refactor_branch", lambda base, ref: None)
    monkeypatch.setattr(cli, "load_plan", lambda plan_id, plans_dir=None: plan)
    monkeypatch.setattr(cli, "build_spec_backend", lambda cfg: FakeBackend())
    monkeypatch.setattr(cli, "build_code_executor", lambda cfg: FakeExecutor())
    monkeypatch.setattr(cli, "get_diff_stat", lambda: "Changes:\n none")

    exit_code = cli.main(["apply", "plan-tests"])

    assert exit_code == 2
    output = capsys.readouterr().out
    assert "Tests: FAILED" in output
    assert "Tests command: pytest" in output
    assert "See execution logs at" in output


def test_apply_command_reports_apply_failure(
    monkeypatch: pytest.MonkeyPatch, capsys, tmp_path
) -> None:
    plan = _make_plan("plan-fail")
    config = _make_config(tmp_path)

    class FakeBackend:
        def plan_to_spec(self, provided_plan: CleanupPlan) -> SpecChange:
            return SpecChange(id="spec-4", backend_type="openspec", payload={})

        def write_spec(self, spec: SpecChange, directory: str) -> str:
            return f"{directory}/spec.yaml"

    class FakeExecutor:
        def apply_spec(self, spec_path: str) -> ExecutionResult:
            return ExecutionResult(
                spec_id="spec-4",
                success=False,
                tests_passed=None,
                stdout="apply",
                stderr="fail",
                metadata={
                    "apply": {
                        "command": ["apply"],
                        "returncode": 1,
                        "stdout": "",
                        "stderr": "fail",
                    },
                    "tests": {"reason": "apply_failed"},
                },
            )

    monkeypatch.setattr(cli, "load_config", lambda: config)
    monkeypatch.setattr(cli, "ensure_on_refactor_branch", lambda base, ref: None)
    monkeypatch.setattr(cli, "load_plan", lambda plan_id, plans_dir=None: plan)
    monkeypatch.setattr(cli, "build_spec_backend", lambda cfg: FakeBackend())
    monkeypatch.setattr(cli, "build_code_executor", lambda cfg: FakeExecutor())
    monkeypatch.setattr(cli, "get_diff_stat", lambda: "Changes:\n none")

    exit_code = cli.main(["apply", "plan-fail"])

    assert exit_code == 2
    output = capsys.readouterr().out
    assert "Apply success: no" in output
    assert "Apply command: apply" in output
    assert "Apply return code: 1" in output
    assert "Apply failed." in output
