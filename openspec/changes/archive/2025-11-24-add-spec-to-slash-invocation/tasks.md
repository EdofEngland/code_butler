## 1. Implementation
- [x] 1.1 Define the handoff contract
  - [x] 1.1.1 Add a short section to `openspec/changes/add-spec-to-slash-invocation/proposal.md` describing the user action (`codex /butler-exec <spec_path>` inside Codex) and that ai-clean stops after writing the spec.
  - [x] 1.1.2 State working directory assumptions and how to find the spec path from `.ai-clean/specs/` (absolute path preferred; relative from repo root is acceptable).
  - [x] 1.1.3 Document assumptions/non-goals: ai-clean never auto-invokes Codex; no multi-spec batching.
- [x] 1.2 Adjust ai-clean apply UX
  - [x] 1.2.1 In `ai_clean/commands/apply.py`, ensure apply prints the exact slash command string with the resolved spec path.
  - [x] 1.2.2 If manual result capture is supported later, sketch (in proposal/tasks) how users would paste diff/output back; otherwise, set ExecutionResult to “not executed.”
- [x] 1.3 Keep ExecutionResult consistent
  - [x] 1.3.1 Ensure `ExecutionResult` written by apply keeps `spec_id`/`plan_id` and sets `success=False`, `tests_passed=None`, `metadata.manual_execution_required=True`.
  - [x] 1.3.2 Define and document the expected schema if user-provided results are ingested: `diff` (text), `stdout`, `stderr`, `tests` (status/command/exit_code/stdout/stderr); when not executed, these should be absent or clearly marked.
- [x] 1.4 Guardrails before handoff
  - [x] 1.4.1 Reuse ButlerSpec validations (single target, <=25 actions) and plan limits before printing the Codex command; fail early with a clear error message.
  - [x] 1.4.2 Do not print/suggest Codex execution if validations fail; surface the validation error instead.

## 2. Validation
- [x] 2.1 CLI behavior
  - [x] 2.1.1 Add a smoke test/manual check that `ai_clean apply <PLAN_ID>` writes the spec and prints the Codex slash command instead of calling Codex.
  - [x] 2.1.2 Verify ExecutionResult reflects "not executed" with appropriate notes and empty diff/tests fields.
- [x] 2.2 Docs/examples
  - [x] 2.2.1 Update docs to show the handoff flow and example command (`codex /butler-exec <spec_path>`).
  - [x] 2.2.2 Note environment/working-directory considerations for the user when running the slash command (absolute vs relative paths, from repo root).
