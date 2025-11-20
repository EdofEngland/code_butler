## ADDED Requirements
### Requirement: Codex Helper Prompt Reference
Operations docs MUST include a Codex-first helper flow so maintainers can trigger ai-clean plus `/openspec-apply` with a single prompt or slash command.

#### Scenario: Helper prompt is versioned
- **GIVEN** a contributor wants to run Code Butler inside Codex
- **WHEN** they open the repository docs
- **THEN** they find a checked-in prompt or slash-command snippet that chains ai-clean execution with `/openspec-apply <change-id>` so they can copy/paste it into their Codex CLI setup

#### Scenario: Instructions cover command customization
- **GIVEN** a team needs to tweak the helper command (different prompt path, alternate executor backend)
- **WHEN** they review the referenced doc
- **THEN** it explains which env vars or config keys control the backend type and `/openspec-apply` text so they can adapt the workflow without editing core ai-clean code
