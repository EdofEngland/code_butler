## ADDED Requirements
### Requirement: Phase 7.7 Cleanup Advanced Command
- Phase 7.7 `/cleanup-advanced` Command deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Cleanup-advanced lists advisory plans
- **GIVEN** advanced_cleanup findings
- **WHEN** ai-clean cleanup-advanced PATH runs
- **THEN** the CLI shows limited suggestions, creates plans for them, and reports plan IDs without applying
