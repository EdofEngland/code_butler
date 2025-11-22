"""Factory helpers that turn config objects into runtime components."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Sequence

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
from ai_clean.spec_backends import ButlerSpecBackend

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ai_clean.models import CleanupPlan, ExecutionResult


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


BACKEND_BUILDERS: dict[str, Callable[[SpecBackendConfig], SpecBackend]] = {
    "butler": ButlerSpecBackend,
}


def get_spec_backend(config: AiCleanConfig) -> SpecBackendHandle:
    backend_type = (config.spec_backend.type or "").strip().lower()
    builder = BACKEND_BUILDERS.get(backend_type)
    if builder is None:
        raise ValueError(f"Unsupported spec backend: {backend_type or '<empty>'}")
    backend = builder(config.spec_backend)
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
