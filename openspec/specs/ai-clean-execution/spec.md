# ai-clean-execution Specification

## Purpose
TBD - created by archiving change add-phase-5-1-codex-executor-apply. Update Purpose after archive.
## Requirements
### Requirement: Phase 5.1 Code Executor Applies Spec
- Phase 5.1 CodexExecutor: Apply Spec deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Executor applies spec and captures output
- **GIVEN** a valid spec file path
- **WHEN** the executor runs the apply command
- **THEN** ExecutionResult records success from the exit code along with stdout and stderr logs

### Requirement: Phase 5.2 Executor Runs Tests
- Phase 5.2 CodexExecutor: Run Tests After Apply deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Tests run after successful apply
- **GIVEN** apply_spec completes successfully
- **WHEN** the executor runs configured tests
- **THEN** ExecutionResult updates tests_passed according to test exit code and appends test logs

### Requirement: Phase 5.3 Review Executor
- Phase 5.3 ReviewExecutor: Changes Review deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Review executor summarizes change
- **GIVEN** a plan id, associated diff, and execution result
- **WHEN** the review executor runs
- **THEN** it returns a review summary with what changed, risks, and manual check suggestions without modifying files

### Requirement: Phase 5.4 Executor Factories
- Phase 5.4 Executor Factories deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Factories return configured executors
- **GIVEN** ai-clean.toml defines executor and review types
- **WHEN** the factories are invoked
- **THEN** they return the configured implementations or raise clear errors for unsupported values

### Requirement: Phase 8.4 Test-First Policy
- Phase 8.4 Test-First Policy deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: CLI surfaces apply/test outcomes
- **GIVEN** `/apply` runs for a plan
- **WHEN** code execution completes
- **THEN** the CLI prints whether tests ran and passed, stores the execution result path, and `/changes-review` echoes the stored test status before running the reviewer
