## ADDED Requirements
### Requirement: Phase 7.3 Apply Command
- Phase 7.3 `/apply` Command deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Apply runs spec and tests with git summary
- **GIVEN** a stored plan ID and configured git branches
- **WHEN** ai-clean apply PLAN_ID is executed
- **THEN** the command ensures the refactor branch, writes an openspec file, applies it, runs tests, and shows results plus diff stat
