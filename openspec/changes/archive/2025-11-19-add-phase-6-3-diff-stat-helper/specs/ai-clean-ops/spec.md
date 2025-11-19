## ADDED Requirements
### Requirement: Phase 6.3 Diff Stat Helper
- Phase 6.3 Diff Stat Helper deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Diff stat summarises changes
- **GIVEN** there are working tree modifications
- **WHEN** get_diff_stat is called
- **THEN** it returns the git diff --stat style summary of files and line changes
