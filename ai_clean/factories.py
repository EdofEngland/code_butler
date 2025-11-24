"""Factory helpers that turn config objects into runtime components."""

from __future__ import annotations

import hashlib
import json
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Sequence

import yaml

from ai_clean.config import (
    AiCleanConfig,
    ExecutorConfig,
    ReviewConfig,
    SpecBackendConfig,
    TestsConfig,
)
from ai_clean.interfaces import (
    CodeExecutor,
    CodexPromptRunner,
    PromptAttachment,
    ReviewExecutor,
    SpecBackend,
    StructuredReview,
)
from ai_clean.models import CleanupPlan, ExecutionResult
from ai_clean.spec_backends import ButlerSpecBackend

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ai_clean.models import CleanupPlan


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

    def run(self, prompt: str, attachments: Sequence[PromptAttachment]) -> str:
        # Minimal stub that callers can monkeypatch; keeps deterministic output shape.
        _ = attachments
        return f"[codex-stub-response]\n{prompt}"


class _CodexShellExecutor:
    """Run a single Codex apply via a deterministic bash wrapper with no extras."""

    _APPLY_TIMEOUT_SECONDS = 300.0
    _TEST_TIMEOUT_SECONDS = 600.0
    _TEST_STATUS_RAN = "ran"
    _TEST_STATUS_SKIPPED = "skipped"
    _TEST_STATUS_NOT_CONFIGURED = "not_configured"
    _TEST_STATUS_APPLY_FAILED = "apply_failed"
    _TEST_STATUS_CMD_NOT_FOUND = "command_not_found"
    _TEST_STATUS_TIMED_OUT = "timed_out"

    def __init__(self, config: ExecutorConfig, tests_config: TestsConfig) -> None:
        self._config = config
        self._tests_config = tests_config

    def apply_spec(self, spec_path: Path) -> ExecutionResult:
        resolved_path = self._normalize_spec_path(spec_path)
        initial_checksum = self._checksum(resolved_path)
        spec_id, plan_id = self._extract_spec_ids(resolved_path)
        command = self._build_command(resolved_path)

        try:
            completed = self._run_apply(command, resolved_path)
        except FileNotFoundError as exc:
            self._assert_unchanged(resolved_path, initial_checksum)
            raise FileNotFoundError(
                f"Executor binary not found: {self._config.binary}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            self._assert_unchanged(resolved_path, initial_checksum)
            raise TimeoutError(
                f"Codex apply timed out after {exc.timeout} seconds for {resolved_path}"
            ) from exc

        stdout = completed.stdout
        stderr = completed.stderr
        success = completed.returncode == 0
        tests_passed: bool | None
        tests_metadata: dict[str, object]

        if not success:
            tests_passed = None
            tests_metadata = {
                "status": self._TEST_STATUS_APPLY_FAILED,
                "reason": "apply_failed",
                "apply_exit_code": completed.returncode,
            }
        else:
            test_command = (self._tests_config.default_command or "").strip()
            if not test_command:
                tests_passed = False
                tests_metadata = {
                    "status": self._TEST_STATUS_NOT_CONFIGURED,
                    "reason": "no_test_command",
                }
            else:
                tests_passed, tests_metadata = self._run_tests(
                    test_command, resolved_path
                )

        self._assert_unchanged(resolved_path, initial_checksum)

        metadata: dict[str, object] = {"exit_code": completed.returncode}
        metadata["tests"] = tests_metadata

        return ExecutionResult(
            spec_id=spec_id,
            plan_id=plan_id,
            success=success,
            tests_passed=tests_passed,
            stdout=stdout,
            stderr=stderr,
            git_diff=None,
            metadata=metadata,
        )

    def _normalize_spec_path(self, spec_path: Path) -> Path:
        if isinstance(spec_path, (list, tuple, set)):
            raise TypeError("apply_spec only accepts a single spec file path.")

        candidate = Path(spec_path).expanduser()
        raw_path = str(candidate)
        if any(char in raw_path for char in ("*", "?", "[")):
            raise ValueError(f"Spec path must not be a glob or pattern: {spec_path}")

        resolved = candidate.resolve()
        if resolved.is_dir():
            raise ValueError(f"Spec path must be a file, not a directory: {resolved}")
        if not resolved.is_file():
            raise ValueError(f"Spec path must exist and be a file: {resolved}")
        return resolved

    def _extract_spec_ids(self, spec_path: Path) -> tuple[str, str]:
        try:
            parsed = yaml.safe_load(spec_path.read_text())
        except yaml.YAMLError as exc:
            raise ValueError(f"Unable to parse spec YAML: {spec_path}") from exc

        if not isinstance(parsed, dict):
            raise ValueError(f"Spec YAML must be a mapping: {spec_path}")

        spec_id = parsed.get("id") or self._spec_id_from_path(spec_path)
        plan_id = parsed.get("plan_id")

        if not plan_id:
            raise ValueError(f"Spec file is missing required plan_id: {spec_path}")

        return str(spec_id), str(plan_id)

    def _spec_id_from_path(self, spec_path: Path) -> str:
        filename = spec_path.name
        if filename.endswith(".butler.yaml"):
            return filename[: -len(".butler.yaml")]
        return spec_path.stem

    def _build_command(self, spec_path: Path) -> list[str]:
        if shutil.which(self._config.binary) is None:
            raise FileNotFoundError(f"Executor binary not found: {self._config.binary}")

        base_command = [
            self._config.binary,
            *self._config.apply_args,
            str(spec_path),
        ]
        # Keep Codex invocation predictable: one apply per call, no env tweaks.
        shell_command = " ".join(shlex.quote(part) for part in base_command)
        return ["bash", "-lc", shell_command]

    def _checksum(self, spec_path: Path) -> str:
        return hashlib.sha256(spec_path.read_bytes()).hexdigest()

    def _assert_unchanged(self, spec_path: Path, expected_checksum: str) -> None:
        current = self._checksum(spec_path)
        if current != expected_checksum:
            raise RuntimeError(f"Spec file was modified during execution: {spec_path}")

    def _run_apply(
        self, command: list[str], spec_path: Path
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=spec_path.parent,
            check=False,
            timeout=self._APPLY_TIMEOUT_SECONDS,
        )

    def _run_tests(
        self, command: str, spec_path: Path
    ) -> tuple[bool, dict[str, object]]:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=spec_path.parent,
                shell=True,
                check=False,
                timeout=self._TEST_TIMEOUT_SECONDS,
            )
        except FileNotFoundError as exc:
            return False, {
                "status": self._TEST_STATUS_CMD_NOT_FOUND,
                "command": command,
                "error": str(exc),
            }
        except subprocess.TimeoutExpired as exc:
            return False, {
                "status": self._TEST_STATUS_TIMED_OUT,
                "command": command,
                "timeout_seconds": exc.timeout,
            }

        return result.returncode == 0, {
            "status": self._TEST_STATUS_RAN,
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }


class _CodexReviewExecutor:
    """Codex-powered review executor that emits advisory-only feedback."""

    def __init__(
        self,
        config: ReviewConfig,
        metadata_root: Path,
        prompt_runner: CodexPromptRunner,
    ) -> None:
        self._config = config
        self._metadata_root = Path(metadata_root)
        self._prompt_runner = prompt_runner

    def review_change(
        self,
        plan: "CleanupPlan | None",
        diff: str,
        exec_result: ExecutionResult,
        *,
        plan_id: str | None = None,
    ) -> StructuredReview:
        resolved_plan = self._load_plan(plan, plan_id or exec_result.plan_id)
        self._validate_execution_result(exec_result)

        prompt = self._build_prompt(resolved_plan, diff, exec_result)
        try:
            output = self._prompt_runner.run(prompt, [])
            exit_code = 0
        except Exception as exc:
            raise RuntimeError(f"Codex review invocation failed: {exc}") from exc

        self._assert_advisory_only(output)
        review_payload, review_metadata = self._normalize_review_output(output)

        metadata = {
            "prompt": prompt,
            "attachments": {
                "plan_id": resolved_plan.id,
                "diff_provided": bool(diff.strip()),
                "spec_id": exec_result.spec_id,
            },
            "exit_code": exit_code,
        }
        metadata.update(review_metadata)

        review_payload.setdefault("risk_grade", "unknown")
        review_payload.setdefault("manual_checks", [])

        review_payload["metadata"] = metadata
        return review_payload

    def _load_plan(
        self, plan: "CleanupPlan | None", plan_id: str | None
    ) -> "CleanupPlan":
        if plan is not None:
            return plan
        if not plan_id:
            raise ValueError("CleanupPlan or plan_id is required for review.")
        plan_path = self._metadata_root / "plans" / f"{plan_id}.json"
        if not plan_path.is_file():
            raise FileNotFoundError(f"Plan file not found: {plan_path}")
        return CleanupPlan.from_json(plan_path.read_text())

    def _validate_execution_result(self, exec_result: ExecutionResult) -> None:
        missing = []
        if not exec_result.spec_id:
            missing.append("spec_id")
        if not exec_result.plan_id:
            missing.append("plan_id")
        if missing:
            raise ValueError(
                f"ExecutionResult missing required fields: {', '.join(missing)}"
            )

    def _build_prompt(
        self, plan: "CleanupPlan", diff: str, exec_result: ExecutionResult
    ) -> str:
        base_instruction = (
            "Summarize these changes, flag risks, and ensure plan constraints are "
            "respected. Provide advisory notes only. Do NOT propose or apply code "
            "modifications or new tasks."
        )
        diff_text = diff if diff.strip() else "(no code changes provided)"
        constraints = plan.constraints or []
        constraints_text = "; ".join(constraints) if constraints else "none"
        target_file = plan.metadata.get("target_file") if plan.metadata else None
        stdout_snippet = self._truncate(exec_result.stdout)
        stderr_snippet = self._truncate(exec_result.stderr)
        tests_status = (
            "unknown" if exec_result.tests_passed is None else exec_result.tests_passed
        )
        return "\n".join(
            [
                f"[mode={self._config.mode}] Codex review request",
                base_instruction,
                "",
                "Plan:",
                f"- id: {plan.id}",
                f"- intent: {plan.intent}",
                f"- target_file: {target_file or '<unknown>'}",
                f"- constraints: {constraints_text}",
                "",
                "Diff:",
                diff_text,
                "",
                "Execution Result:",
                f"- success: {exec_result.success}",
                f"- tests_passed: {tests_status}",
                f"- stdout: {stdout_snippet}",
                f"- stderr: {stderr_snippet}",
                "",
                "Respond with summary, risk_grade (low|medium|high), "
                "manual_checks (list), and optional constraints notes.",
            ]
        )

    def _assert_advisory_only(self, output: str) -> None:
        prohibited = ("```", "diff --git", "apply_patch", "+++ ", "--- ")
        if any(marker in output for marker in prohibited):
            raise ValueError(
                "Review output must be advisory-only without code patches."
            )

    def _normalize_review_output(
        self, output: str
    ) -> tuple[dict[str, object], dict[str, object]]:
        metadata: dict[str, object] = {}
        try:
            loaded = json.loads(output)
            if isinstance(loaded, dict):
                return self._ensure_review_keys(loaded), {"parsed": "json"}
        except Exception:
            pass

        metadata["unparsed_review"] = True
        return (
            {
                "summary": output.strip(),
                "risk_grade": "unknown",
                "manual_checks": [],
            },
            metadata,
        )

    def _ensure_review_keys(self, payload: dict[str, object]) -> dict[str, object]:
        manual_checks = payload.get("manual_checks")
        if not isinstance(manual_checks, list):
            manual_checks = []
        summary = str(payload.get("summary", "")).strip()
        if not summary:
            summary = json.dumps(payload)
        review: dict[str, object] = {
            "summary": summary,
            "risk_grade": str(payload.get("risk_grade", "unknown")).strip()
            or "unknown",
            "manual_checks": manual_checks,
        }
        if "constraints" in payload:
            review["constraints"] = payload["constraints"]
        return review

    def _truncate(self, text: str, limit: int = 800) -> str:
        if len(text) <= limit:
            return text
        return text[: limit - 3] + "..."


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
    exec_type = (config.executor.type or "").strip().lower()
    if exec_type != "codex_shell":
        raise ValueError(
            f"Unsupported executor type: {exec_type or '<empty>'}. "
            "Supported executors: codex_shell"
        )
    executor = _CodexShellExecutor(config.executor, config.tests)
    return ExecutorHandle(executor=executor, results_dir=config.executor.results_dir)


def get_review_executor(config: AiCleanConfig) -> ReviewExecutorHandle:
    review_type = (config.review.type or "").strip().lower()
    if review_type != "codex_review":
        raise ValueError(
            f"Unsupported review executor type: {review_type or '<empty>'}. "
            "Supported review executors: codex_review"
        )
    reviewer = _CodexReviewExecutor(
        config.review, config.metadata_root, get_codex_prompt_runner(config)
    )
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
