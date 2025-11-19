## ADDED Requirements
### Requirement: Phase 1.2 Core Data Models
- Phase 1.2 Core Data Model Definitions deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Core models serialize without external dependencies
- **GIVEN** a Finding and CleanupPlan are instantiated with plain Python types
- **WHEN** the objects are serialized using the standard library
- **THEN** their fields (ids, categories, locations, metadata) are preserved without referencing Codex or OpenSpec
