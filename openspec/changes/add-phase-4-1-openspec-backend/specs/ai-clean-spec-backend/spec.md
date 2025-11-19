## ADDED Requirements
### Requirement: Phase 4.1 OpenSpec Backend
- Phase 4.1 OpenSpec Backend: Plan → SpecChange deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: CleanupPlan converts to SpecChange payload
- **GIVEN** a CleanupPlan with intent, steps, constraints, and tests
- **WHEN** OpenSpecBackend.plan_to_spec is called
- **THEN** it returns a SpecChange tagged openspec whose payload mirrors the plan data in structured form
