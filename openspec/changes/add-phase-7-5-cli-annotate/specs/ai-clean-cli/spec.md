## ADDED Requirements
### Requirement: Phase 7.5 Annotate Command
- Phase 7.5 `/annotate` Command deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Annotate surfaces docstring targets
- **GIVEN** doc analyzer findings for missing or weak docstrings
- **WHEN** ai-clean annotate PATH [--mode all] executes
- **THEN** the CLI shows targets, lets users choose scope, generates docstring plans, and can optionally apply them
