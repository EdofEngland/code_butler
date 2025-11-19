"""Tests for the ai-clean cleanup-advanced CLI command."""

from __future__ import annotations

from types import SimpleNamespace
from typing import List

import pytest

from ai_clean import cli
from ai_clean.models import CleanupPlan, Finding, FindingLocation


def _make_location() -> FindingLocation:
    return FindingLocation(path="pkg/a.py", start_line=1, end_line=2)


def _make_finding(finding_id: str, description: str) -> Finding:
    return Finding(
        id=finding_id,
        category="advanced_cleanup",
        description=description,
        locations=[_make_location()],
    )


def _make_plan(plan_id: str) -> CleanupPlan:
    return CleanupPlan(
        id=plan_id,
        finding_id=plan_id,
        title=f"Advanced {plan_id}",
        intent="Improve code",
        steps=["Refactor"],
        constraints=["Advisory only"],
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


def test_cleanup_advanced_limit_and_plan_creation(
    monkeypatch: pytest.MonkeyPatch, capsys, tmp_path
) -> None:
    findings = [
        _make_finding("adv-1", "Refactor module"),
        _make_finding("adv-2", "Refactor service"),
    ]
    monkeypatch.setattr(cli, "analyze_repo", lambda path: findings)
    config = _make_config(tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda: config)

    created: List[str] = []

    def fake_plan_from_finding(finding, *, config: object, chunk_index: int = 0):
        created.append(finding.id)
        return _make_plan(f"plan-{finding.id}")

    monkeypatch.setattr(cli, "plan_from_finding", fake_plan_from_finding)
    exit_code = cli.main(["cleanup-advanced", "repo", "--limit", "1"])

    assert exit_code == 0
    assert created == ["adv-1"]
    output = capsys.readouterr().out
    assert "Codex advisory suggestions" in output
    assert "[plan-adv-1]" in output


def test_cleanup_advanced_handles_no_findings(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(cli, "analyze_repo", lambda path: [])

    exit_code = cli.main(["cleanup-advanced", "repo"])

    assert exit_code == 0
    assert "No advisory advanced cleanups" in capsys.readouterr().out
