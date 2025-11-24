## Execution flow: manual Codex invocation

Current behavior:
- `ai_clean/commands/apply.py` loads a plan, validates plan limits/single target/<=25 actions, converts it to ButlerSpec, and writes `.ai-clean/specs/<plan>-spec.butler.yaml`.
- Execution no longer shells out to `codex apply <spec>` because the Codex CLI expects task IDs; passing ButlerSpec files returns 404 and slash commands are not invokable from ai-clean.
- `apply` stops after spec generation, records an `ExecutionResult` with `success=False`, `tests_passed=None`, `metadata.manual_execution_required=True`, and `metadata.tests.status="not_run"`, and prints a Codex slash command instead of running anything.

Slash command:
- ai-clean prints the resolved spec path plus `codex /butler-exec <SPEC_PATH>` so the user can run it from Codex CLI. Paths are emitted as absolute; repo-root-relative paths are fine if the user prefers them, but they should run from the repo root that contains `.ai-clean/` to keep references correct.
- Apply/review is therefore a two-step flow: ai-clean generates the spec; Codex executes it interactively.

ExecutionResult storage:
- Stored under `.ai-clean/results/<plan>.json` with `spec_id`, `plan_id`, `success=False`, `tests_passed=None`, `stdout` containing the instructions, `metadata.manual_execution_required=True`, `metadata.slash_command`, and `metadata.tests.status="not_run"`. No diff/tests output is present until the slash command runs.
- If we later ingest user-provided output, expect `diff` (text), `stdout`, `stderr`, and a `tests` block containing `status`, `command`, `exit_code`, `stdout`, and `stderr`. When the user does not run Codex, leave these fields empty and keep `manual_execution_required` true.

## Ingesting Codex artifacts

- Command: `ai-clean ingest --plan-id <id> --artifact <path> [--root <repo>] [--config <file>] [--update-findings]`.
- Artifact: JSON object with `diff` (unified, single file), `stdout`, `stderr`, and `tests` (`status`, `command`, `exit_code`, `stdout`, `stderr`; optional `reason`). Optional `plan_id/spec_path` for cross-checking and `suggestions` array from `/cleanup-advanced`.
- Validation: rejects missing/extra fields, non-unified or empty diff (unless `tests.status=apply_failed`), unsupported test status, plan_id mismatch, or multi-file diffs. Allowed statuses: `ran`, `failed`, `not_run`, `timed_out`, `command_not_found`, `apply_failed`.
- Effects: updates `.ai-clean/results/<plan>.json`, sets `metadata.manual_execution_required=False`, writes `git_diff/stdout/stderr/metadata.tests`, derives `success/tests_passed`, and prints a summary (diff stat + tests).
- Suggestions: when `--update-findings` is set and the artifact includes a `suggestions` array, valid entries are converted to `Finding` objects (category `advanced_cleanup`) and appended to findings JSON (default `.ai-clean/findings.json`). Invalid suggestions abort ingest.
