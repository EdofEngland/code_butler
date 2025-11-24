## 1. Implementation
- [x] 1.1 Slash command template
  - [x] 1.1.1 Create `.codex/commands/cleanup-advanced.md` defining the slash command name, expected arguments (findings/snippets payload path), and JSON response format.
  - [x] 1.1.2 Include guardrails: bounded suggestions, no edits, respect limits (max files/snippets/suggestions).
- [x] 1.2 Output contract
  - [x] 1.2.1 Require JSON array of suggestions with fields: `description`, `path`, `start_line`, `end_line`, `change_type`, `model`, `prompt_hash`.
  - [x] 1.2.2 On rejection/invalid input, return `Error: <reason>` with no JSON payload.
- [x] 1.3 Docs/UX
  - [x] 1.3.1 Add usage docs showing how to run `codex /cleanup-advanced <PAYLOAD_PATH>` from Codex CLI and where to place the payload.
  - [x] 1.3.2 Note environment assumptions (run from repo root or use absolute paths; Codex CLI handles auth).

## 2. Validation
- [x] 2.1 Prompt sanity check
  - [x] 2.1.1 Dry-run the prompt with a sample payload to verify JSON-only output and guardrail enforcement (documentation-level; Codex not executed here).
- [x] 2.2 Integration notes
  - [x] 2.2.1 Ensure docs describe how ai-clean will surface the slash command and ingest results (manual step).
