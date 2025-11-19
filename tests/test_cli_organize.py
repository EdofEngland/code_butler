"""Tests for the ai-clean organize CLI command."""

from __future__ import annotations

from types import SimpleNamespace
from typing import List

import pytest

from ai_clean import cli
from ai_clean.models import CleanupPlan, Finding, FindingLocation


def _make_location(path: str) -> FindingLocation:
    return FindingLocation(path=path, start_line=1, end_line=2)


def _make_finding(
    finding_id: str,
    files: List[str],
    *,
    target_folder: str = "pkg/new",
) -> Finding:
    return Finding(
        id=finding_id,
        category="organize_candidate",
        description="Move files",
        locations=[_make_location(path) for path in files],
        metadata={"target_folder": target_folder},
    )


def _make_config(tmp_path) -> SimpleNamespace:
    return SimpleNamespace(
        plans_dir=tmp_path / "plans",
        specs_dir=tmp_path / "specs",
        executions_dir=tmp_path / "executions",
        git=SimpleNamespace(base_branch="main", refactor_branch="feat"),
        tests=SimpleNamespace(default_command="pytest"),
    )


def _make_plan(plan_id: str) -> CleanupPlan:
    return CleanupPlan(
        id=plan_id,
        finding_id=plan_id,
        title="Organize files",
        intent="Move files",
        steps=["move"],
        constraints=["no edits"],
        tests_to_run=["pytest"],
        metadata={"stored_at": f"/plans/{plan_id}.json"},
    )


def test_organize_filters_by_max_files(
    monkeypatch: pytest.MonkeyPatch, capsys, tmp_path
) -> None:
    findings = [
        _make_finding("org-1", ["pkg/a.py"]),
        _make_finding("org-2", ["pkg/a.py", "pkg/b.py", "pkg/c.py"]),
    ]
    monkeypatch.setattr(cli, "analyze_repo", lambda path: findings)
    config = _make_config(tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda: config)
    planned: List[str] = []

    def fake_plan_from_finding(finding, *, config: object, chunk_index: int = 0):
        planned.append(finding.id)
        return _make_plan(f"plan-{finding.id}")

    monkeypatch.setattr(cli, "plan_from_finding", fake_plan_from_finding)
    monkeypatch.setattr(cli, "_run_apply_flow", lambda **kwargs: 0)
    responses = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    exit_code = cli.main(["organize", "repo", "--max-files", "1"])

    assert exit_code == 0
    assert planned == ["org-1"]
    output = capsys.readouterr().out
    assert "org-1" in output
    assert "org-2" not in output


def test_organize_selects_ids_and_applies(
    monkeypatch: pytest.MonkeyPatch, capsys, tmp_path
) -> None:
    findings = [
        _make_finding("org-1", ["pkg/a.py"]),
        _make_finding("org-2", ["pkg/d.py"]),
    ]
    monkeypatch.setattr(cli, "analyze_repo", lambda path: findings)
    config = _make_config(tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda: config)

    def fake_plan_from_finding(finding, *, config: object, chunk_index: int = 0):
        return _make_plan(f"plan-{finding.id}")

    monkeypatch.setattr(cli, "plan_from_finding", fake_plan_from_finding)
    apply_calls: List[dict] = []
    monkeypatch.setattr(
        cli, "_run_apply_flow", lambda **kwargs: apply_calls.append(kwargs) or 0
    )

    responses = iter(["", "y", "n"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    exit_code = cli.main(["organize", "repo", "--ids", "org-1", "org-2"])

    assert exit_code == 0
    assert len(apply_calls) == 1
    assert apply_calls[0]["plan_id"] == "plan-org-1"
    assert apply_calls[0]["config"] is config
    output = capsys.readouterr().out
    assert "Plan plan-org-1" in output


def test_organize_handles_no_candidates(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(cli, "analyze_repo", lambda path: [])

    exit_code = cli.main(["organize"])

    assert exit_code == 0
    assert "No organize candidates" in capsys.readouterr().out
