## ADDED Requirements
### Requirement: Phase 6.2 Git Branch Management
- Phase 6.2 Git Branch Management deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Helper switches to refactor branch safely
- **GIVEN** a repository with base and refactor branch names configured
- **WHEN** ensure_on_refactor_branch is called while on a different branch
- **THEN** it updates base, creates or fast-forwards the refactor branch from base, checks it out, and leaves conflicts to the user
