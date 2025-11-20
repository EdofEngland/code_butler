## ADDED Requirements
### Requirement: Executor Backend Abstraction
ai-clean MUST expose a lightweight executor-backend interface so Codex/manual runs and future automated executors plug into the same apply flow without touching planners or spec backends.

#### Scenario: Backend apply contract isolates Codex behavior
- **GIVEN** the CLI finishes writing an OpenSpec change for a plan
- **WHEN** it requests `ExecutorBackend.apply(change_id, spec_path)`
- **THEN** the backend returns a structured result that includes a status flag (`manual` vs `automatic`) plus instructions so the CLI knows whether to run shell commands or display Codex guidance

#### Scenario: Codex backend emits prompts command
- **GIVEN** the backend type is `codex`
- **WHEN** `apply` runs
- **THEN** it returns instructions that include `/openspec-apply <change-id>` (or `/prompts:openspec-apply ...`) so Codex operators can apply the generated change without needing local executor binaries

#### Scenario: Metadata persists for review tooling
- **GIVEN** an apply result from any backend
- **WHEN** the CLI stores execution metadata
- **THEN** backend details (type, manual vs automatic, emitted command text) are persisted so later review/reporting commands can reflect how the change was executed
