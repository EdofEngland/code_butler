"""Core data models for ai-clean.

The classes defined here encapsulate metadata flowing through the ButlerSpec
pipeline. They are intentionally pure data carriers—do not import Codex,
executors, or CLI-specific logic in this module.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, ClassVar, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from ai_clean.paths import (
    default_metadata_root,
    default_plan_path,
    default_result_path,
    default_spec_path,
)

try:  # Optional dependency for YAML support.
    import yaml as _yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised via runtime checks
    _yaml = None


def yaml_available() -> bool:
    """Return True when the optional PyYAML dependency is installed."""

    return _yaml is not None


def _require_yaml():
    if _yaml is None:  # pragma: no cover - tested by example script
        raise RuntimeError(
            'pyyaml is not installed. Install with `pip install "ai-clean[yaml]"` '
            "to enable YAML serialization."
        )
    return _yaml


ModelT = TypeVar("ModelT", bound="SerializableModel")


class SerializableModel(BaseModel):
    """Base class with JSON/YAML helpers shared by all ai-clean models."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    def to_json(self, *, indent: int | None = 2) -> str:
        """Serialize the model to a JSON string."""

        return json.dumps(self.model_dump(mode="json"), indent=indent)

    @classmethod
    def from_json(cls, data: str) -> ModelT:
        """Deserialize an instance from a JSON string."""

        return cls.model_validate_json(data)

    def to_yaml(self) -> str:
        """Serialize the model to YAML, requiring the optional PyYAML extra."""

        yaml_mod = _require_yaml()
        return yaml_mod.safe_dump(self.model_dump(mode="json"), sort_keys=False)

    @classmethod
    def from_yaml(cls, data: str) -> ModelT:
        """Deserialize an instance from YAML, requiring the optional PyYAML extra."""

        yaml_mod = _require_yaml()
        payload = yaml_mod.safe_load(data)
        return cls.model_validate(payload)


class FindingLocation(SerializableModel):
    """Location details for a Finding. Pure metadata—no executor logic here."""

    path: Path
    start_line: int
    end_line: int


class Finding(SerializableModel):
    """Represents a cleanup opportunity detected by analyzers."""

    id: str
    category: Literal[
        "duplicate_block",
        "large_file",
        "missing_docstring",
        "weak_docstring",
        "organize_candidate",
        "advanced_cleanup",
        "long_function",
    ]
    description: str
    locations: list[FindingLocation]
    metadata: dict[str, Any] = Field(default_factory=dict)


class CleanupPlan(SerializableModel):
    """A ButlerSpec-ready description of how to fix a Finding."""

    id: str
    finding_id: str
    title: str
    intent: str
    steps: list[str]
    constraints: list[str]
    tests_to_run: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)


class ButlerSpec(SerializableModel):
    """Serialized spec describing the actions Codex should execute."""

    id: str
    plan_id: str
    target_file: str
    intent: str
    actions: list[dict[str, Any]]
    model: str
    batch_group: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(SerializableModel):
    """Outcome of applying a ButlerSpec via Codex or another executor."""

    spec_id: str
    plan_id: str
    success: bool
    tests_passed: bool | None
    stdout: str
    stderr: str
    git_diff: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__: ClassVar[list[str]] = [
    "FindingLocation",
    "Finding",
    "CleanupPlan",
    "ButlerSpec",
    "ExecutionResult",
    "default_metadata_root",
    "default_plan_path",
    "default_spec_path",
    "default_result_path",
    "yaml_available",
]
