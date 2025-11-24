# add-spec-to-slash-invocation Specification

## Purpose
TBD - created by archiving change add-spec-to-slash-invocation. Update Purpose after archive.
## Requirements
### Requirement: Manual Slash Invocation Handoff
The system SHALL generate a ButlerSpec, stop before execution, and instruct the user to run the Codex `/butler-exec` slash command with the resolved spec path.

#### Scenario: Valid plan yields slash command and saved ExecutionResult
- **WHEN** `ai-clean apply <PLAN_ID>` is run with a plan that passes plan limits and ButlerSpec guardrails (single target file, ≤25 actions, valid metadata)
- **THEN** it writes `.ai-clean/specs/<PLAN_ID>-spec.butler.yaml` and prints a Codex command `codex /butler-exec <ABSOLUTE_SPEC_PATH>` using the resolved absolute path
- **AND** it saves an `ExecutionResult` under `.ai-clean/results/<PLAN_ID>.json` with `spec_id` derived from the spec file, `plan_id`, `success=False`, `tests_passed=None`, `git_diff=None`
- **AND** `ExecutionResult.metadata.manual_execution_required` is `True`, `metadata.slash_command` stores the printed command, and `metadata.tests.status="not_run"` with reason `manual_execution_required`
- **AND** no code execution occurs (stdout only contains instructions; stderr is empty).

#### Scenario: Validation failure blocks handoff
- **WHEN** the plan exceeds configured plan limits or ButlerSpec validation fails (multiple targets, >25 actions, invalid metadata)
- **THEN** `ai-clean apply` aborts with an error and does NOT print a slash command, write a spec, or save an `ExecutionResult`.

#### Scenario: Tests omitted until manual run
- **WHEN** a valid plan is applied but tests are not executed (manual flow)
- **THEN** the saved `ExecutionResult` leaves `tests_passed=None` and records tests metadata as `status=not_run` with `reason=manual_execution_required`, without stdout/stderr for tests.
