## MODIFIED Requirements
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
