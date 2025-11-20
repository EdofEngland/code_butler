# ai-clean-execution Specification

## Purpose
TBD - created by archiving change add-phase-5-1-codex-executor-apply. Update Purpose after archive.
## Requirements
### Requirement: Phase 5.1 Code Executor Applies Spec
The executor MUST call `/prompts:openspec-apply {spec_path}` when running inside Codex and MUST explain how contributors can override the command or enable the stub when `/prompts:openspec-apply` is unavailable locally.

#### Scenario: Codex runs use prompts apply command
- **GIVEN** `ai-clean apply` runs inside the Codex CLI
- **WHEN** the executor invokes the apply command
- **THEN** it shells out to `/prompts:openspec-apply {spec_path}` so the OpenSpec change file produced by ai-clean is applied

#### Scenario: Local runs document override path
- **GIVEN** a contributor runs ai-clean outside Codex
- **WHEN** `/prompts:openspec-apply` is unavailable
- **THEN** the documentation explains how to set `AI_CLEAN_APPLY_COMMAND` or `AI_CLEAN_USE_APPLY_STUB=1` so the pipeline still runs end-to-end

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
