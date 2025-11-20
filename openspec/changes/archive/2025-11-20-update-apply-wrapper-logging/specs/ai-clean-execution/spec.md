## MODIFIED Requirements
### Requirement: Phase 5.1 Code Executor Applies Spec
- Phase 5.1 CodexExecutor: Apply Spec deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Executor output captures apply logs
- **GIVEN** ai-clean apply invokes the Codex executor
- **WHEN** the executor runs `openspec apply`
- **THEN** stdout and stderr from the real apply command are captured and emitted so `.ai-clean/executions/` stores the logs
