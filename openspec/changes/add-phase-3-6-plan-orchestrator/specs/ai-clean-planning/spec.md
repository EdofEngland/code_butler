## ADDED Requirements
### Requirement: Phase 3.6 Planning Orchestrator
- Phase 3.6 Planning Orchestrator deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Orchestrator generates and stores plans
- **GIVEN** a finding and configured storage directory
- **WHEN** plan_from_finding is invoked
- **THEN** it produces a CleanupPlan with a unique ID and saves it under .ai-clean/plans
