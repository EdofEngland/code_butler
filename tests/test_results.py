from __future__ import annotations

from pathlib import Path

from ai_clean.models import ExecutionResult
from ai_clean.results import load_execution_result, save_execution_result


def test_save_and_load_execution_result(tmp_path: Path) -> None:
    metadata_root = tmp_path / ".ai-clean"
    results_dir = metadata_root / "results"
    result = ExecutionResult(
        spec_id="spec-1",
        plan_id="plan-1",
        success=True,
        tests_passed=True,
        stdout="ok",
        stderr="",
        metadata={"tests": {"status": "ran", "command": "pytest", "exit_code": 0}},
    )

    path = save_execution_result(result, results_dir)
    assert path.name == "plan-1.json"
    loaded = load_execution_result("plan-1", results_dir)
    assert loaded == result
