# ai-clean-analysis Specification

## Purpose
TBD - created by archiving change add-phase-2-1-duplicate-analyzer. Update Purpose after archive.
## Requirements
### Requirement: Phase 2.1 Duplicate Code Analyzer
- Phase 2.1 Duplicate Code Analyzer (Local) deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Duplicate windows emit duplicate_block findings
- **GIVEN** two Python files share repeated code blocks that meet the window and occurrence thresholds
- **WHEN** the duplicate analyzer runs on the repository
- **THEN** it emits a duplicate_block finding describing the occurrences and listing each file and line range

### Requirement: Phase 2.2 Structure Analyzer
- Phase 2.2 Structure Analyzer: Large Files & Long Functions deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Large files and functions are reported
- **GIVEN** a file and function exceed their configured line thresholds
- **WHEN** the structure analyzer runs
- **THEN** it emits large_file and long_function findings with the relevant file and function line ranges

### Requirement: Phase 2.3 Docstring Analyzer
- Phase 2.3 Docstring Analyzer deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Public symbols without docstrings are flagged
- **GIVEN** a module and public function lacking meaningful docstrings
- **WHEN** the docstring analyzer runs
- **THEN** it emits missing_docstring or weak_docstring findings referencing the symbol definitions

### Requirement: Phase 2.4 Organize Seed Analyzer
- Phase 2.4 Organize Seed Analyzer deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Related files yield organize_candidate finding
- **GIVEN** a folder with several files that share imports and naming
- **WHEN** the organize seed analyzer runs
- **THEN** it emits an organize_candidate finding suggesting a destination folder and listing the candidate file paths

### Requirement: Phase 2.5 Analyzer Orchestrator
- Phase 2.5 Analyzer Orchestrator deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Orchestrator returns combined findings
- **GIVEN** a repository with duplicates, large files, and docstring gaps
- **WHEN** analyze_repo is invoked
- **THEN** it returns findings from all analyzers with stable IDs and /analyze displays them with summaries

### Requirement: Phase 2.6 Advanced Cleanup Analyzer
- Phase 2.6 Codex-Powered Advanced Cleanup Analyzer deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Codex suggestions become advanced_cleanup findings
- **GIVEN** a curated set of files and constraints for small cleanups
- **WHEN** the advanced analyzer requests suggestions from Codex
- **THEN** it emits a limited number of advanced_cleanup findings with targeted locations and advisory metadata
