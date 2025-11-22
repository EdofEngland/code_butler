## ADDED Requirements

### Requirement: Phase 3.1 – Planner for Duplicate Blocks
The ai-clean project MUST fulfill the deliverables for Phase 3.1 described in docs/butlerspec_plan.md to keep the ButlerSpec roadmap on track.

#### Scenario: Phase 3.1 complete
- **GIVEN** the team is executing 3 – Planner (Findings → CleanupPlans)
- **WHEN** Phase 3.1 (Planner for Duplicate Blocks) is completed
- **THEN** the repository provides planner for duplicate blocks outputs covering: For each `duplicate_block` finding, create a `CleanupPlan`:; Keep each plan **small**:
- **AND** the work remains within ButlerSpec guardrails (one-plan-per-file, specs on disk, Codex executor).
