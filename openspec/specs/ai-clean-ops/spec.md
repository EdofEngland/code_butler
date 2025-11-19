# ai-clean-ops Specification

## Purpose
TBD - created by archiving change add-phase-6-1-plan-storage. Update Purpose after archive.
## Requirements
### Requirement: Phase 6.1 Plan Storage
- Phase 6.1 Plan Storage Helpers deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Plans round-trip via storage
- **GIVEN** a CleanupPlan with populated fields
- **WHEN** it is saved and then loaded from .ai-clean/plans
- **THEN** the reloaded plan matches the original fields required by executors

### Requirement: Phase 6.2 Git Branch Management
- Phase 6.2 Git Branch Management deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Helper switches to refactor branch safely
- **GIVEN** a repository with base and refactor branch names configured
- **WHEN** ensure_on_refactor_branch is called while on a different branch
- **THEN** it updates base, creates or fast-forwards the refactor branch from base, checks it out, and leaves conflicts to the user

### Requirement: Phase 6.3 Diff Stat Helper
- Phase 6.3 Diff Stat Helper deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Diff stat summarises changes
- **GIVEN** there are working tree modifications
- **WHEN** get_diff_stat is called
- **THEN** it returns the git diff --stat style summary of files and line changes
