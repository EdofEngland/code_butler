## ADDED Requirements

### Requirement: Duplicate block planner emits helper extraction plans
The planner MUST translate every `duplicate_block` finding into one or more ButlerSpec-ready `CleanupPlan`s that capture a helper extraction workflow using the standard pure-planner signature.

#### Scenario: Single-file duplicates produce one helper plan
- **GIVEN** a `duplicate_block` finding whose occurrences all live in the same module
- **WHEN** the planner runs
- **THEN** it emits a `CleanupPlan` containing:
  - **INTENT** stating “Extract reusable helper” for that module
  - **STEPS** that (1) confirm the helper location, (2) create the helper function/class, and (3) replace each listed duplicate block with a helper call
  - **CONSTRAINTS** listing “No external behavior changes” and “No public API changes,” referencing the affected module or symbol names
- **AND** the plan metadata references the helper target path chosen by the planner so reviewers know where extraction happens, defaulting to the module of the first occurrence when no better signal exists.

### Requirement: Large duplicate findings are split into ordered plans
The planner MUST keep each plan small and deterministic so reviewers can apply them sequentially.

#### Scenario: Multi-file or >3 duplicates are split
- **GIVEN** a `duplicate_block` finding that spans multiple files or contains more than three occurrences
- **WHEN** the planner runs
- **THEN** it groups occurrences by helper target, caps each `CleanupPlan` at three duplicates, and emits additional plans for the remainder
- **AND** each plan is sorted by helper path and the first duplicate line number, ensuring reviewers can process plans in a predictable order
- **AND** no plan mixes duplicates with different helper locations.

### Requirement: Planner guardrails and test expectations
Planned helpers MUST respect ButlerSpec guardrails, cite the repository’s configured test command, and return plan objects without touching the filesystem.

#### Scenario: Plans reiterate constraints and default tests
- **GIVEN** the planner converts a `duplicate_block` finding into `CleanupPlan`s
- **WHEN** no custom test command is provided in finding metadata
- **THEN** each plan’s `tests_to_run` field includes exactly the configured `tests.default_command`
- **AND** the plan constraints reiterate “No external behavior changes” and “No public API changes”
- **AND** overlapping duplicate ranges remain in deterministic order within each plan’s steps so Codex can apply them safely.
- **AND** the planner returns a list of `CleanupPlan`s (possibly multiple) while leaving plan serialization to higher-level orchestration.
