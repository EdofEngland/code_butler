# phase-8-1 Specification

## Purpose
TBD - created by archiving change phase-8-1. Update Purpose after archive.
## Requirements
### Requirement: Phase 8.1 – Change Size Limits
The ai-clean project MUST enforce deterministic cleanup plan size limits: max 1 file per plan (v0) and a configured cap on changed lines (absolute additions + deletions), and MUST reject or split plans that exceed these limits.

#### Scenario: Plan within limits is accepted
- **GIVEN** plan-size limits are configured (1 file, line cap defined)
- **WHEN** a cleanup plan targets exactly 1 file and total changed lines are ≤ the cap
- **THEN** the plan SHALL be considered valid for execution without splitting

#### Scenario: Multi-file plan is rejected and must be split
- **WHEN** a cleanup plan targets more than 1 file
- **THEN** validation SHALL fail with a clear error explaining multi-file plans are disallowed
- **AND** the planner/advanced analyzer SHALL produce multiple single-file plans instead

#### Scenario: Over-cap line count is rejected and must be split
- **WHEN** a cleanup plan exceeds the configured changed-line cap
- **THEN** validation SHALL fail with a clear error explaining the line overage
- **AND** the planner/advanced analyzer SHALL split the work into multiple plans whose line totals each fit under the cap

#### Scenario: Split output stays within limits
- **WHEN** the planner/advanced analyzer splits a multi-file or over-cap request
- **THEN** each emitted plan SHALL target only one file and SHALL remain under the changed-line cap
- **AND** emitted plans SHALL include trace/log metadata showing why the split occurred

#### Scenario: Multi-concern plans are out of scope
- **WHEN** a plan mixes unrelated concerns or attempts to bypass limits by bundling topics
- **THEN** validation SHALL reject the plan with guidance to create separate, single-concern plans
