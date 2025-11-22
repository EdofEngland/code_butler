# phase-3-6 Specification

## Purpose
TBD - created by archiving change phase-3-6. Update Purpose after archive.
## Requirements
### Requirement: Planning Orchestrator Dispatch
`plan_from_finding(finding: Finding, config: ButlerConfig) -> list[CleanupPlan]` SHALL be the single public entrypoint that routes analyzer findings to the correct phase-specific planner.

#### Scenario: Dispatch by known category
- **WHEN** `plan_from_finding` receives a `Finding`
- **THEN** it SHALL dispatch according to:
  - `duplicate_block` → wrap `plan_duplicate_blocks([finding], config)` and return the list of helper plans as-is
  - `large_file` or `long_function` → Phase 3.2 helper
  - `missing_docstring` or `weak_docstring` → Phase 3.3 helper
  - `organize_candidate` → Phase 3.4 helper
  - `advanced_cleanup` → Phase 3.5 helper
- **AND** the orchestrator SHALL return the resulting list of plans without mutating or persisting it.

#### Scenario: Unknown category guardrail
- **WHEN** `plan_from_finding` receives a category outside the list above
- **THEN** it SHALL raise `NotImplementedError` naming the unsupported category instead of silently falling back.

### Requirement: Multi-plan friendly results
The orchestrator SHALL allow helpers to return zero, one, or multiple plans, leaving any “exactly one plan” enforcement to the caller.

#### Scenario: Caller-enforced single-plan requirement
- **WHEN** a CLI command needs exactly one plan
- **THEN** it SHALL call `plan_from_finding`, inspect the returned list, and raise its own `ValueError` when the length is not 1 instead of relying on the orchestrator to do so implicitly.

### Requirement: Deterministic Plan IDs
The orchestrator SHALL expose `generate_plan_id(finding_id: str, suffix: str) -> str` so downstream tooling gets deterministic, reproducible identifiers.

#### Scenario: Stable ID format
- **WHEN** planners call `generate_plan_id("finding-123", "doc")`
- **THEN** they receive the lowercase ID `finding-123-doc`
- **AND** the helper SHALL strip whitespace, reject characters outside `[a-z0-9-]`, and guarantee that the same inputs always yield the same ID.

#### Scenario: Invalid suffix handling
- **WHEN** the suffix contains uppercase letters or punctuation
- **THEN** the helper SHALL raise `ValueError` so planners fix their suffix logic instead of generating inconsistent filenames.

### Requirement: Plan Serialization Contract
The planning layer SHALL expose a helper for deterministic plan persistence so CLI commands can write `.ai-clean/plans/{plan_id}.json` artifacts after planning completes.

#### Scenario: Writing plan JSON
- **WHEN** `write_plan_to_disk(plan, base_dir)` is invoked
- **THEN** it SHALL create `base_dir` if missing, write UTF-8 JSON produced by `CleanupPlan.to_json()`, and return the `Path`.

#### Scenario: Deterministic persistence
- **WHEN** the CLI receives plans from `plan_from_finding`
- **THEN** it SHALL loop over them, call `write_plan_to_disk(plan, config.plans_dir)` for each, and confirm `.ai-clean/plans/{plan_id}.json` is deterministic across runs.
