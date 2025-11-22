## ADDED Requirements

### Requirement: Planner emits structured plans for `large_file` findings
The planner MUST convert every `large_file` finding into one or more deterministic `CleanupPlan`s (returned as a list) that describe splitting the file into 2–3 logical modules while preserving the public API.

#### Scenario: Generate plan for large file
- **GIVEN** a `Finding` with `category="large_file"` plus metadata (`line_count`, `threshold`)
- **WHEN** the planner runs
- **THEN** it emits plans whose ids/titles reference the source file
- **AND** each plan enumerates steps for grouping responsibilities, creating new module files/folders, and moving code plus updating imports/re-exports
- **AND** constraints reiterate that public APIs must remain intact via re-exports
- **AND** plan metadata includes the source file, module target list (max three per plan), clustered target details, and size stats pulled from the finding

#### Scenario: Guardrails for large file planner
- **GIVEN** a `large_file` finding missing required metadata or spanning more than three module clusters
- **WHEN** the planner executes
- **THEN** it raises a clear error for missing metadata instead of guessing
- **AND** splits the work into additional plans so no plan exceeds three module targets

### Requirement: Planner emits structured plans for `long_function` findings
The planner MUST convert every `long_function` finding into a list containing exactly one `CleanupPlan` describing helper extraction that stays local to the function and keeps behavior identical.

#### Scenario: Generate plan for long function
- **GIVEN** a `Finding` with `category="long_function"` and metadata (`qualified_name`, `line_count`, `start_line`, `end_line`)
- **WHEN** the planner runs
- **THEN** it emits a plan whose id/title/intention reference the function
- **AND** the plan steps identify logical sub-blocks (with line ranges), extract helper functions colocated with the original code, and replace the original blocks with helper calls
- **AND** constraints forbid API changes and limit edits to the function plus immediate helpers
- **AND** metadata records helper-placement guidance (e.g., helper module/path and naming prefix) plus any optional segments provided by the analyzer without re-validating thresholds

#### Scenario: Guardrails for long function planner
- **GIVEN** a `long_function` finding with missing metadata or multiple file locations
- **WHEN** the planner runs
- **THEN** it raises a `ValueError` rather than emitting a plan with incomplete context
- **AND** the planner documents in metadata that helper extraction stays scoped to a single module (e.g., `scope: single_function`)
