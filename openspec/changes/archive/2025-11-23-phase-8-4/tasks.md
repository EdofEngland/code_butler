## 1. Deliverables

- [x] `/apply` must always:

  - [x] Record whether tests ran.
    - [x] In `ai_clean/factories._CodexShellExecutor.apply_spec`, add a deterministic `tests` block in `ExecutionResult.metadata` including `command`, `status` (`ran|skipped|not_configured|apply_failed|command_not_found|timed_out`), and stdout/stderr snippets when tests ran.
    - [x] Populate `tests_passed` alongside the status: `True` only when tests ran and exited 0; `False` otherwise; `None` only when apply failed before tests.
  - [x] Include test status in:
    - [x] CLI output: update `_print_apply_summary` and `_run_apply_command` in `ai_clean/cli.py` to show test status/reason and test command.
    - [x] Stored `ExecutionResult`: add a `results.save_execution_result(result, results_dir)` helper (e.g., `ai_clean/results.py`) invoked from `ai_clean/commands/apply.apply_plan` using `resolve_metadata_paths(...)[3]`.
    - [x] `/changes-review` output: surface test status/reason in `_print_review_summary`, adding warnings when tests were skipped/failed/missing.

- [x] Error paths:
  - [x] Failed apply → emit explicit diagnostics (nonzero exit, stderr, and a note that tests were skipped due to apply failure) in CLI and stored metadata.
  - [x] Failed tests → emit explicit diagnostics (exit code, stderr excerpt) in CLI, set `tests_passed=False`, and store the failure details in `ExecutionResult.metadata["tests"]`.
  - [x] Add unit/integration tests covering: apply success with tests run; apply success with no test command; apply failure (tests skipped); test failure path; ensure saved `ExecutionResult` JSON contains the test status fields and `/changes-review` prints the status/warnings.
