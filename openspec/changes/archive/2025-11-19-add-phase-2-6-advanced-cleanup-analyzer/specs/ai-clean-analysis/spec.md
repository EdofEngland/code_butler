## ADDED Requirements
### Requirement: Phase 2.6 Advanced Cleanup Analyzer
- Phase 2.6 Codex-Powered Advanced Cleanup Analyzer deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Codex suggestions become advanced_cleanup findings
- **GIVEN** a curated set of files and constraints for small cleanups
- **WHEN** the advanced analyzer requests suggestions from Codex
- **THEN** it emits a limited number of advanced_cleanup findings with targeted locations and advisory metadata
