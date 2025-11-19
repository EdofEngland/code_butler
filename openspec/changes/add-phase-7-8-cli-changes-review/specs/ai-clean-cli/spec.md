## ADDED Requirements
### Requirement: Phase 7.8 Changes Review Command
- Phase 7.8 `/changes-review` Command deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Changes-review outputs summary and risks
- **GIVEN** a plan ID, corresponding diff, and execution result
- **WHEN** ai-clean changes-review PLAN_ID runs
- **THEN** the CLI invokes the review executor and prints summary, risks, and suggested manual checks
