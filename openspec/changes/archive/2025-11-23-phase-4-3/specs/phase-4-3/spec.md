## ADDED Requirements

### Requirement: Butler backend selection
The backend factory SHALL read `spec_backend.type` from `ai-clean.toml` and instantiate `ButlerSpecBackend` when (and only when) the type equals `"butler"`.

#### Scenario: Selecting the Butler backend
- **GIVEN** an `ai-clean.toml` whose `[spec_backend]` table sets `type = "butler"` and a valid specs directory
- **WHEN** `get_spec_backend` is called
- **THEN** it SHALL return a `SpecBackendHandle` whose backend is a `ButlerSpecBackend` wired to the provided configuration
- **AND** the handle’s `specs_dir` mirrors `spec_backend.specs_dir` so downstream tooling persists specs deterministically.

### Requirement: Unsupported backend guardrail
The backend factory SHALL reject missing, empty, or unknown backend identifiers before performing any backend work.

#### Scenario: Rejecting unsupported type
- **GIVEN** `spec_backend.type` is unset, blank, or set to a value other than `butler`
- **WHEN** the factory resolves a backend
- **THEN** it SHALL raise `ValueError("Unsupported spec backend: <value>")` (or the blank representation)
- **AND** surface the error without touching the filesystem or instantiating placeholders.

### Requirement: Configuration contract documentation
Phase 4.3 documentation SHALL describe the `[spec_backend]` contract, including required fields, current limitations, and the need for a new change proposal to add other backends.

#### Scenario: Documenting configuration contract
- **GIVEN** a contributor references the Phase 4.3 docs/plan
- **WHEN** they look up backend configuration guidance
- **THEN** they SHALL see that `type` and `specs_dir` are required, `butler` is the lone supported backend, and all future backend additions need a proposal before implementation.
