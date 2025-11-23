## 1. Implement CodexShellExecutor.apply_spec (ai_clean/factories.py)

- [x] 1.1 Replace `_CodexShellExecutor.apply_spec` stub with real logic that accepts a single `spec_path: Path` (reject lists/globs) and resolves it to an absolute path.
- [x] 1.2 Build the command array using `config.executor.binary` + `config.executor.apply_args` + `[str(spec_path)]`, then wrap it in `bash -lc 'codex apply "<abs_path>"'` style for determinism; set `cwd=spec_path.parent`.
- [x] 1.3 Run `subprocess.run(..., capture_output=True, text=True)`; surface `FileNotFoundError` for missing binary and timeouts as structured errors without mutating the spec file.
- [x] 1.4 Parse the spec YAML to extract `id`/`plan_id` (fallback to filename for `spec_id`); raise a descriptive error if missing.
- [x] 1.5 Return `ExecutionResult` with `spec_id`, `plan_id`, `success = (exit_code == 0)`, `stdout`, `stderr`, `tests_passed=None`, `git_diff=None`, and include raw `exit_code` in metadata for debugging.

## 2. Guardrails and read-only guarantees

- [x] 2.1 Before/after execution, verify the spec file content is unchanged (e.g., checksum) to enforce read-only behavior.
- [x] 2.2 Reject multi-spec execution: fail if the caller passes directories, patterns, or non-file paths.
- [x] 2.3 Document the deterministic command shape and prohibited extras (no env injection, no chained commands) in inline comments or docstring.

## 3. Smoke tests for command and mapping

- [x] 3.1 Add a unit test (e.g., in `tests/test_factories.py`) that monkeypatches `subprocess.run` to assert the constructed command includes the configured binary/apply_args and quoted spec path.
- [x] 3.2 Add a unit test that feeds mocked stdout/stderr/exit_code and asserts `ExecutionResult` fields (`spec_id`, `plan_id`, `success`, `tests_passed=None`, `git_diff=None`) are mapped verbatim.
