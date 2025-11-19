## ADDED Requirements
### Requirement: Phase 7.1 Analyze Command
- Phase 7.1 `/analyze` Command deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Analyze lists findings
- **GIVEN** a repository with analyzer-detectable issues
- **WHEN** ai-clean analyze PATH is executed
- **THEN** the CLI prints each finding's ID, category, description, and location summary without creating plans
