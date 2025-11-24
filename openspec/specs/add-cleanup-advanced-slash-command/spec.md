# add-cleanup-advanced-slash-command Specification

## Purpose
TBD - created by archiving change add-cleanup-advanced-slash-command. Update Purpose after archive.
## Requirements
### Requirement: Codex Cleanup Advanced Slash Command
The system SHALL provide a Codex slash command that produces bounded advanced cleanup suggestions from a provided payload, without performing edits.

#### Scenario: Valid payload produces suggestions
- **WHEN** the user runs `/cleanup-advanced <PAYLOAD_PATH>` with a readable JSON payload containing findings/snippets and limits
- **THEN** the command emits a JSON array of suggestions, each with `description`, `path`, `start_line`, `end_line`, `change_type`, `model`, and `prompt_hash`
- **AND** it returns no code fences, no extra prose, and no file edits.

#### Scenario: Guardrails enforced
- **WHEN** the payload exceeds limits (max files/snippets/suggestions) or is missing required fields
- **THEN** the command returns `Error: <reason>` and emits no suggestions.

#### Scenario: Path handling and environment
- **WHEN** a relative payload path is provided
- **THEN** it is resolved from the repository root containing the target files; absolute paths are accepted.
