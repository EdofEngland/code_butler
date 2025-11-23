## 1. Wire executor factory to concrete CodexShellExecutor

- [x] 1.1 Replace `_CodexShellExecutor` placeholder in `ai_clean/factories.py` with the Phase 5.1/5.2 implementation and expose it from `get_executor`.
- [x] 1.2 Update `get_executor(config: AiCleanConfig)` to map `executor.type == "codex_shell"` to the concrete CodexShellExecutor; include a defensive error message listing supported types when unknown.
- [x] 1.3 Ensure the returned `ExecutorHandle` carries `results_dir` from config and no longer instantiates unused executors.

## 2. Wire review executor factory to concrete CodexReviewExecutor

- [x] 2.1 Replace `_CodexReviewExecutor` placeholder with the Phase 5.3 implementation and expose it from `get_review_executor`.
- [x] 2.2 Update `get_review_executor(config: AiCleanConfig)` to map `review.type == "codex_review"` to the concrete review executor; emit a clear error with supported types when type is unsupported.
- [x] 2.3 Pass `metadata_root` (and any required prompt runner wiring) into the review executor so it can load plans/diffs deterministically.

## 3. Tests for factory routing

- [x] 3.1 Add unit tests in `tests/test_factories.py` ensuring `get_executor` returns CodexShellExecutor for `executor.type="codex_shell"` and raises for unknown types.
- [x] 3.2 Add unit tests ensuring `get_review_executor` returns CodexReviewExecutor for `review.type="codex_review"` and raises for unknown types.
- [x] 3.3 Verify factories propagate config values (results_dir, metadata_root) onto the returned handles to keep downstream code deterministic.
