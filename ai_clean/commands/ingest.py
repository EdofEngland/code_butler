"""Ingest Codex slash-command artifacts into ExecutionResult (and optional findings)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from ai_clean.models import ExecutionResult, Finding, FindingLocation
from ai_clean.results import load_execution_result, save_execution_result

AllowedTestStatus = {
    "ran",
    "failed",
    "not_run",
    "timed_out",
    "command_not_found",
    "apply_failed",
}


@dataclass(frozen=True)
class IngestSummary:
    tests_status: str
    tests_passed: bool | None
    success: bool
    diff_added: int
    diff_removed: int
    suggestions_ingested: int


class IngestError(ValueError):
    """Raised when an ingest artifact is invalid or cannot be applied."""


def _load_artifact(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise IngestError(f"Artifact not found: {path}")
    try:
        payload = json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - defensive
        raise IngestError(f"Artifact is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise IngestError(
            "Artifact must be a JSON object with diff/stdout/stderr/tests"
        )
    return payload


def _validate_tests_block(tests: Any) -> dict[str, Any]:
    if not isinstance(tests, dict):
        raise IngestError("Artifact.tests must be an object")

    required = {"status", "command", "exit_code", "stdout", "stderr"}
    unexpected = set(tests.keys()) - (required | {"reason", "error", "timeout_seconds"})
    if unexpected:
        raise IngestError(
            f"Artifact.tests has unexpected fields: {', '.join(sorted(unexpected))}"
        )

    missing = [key for key in required if key not in tests]
    if missing:
        raise IngestError(
            f"Artifact.tests missing required fields: {', '.join(missing)}"
        )

    status = str(tests.get("status", "")).strip()
    if status not in AllowedTestStatus:
        raise IngestError(
            "Artifact.tests.status must be one of "
            f"{sorted(AllowedTestStatus)}, got {status!r}"
        )

    exit_code = tests.get("exit_code")
    if status in {"ran", "failed"}:
        if not isinstance(exit_code, int):
            raise IngestError(
                "Artifact.tests.exit_code must be an integer when status is ran/failed"
            )
    return {
        "status": status,
        "command": str(tests.get("command") or ""),
        "exit_code": exit_code,
        "stdout": str(tests.get("stdout") or ""),
        "stderr": str(tests.get("stderr") or ""),
        "reason": str(tests.get("reason") or tests.get("error") or "").strip(),
        "timeout_seconds": tests.get("timeout_seconds"),
    }


def _is_unified_diff(diff: str) -> bool:
    marker_count = diff.count("diff --git ")
    return (
        marker_count == 1
        and "--- " in diff
        and "+++ " in diff
        and any(line.startswith("@@") for line in diff.splitlines())
    )


def _diff_stats(diff: str) -> tuple[int, int]:
    added = 0
    removed = 0
    for line in diff.splitlines():
        if line.startswith(("+++ ", "--- ", "diff ")):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1
    return added, removed


def _derive_status(
    tests: dict[str, Any], diff_present: bool
) -> tuple[bool, bool | None]:
    status = tests["status"]
    exit_code = tests.get("exit_code")
    if status == "ran":
        tests_passed = exit_code == 0
        return bool(diff_present and tests_passed), tests_passed
    if status == "failed":
        return False, False
    if status == "not_run":
        return bool(diff_present), None
    if status in {"timed_out", "command_not_found", "apply_failed"}:
        return False, None
    return False, None


def _validate_suggestions(
    suggestions: Any,
    root: Path,
    max_files: int | None = None,
    max_suggestions: int | None = None,
) -> list[Finding]:
    if suggestions is None:
        return []
    if not isinstance(suggestions, list):
        raise IngestError("Artifact.suggestions must be an array when provided")

    findings: list[Finding] = []
    file_set: set[str] = set()

    if max_suggestions is not None and len(suggestions) > max_suggestions:
        raise IngestError("Artifact.suggestions exceeds configured max_suggestions")

    for idx, item in enumerate(suggestions, start=1):
        if not isinstance(item, dict):
            raise IngestError("Artifact.suggestions entries must be objects")
        required = {
            "description",
            "path",
            "start_line",
            "end_line",
            "change_type",
            "model",
            "prompt_hash",
        }
        missing = [key for key in required if key not in item]
        if missing:
            raise IngestError(
                f"Suggestion missing required fields: {', '.join(missing)}"
            )
        unexpected = set(item.keys()) - required
        if unexpected:
            raise IngestError(
                f"Suggestion has unexpected fields: {', '.join(sorted(unexpected))}"
            )
        path = Path(str(item["path"])).as_posix()
        file_set.add(path)
        start_line = int(item["start_line"])
        end_line = int(item["end_line"])
        if start_line <= 0 or end_line < start_line:
            raise IngestError("Suggestion line numbers must be positive and ordered")

        finding_id = f"adv-ingest-{idx}"
        findings.append(
            Finding(
                id=finding_id,
                category="advanced_cleanup",
                description=str(item["description"]),
                locations=[
                    FindingLocation(
                        path=Path(path),
                        start_line=start_line,
                        end_line=end_line,
                    )
                ],
                metadata={
                    "change_type": str(item["change_type"]),
                    "codex_model": str(item["model"]),
                    "prompt_hash": str(item["prompt_hash"]),
                    "target_path": path,
                    "start_line": start_line,
                    "end_line": end_line,
                    "description": str(item["description"]),
                    "source": "codex_ingest",
                    "raw": item,
                },
            )
        )

    if max_files is not None and len(file_set) > max_files:
        raise IngestError("Artifact.suggestions spans more files than allowed")

    for finding in findings:
        resolved = (root / finding.locations[0].path).resolve()
        if not str(resolved).startswith(str(root.resolve())):
            raise IngestError(
                f"Suggestion path outside root: {finding.locations[0].path}"
            )

    return findings


def _load_findings(path: Path) -> list[Finding]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - defensive
        raise IngestError(f"Failed to parse findings JSON: {exc}") from exc
    if not isinstance(payload, list):
        raise IngestError("Findings JSON must be an array")
    return [Finding.model_validate(item) for item in payload]


def _save_findings(path: Path, findings: Iterable[Finding]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [finding.model_dump(mode="json") for finding in findings]
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def ingest_codex_artifact(
    *,
    plan_id: str,
    artifact_path: Path,
    results_dir: Path,
    root: Path,
    update_findings: bool = False,
    findings_path: Path | None = None,
    max_suggestions: int | None = None,
    max_suggestion_files: int | None = None,
) -> tuple[ExecutionResult, IngestSummary]:
    """Ingest a Codex artifact and update the stored ExecutionResult."""

    artifact = _load_artifact(artifact_path)
    allowed_keys = {
        "plan_id",
        "spec_path",
        "diff",
        "stdout",
        "stderr",
        "tests",
        "suggestions",
    }
    unexpected = set(artifact.keys()) - allowed_keys
    if unexpected:
        raise IngestError(
            f"Artifact has unexpected fields: {', '.join(sorted(unexpected))}"
        )

    artifact_plan = artifact.get("plan_id")
    if artifact_plan and artifact_plan != plan_id:
        raise IngestError(
            f"Artifact plan_id {artifact_plan!r} does not match requested plan "
            f"{plan_id!r}"
        )

    for required in ("diff", "stdout", "stderr", "tests"):
        if required not in artifact:
            raise IngestError(f"Artifact missing required field: {required}")

    diff = artifact.get("diff")
    stdout = artifact.get("stdout")
    stderr = artifact.get("stderr")
    tests_raw = artifact.get("tests")

    if not isinstance(stdout, str) or not isinstance(stderr, str):
        raise IngestError("Artifact stdout/stderr must be strings")
    if not isinstance(diff, str):
        raise IngestError(
            "Artifact diff must be a string (may be empty only for apply_failed)"
        )

    tests = _validate_tests_block(tests_raw)

    diff_required = tests["status"] != "apply_failed"
    if diff_required and not diff.strip():
        raise IngestError("Artifact diff is required unless tests.status=apply_failed")
    if diff.strip() and not _is_unified_diff(diff):
        raise IngestError("Artifact diff must be a unified diff for a single file")

    existing = load_execution_result(plan_id, results_dir)

    diff_present = bool(diff.strip())
    success, tests_passed = _derive_status(tests, diff_present)

    metadata = dict(existing.metadata or {})
    metadata["manual_execution_required"] = False
    metadata["tests"] = {
        k: v for k, v in tests.items() if v is not None and k != "reason"
    }
    if tests.get("reason"):
        metadata["tests"]["reason"] = tests["reason"]
    if "timeout_seconds" in tests and tests["timeout_seconds"] is not None:
        metadata["tests"]["timeout_seconds"] = tests["timeout_seconds"]

    updated = existing.model_copy(
        update={
            "success": success,
            "tests_passed": tests_passed,
            "stdout": stdout,
            "stderr": stderr,
            "git_diff": diff if diff_present else None,
            "metadata": metadata,
        }
    )

    save_execution_result(updated, results_dir)

    suggestions_count = 0
    suggestions = artifact.get("suggestions")
    if update_findings and suggestions is not None:
        findings = _validate_suggestions(
            suggestions,
            root.resolve(),
            max_files=max_suggestion_files,
            max_suggestions=max_suggestions,
        )
        target_path = findings_path or (root / ".ai-clean" / "findings.json")
        existing_findings = _load_findings(target_path)
        existing_ids = {finding.id for finding in existing_findings}
        normalized: list[Finding] = []
        for finding in findings:
            candidate_id = finding.id
            counter = 1
            while candidate_id in existing_ids:
                counter += 1
                candidate_id = f"{finding.id}-{counter}"
            normalized.append(finding.model_copy(update={"id": candidate_id}))
            existing_ids.add(candidate_id)
        _save_findings(target_path, [*existing_findings, *normalized])
        suggestions_count = len(normalized)

    added, removed = _diff_stats(diff) if diff_present else (0, 0)

    return updated, IngestSummary(
        tests_status=tests["status"],
        tests_passed=tests_passed,
        success=success,
        diff_added=added,
        diff_removed=removed,
        suggestions_ingested=suggestions_count,
    )
