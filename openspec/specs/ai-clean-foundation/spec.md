# ai-clean-foundation Specification

## Purpose
TBD - created by archiving change add-phase-1-1-repo-setup. Update Purpose after archive.
## Requirements
### Requirement: Phase 1.1 Repo and Packaging Setup
- Phase 1.1 Repo & Packaging Setup deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: CLI help enumerates placeholder commands
- **GIVEN** the ai-clean package is installed with its entrypoint
- **WHEN** a user runs `ai-clean --help`
- **THEN** the output lists the placeholder commands /analyze, /clean, /annotate, /organize, /cleanup-advanced, /plan, /apply, and /changes-review

### Requirement: Phase 1.2 Core Data Models
- Phase 1.2 Core Data Model Definitions deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Core models serialize without external dependencies
- **GIVEN** a Finding and CleanupPlan are instantiated with plain Python types
- **WHEN** the objects are serialized using the standard library
- **THEN** their fields (ids, categories, locations, metadata) are preserved without referencing Codex or OpenSpec
