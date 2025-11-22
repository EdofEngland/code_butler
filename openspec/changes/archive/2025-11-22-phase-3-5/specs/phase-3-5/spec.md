## ADDED Requirements

### Requirement: Planner emits micro-cleanup plans
The planner MUST convert each `advanced_cleanup` finding into one or more deterministic `CleanupPlan`s (returned as a list) that apply exactly one Codex-suggested micro-change within the provided file/line span.

#### Scenario: Generate plan for advanced cleanup
- **GIVEN** a `Finding` with `category="advanced_cleanup"` and metadata (target path, start/end lines, change type, prompt hash, codex model)
- **WHEN** the planner runs
- **THEN** each plan id/title reference the change type and file
- **AND** steps cover verifying the snippet, applying the change within lines `start_line`–`end_line`, and running the specified tests
- **AND** constraints forbid touching other files or APIs and reiterate the exact line span
- **AND** metadata records the target file, span length, change type, prompt hash, codex model, chosen test command, and any index used when multiple plans are emitted for one finding

### Requirement: Guardrails for advanced cleanup plans
The planner MUST enforce small scope and reject findings that exceed local-change limits.

#### Scenario: Reject oversized or ambiguous advanced cleanup
- **GIVEN** a finding missing required metadata, referencing multiple files, or spanning more than the allowed line range
- **WHEN** the planner processes it
- **THEN** it raises a descriptive error (or splits multiple suggestions into separate plans) instead of emitting an overly broad plan
- **AND** no plan is produced unless it remains review-friendly (single file, small span, single action)
