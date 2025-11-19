## ADDED Requirements
### Requirement: Phase 8.1 Change Size Limits
- Phase 8.1 Change Size Limits deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Plans respect configured size limits
- **GIVEN** size limits are set in configuration
- **WHEN** a finding would produce a plan exceeding file or line limits
- **THEN** the planner splits or rejects the plan so that each resulting plan stays within limits
