"""Configuration loader for ai-clean.

Uses standard library `tomllib` when available (Python 3.11+) and falls back
on `tomli` if installed for earlier Python versions. Raises a clear error when
no TOML parser is available.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from ai_clean.spec_backends.factory import SUPPORTED_SPEC_BACKENDS

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - Python <3.11 fallback
    tomllib = None  # type: ignore[assignment]


if tomllib is None:  # pragma: no cover - Python <3.11 fallback
    try:
        import tomli as tomllib  # type: ignore[no-redef,assignment]
    except ModuleNotFoundError as exc:  # pragma: no cover - explicit error
        raise RuntimeError(
            "No TOML parser available. Install tomli for Python <3.11."
        ) from exc


SUPPORTED_EXECUTORS = {"codex"}
SUPPORTED_EXECUTOR_BACKENDS = {"codex"}
SUPPORTED_REVIEW = {"codex_review"}
DEFAULT_MAX_PLAN_FILES = 5
DEFAULT_MAX_PLAN_LINES = 400
ENV_EXECUTOR_BACKEND = "AI_CLEAN_EXECUTOR_BACKEND"
ENV_EXECUTOR_COMMAND_PREFIX = "AI_CLEAN_EXECUTOR_COMMAND_PREFIX"
ENV_EXECUTOR_PROMPT_HINT = "AI_CLEAN_EXECUTOR_PROMPT_HINT"


@dataclass
class SpecBackendConfig:
    type: str


@dataclass
class ExecutorConfig:
    type: str
    apply_command: List[str]


@dataclass
class ExecutorBackendConfig:
    type: str
    command_prefix: str
    prompt_hint: str


@dataclass
class ReviewConfig:
    type: str


@dataclass
class GitConfig:
    base_branch: str
    refactor_branch: str


@dataclass
class TestsConfig:
    default_command: str


@dataclass
class AiCleanConfig:
    spec_backend: SpecBackendConfig
    executor: ExecutorConfig
    executor_backend: ExecutorBackendConfig
    review: ReviewConfig
    git: GitConfig
    tests: TestsConfig
    metadata_root: Path
    plans_dir: Path
    specs_dir: Path
    executions_dir: Path
    max_plan_files: int
    max_plan_lines: int
    allow_global_rename: bool


def _require(section: Dict[str, Any], key: str) -> str:
    if key not in section or section[key] in (None, ""):
        section_name = section.get("__name__") or "unknown"
        raise ValueError(
            f"Missing required config key '{key}' in [{section_name}] section"
        )
    value = str(section[key])
    return value


def _validate_choice(section: str, key: str, value: str, allowed: set[str]) -> str:
    if value not in allowed:
        raise ValueError(
            f"Unsupported value '{value}' for key '{key}' in [{section}] section. "
            f"Allowed: {sorted(allowed)}"
        )
    return value


def _get_section(config: Dict[str, Any], name: str) -> Dict[str, Any]:
    section = dict(config.get(name, {}) or {})
    section["__name__"] = name
    return section


def _get_int(
    section: Dict[str, Any],
    key: str,
    *,
    default: int,
) -> int:
    value = section.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        section_name = section.get("__name__") or "unknown"
        raise ValueError(
            f"Invalid integer value for '{key}' in [{section_name}] section"
        ) from None


def _require_command_list(
    section: Dict[str, Any],
    key: str,
    *,
    require_placeholder: bool = False,
) -> List[str]:
    section_name = section.get("__name__") or "unknown"
    value = section.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(
            f"Missing required list key '{key}' in [{section_name}] section"
        )
    command = [str(part) for part in value if str(part).strip()]
    if not command:
        raise ValueError(
            (
                f"List key '{key}' in [{section_name}] section must include at least "
                "one item"
            )
        )
    if require_placeholder and not any("{spec_path}" in part for part in command):
        raise ValueError(
            f"List key '{key}' in [{section_name}] must include '{{spec_path}}' so "
            "the executor can substitute the spec path."
        )
    return command


def load_config(config_path: Path | str = "ai-clean.toml") -> AiCleanConfig:
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("rb") as fh:
        raw_cfg = tomllib.load(fh)

    spec_backend_section = _get_section(raw_cfg, "spec_backend")
    executor_section = _get_section(raw_cfg, "executor")
    executor_backend_section = _get_section(raw_cfg, "executor_backend")
    review_section = _get_section(raw_cfg, "review")
    git_section = _get_section(raw_cfg, "git")
    tests_section = _get_section(raw_cfg, "tests")
    limits_section = _get_section(raw_cfg, "limits")

    spec_backend = SpecBackendConfig(type=_require(spec_backend_section, "type"))
    executor = ExecutorConfig(
        type=_require(executor_section, "type"),
        apply_command=_require_command_list(
            executor_section,
            "apply_command",
            require_placeholder=True,
        ),
    )
    backend_type = (
        os.getenv(ENV_EXECUTOR_BACKEND)
        or executor_backend_section.get("type")
        or "codex"
    )
    backend_prefix = (
        os.getenv(ENV_EXECUTOR_COMMAND_PREFIX)
        or executor_backend_section.get("command_prefix")
        or "/openspec-apply"
    )
    backend_prompt = (
        os.getenv(ENV_EXECUTOR_PROMPT_HINT)
        or executor_backend_section.get("prompt_hint")
        or "/prompts:openspec-apply"
    )
    executor_backend = ExecutorBackendConfig(
        type=str(backend_type).strip(),
        command_prefix=str(backend_prefix).strip() or "/openspec-apply",
        prompt_hint=str(backend_prompt).strip(),
    )
    review = ReviewConfig(type=_require(review_section, "type"))
    git = GitConfig(
        base_branch=_require(git_section, "base_branch"),
        refactor_branch=_require(git_section, "refactor_branch"),
    )
    tests = TestsConfig(default_command=_require(tests_section, "default_command"))

    spec_backend.type = _validate_choice(
        "spec_backend",
        "type",
        spec_backend.type,
        set(SUPPORTED_SPEC_BACKENDS.keys()),
    )
    executor.type = _validate_choice(
        "executor", "type", executor.type, SUPPORTED_EXECUTORS
    )
    executor_backend.type = _validate_choice(
        "executor_backend",
        "type",
        executor_backend.type or "codex",
        SUPPORTED_EXECUTOR_BACKENDS,
    )
    if not executor_backend.command_prefix:
        raise ValueError("executor_backend.command_prefix cannot be empty.")

    review.type = _validate_choice("review", "type", review.type, SUPPORTED_REVIEW)

    metadata_root = Path(".ai-clean")
    plans_dir = metadata_root / "plans"
    specs_dir = metadata_root / "specs"
    executions_dir = metadata_root / "executions"
    plans_dir.mkdir(parents=True, exist_ok=True)
    specs_dir.mkdir(parents=True, exist_ok=True)
    executions_dir.mkdir(parents=True, exist_ok=True)

    max_plan_files = _get_int(
        limits_section,
        "max_plan_files",
        default=DEFAULT_MAX_PLAN_FILES,
    )
    max_plan_lines = _get_int(
        limits_section,
        "max_plan_lines",
        default=DEFAULT_MAX_PLAN_LINES,
    )
    allow_global_rename = bool(limits_section.get("allow_global_rename", False))

    return AiCleanConfig(
        spec_backend=spec_backend,
        executor=executor,
        executor_backend=executor_backend,
        review=review,
        git=git,
        tests=tests,
        metadata_root=metadata_root,
        plans_dir=plans_dir,
        specs_dir=specs_dir,
        executions_dir=executions_dir,
        max_plan_files=max_plan_files,
        max_plan_lines=max_plan_lines,
        allow_global_rename=allow_global_rename,
    )


__all__ = [
    "SpecBackendConfig",
    "ExecutorConfig",
    "ReviewConfig",
    "GitConfig",
    "TestsConfig",
    "AiCleanConfig",
    "load_config",
]
