## ADDED Requirements

### Requirement: Phase 3.6 – Planning Orchestrator
The ai-clean project MUST fulfill the deliverables for Phase 3.6 described in docs/butlerspec_plan.md to keep the ButlerSpec roadmap on track.

#### Scenario: Phase 3.6 complete
- **GIVEN** the team is executing 3 – Planner (Findings → CleanupPlans)
- **WHEN** Phase 3.6 (Planning Orchestrator) is completed
- **THEN** the repository provides planning orchestrator outputs covering: Implement `plan_from_finding(finding: Finding) -> CleanupPlan`:; Provide helpers to:
- **AND** the work remains within ButlerSpec guardrails (one-plan-per-file, specs on disk, Codex executor).
