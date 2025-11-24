## Why
ai-clean can only write specs and a placeholder ExecutionResult; there is no way to ingest Codex run output, so plans remain “manual_execution_required” and re-runs reapply the same spec blindly.

## What Changes
- Add an `ai-clean ingest` CLI command that reads a Codex artifact (diff/stdout/stderr/tests) and updates the saved ExecutionResult for a plan, clearing `manual_execution_required`.
- Enforce strict schema/guardrails: unified diff only, single target file, required tests block, optional plan_id/spec_path cross-check, and reject invalid/missing fields.
- Surface status after ingest (diff stats, tests status) and persist back to `.ai-clean/results/<plan>.json`; error out on invalid artifacts.
- Document the workflow: run slash command in Codex, save output to file, run `ai-clean ingest ...`; note test tooling expectations.

## Impact
- Affected specs: ingest-codex-results
- Affected code: `ai_clean/cli.py`, new ingest command module, results helpers, docs (`docs/executor_manual.md`, README)
