## ADDED Requirements
### Requirement: Phase 7.2 Plan Command
- Phase 7.2 `/plan` Command deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Plan command creates and saves plan
- **GIVEN** an existing finding ID
- **WHEN** ai-clean plan FINDING_ID is executed
- **THEN** the CLI generates a CleanupPlan for that finding, saves it, and prints the plan details
