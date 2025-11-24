"""Helpers for persisting ExecutionResult objects to disk."""

from __future__ import annotations

from pathlib import Path

from ai_clean.models import ExecutionResult
from ai_clean.paths import default_metadata_root


def _resolve_results_dir(results_dir: Path | None) -> Path:
    if results_dir is None:
        return (default_metadata_root().resolve() / "results").resolve()
    return results_dir.resolve()


def save_execution_result(
    result: ExecutionResult, results_dir: Path | None = None
) -> Path:
    """Serialize an ExecutionResult to JSON inside the provided results directory."""

    destination_dir = _resolve_results_dir(results_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{result.plan_id}.json"
    destination.write_text(result.to_json())
    return destination


def load_execution_result(
    plan_id: str, results_dir: Path | None = None
) -> ExecutionResult:
    """Load an ExecutionResult from the provided results directory."""

    destination_dir = _resolve_results_dir(results_dir)
    path = destination_dir / f"{plan_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"ExecutionResult not found: {path}")
    return ExecutionResult.from_json(path.read_text())


__all__ = ["save_execution_result", "load_execution_result"]
