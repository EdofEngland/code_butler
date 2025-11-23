from __future__ import annotations

from pathlib import Path

import pytest

from ai_clean.models import CleanupPlan
from ai_clean.plans import load_plan, save_plan


def _sample_plan() -> CleanupPlan:
    return CleanupPlan(
        id="plan-xyz",
        finding_id="finding-1",
        title="Demo",
        intent="Clean up something",
        steps=["do one thing"],
        constraints=["keep changes small"],
        tests_to_run=["pytest -q"],
        metadata={"extra": "value"},
    )


def test_save_and_load_round_trip(tmp_path: Path):
    plan = _sample_plan()
    root = tmp_path / ".ai-clean"

    saved_path = save_plan(plan, root)
    loaded = load_plan(plan.id, root)

    assert saved_path.exists()
    assert saved_path.parent == (root.resolve() / "plans")
    assert loaded == plan


def test_load_plan_missing_file_raises(tmp_path: Path):
    root = tmp_path / ".ai-clean"
    with pytest.raises(FileNotFoundError, match="Plan file not found"):
        load_plan("missing", root)
