# phase-2-1 Specification

## Purpose
TBD - created by archiving change phase-2-1. Update Purpose after archive.
## Requirements
### Requirement: Phase 2.1 – Duplicate Code Analyzer (Local)
The ai-clean project MUST fulfill the deliverables for Phase 2.1 described in docs/butlerspec_plan.md to keep the ButlerSpec roadmap on track.

#### Scenario: Deterministic duplicate detection
- **GIVEN** the team is executing 2 – Analyzers
- **WHEN** Phase 2.1 (Duplicate Code Analyzer (Local)) is completed
- **THEN** the repository provides duplicate code analyzer outputs that:
  - Capture configuration-driven thresholds for `window_size`, `min_occurrences`, and ignored directories.
  - Normalize and hash sliding windows of Python code so duplicate groups share a deterministic ID and description.
  - Emit `duplicate_block` findings listing every file + line range in lexicographic order.
  - Preserve deterministic behavior by sorting file traversal, grouping, and output ordering so identical repositories always yield the same finding list.
- **AND** the work remains within ButlerSpec guardrails (one-plan-per-file, specs on disk, Codex executor).

#### Scenario: Threshold and overlap handling
- **GIVEN** the analyzer processes files smaller than `window_size`, files with overlapping duplicate windows, and directories configured in `ignore_dirs`
- **WHEN** Phase 2.1 runs on such repositories
- **THEN** files shorter than the configured window are skipped without errors
- **AND** overlapping duplicates are reported as separate occurrences with accurate line ranges
- **AND** directories listed in `ignore_dirs` are excluded from traversal and do not influence findings.
