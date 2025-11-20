# ai-clean-spec-backend Specification

## Purpose
TBD - created by archiving change add-phase-4-1-openspec-backend. Update Purpose after archive.
## Requirements
### Requirement: Phase 4.1 OpenSpec Backend
- Phase 4.1 OpenSpec Backend: Plan → SpecChange deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: CleanupPlan converts to SpecChange payload
- **GIVEN** a CleanupPlan with intent, steps, constraints, and tests
- **WHEN** OpenSpecBackend.plan_to_spec is called
- **THEN** it returns a SpecChange tagged openspec whose payload mirrors the plan data in structured form

### Requirement: Phase 4.2 Spec File Writing
- Phase 4.2 Writing Spec Files deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: SpecChange writes to YAML file
- **GIVEN** a SpecChange produced by the backend
- **WHEN** write_spec is called with .ai-clean/specs as the directory
- **THEN** a YAML file with a stable name is created containing the SpecChange payload for a single change

### Requirement: Phase 4.3 Backend Factory
- Phase 4.3 Backend Factory & Configuration deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Factory builds configured spec backend
- **GIVEN** an ai-clean.toml specifying spec_backend type openspec
- **WHEN** the backend factory is invoked
- **THEN** it returns an OpenSpecBackend instance or raises a clear error for unsupported types

#### Scenario: Backend interface validation is runtime-checkable
- **GIVEN** the factory instantiates the configured spec backend
- **WHEN** it verifies the backend implements `SpecBackend`
- **THEN** the `SpecBackend` protocol is runtime-checkable so `isinstance` succeeds for valid implementations and raises a clear error otherwise
