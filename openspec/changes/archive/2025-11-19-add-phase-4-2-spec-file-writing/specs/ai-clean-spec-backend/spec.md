## ADDED Requirements
### Requirement: Phase 4.2 Spec File Writing
- Phase 4.2 Writing Spec Files deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: SpecChange writes to YAML file
- **GIVEN** a SpecChange produced by the backend
- **WHEN** write_spec is called with .ai-clean/specs as the directory
- **THEN** a YAML file with a stable name is created containing the SpecChange payload for a single change
