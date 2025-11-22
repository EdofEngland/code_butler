"""Sanity check for ai-clean core models.

Run `python examples/model_roundtrip.py` to ensure serialization helpers and
default metadata path utilities behave deterministically.
"""

from __future__ import annotations

from pathlib import Path

from ai_clean.models import (
    ButlerSpec,
    CleanupPlan,
    ExecutionResult,
    Finding,
    FindingLocation,
    default_plan_path,
    default_result_path,
    default_spec_path,
    yaml_available,
)


def _assert_roundtrip(instance):
    payload = instance.to_json()
    reconstructed = type(instance).from_json(payload)
    assert (
        reconstructed == instance
    ), f"JSON round-trip failed for {type(instance).__name__}"

    if yaml_available():
        yaml_payload = instance.to_yaml()
        reconstructed_yaml = type(instance).from_yaml(yaml_payload)
        assert (
            reconstructed_yaml == instance
        ), f"YAML round-trip failed for {type(instance).__name__}"


def main() -> None:
    loc = FindingLocation(path=Path("src/module.py"), start_line=10, end_line=20)
    finding = Finding(
        id="finding-1",
        category="duplicate_block",
        description="Duplicate block detected",
        locations=[loc],
    )
    plan = CleanupPlan(
        id="plan-1",
        finding_id=finding.id,
        title="Remove duplication",
        intent="Refactor repeated logic into helper",
        steps=["Extract helper", "Replace repeated code"],
        constraints=["Preserve behavior"],
        tests_to_run=["pytest -q"],
    )
    spec = ButlerSpec(
        id="spec-1",
        plan_id=plan.id,
        target_file="src/module.py",
        intent=plan.intent,
        actions=[{"type": "edit", "path": "src/module.py"}],
        model="gpt-4o-mini",
        batch_group="default",
    )
    result = ExecutionResult(
        spec_id=spec.id,
        plan_id=plan.id,
        success=True,
        tests_passed=True,
        stdout="ok",
        stderr="",
    )

    for instance in (loc, finding, plan, spec, result):
        _assert_roundtrip(instance)

    assert (
        str(default_plan_path(plan.id)) == ".ai-clean/plans/plan-1.json"
    ), "Unexpected plan path"
    assert (
        str(default_spec_path(spec.id)) == ".ai-clean/specs/spec-1.butler.yaml"
    ), "Unexpected spec path"
    assert (
        str(default_result_path(plan.id)) == ".ai-clean/results/plan-1.json"
    ), "Unexpected result path"

    print("Model round-trip checks passed")


if __name__ == "__main__":  # pragma: no cover
    main()
