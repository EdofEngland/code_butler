"""Tests for the ai-clean clean CLI command."""

from __future__ import annotations

from types import SimpleNamespace
from typing import List

import pytest

from ai_clean import cli
from ai_clean.models import CleanupPlan, Finding, FindingLocation


def _make_location(path: str, start: int = 1, end: int = 2) -> FindingLocation:
    return FindingLocation(path=path, start_line=start, end_line=end)


def _make_finding(
    *,
    finding_id: str,
    category: str,
    description: str,
    path: str,
) -> Finding:
    return Finding(
        id=finding_id,
        category=category,
        description=description,
        locations=[_make_location(path)],
    )


def _make_plan(plan_id: str) -> CleanupPlan:
    return CleanupPlan(
        id=plan_id,
        finding_id=plan_id,
        title=f"Plan {plan_id}",
        intent="Fix issue",
        steps=["step"],
        constraints=["constraint"],
        tests_to_run=["pytest"],
        metadata={"stored_at": f"/plans/{plan_id}.json"},
    )


def _make_config(tmp_path) -> SimpleNamespace:
    return SimpleNamespace(
        plans_dir=tmp_path / "plans",
        specs_dir=tmp_path / "specs",
        executions_dir=tmp_path / "executions",
        git=SimpleNamespace(base_branch="main", refactor_branch="feat"),
        tests=SimpleNamespace(default_command="pytest"),
    )


def test_clean_auto_selects_and_stores_plans(
    monkeypatch: pytest.MonkeyPatch, capsys, tmp_path
) -> None:
    findings = [
        _make_finding(
            finding_id="dup-1",
            category="duplicate_block",
            description="Duplicate block in module",
            path="pkg/a.py",
        ),
        _make_finding(
            finding_id="doc-1",
            category="missing_docstring",
            description="Ignore docstring issues",
            path="pkg/b.py",
        ),
        _make_finding(
            finding_id="large-1",
            category="large_file",
            description="Large file",
            path="pkg/c.py",
        ),
    ]
    monkeypatch.setattr(cli, "analyze_repo", lambda path: findings)
    config = _make_config(tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda: config)

    created: List[str] = []

    def fake_plan_from_finding(
        finding: Finding, *, config: object, chunk_index: int = 0
    ) -> CleanupPlan:
        created.append(finding.id)
        return _make_plan(f"plan-{finding.id}")

    monkeypatch.setattr(cli, "plan_from_finding", fake_plan_from_finding)

    apply_calls: List[dict] = []

    def fake_apply(**kwargs):
        apply_calls.append(kwargs)
        return 0

    monkeypatch.setattr(cli, "_run_apply_flow", fake_apply)

    responses = iter(["", ""])

    def fake_input(_: str) -> str:
        return next(responses, "")

    monkeypatch.setattr("builtins.input", fake_input)

    exit_code = cli.main(["clean", "repo", "--auto"])

    assert exit_code == 0
    assert created == ["dup-1", "large-1"]
    assert apply_calls == []
    output = capsys.readouterr().out
    assert "duplicate_block" in output
    assert "large_file" in output
    assert "Created plan plan-dup-1" in output


def test_clean_manual_selection_and_apply(
    monkeypatch: pytest.MonkeyPatch, capsys, tmp_path
) -> None:
    findings = [
        _make_finding(
            finding_id="dup-1",
            category="duplicate_block",
            description="Duplicate block",
            path="pkg/a.py",
        ),
        _make_finding(
            finding_id="large-1",
            category="large_file",
            description="Large file",
            path="pkg/b.py",
        ),
        _make_finding(
            finding_id="long-1",
            category="long_function",
            description="Long function",
            path="pkg/c.py",
        ),
    ]
    monkeypatch.setattr(cli, "analyze_repo", lambda path: findings)
    config = _make_config(tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda: config)

    def fake_plan_from_finding(
        finding: Finding, *, config: object, chunk_index: int = 0
    ) -> CleanupPlan:
        return _make_plan(f"plan-{finding.id}")

    monkeypatch.setattr(cli, "plan_from_finding", fake_plan_from_finding)

    apply_calls: List[dict] = []

    def fake_apply(**kwargs):
        apply_calls.append(kwargs)
        return 0

    monkeypatch.setattr(cli, "_run_apply_flow", fake_apply)

    responses = iter(["1,3", "y", "n"])

    def fake_input(_: str) -> str:
        return next(responses)

    monkeypatch.setattr("builtins.input", fake_input)

    exit_code = cli.main(["clean", "repo"])

    assert exit_code == 0
    assert len(apply_calls) == 1
    assert apply_calls[0]["plan_id"] == "plan-dup-1"
    assert apply_calls[0]["config"] is config
    output = capsys.readouterr().out
    assert "Created plan plan-dup-1" in output
    assert "Created plan plan-long-1" in output


def test_clean_handles_no_eligible_findings(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(cli, "analyze_repo", lambda path: [])

    exit_code = cli.main(["clean", "repo"])

    assert exit_code == 0
    assert "No cleanup findings" in capsys.readouterr().out
