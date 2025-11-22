# phase-1-2 Specification

## Purpose
TBD - created by archiving change phase-1-2. Update Purpose after archive.
## Requirements
### Requirement: Core data models defined
The system MUST expose typed classes for every core abstraction referenced in the ButlerSpec workflow.

#### Scenario: Models list all required fields
- **WHEN** `ai_clean.models.core` is inspected
- **THEN** it contains `FindingLocation`, `Finding`, `CleanupPlan`, `ButlerSpec`, and `ExecutionResult`
- **AND** each class inherits from `pydantic.BaseModel` with the fields enumerated in Phase 1.2 tasks (ids, metadata, locations, stdout/stderr, etc.).

### Requirement: Serialization API exists
Each model MUST support JSON serialization/deserialization plus optional YAML helpers.

#### Scenario: JSON round-trips succeed
- **WHEN** a model instance calls `.to_json()`
- **AND** the resulting string feeds into `.from_json()`
- **THEN** the reconstructed instance equals the original
- **AND** missing optional metadata defaults to `{}` without raising errors.

#### Scenario: YAML extra is discoverable
- **GIVEN** `pyyaml` is not installed
- **WHEN** `.to_yaml()` is invoked
- **THEN** the call raises a clear error instructing the user to install the `[yaml]` optional dependency
- **AND** once the extra is installed, YAML round-trips behave like JSON.

### Requirement: Default metadata paths are published
Helper functions MUST describe how to store serialized artifacts under `.ai-clean/` directories.

#### Scenario: Default path helpers point to ButlerSpec layout
- **WHEN** `default_plan_path("abc")` and `default_spec_path("spec-1")` are called
- **THEN** they return `.ai-clean/plans/abc.json` and `.ai-clean/specs/spec-1.yaml` (or similar) without touching the filesystem.

### Requirement: Guardrails communicated and tested
Documentation MUST reinforce the “data-only” boundary and include a deterministic roundtrip example.

#### Scenario: Roundtrip example enforces constraints
- **WHEN** `examples/model_roundtrip.py` is executed
- **THEN** it instantiates each model, serializes/deserializes via both JSON and YAML (when available), touches the default path helpers, and asserts equality
- **AND** docstrings explain that Codex/executor logic belongs outside `ai_clean.models`.
