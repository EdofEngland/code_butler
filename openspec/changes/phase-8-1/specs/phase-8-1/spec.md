## ADDED Requirements

### Requirement: Phase 8.1 – Change Size Limits
The ai-clean project MUST fulfill the deliverables for Phase 8.1 described in docs/butlerspec_plan.md to keep the ButlerSpec roadmap on track.

#### Scenario: Phase 8.1 complete
- **GIVEN** the team is executing 8 – Global Guardrails & Limits
- **WHEN** Phase 8.1 (Change Size Limits) is completed
- **THEN** the repository provides change size limits outputs covering: Config + enforcement for:; Planners and advanced analyzer must split large changes into multiple plans when limits are exceeded.
- **AND** the work remains within ButlerSpec guardrails (one-plan-per-file, specs on disk, Codex executor).
