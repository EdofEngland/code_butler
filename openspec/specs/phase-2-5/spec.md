# phase-2-5 Specification

## Purpose
TBD - created by archiving change phase-2-5. Update Purpose after archive.
## Requirements
### Requirement: Phase 2.5 – Analyzer Orchestrator
The ai-clean project MUST fulfill the deliverables for Phase 2.5 described in docs/butlerspec_plan.md to keep the ButlerSpec roadmap on track.

#### Scenario: Aggregating analyzer results
- **GIVEN** duplicate, structure, docstring, and organize analyzers exist
- **WHEN** `analyze_repo(path)` runs
- **THEN** it invokes each analyzer with shared config and concatenates their `Finding`s in the fixed order (duplicate → structure → docstrings → organize).

#### Scenario: Deduplication and stable IDs
- **GIVEN** two analyzers emit findings with the same `id`
- **WHEN** the orchestrator aggregates them
- **THEN** locations and metadata are merged (sorted/deduped) while the first description is retained.
- **AND** the final list is sorted by `(category, id)` to keep IDs/states deterministic across runs.

#### Scenario: CLI text output
- **GIVEN** a user runs `ai-clean analyze --root src`
- **WHEN** findings exist
- **THEN** the CLI prints a table listing `id | category | description` plus indented `file.py:start-end` lines for each location.
- **AND** the ordering matches the orchestrator result order.

#### Scenario: CLI JSON output
- **GIVEN** the `--json` flag is supplied
- **WHEN** `/analyze` runs
- **THEN** it emits the serialized `Finding` list (stable ordering) to stdout and suppresses the human-readable table.
