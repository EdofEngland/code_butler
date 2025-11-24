# add-butler-exec-slash-command Specification

## Purpose
TBD - created by archiving change add-butler-exec-slash-command. Update Purpose after archive.
## Requirements
### Requirement: Codex Butler Exec Slash Command
The system SHALL provide a Codex slash command that executes a single ButlerSpec with strict guardrails.

#### Scenario: Valid spec executed
- **WHEN** the user runs `/butler-exec <spec_path>` and the ButlerSpec is valid (single target file, <= 25 actions, no invalid metadata)
- **THEN** the command summarizes intent/actions and emits only the unified diff for those actions, with no additional edits.
- **AND** if tests are specified, the command reports tests metadata (status, command, exit_code, stdout/stderr); otherwise it notes tests not run.

#### Scenario: Spec rejected by guardrails
- **WHEN** the ButlerSpec has multiple target files, exceeds 25 actions, or requests signature/rename/structural changes
- **THEN** the command refuses execution and emits an explicit error reason without any diff.

#### Scenario: Missing or unreadable spec
- **WHEN** the provided spec path does not exist or cannot be read
- **THEN** the command fails with an explanatory message and no diff.

#### Scenario: No edits outside scope
- **WHEN** the command applies the spec
- **THEN** it MUST NOT edit files or lines outside the specified target file and action ranges, nor perform replanning or speculative changes.
