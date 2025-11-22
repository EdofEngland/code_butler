# phase-3-4 Specification

## Purpose
TBD - created by archiving change phase-3-4. Update Purpose after archive.
## Requirements
### Requirement: Planner emits scoped organize plans
The planner MUST translate each `organize_candidate` finding into one or more `CleanupPlan`s (returned as a list) that describe moving a small, coherent set of files into an improved folder, updating imports, and adding re-exports.

#### Scenario: Generate organize plan
- **GIVEN** a `Finding` with `category="organize_candidate"` and metadata (`topic`, `files`)
- **WHEN** the planner runs
- **THEN** it emits one plan per file whose id/title reference the topic, the specific file, and the destination folder
- **AND** the plan steps explicitly mention creating the folder (if needed), moving that file, updating imports, and adding re-exports
- **AND** constraints state “no function body changes” and “avoid deep nesting”
- **AND** plan metadata records the original file, target directory, split index/batch size, and whether re-exports are required

### Requirement: Guardrails for organize plans
The planner MUST enforce small scope and safe folder selection rules for organize plans.

#### Scenario: Reject oversized or ambiguous groups
- **GIVEN** a finding with more than five files or files spanning disjoint parent directories
- **WHEN** the planner processes it
- **THEN** it either raises a clear error or splits the work into multiple plans so each plan stays within the small-set rule
- **AND** plans never introduce folder structures deeper than allowed (e.g., more than two new levels relative to the shared parent)
- **AND** metadata/logging reflects how the planner resolved the ambiguity (chosen folder, re-export requirements, per-file scope markers)
