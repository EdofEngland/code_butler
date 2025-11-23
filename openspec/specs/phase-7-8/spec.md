# phase-7-8 Specification

## Purpose
TBD - created by archiving change phase-7-8. Update Purpose after archive.
## Requirements
### Requirement: Phase 7.8 – `/changes-review` Command
The ai-clean project MUST provide an `ai-clean changes-review PLAN_ID` command that performs a read-only, Codex-powered review of a completed plan’s changes and surfaces a deterministic summary to the user.

#### Scenario: Phase 7.8 complete
- **GIVEN** the team is executing 7 – CLI Commands
- **WHEN** Phase 7.8 (`/changes-review` Command) is completed
- **THEN** the repository provides `ai-clean changes-review PLAN_ID`
- **AND** the command performs a review-only, read-only inspection of artifacts for that `PLAN_ID`
- **AND** the work remains within ButlerSpec guardrails (one-plan-per-file, specs on disk, Codex executor).

### Requirement: PLAN_ID-scoped artifact loading
The `/changes-review` command SHALL load only the artifacts associated with the specified `PLAN_ID` and MUST NOT modify them.

#### Scenario: PLAN_ID artifact resolution
- **WHEN** the user runs `ai-clean changes-review PLAN_ID`
- **THEN** the system resolves `PLAN_ID` to:
- **AND** loads, in a read-only way:
  - the `CleanupPlan`
  - the associated `ButlerSpec`
  - the `ExecutionResult` (apply + tests)
  - the `git diff` for the plan’s changes
- **AND** does not load or alter artifacts for any other plans.

#### Scenario: Unknown PLAN_ID
- **WHEN** the user runs `ai-clean changes-review` with a `PLAN_ID` that cannot be resolved
- **THEN** the command fails fast with a clear, deterministic error message
- **AND** the system does not invoke Codex or attempt to infer artifacts.

### Requirement: Review-only Codex behavior
The ReviewExecutor integration SHALL be strictly review-only and MUST NOT suggest or apply code changes.

#### Scenario: Advisory review output
- **WHEN** `/changes-review` invokes Codex with artifacts for a completed plan
- **THEN** Codex returns an advisory description of the changes, risks, and constraint adherence
- **AND** uses language like “Consider checking…” rather than imperative change instructions
- **AND** does not propose patches, refactors, or new implementation tasks.

#### Scenario: Out-of-scope suggestions
- **WHEN** Codex attempts to suggest edits, patches, or new tasks
- **THEN** the CLI either omits or clearly downscopes those suggestions in the final output
- **AND** no automated edits, applies, or test runs are triggered.

### Requirement: Structured review output
The `/changes-review` command SHALL render review output in a deterministic, user-friendly structure.

#### Scenario: Structured sections
- **WHEN** a review is successfully produced
- **THEN** the CLI output is organized into four sections in this order:
  - `Summary of Changes`
  - `Risk Assessment`
  - `Manual QA Suggestions`
  - `Constraint Validation Notes` (optional when constraints are implicit)
- **AND** each section is clearly labeled and concise.

#### Scenario: Deterministic formatting
- **WHEN** the same `PLAN_ID` and artifacts are reviewed multiple times
- **THEN** the section ordering and labels remain stable
- **AND** the command does not include timestamps, environment-specific paths, or other non-deterministic details in the output.

### Requirement: Handling missing or partial artifacts
The `/changes-review` command SHALL handle missing or partial artifacts explicitly and stay within review-only scope.

#### Scenario: Missing CleanupPlan
- **WHEN** there is no `CleanupPlan` for the specified `PLAN_ID`
- **THEN** the command fails fast with a clear error stating that the plan could not be found
- **AND** Codex is not invoked.

#### Scenario: Missing ExecutionResult
- **WHEN** a `CleanupPlan` and diff exist for `PLAN_ID` but there is no `ExecutionResult`
- **THEN** the command may still run a review that clearly calls out the missing apply/test results
- **AND** the output avoids overstating confidence about runtime behavior or test coverage.

#### Scenario: Missing diff
- **WHEN** a `CleanupPlan` exists but no `git diff` can be found for the plan’s changes
- **THEN** the command reports that no diff is available
- **AND** either:
  - omits the Codex review entirely, or
  - runs a limited review that clearly marks the missing diff and reduced visibility.
