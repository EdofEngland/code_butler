## ADDED Requirements

### Requirement: Phase 4.1 – ButlerSpec Backend: Plan → ButlerSpec
The ai-clean project MUST provide a ButlerSpec backend that converts a single serialized `CleanupPlan` into a deterministic `ButlerSpec`, enforcing the governance, schema, and action vocabulary documented in `docs/butlerspec_plan.md#phase-4-1`.

#### Scenario: Happy-path conversion produces deterministic ButlerSpec
- **GIVEN** a `.ai-clean/plans/{plan_id}.json` payload whose `metadata.target_file` is a non-empty path
- **WHEN** `ButlerSpecBackend.plan_to_spec` runs
- **THEN** it SHALL emit a ButlerSpec whose `id` equals `f"{plan_id}-spec"`, `plan_id` echoes the source plan, and `target_file`, `intent`, `model="codex"`, and `batch_group=config.default_batch_group` are populated
- **AND** `actions` SHALL contain ordered `plan_step` dictionaries (`type`, `index`, `summary`, `payload`) with trimmed summaries and deterministic indexing
- **AND** `metadata` SHALL be a detached copy containing `plan_title`, normalized `constraints[]`, `tests_to_run[]`, and the rest of the plan metadata so executors never read the plan file directly

#### Scenario: Missing or invalid target_file is rejected
- **WHEN** a plan lacks `metadata.target_file` or includes multiple/conflicting targets
- **THEN** `plan_to_spec` SHALL raise `ValueError("ButlerSpec plans must declare exactly one target_file")` (or a more specific variant called out in docs)
- **AND** SHALL NOT create a ButlerSpec artifact so multi-file plans cannot slip through

#### Scenario: Canonicalization protects determinism
- **GIVEN** a plan whose IDs, steps, or metadata include redundant whitespace or more than 25 steps
- **WHEN** the backend canonicalizes the plan before conversion
- **THEN** IDs and steps SHALL be trimmed, arrays truncated per limits, and oversized metadata SHALL cause deterministic validation errors referencing the offending field
- **AND** mutating the returned ButlerSpec metadata SHALL NOT mutate the original plan payload, preserving deterministic replays
