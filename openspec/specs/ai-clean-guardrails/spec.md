# ai-clean-guardrails Specification

## Purpose
TBD - created by archiving change add-phase-8-1-change-size-limits. Update Purpose after archive.
## Requirements
### Requirement: Phase 8.1 Change Size Limits
- Phase 8.1 Change Size Limits deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Plans respect configured size limits
- **GIVEN** size limits are set in configuration
- **WHEN** a finding would produce a plan exceeding file or line limits
- **THEN** the planner splits or rejects the plan so that each resulting plan stays within limits

### Requirement: Phase 8.2 Single Concern Plans
- Phase 8.2 Single Concern per Plan deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Planner enforces single concern
- **GIVEN** a planner attempts to bundle multiple concerns
- **WHEN** single-concern guardrails are applied
- **THEN** the planner splits the work so each plan addresses only one concern

### Requirement: Phase 8.3 No Global Renames or API Overhauls
- Phase 8.3 No Global Renames or API Overhauls in V0 deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Global rename suggestions are blocked
- **GIVEN** a planner or advanced analyzer encounters a suggestion to rename public APIs broadly
- **WHEN** guardrails are evaluated
- **THEN** the suggestion is downgraded or rejected in v0 with clear constraints noted

### Requirement: Phase 8.4 Test-First Execution Policy
- Phase 8.4 Test-First Execution Policy deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Apply surfaces test status
- **GIVEN** a plan is applied via /apply
- **WHEN** tests run or are skipped due to apply failure
- **THEN** ExecutionResult and CLI output clearly show whether tests ran and passed, with errors surfaced
