## ADDED Requirements
### Requirement: Phase 2.4 Organize Seed Analyzer
- Phase 2.4 Organize Seed Analyzer deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Related files yield organize_candidate finding
- **GIVEN** a folder with several files that share imports and naming
- **WHEN** the organize seed analyzer runs
- **THEN** it emits an organize_candidate finding suggesting a destination folder and listing the candidate file paths
