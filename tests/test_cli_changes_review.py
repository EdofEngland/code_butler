"""Tests for the ai-clean changes-review CLI command."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ai_clean import cli
from ai_clean.models import CleanupPlan, ExecutionResult


def _make_plan() -> CleanupPlan:
    return CleanupPlan(
        id="plan-1",
        finding_id="f-1",
        title="Title",
        intent="Intent",
        steps=["step"],
        constraints=["constraint"],
        tests_to_run=["pytest"],
    )


def _make_execution_result() -> ExecutionResult:
    return ExecutionResult(
        spec_id="spec",
        success=True,
        tests_passed=True,
        stdout="ok",
        stderr="",
        metadata={},
    )


def test_changes_review_prints_sections(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    plan = _make_plan()
    execution = _make_execution_result()
    config = SimpleNamespace(
        plans_dir="plans",
        executions_dir="executions",
        review=SimpleNamespace(type="codex_review"),
    )
    monkeypatch.setattr(cli, "load_config", lambda: config)
    monkeypatch.setattr(cli, "load_plan", lambda plan_id, plans_dir=None: plan)
    monkeypatch.setattr(
        cli,
        "load_execution_result",
        lambda plan_id, executions_dir=None: execution,
    )
    monkeypatch.setattr(cli, "_capture_diff_text", lambda cmd: "diff text")
    monkeypatch.setattr(cli, "_load_review_completion", lambda: lambda prompt: {})

    review_payload = {
        "summary": "Looks good",
        "risks": ["Risk 1"],
        "suggested_checks": ["Check docs"],
        "metadata": {"prompt": "details"},
    }

    class FakeReviewer:
        def review_change(self, plan_arg, diff, execution_result):
            assert diff == "diff text"
            return review_payload

    monkeypatch.setattr(
        cli, "build_review_executor", lambda config, codex_completion: FakeReviewer()
    )

    exit_code = cli.main(["changes-review", "plan-1", "--verbose"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Stored tests: passed" in output
    assert "Summary:" in output
    assert "Risks:" in output
    assert "Suggested checks:" in output
    assert "Metadata:" in output


def test_changes_review_errors_when_execution_missing(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    plan = _make_plan()
    config = SimpleNamespace(
        plans_dir="plans",
        executions_dir="executions",
        review=SimpleNamespace(type="codex_review"),
    )
    monkeypatch.setattr(cli, "load_config", lambda: config)
    monkeypatch.setattr(cli, "load_plan", lambda plan_id, plans_dir=None: plan)

    def fake_load_execution_result(plan_id, executions_dir=None):
        raise FileNotFoundError("missing")

    monkeypatch.setattr(cli, "load_execution_result", fake_load_execution_result)

    exit_code = cli.main(["changes-review", "plan-1"])

    assert exit_code == 2
    assert "No execution result found" in capsys.readouterr().out
