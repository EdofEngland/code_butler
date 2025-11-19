## ADDED Requirements
### Requirement: Phase 3.1 Duplicate Block Planner
- Phase 3.1 Planner for Duplicate Blocks deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Duplicate finding yields helper extraction plan
- **GIVEN** a duplicate_block finding with multiple occurrences
- **WHEN** plan_from_finding builds a plan for that finding
- **THEN** the CleanupPlan targets only those locations, describes helper extraction steps, and records tests to run
