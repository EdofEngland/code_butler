# phase-2-3 Specification

## Purpose
TBD - created by archiving change phase-2-3. Update Purpose after archive.
## Requirements
### Requirement: Phase 2.3 – Docstring Analyzer
The ai-clean project MUST fulfill the deliverables for Phase 2.3 described in docs/butlerspec_plan.md to keep the ButlerSpec roadmap on track.

#### Scenario: Module docstrings
- **GIVEN** Phase 2.3 scans Python modules under analysis
- **WHEN** a module lacks a docstring or has an empty/whitespace-only string
- **THEN** it emits a `missing_docstring` finding with module path + context in the description and `FindingLocation(path, 1, 1)`.

#### Scenario: Public symbol docstrings
- **GIVEN** public classes/functions (names without a leading `_`) are parsed
- **WHEN** a symbol is missing a docstring
- **THEN** emit a `missing_docstring` finding referencing the qualified name, file path, and definition span.
- **WHEN** a symbol’s docstring is shorter than `min_docstring_length` or matches any entry in `weak_markers`
- **THEN** emit a `weak_docstring` finding capturing the preview text and rationale.

#### Scenario: Noise controls and determinism
- **GIVEN** `[analyzers.docstring]` configuration defines `min_symbol_lines`, `ignore_dirs`, and `important_symbols_only`
- **WHEN** the analyzer runs with the important-symbol filter enabled
- **THEN** symbols with fewer lines than `min_symbol_lines` are skipped without findings.
- **AND** directories listed in `ignore_dirs` are not traversed.
- **WHEN** the analyzer is rerun on the same source tree and config
- **THEN** the finding list remains deterministic (same IDs/order) because modules and symbols are processed in sorted order.
