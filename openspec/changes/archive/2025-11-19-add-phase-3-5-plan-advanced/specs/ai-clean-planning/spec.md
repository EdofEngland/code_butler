## ADDED Requirements
### Requirement: Phase 3.5 Advanced Cleanup Planner
- Phase 3.5 Planner for Advanced Cleanup deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Advanced cleanup suggestion becomes scoped plan
- **GIVEN** an advanced_cleanup finding targeting specific lines
- **WHEN** the planner creates a plan
- **THEN** the CleanupPlan limits changes to those locations, keeps file count small, and records intent/tests
