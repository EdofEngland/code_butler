## ADDED Requirements
### Requirement: Phase 1.1 Repo and Packaging Setup
- Phase 1.1 Repo & Packaging Setup deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: CLI help enumerates placeholder commands
- **GIVEN** the ai-clean package is installed with its entrypoint
- **WHEN** a user runs `ai-clean --help`
- **THEN** the output lists the placeholder commands /analyze, /clean, /annotate, /organize, /cleanup-advanced, /plan, /apply, and /changes-review
