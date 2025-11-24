## Why
Codex needs a custom slash command that can read a ButlerSpec file and perform only the described edits. Without it, `codex apply` cannot execute specs (expects task IDs), and ai-clean apply/review remain broken.

## What Changes
- Author a `/butler-exec` (or similar) slash command definition under `.codex/commands/` that:
  - Accepts a ButlerSpec file path.
  - Summarizes intent/actions.
  - Applies only those changes to the specified target file.
  - Emits a unified diff (no replanning) and respects guardrails.
- Define guardrails in the prompt: single target file, <=25 actions, no signature changes, no renames/structural redesigns, no edits outside action ranges, reject invalid/over-broad specs.
- Specify expected outputs: diff text; minimal summary; optional tests block (status/command/exit_code/stdout/stderr) when tests are run; explicit failure message when rejecting a spec.

## Impact
- Adds a Codex-facing command template; no planner/spec changes.
- Must align with the new invocation contract so inputs/outputs match ai-clean expectations (manual Codex run; ai-clean may later parse diff/tests).

## Assumptions / Non-goals
- ai-clean does not auto-run the slash command; execution is manual in Codex.
- Only one spec path per invocation; no batching.
- No API/surface changes, renames, or signature changes unless explicitly present in the ButlerSpec.
