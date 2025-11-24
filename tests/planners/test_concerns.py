from __future__ import annotations

import logging
from pathlib import Path

import pytest

from ai_clean.models import CleanupPlan
from ai_clean.planners.concerns import (
    Concern,
    ConcernError,
    classify_plan_concern,
    classify_plan_group,
    split_mixed_concerns,
    split_plan_concerns,
    validate_plan_concerns,
)


def _plan(plan_kind: str, metadata: dict[str, object] | None = None) -> CleanupPlan:
    return CleanupPlan(
        id=f"{plan_kind}-plan",
        finding_id="f-1",
        title="Sample",
        intent="Do something",
        steps=["step"],
        constraints=["constraint"],
        tests_to_run=["pytest -q"],
        metadata={"plan_kind": plan_kind, **(metadata or {})},
    )


def test_classify_plan_concern_maps_known_plan_kinds() -> None:
    cases = {
        "duplicate_block_helper": Concern.HELPER_EXTRACTION,
        "long_function_helpers": Concern.HELPER_EXTRACTION,
        "large_file_split": Concern.FILE_SPLIT,
        "organize": Concern.FILE_GROUP_MOVE,
        "docstring": Concern.DOCSTRING_BATCH,
        "advanced_cleanup": Concern.ADVANCED_CLEANUP,
    }
    for plan_kind, expected in cases.items():
        concern = classify_plan_concern(_plan(plan_kind))
        assert concern is expected


def test_classify_plan_concern_uses_metadata_keys() -> None:
    plan = _plan("unknown", metadata={"helper_path": "src/helpers.py"})
    assert classify_plan_concern(plan) is Concern.HELPER_EXTRACTION


def test_classify_plan_concern_rejects_mixed_concerns() -> None:
    plan = _plan(
        "docstring",
        metadata={"helper_path": "src/helpers.py", "docstring_type": "missing"},
    )
    with pytest.raises(ConcernError, match="mixes multiple concerns"):
        classify_plan_concern(plan)


def test_split_plan_concerns_clones_when_mixed() -> None:
    plan = _plan(
        "docstring",
        metadata={"helper_path": "src/helpers.py", "docstring_type": "missing"},
    )
    split = split_plan_concerns(plan, logger=logging.getLogger(__name__))
    assert [p.id for p in split] == [
        "docstring-plan-concern-1",
        "docstring-plan-concern-2",
    ]
    concerns = {p.metadata["concern"] for p in split}
    assert concerns == {Concern.DOCSTRING_BATCH.value, Concern.HELPER_EXTRACTION.value}


def test_validate_plan_concerns_rejects_mixed_batch() -> None:
    helper_plan = _plan("duplicate_block_helper")
    doc_plan = _plan("docstring")
    with pytest.raises(ConcernError, match="mixes concerns"):
        validate_plan_concerns([helper_plan, doc_plan])


def test_split_mixed_concerns_handles_mixed_plans() -> None:
    plans = split_mixed_concerns(
        [
            _plan("advanced_cleanup"),
            _plan(
                "docstring",
                metadata={
                    "helper_path": Path("src/helpers.py").as_posix(),
                    "docstring_type": "missing",
                },
            ),
        ],
        logger=logging.getLogger(__name__),
    )
    concerns = classify_plan_group(plans)
    assert Concern.ADVANCED_CLEANUP in concerns
    assert Concern.DOCSTRING_BATCH in concerns
    assert Concern.HELPER_EXTRACTION in concerns
