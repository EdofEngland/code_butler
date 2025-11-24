## Why
`ai_clean` currently shells out to `codex apply <spec>` via the `codex_shell` executor, but the Codex CLI only accepts task IDs. Passing ButlerSpec files returns 404, so apply/review paths can never succeed. Codex slash commands run inside an active Codex session; they are not invokable by `ai_clean` directly.

## What Changes
- Remove the `codex_shell` executor path and stop calling Codex from `ai_clean`.
- Adjust `ai_clean` apply flow to stop at spec generation; instruct users to execute specs manually via a Codex slash command inside the Codex CLI.
- Document the migration path away from the broken executor and the new manual execution flow.

## Impact
- Affects executor config and apply/review wiring in `ai_clean` (execution disabled/delegated).
- No ButlerSpec or planner changes; execution is external/manual via Codex.
