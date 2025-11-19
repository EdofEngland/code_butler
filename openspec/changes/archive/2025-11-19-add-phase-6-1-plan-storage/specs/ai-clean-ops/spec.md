## ADDED Requirements
### Requirement: Phase 6.1 Plan Storage
- Phase 6.1 Plan Storage Helpers deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Plans round-trip via storage
- **GIVEN** a CleanupPlan with populated fields
- **WHEN** it is saved and then loaded from .ai-clean/plans
- **THEN** the reloaded plan matches the original fields required by executors
