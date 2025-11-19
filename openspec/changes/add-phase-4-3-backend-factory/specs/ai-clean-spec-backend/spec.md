## ADDED Requirements
### Requirement: Phase 4.3 Backend Factory
- Phase 4.3 Backend Factory & Configuration deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Factory builds configured spec backend
- **GIVEN** an ai-clean.toml specifying spec_backend type openspec
- **WHEN** the backend factory is invoked
- **THEN** it returns an OpenSpecBackend instance or raises a clear error for unsupported types
