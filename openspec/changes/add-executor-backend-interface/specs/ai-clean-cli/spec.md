## ADDED Requirements
### Requirement: Apply Command Shows Backend Instructions
`ai-clean apply` MUST call the configured executor backend immediately after writing a spec and show the returned instructions/status so Codex operators know the next action.

#### Scenario: Manual backends short-circuit executor flow
- **GIVEN** the backend result marks `manual`
- **WHEN** `ai-clean apply` completes the spec write step
- **THEN** it prints the backend instruction string (e.g., “In Codex, run `/openspec-apply add-change-id`”), skips shelling out to local executors/tests, and saves the backend metadata with the plan’s execution record

#### Scenario: Automatic backends reuse existing executor path
- **GIVEN** the backend result marks `automatic`
- **WHEN** `ai-clean apply` runs locally or in CI
- **THEN** it falls back to the existing `build_code_executor` flow, keeps the diff/test output, and still stores the backend metadata for reporting
