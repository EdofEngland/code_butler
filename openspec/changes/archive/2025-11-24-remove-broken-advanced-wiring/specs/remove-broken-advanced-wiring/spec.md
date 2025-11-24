## ADDED Requirements
### Requirement: Disable Advanced Analyzer Until Codex Slash Command Exists
The system SHALL disable the advanced analyzer execution path that depends on direct Codex access and fail fast with a clear message until a Codex slash command is available.

#### Scenario: Advanced analyzer invoked while Codex unavailable
- **WHEN** the user runs `ai-clean cleanup-advanced` or any advanced analyzer path
- **THEN** the command exits without attempting Codex, printing an explicit error that advanced cleanup requires a Codex slash command and is currently disabled
- **AND** no Codex prompt runner is invoked, no suggestions are emitted, and exit code is non-zero.

#### Scenario: Docs and help reflect disabled state
- **WHEN** a user reads CLI help or docs for advanced analyzer
- **THEN** they see that advanced cleanup is disabled until a Codex slash command is integrated, with no promise of Codex-backed execution today.
