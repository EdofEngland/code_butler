## ADDED Requirements
### Requirement: Phase 5.3 Review Executor
- Phase 5.3 ReviewExecutor: Changes Review deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Review executor summarizes change
- **GIVEN** a plan id, associated diff, and execution result
- **WHEN** the review executor runs
- **THEN** it returns a review summary with what changed, risks, and manual check suggestions without modifying files
