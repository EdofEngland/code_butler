## Why
Slash commands run inside Codex; `ai_clean` cannot invoke them directly. Once apply stops calling `codex apply`, we need a clear handoff: ai-clean generates a ButlerSpec, and the user runs a Codex slash command (e.g., `/butler-exec <spec>`) from within Codex. We need to document the invocation contract and how outputs map back into `ai_clean` results if we capture them.

## What Changes
- Define the handoff: after spec generation, ai-clean instructs the user to run a Codex slash command with the spec path.
- Document expected inputs/outputs (diff, stdout/stderr, tests metadata) and the schema for storing them in `.ai-clean/results/` when provided. If the user does not run Codex, record “not executed.”
- Add guardrails: single spec per invocation, no auto-exec, no multi-spec batching, fail fast if validations fail.
- Keep planners/spec generation untouched; this is a user-facing invocation/IO contract change, not an automatic call from ai-clean.

## Impact
- Affects apply UX and documentation in `ai_clean`; execution is manual via Codex CLI.
- Must align with the slash-command prompt so both sides agree on inputs/outputs and constraints.

## Handoff contract
- After `apply` writes the ButlerSpec to `.ai-clean/specs/<PLAN_ID>-spec.butler.yaml`, ai-clean stops and prints the slash command to run inside Codex CLI: `codex /butler-exec <SPEC_PATH>`. The path should be absolute; a repo-root-relative path is acceptable if the user prefers it.
- Working directory: paths are printed as absolute so the command is insensitive to the current directory. If a relative path is used instead, the user should run it from the repository root that contains `.ai-clean/`.
- Non-goals: ai-clean never auto-invokes Codex, does not batch multiple specs, and only ever hands off a single spec per apply.
- ExecutionResult stays "not executed" until Codex runs. If we later ingest user-provided output, expect `diff` (text), `stdout`, `stderr`, and `tests` with `status/command/exit_code/stdout/stderr`; when skipped, these fields remain empty and `manual_execution_required` stays true.

## Scenarios (acceptance)
- Success: Spec is valid; ai-clean prints `/butler-exec <spec>` instructions; user runs it in Codex; diff/stdout/stderr/tests metadata can be captured and stored.
- Not executed: User does not run Codex; ai-clean records “not executed” with no diff/tests.
- Validation failure: Spec invalid or plan limits violated; ai-clean refuses to suggest Codex run.
- Codex refusal/error: User runs the command but Codex returns an error; ai-clean can store failure metadata if provided.
- Tests failed: Codex reports test failures; record tests metadata accordingly.
