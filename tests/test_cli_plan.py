"""Regression tests for the ai-clean plan CLI command."""

from __future__ import annotations

from types import SimpleNamespace
from typing import List
from unittest.mock import Mock

import pytest

from ai_clean import cli
from ai_clean.models import CleanupPlan, Finding, FindingLocation
from ai_clean.planners.orchestrator import PlannerError


def _make_location(path: str, start: int, end: int) -> FindingLocation:
    return FindingLocation(path=path, start_line=start, end_line=end)


def _make_finding(
    *,
    finding_id: str,
    path: str,
    category: str = "missing_docstring",
    description: str = "desc",
) -> Finding:
    return Finding(
        id=finding_id,
        category=category,
        description=description,
        locations=[_make_location(path, 1, 2)],
    )


def _make_plan(plan_id: str) -> CleanupPlan:
    return CleanupPlan(
        id=plan_id,
        finding_id=plan_id,
        title="Docstring Fix",
        intent="Add docstrings",
        steps=["Add module docstring", "Add helper docstring"],
        constraints=["Keep formatting"],
        tests_to_run=["pytest"],
        metadata={"stored_at": ".ai-clean/plans/docstring.json"},
    )


def test_plan_command_prints_summary(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    finding = _make_finding(finding_id="doc-1", path="pkg/module.py")
    plan = _make_plan("plan-doc-1")
    analyze_calls: List[str] = []

    def fake_analyze(path: str):
        analyze_calls.append(path)
        return [finding]

    monkeypatch.setattr(cli, "analyze_repo", fake_analyze)
    fake_config = SimpleNamespace(plans_dir="dir")
    monkeypatch.setattr(cli, "load_config", lambda: fake_config)

    plan_mock = Mock(return_value=plan)
    monkeypatch.setattr(cli, "plan_from_finding", plan_mock)

    exit_code = cli.main(["plan", "doc-1", "--path", "repo", "--chunk-index", "1"])

    assert exit_code == 0
    assert analyze_calls == ["repo"]
    plan_mock.assert_called_once()
    _, kwargs = plan_mock.call_args
    assert kwargs["chunk_index"] == 1
    assert kwargs["config"] is fake_config
    output = capsys.readouterr().out
    assert "Plan ID: plan-doc-1" in output
    assert "Title: Docstring Fix" in output
    assert "Intent: Add docstrings" in output
    assert "Stored at: .ai-clean/plans/docstring.json" in output
    assert "Steps:\n  1. Add module docstring\n  2. Add helper docstring" in output
    assert "Constraints:\n  1. Keep formatting" in output
    assert "Tests to run:\n  1. pytest" in output


def test_plan_command_errors_when_finding_missing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "analyze_repo", lambda path: [])

    exit_code = cli.main(["plan", "missing-1"])

    assert exit_code == 2
    assert "Finding 'missing-1' not found" in capsys.readouterr().out


def test_plan_command_errors_when_ids_ambiguous(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    duplicate = [
        _make_finding(finding_id="dup-1", path="pkg/a.py"),
        _make_finding(finding_id="dup-1", path="pkg/b.py"),
    ]
    monkeypatch.setattr(cli, "analyze_repo", lambda path: duplicate)

    exit_code = cli.main(["plan", "dup-1"])

    assert exit_code == 2
    assert "Provide a narrower --path" in capsys.readouterr().out


def test_plan_command_surfaces_planner_errors(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    finding = _make_finding(finding_id="doc-1", path="pkg/module.py")
    monkeypatch.setattr(cli, "analyze_repo", lambda path: [finding])
    fake_config = SimpleNamespace(plans_dir="dir")
    monkeypatch.setattr(cli, "load_config", lambda: fake_config)

    def fake_plan_from_finding(*_, **__):
        raise PlannerError("limit exceeded")

    monkeypatch.setattr(cli, "plan_from_finding", fake_plan_from_finding)

    exit_code = cli.main(["plan", "doc-1"])

    assert exit_code == 2
    output = capsys.readouterr().out
    assert "Failed to build plan: limit exceeded" in output
