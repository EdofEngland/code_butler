"""Core data models for ai-clean.

All types are dataclasses that serialize to/from plain dicts without extra
dependencies or tool-specific references.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

# Allowed categories for findings.
FINDING_CATEGORIES: tuple[str, ...] = (
    "duplicate_block",
    "large_file",
    "long_function",
    "missing_docstring",
    "weak_docstring",
    "organize_candidate",
    "advanced_cleanup",
)


@dataclass
class FindingLocation:
    path: str
    start_line: int
    end_line: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "FindingLocation":
        return FindingLocation(
            path=data["path"],
            start_line=int(data["start_line"]),
            end_line=int(data["end_line"]),
        )


@dataclass
class Finding:
    id: str
    category: str
    description: str
    locations: List[FindingLocation]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.category not in FINDING_CATEGORIES:
            # Keep validation lightweight; only enforce known categories.
            raise ValueError(f"Unsupported finding category: {self.category}")

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["locations"] = [loc.to_dict() for loc in self.locations]
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Finding":
        locations = [
            FindingLocation.from_dict(item) for item in data.get("locations", [])
        ]
        return Finding(
            id=str(data["id"]),
            category=str(data["category"]),
            description=str(data["description"]),
            locations=locations,
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class CleanupPlan:
    id: str
    finding_id: str
    title: str
    intent: str
    steps: List[str]
    constraints: List[str]
    tests_to_run: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CleanupPlan":
        return CleanupPlan(
            id=str(data["id"]),
            finding_id=str(data["finding_id"]),
            title=str(data["title"]),
            intent=str(data["intent"]),
            steps=list(data.get("steps", [])),
            constraints=list(data.get("constraints", [])),
            tests_to_run=list(data.get("tests_to_run", [])),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class SpecChange:
    id: str
    backend_type: str
    payload: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SpecChange":
        return SpecChange(
            id=str(data["id"]),
            backend_type=str(data["backend_type"]),
            payload=dict(data.get("payload", {})),
        )


@dataclass
class ExecutionResult:
    spec_id: str
    success: bool
    tests_passed: Optional[bool]
    stdout: str
    stderr: str
    git_diff: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ExecutionResult":
        return ExecutionResult(
            spec_id=str(data["spec_id"]),
            success=bool(data["success"]),
            tests_passed=data.get("tests_passed"),
            stdout=str(data.get("stdout", "")),
            stderr=str(data.get("stderr", "")),
            git_diff=data.get("git_diff"),
            metadata=dict(data.get("metadata", {})),
        )


__all__ = [
    "FINDING_CATEGORIES",
    "FindingLocation",
    "Finding",
    "CleanupPlan",
    "SpecChange",
    "ExecutionResult",
]
