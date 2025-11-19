"""Configuration loader for ai-clean.

Uses standard library `tomllib` when available (Python 3.11+) and falls back
on `tomli` if installed for earlier Python versions. Raises a clear error when
no TOML parser is available.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

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


SUPPORTED_SPEC_BACKENDS = {"openspec"}
SUPPORTED_EXECUTORS = {"codex"}
SUPPORTED_REVIEW = {"codex_review"}


@dataclass
class SpecBackendConfig:
    type: str


@dataclass
class ExecutorConfig:
    type: str


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
    review: ReviewConfig
    git: GitConfig
    tests: TestsConfig
    metadata_root: Path
    plans_dir: Path
    specs_dir: Path


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


def load_config(config_path: Path | str = "ai-clean.toml") -> AiCleanConfig:
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("rb") as fh:
        raw_cfg = tomllib.load(fh)

    spec_backend_section = _get_section(raw_cfg, "spec_backend")
    executor_section = _get_section(raw_cfg, "executor")
    review_section = _get_section(raw_cfg, "review")
    git_section = _get_section(raw_cfg, "git")
    tests_section = _get_section(raw_cfg, "tests")

    spec_backend = SpecBackendConfig(type=_require(spec_backend_section, "type"))
    executor = ExecutorConfig(type=_require(executor_section, "type"))
    review = ReviewConfig(type=_require(review_section, "type"))
    git = GitConfig(
        base_branch=_require(git_section, "base_branch"),
        refactor_branch=_require(git_section, "refactor_branch"),
    )
    tests = TestsConfig(default_command=_require(tests_section, "default_command"))

    spec_backend.type = _validate_choice(
        "spec_backend", "type", spec_backend.type, SUPPORTED_SPEC_BACKENDS
    )
    executor.type = _validate_choice(
        "executor", "type", executor.type, SUPPORTED_EXECUTORS
    )
    review.type = _validate_choice("review", "type", review.type, SUPPORTED_REVIEW)

    metadata_root = Path(".ai-clean")
    plans_dir = metadata_root / "plans"
    specs_dir = metadata_root / "specs"
    plans_dir.mkdir(parents=True, exist_ok=True)
    specs_dir.mkdir(parents=True, exist_ok=True)

    return AiCleanConfig(
        spec_backend=spec_backend,
        executor=executor,
        review=review,
        git=git,
        tests=tests,
        metadata_root=metadata_root,
        plans_dir=plans_dir,
        specs_dir=specs_dir,
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
