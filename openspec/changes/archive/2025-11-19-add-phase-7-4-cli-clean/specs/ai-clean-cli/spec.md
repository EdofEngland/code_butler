## ADDED Requirements
### Requirement: Phase 7.4 Clean Command
- Phase 7.4 `/clean` Command (Basic Cleanup Wrapper) deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Clean guides finding selection and plan creation
- **GIVEN** analyze results with duplicates or large structures
- **WHEN** ai-clean clean PATH runs
- **THEN** the CLI presents filtered findings, lets the user pick, builds plans, and offers to apply or store each
