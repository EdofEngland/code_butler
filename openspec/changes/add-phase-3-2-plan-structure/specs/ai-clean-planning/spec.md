## ADDED Requirements
### Requirement: Phase 3.2 Structure Planners
- Phase 3.2 Planner for Large Files & Long Functions deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Structure findings yield scoped refactor plans
- **GIVEN** a large_file or long_function finding
- **WHEN** the planner processes the finding
- **THEN** it produces a CleanupPlan with intent, steps, constraints, and tests aligned to the specific file or function
