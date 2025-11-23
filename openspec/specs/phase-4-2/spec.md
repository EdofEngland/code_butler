# phase-4-2 Specification

## Purpose
TBD - created by archiving change phase-4-2. Update Purpose after archive.
## Requirements
### Requirement: Phase 4.2 – Writing ButlerSpec Files
The ai-clean project MUST serialize validated ButlerSpecs to `.butler.yaml` files deterministically, enforcing the guardrails documented in `docs/butlerspec_plan.md#phase-4-2` so each file remains a small, single-file change artifact.

#### Scenario: Deterministic YAML write succeeds
- **GIVEN** a validated ButlerSpec targeting a single file with ≤25 actions
- **WHEN** `write_spec(spec, Path(".ai-clean/specs"))` executes
- **THEN** it SHALL create the directory if missing, write `{spec.id}.butler.yaml` using UTF-8 with keys ordered (`id`, `plan_id`, `target_file`, `intent`, `model`, `batch_group`, `actions`, `metadata`), and append a trailing newline
- **AND** subsequent reads via `ButlerSpec.from_yaml` SHALL reconstruct an identical object, proving the on-disk schema is stable

#### Scenario: Guardrails stop multi-topic or oversized specs
- **WHEN** a ButlerSpec contains multiple target files, more than 25 actions, or metadata exceeding the size cap
- **THEN** `write_spec` SHALL raise a descriptive error before touching the filesystem
- **AND** no `.butler.yaml` file SHALL be created, preserving the one-spec-per-file rule

#### Scenario: Deterministic overwrite behavior
- **GIVEN** a spec file already exists at `.ai-clean/specs/{spec.id}.butler.yaml`
- **WHEN** `write_spec` runs again with the same ButlerSpec payload
- **THEN** the resulting bytes SHALL match exactly (idempotent write)
- **AND** IF the payload differs, the file SHALL be replaced with the new deterministic serialization while emitting a warning/log for visibility

#### Scenario: Error propagation for unwritable directories
- **WHEN** the destination directory is read-only or otherwise unwritable
- **THEN** `write_spec` SHALL surface the underlying permission error with a message referencing the path so callers can react, rather than silently swallowing the failure
