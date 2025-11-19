from __future__ import annotations

import unittest

from ai_clean.config import (
    AiCleanConfig,
    ExecutorConfig,
    GitConfig,
    ReviewConfig,
    SpecBackendConfig,
    TestsConfig,
)
from ai_clean.executors import CodexExecutor
from ai_clean.executors.factory import build_code_executor, build_review_executor


def _config(
    *,
    executor_type: str = "codex",
    review_type: str = "codex_review",
) -> AiCleanConfig:
    return AiCleanConfig(
        spec_backend=SpecBackendConfig(type="openspec"),
        executor=ExecutorConfig(
            type=executor_type, apply_command=["echo", "{spec_path}"]
        ),
        review=ReviewConfig(type=review_type),
        git=GitConfig(base_branch="main", refactor_branch="feature"),
        tests=TestsConfig(default_command="pytest -q"),
        metadata_root=None,  # type: ignore[arg-type]
        plans_dir=None,  # type: ignore[arg-type]
        specs_dir=None,  # type: ignore[arg-type]
    )


class ExecutorFactoryTests(unittest.TestCase):
    def test_build_code_executor_success(self) -> None:
        config = _config()
        executor = build_code_executor(config)
        self.assertIsInstance(executor, CodexExecutor)

    def test_build_code_executor_invalid_type(self) -> None:
        config = _config(executor_type="unknown")
        config.executor.apply_command = ["echo", "{spec_path}"]
        with self.assertRaises(ValueError):
            build_code_executor(config)

    def test_build_review_executor_requires_completion(self) -> None:
        config = _config()
        with self.assertRaises(RuntimeError):
            build_review_executor(config)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
