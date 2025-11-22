from __future__ import annotations

from pathlib import Path

import pytest

from ai_clean.config import (
    AdvancedAnalyzerConfig,
    AiCleanConfig,
    AnalyzersConfig,
    DocstringAnalyzerConfig,
    DuplicateAnalyzerConfig,
    ExecutorConfig,
    GitConfig,
    OrganizeAnalyzerConfig,
    ReviewConfig,
    SpecBackendConfig,
    StructureAnalyzerConfig,
)
from ai_clean.config import TestsConfig as TestsCfg
from ai_clean.factories import get_spec_backend
from ai_clean.spec_backends import ButlerSpecBackend

TestsCfg.__test__ = False  # Prevent pytest from treating the dataclass as a test.


def _sample_config(backend_type: str) -> AiCleanConfig:
    metadata_root = Path(".ai-clean")
    plans_dir = metadata_root / "plans"
    specs_dir = metadata_root / "specs"
    results_dir = metadata_root / "results"

    analyzers = AnalyzersConfig(
        duplicate=DuplicateAnalyzerConfig(
            window_size=5,
            min_occurrences=2,
            ignore_dirs=(".git",),
        ),
        structure=StructureAnalyzerConfig(
            max_file_lines=400,
            max_function_lines=60,
            ignore_dirs=(".git",),
        ),
        docstring=DocstringAnalyzerConfig(
            min_docstring_length=32,
            min_symbol_lines=5,
            weak_markers=("todo",),
            important_symbols_only=True,
            ignore_dirs=(".git",),
        ),
        organize=OrganizeAnalyzerConfig(
            min_group_size=2,
            max_group_size=5,
            max_groups=3,
            ignore_dirs=(".git",),
        ),
        advanced=AdvancedAnalyzerConfig(
            max_files=3,
            max_suggestions=5,
            prompt_template="tmpl",
            codex_model="gpt",
            temperature=0.2,
            ignore_dirs=(".git",),
        ),
    )

    return AiCleanConfig(
        spec_backend=SpecBackendConfig(
            type=backend_type,
            default_batch_group="default",
            specs_dir=specs_dir,
        ),
        executor=ExecutorConfig(
            type="codex_shell",
            binary="codex",
            apply_args=("apply",),
            results_dir=results_dir,
        ),
        review=ReviewConfig(type="codex_review", mode="summarize"),
        git=GitConfig(base_branch="main", refactor_branch="refactor/ai-clean"),
        tests=TestsCfg(default_command="pytest -q"),
        analyzers=analyzers,
        metadata_root=metadata_root,
        plans_dir=plans_dir,
        specs_dir=specs_dir,
        results_dir=results_dir,
    )


def test_get_spec_backend_returns_butler_backend():
    config = _sample_config("butler")
    handle = get_spec_backend(config)

    assert isinstance(handle.backend, ButlerSpecBackend)
    assert handle.specs_dir == config.spec_backend.specs_dir


def test_get_spec_backend_rejects_unknown_type():
    config = _sample_config("other")

    with pytest.raises(ValueError, match="Unsupported spec backend: other"):
        get_spec_backend(config)


def test_get_spec_backend_rejects_blank_type():
    config = _sample_config("")

    with pytest.raises(ValueError, match="Unsupported spec backend: <empty>"):
        get_spec_backend(config)
