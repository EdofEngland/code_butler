## 1. Implementation
- [x] 1.1 Document existing executor flow and failure
  - [x] 1.1.1 Add a brief design note describing how `apply_plan` (`ai_clean/commands/apply.py`) calls `get_executor` and `_CodexShellExecutor` runs `codex apply <spec>`.
  - [x] 1.1.2 Note the failure: Codex CLI expects task IDs, so spec paths return 404; slash commands cannot be invoked this way.
- [x] 1.2 Disable broken executor path and halt at spec generation
  - [x] 1.2.1 In `ai_clean/factories.py`, gate or remove `codex_shell` as the default executor; make execution optional/disabled unless a supported executor is configured.
  - [x] 1.2.2 In `ai_clean/commands/apply.py`, after writing the ButlerSpec, short-circuit execution when no supported executor is configured; emit a clear message that execution must be done via Codex CLI slash command.
  - [x] 1.2.3 Ensure results handling records an appropriate failure/skip state without attempting Codex calls.
- [x] 1.3 Adjust executor configuration schema
  - [x] 1.3.1 Update `ai_clean/config.py` to allow a “no executor” or “manual execution” mode; validate and surface errors if an unsupported executor type is set.
  - [x] 1.3.2 Update `ai-clean.toml` example to reflect that execution is manual via Codex CLI slash command; remove misleading `codex apply` guidance.
- [x] 1.4 Update docs/changelog
  - [x] 1.4.1 Add README/usage notes describing the new flow: ai-clean generates specs; users run a Codex slash command inside Codex CLI to execute.
  - [x] 1.4.2 Note deprecation/removal of the old `codex apply <spec>` path and why it fails (task IDs only).

## 2. Validation
- [x] 2.1 CLI behavior without executor
  - [x] 2.1.1 Add a smoke test or manual check that `ai_clean apply <PLAN_ID>` writes the spec and exits with a clear message when no supported executor is configured.
  - [x] 2.1.2 Verify the ExecutionResult (if recorded) reflects “not executed” rather than an unclear 404 apply failure.
- [x] 2.2 Config validation
  - [x] 2.2.1 Ensure setting the old `codex_shell` type produces a validation error or explicit warning.
  - [x] 2.2.2 Confirm documentation and examples no longer instruct users to run `codex apply <spec>`.
