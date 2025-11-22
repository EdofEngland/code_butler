"""Deterministic ButlerSpec backend (Phases 4.1–4.2).

Implements the plan → spec conversion described in
`docs/butlerspec_plan.md#phase-4-1` and the YAML persistence rules from
`#phase-4-2`, enforcing the guardrails enumerated in `#governance-and-error-catalog`.
"""

from __future__ import annotations

import logging
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from ai_clean.config import SpecBackendConfig
from ai_clean.interfaces import BaseSpecBackend
from ai_clean.models import ButlerSpec, CleanupPlan

from ._validators import (
    assert_intent_matches_target,
    assert_metadata_size,
    ensure_single_target,
    normalize_text_array,
)

LOGGER = logging.getLogger(__name__)
_MAX_ACTIONS = 25

__all__ = ["ButlerSpecBackend"]


class ButlerSpecBackend(BaseSpecBackend):
    """Convert CleanupPlans into ButlerSpec payloads with strict governance.

    Errors follow the catalog in `docs/butlerspec_plan.md#governance-and-error-catalog`.
    """

    def __init__(
        self,
        config: SpecBackendConfig,
        *,
        model_name: str = "codex",
        batch_group: str | None = None,
    ) -> None:
        self._config = config  # docs/butlerspec_plan.md#phase-4-1 explains defaults.
        self._model_name = (
            model_name  # docs/butlerspec_plan.md#phase-4-1 keeps Codex-only.
        )
        self._batch_group = (
            batch_group if batch_group is not None else config.default_batch_group
        )  # docs/butlerspec_plan.md#phase-4-1 enforces deterministic batches.
        self._specs_dir = (
            config.specs_dir
        )  # docs/butlerspec_plan.md#phase-4-1 pins specs dir.

    def plan_to_spec(self, plan: CleanupPlan) -> ButlerSpec:
        """Return a ButlerSpec built from the canonicalized CleanupPlan."""

        plan_id = plan.id.strip() or plan.id
        plan_title = plan.title.strip() or plan.title
        plan_intent = plan.intent.strip()

        steps = normalize_text_array(plan.steps, section_name="steps")
        if not steps:
            raise ValueError("CleanupPlan must include at least one step")

        constraints = normalize_text_array(plan.constraints, section_name="constraints")
        tests = normalize_text_array(plan.tests_to_run, section_name="tests_to_run")

        assert_metadata_size(plan.metadata)
        target_file = ensure_single_target(plan.metadata)
        assert_intent_matches_target(plan_intent, target_file)

        actions = [
            {
                "type": "plan_step",
                "index": index,
                "summary": step,
                "payload": None,
            }
            for index, step in enumerate(steps, start=1)
        ]

        metadata_copy: dict[str, Any] = deepcopy(plan.metadata)
        metadata_copy.update(
            {
                "plan_title": plan_title,
                "constraints": constraints,
                "tests_to_run": tests,
                "target_file": target_file,
            }
        )

        return ButlerSpec(
            id=f"{plan_id}-spec",
            plan_id=plan_id,
            target_file=target_file,
            intent=plan_intent,
            actions=actions,
            model=self._model_name,
            batch_group=self._batch_group,
            metadata=metadata_copy,
        )

    def write_spec(self, spec: ButlerSpec, directory: Path | None = None) -> Path:
        """Persist the ButlerSpec as a deterministic `.butler.yaml` file."""

        target_dir = directory or self._specs_dir
        spec_path = target_dir / f"{spec.id}.butler.yaml"
        spec_path.parent.mkdir(parents=True, exist_ok=True)

        assert_metadata_size(spec.metadata)
        ensure_single_target(spec.metadata)
        if len(spec.actions) > _MAX_ACTIONS:
            raise ValueError("ButlerSpec specs must not exceed 25 actions")

        payload = _serialize_butler_spec(spec)
        if spec_path.exists():
            existing = spec_path.read_text(encoding="utf-8")
            if existing == payload:
                return spec_path
            LOGGER.warning(
                "Overwriting ButlerSpec file %s because content changed", spec_path
            )
        spec_path.write_text(payload, encoding="utf-8")
        return spec_path


def _serialize_butler_spec(spec: ButlerSpec) -> str:
    """Return a canonical YAML string following docs/butlerspec_plan.md#phase-4-2."""

    metadata = {key: spec.metadata[key] for key in sorted(spec.metadata)}
    actions = [_order_action(action) for action in spec.actions]
    payload = {
        "id": spec.id,
        "plan_id": spec.plan_id,
        "target_file": spec.target_file,
        "intent": spec.intent,
        "model": spec.model,
        "batch_group": spec.batch_group,
        "actions": actions,
        "metadata": metadata,
    }
    yaml_text = yaml.safe_dump(
        payload,
        sort_keys=False,
        default_flow_style=False,
        indent=2,
        allow_unicode=True,
    )
    if not yaml_text.endswith("\n"):
        yaml_text += "\n"
    return yaml_text


def _order_action(action: dict[str, Any]) -> dict[str, Any]:
    """Order action keys as required by docs/butlerspec_plan.md#phase-4-2."""

    ordered: dict[str, Any] = {}
    for key in ("type", "index", "summary", "payload"):
        if key in action:
            ordered[key] = action[key]
    for key in sorted(action):
        if key not in ordered:
            ordered[key] = action[key]
    return ordered
