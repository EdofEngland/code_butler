## ADDED Requirements
### Requirement: Phase 8.4 Test-First Execution Policy
- Phase 8.4 Test-First Execution Policy deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Apply surfaces test status
- **GIVEN** a plan is applied via /apply
- **WHEN** tests run or are skipped due to apply failure
- **THEN** ExecutionResult and CLI output clearly show whether tests ran and passed, with errors surfaced
