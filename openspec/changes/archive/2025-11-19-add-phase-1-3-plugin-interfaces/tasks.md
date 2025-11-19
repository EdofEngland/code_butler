## 1. Implementation
- [x] 1.1 Create an interfaces module for plugins (e.g., `ai_clean/interfaces.py`) that imports only standard library + core models.
- [x] 1.2 Define `SpecBackend` protocol/abstract base with `plan_to_spec(plan: CleanupPlan) -> SpecChange` and `write_spec(spec: SpecChange, directory: str) -> str`.
- [x] 1.3 Define `CodeExecutor` protocol/abstract base with `apply_spec(spec_path: str) -> ExecutionResult`.
- [x] 1.4 Define `ReviewExecutor` protocol/abstract base with `review_change(plan_id: str, diff: str, execution_result: ExecutionResult | None) -> str | dict`.
- [x] 1.5 Add minimal docstring/type comments noting the interfaces avoid tool-specific naming (no “Codex”/“OpenSpec”) and rely only on core models.
