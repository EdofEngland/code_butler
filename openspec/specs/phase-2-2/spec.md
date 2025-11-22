# phase-2-2 Specification

## Purpose
TBD - created by archiving change phase-2-2. Update Purpose after archive.
## Requirements
### Requirement: Phase 2.2 – Structure Analyzer: Large Files & Long Functions
The ai-clean project MUST fulfill the deliverables for Phase 2.2 described in docs/butlerspec_plan.md to keep the ButlerSpec roadmap on track.

#### Scenario: Large file detection
- **GIVEN** the team is executing 2 – Analyzers
- **WHEN** Phase 2.2 runs on repositories with files exceeding `max_file_lines`
- **THEN** the analyzer emits `large_file` findings with descriptions noting actual line count vs. threshold and `FindingLocation(path, 1, line_count)`
- **AND** files at or below the threshold are skipped without false positives.

#### Scenario: Long function detection
- **GIVEN** modules contain functions or methods whose body length exceeds `max_function_lines`
- **WHEN** Phase 2.2 processes their AST
- **THEN** each long function (including nested defs and async variants) produces a `long_function` finding with a deterministic ID based on module path + qualified name
- **AND** multiple long functions inside the same file are reported independently with precise spans.

#### Scenario: Deterministic ordering and config controls
- **GIVEN** configuration is loaded from `[analyzers.structure]` with thresholds and ignore directories
- **WHEN** Phase 2.2 is rerun on the same repository
- **THEN** findings (ids, descriptions, location ordering) remain identical across runs because traversal and emission are sorted by `(relative_path, lineno, name)`
- **AND** directories listed in `ignore_dirs` are excluded from traversal without affecting counts.
