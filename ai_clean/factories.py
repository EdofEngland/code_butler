"""Factory helpers that turn config objects into runtime components."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

from ai_clean.config import (
    AiCleanConfig,
    ExecutorConfig,
    ReviewConfig,
    SpecBackendConfig,
)
from ai_clean.interfaces import (
    CodeExecutor,
    CodexPromptRunner,
    PromptAttachment,
    ReviewExecutor,
    SpecBackend,
    StructuredReview,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ai_clean.models import ButlerSpec, CleanupPlan, ExecutionResult


@dataclass(frozen=True)
class SpecBackendHandle:
    backend: SpecBackend
    specs_dir: Path


@dataclass(frozen=True)
class ExecutorHandle:
    executor: CodeExecutor
    results_dir: Path


@dataclass(frozen=True)
class ReviewExecutorHandle:
    reviewer: ReviewExecutor
    metadata_root: Path


class _CodexPromptRunner:
    def __init__(self) -> None:
        self._configured = True

    def run(
        self, prompt: str, attachments: Sequence[PromptAttachment]
    ) -> str:  # pragma: no cover - stub
        raise NotImplementedError(
            "Codex prompt execution is implemented in later milestones."
        )


class _ButlerSpecBackend:
    """Placeholder backend wired to Butler defaults."""

    def __init__(self, config: SpecBackendConfig) -> None:
        self._config = config

    def plan_to_spec(
        self, plan: "CleanupPlan"
    ) -> "ButlerSpec":  # pragma: no cover - stub
        raise NotImplementedError("Spec generation is implemented in later milestones.")

    def write_spec(
        self, spec: "ButlerSpec", directory: Path
    ) -> Path:  # pragma: no cover - stub
        raise NotImplementedError("Spec writing is implemented in later milestones.")


class _CodexShellExecutor:
    """Placeholder executor that documents Codex shell usage."""

    def __init__(self, config: ExecutorConfig) -> None:
        self._config = config

    def apply_spec(
        self, spec_path: Path
    ) -> "ExecutionResult":  # pragma: no cover - stub
        raise NotImplementedError("Execution logic is implemented in later milestones.")


class _CodexReviewExecutor:
    """Placeholder review executor."""

    def __init__(self, config: ReviewConfig) -> None:
        self._config = config

    def review_change(
        self,
        plan: "CleanupPlan",
        diff: str,
        exec_result: "ExecutionResult",
    ) -> StructuredReview:  # pragma: no cover - stub
        raise NotImplementedError("Review logic is implemented in later milestones.")


def get_spec_backend(config: AiCleanConfig) -> SpecBackendHandle:
    backend = _ButlerSpecBackend(config.spec_backend)
    return SpecBackendHandle(backend=backend, specs_dir=config.spec_backend.specs_dir)


def get_executor(config: AiCleanConfig) -> ExecutorHandle:
    executor = _CodexShellExecutor(config.executor)
    return ExecutorHandle(executor=executor, results_dir=config.executor.results_dir)


def get_review_executor(config: AiCleanConfig) -> ReviewExecutorHandle:
    reviewer = _CodexReviewExecutor(config.review)
    return ReviewExecutorHandle(reviewer=reviewer, metadata_root=config.metadata_root)


def get_codex_prompt_runner(config: AiCleanConfig) -> CodexPromptRunner:
    _ = config  # placeholder until advanced analyzer wiring uses model settings
    return _CodexPromptRunner()


__all__ = [
    "ExecutorHandle",
    "ReviewExecutorHandle",
    "SpecBackendHandle",
    "get_executor",
    "get_review_executor",
    "get_spec_backend",
    "get_codex_prompt_runner",
]
