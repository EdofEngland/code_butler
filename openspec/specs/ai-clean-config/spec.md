# ai-clean-config Specification

## Purpose
TBD - created by archiving change add-phase-1-4-config-layout. Update Purpose after archive.
## Requirements
### Requirement: Phase 1.4 Configuration and Metadata Layout
- Phase 1.4 Configuration & Local Metadata Layout deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Config loader validates ai-clean.toml
- **GIVEN** an ai-clean.toml with spec_backend, executor, review, git, and tests sections
- **WHEN** the config loader reads the file
- **THEN** it returns validated settings and ensures .ai-clean/plans and .ai-clean/specs directories are defined
