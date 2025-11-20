## 1. Executor Backend Abstraction
- [x] 1.1 Create `ai_clean/executors/backends.py` containing the shared backend contract.
  - [x] 1.1.1 Define `@dataclass class BackendApplyResult` with exact fields: `status: Literal["manual","automatic"]`, `instructions: str`, `metadata: Dict[str, Any]`, and `tests_supported: bool`; default `metadata` to `{}` and `tests_supported` to `False`.
  - [x] 1.1.2 Declare `ExecutorBackend` as a `Protocol` with two methods: `plan(self, plan_id: str) -> None | Dict[str, Any]` (default implementations can return `None`) and `apply(self, change_id: str, spec_path: str) -> BackendApplyResult`.
  - [x] 1.1.3 Export `BackendApplyResult` and `ExecutorBackend` via `__all__` and add module-level docstring describing manual vs automatic semantics so future backends stay consistent.
- [x] 1.2 Add `ai_clean/executors/codex_backend.py` implementing a manual backend.
  - [x] 1.2.1 Define a `CodexExecutorBackend` class that accepts `command_prefix: str = "/openspec-apply"` and `prompt_hint: str | None = "/prompts:openspec-apply"` at init; store them as private attributes.
  - [x] 1.2.2 Implement `apply` to build the instruction string `f"In Codex, run `{prefix} {change_id}`."` and include an alternate `/prompts:` version when `prompt_hint` is set, then return `BackendApplyResult(status="manual", instructions=..., metadata={"backend": "codex", "command_prefix": prefix}, tests_supported=False)`.
  - [x] 1.2.3 Stub `plan` to return `None` for now so callers can check for optional backend planning later.

## 2. Wire Backend Into ai-clean CLI
- [x] 2.1 Extend configuration to select a backend and customize Codex strings.
  - [x] 2.1.1 In `ai_clean/config.py`, introduce a new `ExecutorBackendConfig` dataclass with fields `type: str`, `command_prefix: str`, and `prompt_hint: str`.
  - [x] 2.1.2 Parse a new `[executor_backend]` section in `load_config`, defaulting empty config to `{"type": "codex", "command_prefix": "/openspec-apply", "prompt_hint": "/prompts:openspec-apply"}`; allow overrides via env vars `AI_CLEAN_EXECUTOR_BACKEND`, `AI_CLEAN_EXECUTOR_COMMAND_PREFIX`, and `AI_CLEAN_EXECUTOR_PROMPT_HINT`.
  - [x] 2.1.3 Add validation so unsupported backend types raise `ValueError` and ensure the command prefix is non-empty.
- [x] 2.2 Teach the factory how to build backend instances.
  - [x] 2.2.1 Update `ai_clean/executors/factory.py` to expose `build_executor_backend(config: AiCleanConfig) -> ExecutorBackend`, mapping `"codex"` to the new `CodexExecutorBackend` and leaving a placeholder dict for future types.
  - [x] 2.2.2 Keep the existing `build_code_executor` logic untouched but gate CLI usage so only automatic backends call it.
  - [x] 2.2.3 Add unit-test-style docstring or TODO referencing `tests/test_executors_factory.py` (create if missing) to verify backend selection errors.
- [x] 2.3 Update `_run_apply_flow` in `ai_clean/cli.py` to use the backend result.
  - [x] 2.3.1 After writing the spec file, call `build_executor_backend(config)` and `backend.apply(plan.id, spec_path)`; print `Backend instructions: {result.instructions}` immediately so Codex users can copy it.
  - [x] 2.3.2 If `result.status == "manual"`, skip `build_code_executor`, create a synthetic `ExecutionResult` (spec_id from spec file, `success=True`, `tests_passed=None`, stdout containing the instruction, stderr empty, metadata merging backend info), and continue to diff summary so apply still reports git status.
  - [x] 2.3.3 If `result.status == "automatic"`, continue with the existing executor flow, but add `result.metadata["backend"] = backend_result.metadata` and rely on `result.tests_passed` for CLI messaging.
  - [x] 2.3.4 Ensure `save_execution_result` receives the updated metadata for both paths and that `tests_label` logic treats `tests_supported=False` as “tests not run (manual backend)”.

## 3. Codex Helper Command/Prompt
- [x] 3.1 Document the Codex workflow.
  - [x] 3.1.1 Add `library_docs/codex-backend.md` describing (a) running `ai-clean apply PLAN_ID`, (b) copying the backend instruction `/openspec-apply <change-id>`, and (c) optional `/prompts:openspec-apply` usage; include the env vars from task 2.1 as a reference table.
- [x] 3.2 Provide a slash-command example.
  - [x] 3.2.1 Create `library_docs/codex-slash-command-example.yaml` (or `.md`) showing a sample `/code-butler-apply` definition that runs ai-clean, detects the emitted `change-id`, and invokes `/openspec-apply CHANGE_ID`; mention which placeholders to edit before use.
