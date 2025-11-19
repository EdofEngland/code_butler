"""Regression tests for the ai-clean analyze CLI command."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from ai_clean import cli
from ai_clean.models import Finding, FindingLocation


def _make_location(path: str, start: int, end: int) -> FindingLocation:
    return FindingLocation(path=path, start_line=start, end_line=end)


def _make_finding(
    *,
    finding_id: str,
    category: str,
    description: str,
    locations: list[FindingLocation],
) -> Finding:
    return Finding(
        id=finding_id,
        category=category,
        description=description,
        locations=locations,
    )


def test_analyze_prints_multiple_locations(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    findings = [
        _make_finding(
            finding_id="doc-1",
            category="missing_docstring",
            description="Add docstring to helper.",
            locations=[
                _make_location("pkg/module.py", 10, 12),
                _make_location("pkg/helpers.py", 2, 5),
            ],
        )
    ]
    monkeypatch.setattr(cli, "analyze_repo", lambda root: findings)

    exit_code = cli.main(["analyze", "repo"])

    assert exit_code == 0
    captured = capsys.readouterr().out.strip()
    assert (
        captured == "[doc-1] missing_docstring - Add docstring to helper. :: "
        "pkg/module.py:10-12; pkg/helpers.py:2-5"
    )


def test_analyze_filters_categories_and_handles_empty_results(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    findings = [
        _make_finding(
            finding_id="dup-1",
            category="duplicate_block",
            description="Duplicate loop detected.",
            locations=[_make_location("pkg/a.py", 1, 5)],
        ),
        _make_finding(
            finding_id="doc-2",
            category="missing_docstring",
            description="Missing docstring.",
            locations=[_make_location("pkg/b.py", 3, 4)],
        ),
    ]
    monkeypatch.setattr(cli, "analyze_repo", lambda root: findings)

    exit_code = cli.main(["analyze", ".", "--categories", "duplicate_block"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "[dup-1] duplicate_block - Duplicate loop detected." in output
    assert "doc-2" not in output

    exit_code = cli.main(["analyze", ".", "--categories", "organize_candidate"])
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "No findings."


def test_analyze_is_read_only(monkeypatch: pytest.MonkeyPatch) -> None:
    findings = [
        _make_finding(
            finding_id="doc-1",
            category="missing_docstring",
            description="Add docstring to helper.",
            locations=[_make_location("pkg/module.py", 10, 12)],
        )
    ]
    monkeypatch.setattr(cli, "analyze_repo", lambda root: findings)

    with (
        patch("ai_clean.planners.orchestrator.plan_from_finding") as plan_mock,
        patch("ai_clean.storage.save_plan") as save_mock,
    ):
        exit_code = cli.main(["analyze", "."])

    assert exit_code == 0
    plan_mock.assert_not_called()
    save_mock.assert_not_called()
