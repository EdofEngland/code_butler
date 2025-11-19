"""Factories for building code/review executors from configuration."""

from __future__ import annotations

from typing import Callable, Dict, Type

from ai_clean.config import AiCleanConfig
from ai_clean.interfaces import CodeExecutor, ReviewExecutor

from .codex import CodexExecutor
from .review import CodexReviewExecutor

CodexCompletion = Callable[[str], object]

SUPPORTED_CODE_EXECUTORS: Dict[str, Type[CodeExecutor]] = {
    "codex": CodexExecutor,
}

SUPPORTED_REVIEW_EXECUTORS: Dict[str, Type[ReviewExecutor]] = {
    "codex_review": CodexReviewExecutor,
}


def build_code_executor(config: AiCleanConfig) -> CodeExecutor:
    executor_type = (config.executor.type or "").strip().lower()
    if not executor_type:
        raise ValueError("executor.type must be set in ai-clean.toml.")

    executor_cls = SUPPORTED_CODE_EXECUTORS.get(executor_type)
    if executor_cls is None:
        allowed = ", ".join(sorted(SUPPORTED_CODE_EXECUTORS))
        raise ValueError(
            f"Unsupported executor '{executor_type}'. Allowed values: {allowed}"
        )

    apply_command = list(config.executor.apply_command or [])
    if not apply_command:
        raise ValueError("executor.apply_command must contain at least one token.")

    tests_command = config.tests.default_command
    return executor_cls(
        apply_command=apply_command,
        tests_command=tests_command,
    )


def build_review_executor(
    config: AiCleanConfig,
    *,
    codex_completion: CodexCompletion | None = None,
) -> ReviewExecutor:
    review_type = (config.review.type or "").strip().lower()
    if not review_type:
        raise ValueError("review.type must be set in ai-clean.toml.")

    review_cls = SUPPORTED_REVIEW_EXECUTORS.get(review_type)
    if review_cls is None:
        allowed = ", ".join(sorted(SUPPORTED_REVIEW_EXECUTORS))
        raise ValueError(
            f"Unsupported review executor '{review_type}'. Allowed values: {allowed}"
        )

    if review_type == "codex_review" and codex_completion is None:
        raise RuntimeError(
            "Codex review executor requires a completion callable (codex_completion)."
        )

    return review_cls(completion=codex_completion)  # type: ignore[arg-type]


__all__ = [
    "build_code_executor",
    "build_review_executor",
    "SUPPORTED_CODE_EXECUTORS",
    "SUPPORTED_REVIEW_EXECUTORS",
]
