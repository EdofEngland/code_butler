## ADDED Requirements

### Requirement: Phase 5.1 – CodexShellExecutor: Apply Spec with Shell Wrapper
The ai-clean project MUST implement `CodexShellExecutor.apply_spec(spec_path: Path) -> ExecutionResult` so each invocation deterministically calls exactly one Codex apply, captures stdout/stderr/exit code, derives `spec_id`, and returns a read-only ExecutionResult that leaves `tests_passed` and `git_diff` unset until Phase 5.2.

#### Scenario: Deterministic subprocess invocation
- **GIVEN** a single spec file path
- **WHEN** `apply_spec` is invoked
- **THEN** it SHALL run `bash -lc 'codex apply "<absolute_spec_path>"'` with the same working directory every time
- **AND** it SHALL NOT append extra flags, environment changes, or chained commands
- **AND** it SHALL treat `exit_code == 0` as success and capture the full stdout/stderr streams verbatim.

#### Scenario: ExecutionResult mapping and guardrails
- **WHEN** Codex completes (successfully or not)
- **THEN** `ExecutionResult.spec_id` SHALL be derived from the spec filename (falling back to parsed YAML when necessary)
- **AND** `ExecutionResult.success` SHALL equal `exit_code == 0` while preserving the numeric exit code for observability
- **AND** `tests_passed` and `git_diff` SHALL remain unset in this phase with clear documentation that later phases fill them
- **AND** the executor SHALL fail rather than mutating spec files or attempting to batch multiple specs.

#### Scenario: Error propagation
- **GIVEN** Codex exits non-zero, cannot be found, or times out
- **WHEN** `apply_spec` returns
- **THEN** stderr SHALL be forwarded untouched, `success` SHALL be false, and the failure SHALL mention the exit condition without retries or hidden fallbacks
- **AND** the spec file on disk SHALL remain unmodified so downstream orchestration can decide how to react.
