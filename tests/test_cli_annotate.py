"""Tests for the ai-clean annotate CLI command."""

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
        intent="Improve docstring",
        steps=["add docstring"],
        constraints=["Be factual"],
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


def test_annotate_mode_all_plans_doc_findings(
    monkeypatch: pytest.MonkeyPatch, capsys, tmp_path
) -> None:
    findings = [
        _make_finding("doc-1", "missing_docstring", "Missing docstring", "pkg/a.py"),
        _make_finding("doc-2", "weak_docstring", "Weak docstring", "pkg/b.py"),
        _make_finding("other-1", "duplicate_block", "Ignore", "pkg/c.py"),
    ]
    monkeypatch.setattr(cli, "analyze_repo", lambda path: findings)
    config = _make_config(tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda: config)

    planned: List[str] = []

    def fake_plan_from_finding(
        finding: Finding, *, config: object, chunk_index: int = 0
    ) -> CleanupPlan:
        planned.append(finding.id)
        return _make_plan(f"plan-{finding.id}")

    monkeypatch.setattr(cli, "plan_from_finding", fake_plan_from_finding)
    monkeypatch.setattr(cli, "_run_apply_flow", lambda **kwargs: 0)

    responses = iter(["", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(responses, ""))

    exit_code = cli.main(["annotate", "repo", "--mode", "all", "--all"])

    assert exit_code == 0
    assert planned == ["doc-1", "doc-2"]
    output = capsys.readouterr().out
    assert "Docstring findings:" in output
    assert "Created plan plan-doc-1" in output


def test_annotate_interactive_selection_and_apply(
    monkeypatch: pytest.MonkeyPatch, capsys, tmp_path
) -> None:
    findings = [
        _make_finding("doc-1", "missing_docstring", "Missing docstring", "pkg/a.py"),
        _make_finding("doc-2", "missing_docstring", "Missing docstring", "pkg/b.py"),
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

    responses = iter(["1", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    exit_code = cli.main(["annotate", "repo"])

    assert exit_code == 0
    assert len(apply_calls) == 1
    assert apply_calls[0]["plan_id"] == "plan-doc-1"
    assert apply_calls[0]["config"] is config
    output = capsys.readouterr().out
    assert "Created plan plan-doc-1" in output


def test_annotate_handles_no_doc_findings(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(cli, "analyze_repo", lambda path: [])

    exit_code = cli.main(["annotate", "repo", "--mode", "weak"])

    assert exit_code == 0
    assert "No docstring findings" in capsys.readouterr().out
