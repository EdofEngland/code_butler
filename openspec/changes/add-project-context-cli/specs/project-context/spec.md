## ADDED Requirements

### Requirement: Project Context CLI
The system MUST provide a CLI command that outputs the latest project context defined in `openspec/project.md`.

#### Scenario: Text summary output
- **GIVEN** the repository contains a populated `openspec/project.md`
- **WHEN** a user runs `code-butler project describe`
- **THEN** the command prints each top-level section (Purpose, Tech Stack, Conventions, Domain, Constraints, Dependencies)
- **AND** the text output includes the last modified timestamp of `openspec/project.md`

#### Scenario: JSON summary output
- **GIVEN** the repository contains a populated `openspec/project.md`
- **WHEN** a user runs `code-butler project describe --format json`
- **THEN** the command outputs valid JSON with keys for `purpose`, `tech_stack`, `conventions`, `domain_context`, `important_constraints`, and `external_dependencies`
- **AND** the JSON includes metadata for `source_path` and `last_updated`
- **AND** the process exits with code 0 so scripts can consume the data.

#### Scenario: Missing sections reported
- **GIVEN** one or more sections in `openspec/project.md` are empty
- **WHEN** `code-butler project describe` runs in any format
- **THEN** the command emits a warning listing the missing sections so contributors know to update them
- **AND** the warning is available in both text and JSON modes (as a `warnings` array in JSON output).
