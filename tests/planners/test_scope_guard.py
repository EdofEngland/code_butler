from __future__ import annotations

import pytest

from ai_clean.models import CleanupPlan
from ai_clean.planners.scope_guard import (
    ForbiddenChange,
    ScopeGuardError,
    detect_forbidden_changes,
    validate_scope,
)


def _plan(text: str) -> CleanupPlan:
    return CleanupPlan(
        id="p-1",
        finding_id="f-1",
        title=text,
        intent=text,
        steps=[text],
        constraints=[text],
        tests_to_run=["pytest -q"],
        metadata={"target_file": "src/app.py"},
    )


def test_detect_allows_local_cleanup() -> None:
    plan = _plan("Refine local variable naming in helper")
    assert detect_forbidden_changes(plan) == []


def test_detect_ignores_negated_warnings() -> None:
    plan = _plan("No renames or signature changes; keep local")
    assert detect_forbidden_changes(plan) == []


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Rename public API foo()", ForbiddenChange.PUBLIC_API_RENAME),
        (
            "Change function signature to add parameter",
            ForbiddenChange.SIGNATURE_CHANGE,
        ),
        ("Rename util across modules", ForbiddenChange.GLOBAL_RENAME),
        ("Redesign subsystem architecture", ForbiddenChange.SUBSYSTEM_RESTRUCTURE),
        ("Module overhaul for whole package", ForbiddenChange.MULTI_MODULE_REDESIGN),
    ],
)
def test_detect_forbidden_patterns(text: str, expected: ForbiddenChange) -> None:
    plan = _plan(text)
    violations = detect_forbidden_changes(plan)
    assert any(v.change is expected for v in violations)


def test_validate_scope_raises_with_violation() -> None:
    plan = _plan("Rename public API and redesign subsystem")
    with pytest.raises(ScopeGuardError) as excinfo:
        validate_scope([plan])
    assert "scope guard" in str(excinfo.value).lower()


def test_metadata_rename_signal_does_not_block_local_work() -> None:
    plan = CleanupPlan(
        id="p-2",
        finding_id="f-2",
        title="Refine helper",
        intent="Tighten helper behavior",
        steps=["Rename local variable inside helper"],
        constraints=["Keep behavior identical"],
        tests_to_run=["pytest -q"],
        metadata={
            "change_type": "rename_variable",
            "target_file": "src/app.py",
        },
    )
    violations = detect_forbidden_changes(plan)
    assert violations == []
