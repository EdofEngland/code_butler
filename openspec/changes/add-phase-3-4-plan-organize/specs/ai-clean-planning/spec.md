## ADDED Requirements
### Requirement: Phase 3.4 Organize Planner
- Phase 3.4 Planner for Organize Candidates deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Organize candidate yields move plan
- **GIVEN** an organize_candidate finding with a suggested folder and file list
- **WHEN** the planner builds a plan
- **THEN** the CleanupPlan lists moves for that small set of files, updates imports, and avoids touching function bodies
