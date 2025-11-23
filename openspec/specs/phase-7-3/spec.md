# phase-7-3 Specification

## Purpose
TBD - created by archiving change phase-7-3. Update Purpose after archive.
## Requirements
### Requirement: Phase 7.3 – `/apply` Command
The ai-clean project MUST provide a deterministic `ai-clean apply PLAN_ID` command that runs a single plan end-to-end: enforce refactor-branch safety, load the plan, materialize a ButlerSpec, apply via CodexShellExecutor, run tests, and print an ASCII-safe summary (apply status, tests status, git diff --stat).

#### Scenario: Successful apply with passing tests
- **GIVEN** a valid PLAN_ID and the refactor branch can be prepared
- **WHEN** the user runs `ai-clean apply PLAN_ID`
- **THEN** the command loads config, switches/creates the refactor branch, loads the plan, writes a ButlerSpec under `.ai-clean/specs/{spec_id}.butler.yaml`, applies it once, runs tests, and exits zero
- **AND** prints a summary including the spec path, apply success, tests_passed=True, and git diff --stat output in deterministic order.

#### Scenario: Apply failure (tests skipped)
- **WHEN** CodexShellExecutor returns success=False or non-zero exit
- **THEN** the command skips tests, exits non-zero, surfaces executor stdout/stderr, and prints apply failure + tests skipped + git diff stat (if available)
- **AND** no retries or batch attempts occur.

#### Scenario: Apply succeeds but tests fail
- **WHEN** the apply step succeeds and tests return non-zero
- **THEN** the command exits non-zero, reports apply success, tests_passed=False, includes test stderr/stdout snippets, and prints git diff stat.

#### Scenario: Git helper failure
- **WHEN** ensuring the refactor branch or computing git diff stat fails
- **THEN** the command exits non-zero with a concise git error message and does not proceed to subsequent steps that depend on the failure.

#### Scenario: Invalid inputs rejected
- **WHEN** PLAN_ID is missing, extra arguments are provided, or the plan file is absent
- **THEN** the command exits non-zero with a clear error and does not write specs or invoke the executor
- **AND** it reiterates single-plan-per-run guardrails.
