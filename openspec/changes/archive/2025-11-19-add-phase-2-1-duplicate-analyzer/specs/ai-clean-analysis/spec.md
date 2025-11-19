## ADDED Requirements
### Requirement: Phase 2.1 Duplicate Code Analyzer
- Phase 2.1 Duplicate Code Analyzer (Local) deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Duplicate windows emit duplicate_block findings
- **GIVEN** two Python files share repeated code blocks that meet the window and occurrence thresholds
- **WHEN** the duplicate analyzer runs on the repository
- **THEN** it emits a duplicate_block finding describing the occurrences and listing each file and line range
