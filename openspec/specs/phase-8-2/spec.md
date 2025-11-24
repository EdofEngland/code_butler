# phase-8-2 Specification

## Purpose
TBD - created by archiving change phase-8-2. Update Purpose after archive.
## Requirements
### Requirement: Phase 8.2 – Single Concern per Plan
The ai-clean project MUST enforce that each CleanupPlan addresses exactly one concern from a defined taxonomy and MUST reject or split any plan that mixes concerns.

#### Scenario: Plan matches one allowed concern
- **GIVEN** the allowed concerns are: helper extraction; file split; small file-group move; small-scope docstring batch; single advanced cleanup suggestion
- **WHEN** a plan is classified as exactly one of those concerns
- **THEN** the plan SHALL be considered valid for execution (subject to other limits)

#### Scenario: Plan mixes multiple concerns → reject
- **WHEN** a plan combines more than one concern (e.g., docstring updates plus helper extraction; move plus rename plus cleanup)
- **THEN** validation SHALL fail with a clear error naming the detected concerns
- **AND** the planner/advanced analyzer SHALL split the work into separate single-concern plans before execution

#### Scenario: Plan with ambiguous/multi-topic scope → reject
- **WHEN** a plan description is ambiguous or spans multiple topics (e.g., cross-file refactor plus doc improvements)
- **THEN** validation SHALL reject with guidance to rephrase/split into single-concern plans

#### Scenario: Split output stays single-concern
- **WHEN** the planner/advanced analyzer splits a mixed request
- **THEN** each emitted plan SHALL map to exactly one allowed concern
- **AND** emitted plans SHALL include trace/log metadata showing the detected concern and why splitting occurred

#### Scenario: Non-goals remain out of scope
- **WHEN** a plan attempts chained refactors or cross-topic bundles to bypass the rule
- **THEN** the system SHALL treat it as multi-concern and reject until split into separate plans
