"""OpenSpec backend that converts CleanupPlans into SpecChange payloads."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

import yaml

from ai_clean.interfaces import SpecBackend
from ai_clean.models import CleanupPlan, SpecChange

DEFAULT_SPEC_DIR = Path(".ai-clean/specs")
_SLUG_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


class OpenSpecBackend(SpecBackend):
    """SpecBackend implementation that emits OpenSpec-friendly payloads."""

    backend_type = "openspec"

    def plan_to_spec(self, plan: CleanupPlan) -> SpecChange:
        """Convert a CleanupPlan into a SpecChange with structured payload."""
        _validate_plan(plan)
        payload = _serialize_plan(plan)
        return SpecChange(
            id=plan.id,
            backend_type=self.backend_type,
            payload=payload,
        )

    def write_spec(self, spec: SpecChange, directory: str) -> str:
        """Persist spec payload to YAML and return the written file path."""
        payload = _require_payload(spec)
        _ensure_single_plan(spec, payload)

        target_dir = Path(directory or DEFAULT_SPEC_DIR)
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = _build_spec_filename(spec)
        path = (target_dir / filename).resolve()
        if path.exists():
            raise ValueError(
                f"Spec file already exists: {path}. Use a unique plan/spec id."
            )

        _dump_yaml(path, payload)

        metadata = payload.get("metadata")
        if isinstance(metadata, dict):
            metadata["spec_path"] = path.as_posix()

        return path.as_posix()


def _validate_plan(plan: CleanupPlan) -> None:
    if not plan.id:
        raise ValueError("CleanupPlan.id is required to build a spec payload.")
    if not plan.steps:
        raise ValueError("CleanupPlan.steps must contain at least one entry.")


def _serialize_plan(plan: CleanupPlan) -> Dict[str, Any]:
    """Return a deterministic payload dictionary for the given plan."""
    payload: Dict[str, Any] = {
        "plan_id": plan.id,
        "finding_id": plan.finding_id,
        "title": plan.title,
        "intent": plan.intent,
        "steps": list(plan.steps),
        "constraints": list(plan.constraints),
        "tests_to_run": list(plan.tests_to_run),
        "metadata": dict(plan.metadata),
    }
    return payload


def _require_payload(spec: SpecChange) -> Dict[str, Any]:
    if not isinstance(spec.payload, dict):
        raise ValueError("SpecChange.payload must be a dictionary for serialization.")
    return spec.payload


def _ensure_single_plan(spec: SpecChange, payload: Dict[str, Any]) -> None:
    plan_id = payload.get("plan_id")
    if not isinstance(plan_id, str) or not plan_id.strip():
        raise ValueError("SpecChange payload must include a plan_id string.")
    if spec.id and plan_id != spec.id:
        raise ValueError(
            "SpecChange.id must match payload plan_id to avoid multi-plan payloads."
        )
    finding_id = payload.get("finding_id")
    if not isinstance(finding_id, str) or not finding_id.strip():
        raise ValueError("SpecChange payload must include a finding_id string.")


def _build_spec_filename(spec: SpecChange) -> str:
    base = spec.id or spec.payload.get("plan_id") or "spec"
    slug = _slugify(str(base))
    return f"{slug}.openspec.yaml"


def _slugify(value: str) -> str:
    value = value.strip() or "spec"
    slug = _SLUG_PATTERN.sub("-", value)
    slug = slug.strip("-_.") or "spec"
    return slug.lower()


def _dump_yaml(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=True, default_flow_style=False)


__all__ = ["OpenSpecBackend"]
