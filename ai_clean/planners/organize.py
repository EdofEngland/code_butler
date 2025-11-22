"""Planner for organize_candidate findings.

This module converts organize analyzer findings into ButlerSpec-ready cleanup
plans. Each plan only describes file moves, folder creation, and import
adjustments—no code edits or filesystem writes occur here so downstream stages
maintain full control.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_clean.config import AiCleanConfig as ButlerConfig
from ai_clean.models import CleanupPlan, Finding

__all__ = ["plan_organize_candidate"]

MAX_FILES_PER_FINDING = 5


@dataclass(frozen=True)
class TargetInfo:
    """Destination folder for an organize plan.

    ``requires_reexports`` signals whether any files act as public entry points
    (e.g., ``__init__.py`` or ``api.py``) so reviewers can ensure re-export
    stubs keep the old locations working.
    """

    path: Path
    requires_reexports: bool


def plan_organize_candidate(
    finding: Finding, config: ButlerConfig
) -> list[CleanupPlan]:
    """Translate an ``organize_candidate`` finding into per-file cleanup plans."""

    if finding.category != "organize_candidate":
        raise ValueError(
            "plan_organize_candidate only accepts organize_candidate findings"
        )
    metadata = finding.metadata or {}

    topic = metadata.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("organize findings require a non-empty topic")
    topic = topic.strip()

    member_paths = _validate_members(metadata.get("files"), config)
    target = _derive_target_folder(member_paths, topic)

    test_command = metadata.get("test_command") or config.tests.default_command
    if not test_command:
        raise ValueError("organize plans require a configured test command")

    members_serialized = [path.as_posix() for path in member_paths]
    target_dir = target.path.as_posix()
    batch_size = len(member_paths)
    plans: list[CleanupPlan] = []

    for index, member in enumerate(member_paths):
        relative_file = member.as_posix()
        plan_id = f"{finding.id}-move-{index + 1}"
        title = f"Move {relative_file} into {target_dir}"
        intent = (
            f"Move {topic} file {relative_file} "
            f"into {target_dir} and update imports "
            "without altering code bodies"  # noqa: E501
        )
        destination = (target.path / member.name).as_posix()
        steps = [
            (
                f"Create {target_dir} if missing to group {topic} files "
                f"and stage {relative_file} for relocation without touching unrelated directories."
            ),
            f"Move {relative_file} to {destination} and keep relative imports intact.",
            (
                f"Update imports/re-exports referencing {relative_file} "
                "without modifying function bodies."
            ),
        ]
        constraints = [
            "No changes inside function/class bodies",
            f"Do not introduce nested packages beyond {target_dir}",
            "Ensure re-exports maintain the existing public API",
        ]
        plan_metadata = dict(finding.metadata)
        plan_metadata.update(
            {
                "plan_kind": "organize",
                "scope": "organize",
                "topic": topic,
                "members": members_serialized,
                "target_directory": target_dir,
                "file": relative_file,
                "split_index": index,
                "batch_size": batch_size,
                "requires_reexports": target.requires_reexports,
            }
        )
        plan = CleanupPlan(
            id=plan_id,
            finding_id=finding.id,
            title=title,
            intent=intent,
            steps=steps,
            constraints=constraints,
            tests_to_run=[test_command],
            metadata=plan_metadata,
        )
        plans.append(plan)
    return plans


def _derive_target_folder(
    files: list[Path], topic: str, *, max_additional_depth: int = 2
) -> TargetInfo:
    if not files:
        raise ValueError("organize findings must include files to move")

    shared_parent = _shared_parent(files)
    # Reject disjoint parents (shared_parent resolves to "." when no folder matches).
    if not shared_parent.parts and len({path.parent for path in files}) > 1:
        raise ValueError(
            "organize findings with disjoint parents must be split by analyzers"
        )
    if not shared_parent.parts:
        shared_parent = files[0].parent

    if any(not file_path.is_relative_to(shared_parent) for file_path in files):
        raise ValueError(
            "organize findings with disjoint parents must be split by analyzers"
        )

    topic_slug = _slugify_topic(topic)
    target_path = shared_parent / Path(topic_slug)
    if not target_path.is_relative_to(shared_parent):
        raise ValueError(
            "derived target directory must reside under the shared parent"  # noqa: E501
        )

    depth_increase = len(target_path.relative_to(shared_parent).parts)
    if depth_increase > max_additional_depth:
        raise ValueError(
            "derived organize target is too deep; analyzers should choose a shallower topic"
        )

    requires_reexports = any(_looks_like_public_api(file_path) for file_path in files)
    return TargetInfo(path=target_path, requires_reexports=requires_reexports)


def _validate_members(files_value: Any, config: ButlerConfig) -> list[Path]:
    if not isinstance(files_value, list) or not files_value:
        raise ValueError("organize findings require a non-empty files list")

    max_group_size = getattr(
        config.analyzers.organize, "max_group_size", MAX_FILES_PER_FINDING
    )
    max_files = min(MAX_FILES_PER_FINDING, max_group_size)
    if len(files_value) > max_files:
        raise ValueError(
            f"organize findings must contain at most {max_files} files; "
            f"received {len(files_value)}"  # noqa: E501
        )

    paths: list[Path] = []
    for entry in files_value:
        if not isinstance(entry, str) or not entry.strip():
            raise ValueError("organize findings require file path strings")
        paths.append(Path(entry))
    return paths


def _shared_parent(files: list[Path]) -> Path:
    parent_parts = [file.parent.parts for file in files if file.parent.parts]
    if not parent_parts:
        return Path(".")
    common_parts = list(parent_parts[0])
    for parts in parent_parts[1:]:
        shared: list[str] = []
        for component_a, component_b in zip(common_parts, parts):
            if component_a == component_b:
                shared.append(component_a)
            else:
                break
        common_parts = shared
        if not common_parts:
            break
    return Path(*common_parts) if common_parts else Path(".")


def _slugify_topic(topic: str) -> str:
    normalized = topic.strip().lower()
    if not normalized:
        return "grouped"

    result: list[str] = []
    previous_sep = False
    for char in normalized:
        if char.isalnum():
            result.append(char)
            previous_sep = False
        elif char in {" ", "-", "_"}:
            if not previous_sep:
                result.append("-")
                previous_sep = True
        elif char == "/":
            if not previous_sep:
                result.append("/")
                previous_sep = True
        else:
            if not previous_sep:
                result.append("-")
                previous_sep = True
    slug = "".join(result).strip("-/")
    return slug or "grouped"


def _looks_like_public_api(path: Path) -> bool:
    filename = path.name
    stem = path.stem
    return filename == "__init__.py" or stem in {"api", "public", "interface"}
