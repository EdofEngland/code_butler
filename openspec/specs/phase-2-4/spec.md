# phase-2-4 Specification

## Purpose
TBD - created by archiving change phase-2-4. Update Purpose after archive.
## Requirements
### Requirement: Phase 2.4 – Organize Seed Analyzer
The ai-clean project MUST fulfill the deliverables for Phase 2.4 described in docs/butlerspec_plan.md to keep the ButlerSpec roadmap on track.

#### Scenario: Topic inference from filename/import/docstring
- **GIVEN** the analyzer scans `.py` files and builds per-file topic signals (filename tokens, import stems, docstring keywords)
- **WHEN** a file has consistent signals
- **THEN** it is assigned the deterministic topic label derived from the highest-weight token (ties broken alphabetically)
- **AND** files without signals are skipped without findings.

#### Scenario: Conservative grouping
- **GIVEN** topics with between `min_group_size` and `max_group_size` members
- **WHEN** findings are emitted
- **THEN** each `organize_candidate` lists 2–5 files, includes the suggested folder (e.g., `api/`), and all listed files appear only once across findings.
- **AND** `max_groups` bounds the total number of findings per run.

#### Scenario: Ambiguity and ignore directories
- **GIVEN** files inside directories listed in `ignore_dirs` or with conflicting signals (e.g., imports vs docstrings disagree)
- **WHEN** the analyzer runs
- **THEN** those files are excluded from groupings to avoid noisy suggestions.

#### Scenario: Deterministic ordering
- **GIVEN** the same repository and configuration
- **WHEN** Phase 2.4 runs multiple times
- **THEN** the emitted findings (IDs, ordering, member order) remain identical because files/topics/outputs are sorted consistently before emission.
