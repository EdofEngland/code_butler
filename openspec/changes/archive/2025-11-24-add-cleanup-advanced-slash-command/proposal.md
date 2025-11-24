## Why
Advanced cleanup needs a Codex slash command since ai-clean cannot call Codex directly. We need a deterministic, guarded `/cleanup-advanced` command that takes findings/snippets and returns JSON suggestions.

## What Changes
- Author a Codex slash command template under `.codex/commands/cleanup-advanced.md`.
- Define inputs (findings/snippets payload), guardrails (scope, limits, no edits), and required JSON output shape.
- Document the manual invocation flow and how ai-clean can surface the command and ingest results.

## Impact
- Enables advanced analyzer via manual Codex invocation.
- No automatic execution from ai-clean; users run the slash command inside Codex CLI.
