## ADDED Requirements
### Requirement: Phase 7.6 Organize Command
- Phase 7.6 `/organize` Command deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Organize guides small file moves
- **GIVEN** organize_candidate findings for a folder
- **WHEN** ai-clean organize PATH runs
- **THEN** the CLI lists suggestions, lets users pick, generates move plans, and offers to apply or store them
