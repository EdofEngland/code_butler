# ai-clean-planning Specification

## Purpose
TBD - created by archiving change add-phase-3-1-plan-duplicate-blocks. Update Purpose after archive.
## Requirements
### Requirement: Phase 3.1 Duplicate Block Planner
- Phase 3.1 Planner for Duplicate Blocks deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Duplicate finding yields helper extraction plan
- **GIVEN** a duplicate_block finding with multiple occurrences
- **WHEN** plan_from_finding builds a plan for that finding
- **THEN** the CleanupPlan targets only those locations, describes helper extraction steps, and records tests to run

### Requirement: Phase 3.2 Structure Planners
- Phase 3.2 Planner for Large Files & Long Functions deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Structure findings yield scoped refactor plans
- **GIVEN** a large_file or long_function finding
- **WHEN** the planner processes the finding
- **THEN** it produces a CleanupPlan with intent, steps, constraints, and tests aligned to the specific file or function

### Requirement: Phase 3.3 Docstring Planner
- Phase 3.3 Planner for Docstring Findings deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Docstring finding becomes documentation plan
- **GIVEN** a missing_docstring finding for a public function
- **WHEN** the planner generates a plan
- **THEN** the CleanupPlan outlines analyzing behavior, writing a concise docstring, inserting it, and keeping scope to related symbols

### Requirement: Phase 3.4 Organize Planner
- Phase 3.4 Planner for Organize Candidates deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Organize candidate yields move plan
- **GIVEN** an organize_candidate finding with a suggested folder and file list
- **WHEN** the planner builds a plan
- **THEN** the CleanupPlan lists moves for that small set of files, updates imports, and avoids touching function bodies

### Requirement: Phase 3.5 Advanced Cleanup Planner
- Phase 3.5 Planner for Advanced Cleanup deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Advanced cleanup suggestion becomes scoped plan
- **GIVEN** an advanced_cleanup finding targeting specific lines
- **WHEN** the planner creates a plan
- **THEN** the CleanupPlan limits changes to those locations, keeps file count small, and records intent/tests

### Requirement: Phase 3.6 Planning Orchestrator
- Phase 3.6 Planning Orchestrator deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Orchestrator generates and stores plans
- **GIVEN** a finding and configured storage directory
- **WHEN** plan_from_finding is invoked
- **THEN** it produces a CleanupPlan with a unique ID and saves it under .ai-clean/plans

### Requirement: Phase 8.2 Single-Concern Plans
- Phase 8.2 Single-Concern Plans deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Docstring plans keep scope to a single file
- **GIVEN** a missing_docstring or weak_docstring finding referencing multiple files
- **WHEN** plan_from_finding validates the finding
- **THEN** it rejects the plan with a descriptive error stating that docstring cleanups must target a single file

#### Scenario: Structure plans stay within one file
- **GIVEN** a large_file or long_function finding referencing code in multiple files
- **WHEN** plan_from_finding validates the finding
- **THEN** it raises an error explaining that structural cleanups operate on one file at a time so the user can rescope the request
- **THEN** it raises an error explaining that structural cleanups operate on one file at a time so the user can rescope the request

### Requirement: Phase 8.3 No Global Renames
- Phase 8.3 No Global Renames deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Rename-heavy suggestions are blocked
- **GIVEN** a generated CleanupPlan whose intent or steps include renaming files, classes, or APIs
- **WHEN** allow_global_rename is disabled in configuration
- **THEN** plan_from_finding rejects the plan with a clear error so the user can craft scoped follow-up tasks
