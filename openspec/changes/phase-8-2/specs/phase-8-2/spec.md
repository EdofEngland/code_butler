## ADDED Requirements

### Requirement: Phase 8.2 – Single Concern per Plan
The ai-clean project MUST fulfill the deliverables for Phase 8.2 described in docs/butlerspec_plan.md to keep the ButlerSpec roadmap on track.

#### Scenario: Phase 8.2 complete
- **GIVEN** the team is executing 8 – Global Guardrails & Limits
- **WHEN** Phase 8.2 (Single Concern per Plan) is completed
- **THEN** the repository provides single concern per plan outputs covering: Enforce that each `CleanupPlan` addresses **one concern**:; This keeps each Butler spec and Codex call small and deterministic.
- **AND** the work remains within ButlerSpec guardrails (one-plan-per-file, specs on disk, Codex executor).
