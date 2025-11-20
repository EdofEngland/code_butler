## Why
Codex is the primary environment for running ai-clean today, so the apply step needs a lightweight executor that can simply instruct contributors to run `/openspec-apply <change-id>` instead of shelling out to a local CLI. The current executor model assumes every run has an apply command and tests command, which breaks when ai-clean is invoked purely inside Codex prompts. We need an explicit "executor backend" abstraction so Codex is one backend implementation and future local/CI backends can reuse the same orchestration without rewriting planning or spec generation.

## What Changes
- Introduce a minimal executor-backend protocol plus data model that captures plan metadata, optional plan summaries, and the instructions returned to the CLI.
- Implement a Codex backend that simply emits `/openspec-apply <change-id>` (or `/prompts:openspec-apply ...`) guidance and records that the action is manual rather than running shell commands.
- Update the `ai-clean apply` flow to call the backend immediately after the spec is written so Codex users see the backend instructions next to the spec path and execution result metadata.
- Expose a backend selector via config/env so the Codex backend is the default today, while future CLI/CI backends can plug in without refactoring the CLI.
- Provide a helper prompt or slash command definition under version control that chains “run ai-clean/Code Butler” with `/openspec-apply <change-id>` so Codex users can trigger the workflow with one instruction.

## Impact
- Protects the apply pipeline from Codex-specific assumptions while keeping current Codex-only usage working.
- Makes it straightforward to introduce non-Codex executor backends later by implementing the same interface.
- Documents a Codex helper prompt so manual `/openspec-apply` steps are less error-prone today.
