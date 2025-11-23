## ADDED Requirements

### Requirement: Phase 5.3 – ReviewExecutor: Codex-Powered Changes Review
The ai-clean project MUST implement a ReviewExecutor that consumes a single CleanupPlan (or plan_id), its explicit git diff, and the latest ExecutionResult, then invokes Codex in deterministic “review mode” to produce advisory-only feedback (summary, risk grade, manual checks, optional constraint notes) without modifying code or specs.

#### Scenario: Deterministic review prompt
- **GIVEN** a plan (or plan_id), an explicit diff, and an ExecutionResult
- **WHEN** `ReviewExecutor` runs
- **THEN** it SHALL call Codex once with a bounded prompt: “Summarize these changes, flag risks, and ensure plan constraints are respected. Provide advisory notes only. Do NOT propose or apply code modifications.”
- **AND** it SHALL forbid chained instructions, retries that alter the prompt shape, or suggestions that expand scope beyond the provided plan/diff/result.

#### Scenario: Input validation and guardrails
- **WHEN** required inputs are missing (plan, diff, or ExecutionResult)
- **THEN** the executor SHALL fail fast with a clear error instead of running Codex
- **AND** it SHALL enforce single-plan context (no batching) and avoid implicit git calls or edits to any files/specs.

#### Scenario: Review output structure
- **WHEN** Codex returns a review
- **THEN** the executor SHALL capture the response as text or structured sections containing: summary of changes, risk assessment with a simple grade, suggested manual checks, and optional constraint validation notes
- **AND** it SHALL format or parse these sections consistently so downstream tooling can render/parse deterministically.

#### Scenario: Error propagation
- **GIVEN** Codex returns an error or malformed response
- **WHEN** the executor completes
- **THEN** it SHALL surface the failure (stderr/exit) without retries or hidden fallbacks
- **AND** it SHALL leave repository state unchanged (review-only, no code/spec modifications).
