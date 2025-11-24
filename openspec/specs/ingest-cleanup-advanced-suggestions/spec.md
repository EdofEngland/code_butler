# ingest-cleanup-advanced-suggestions Specification

## Purpose
TBD - created by archiving change add-cleanup-advanced-ingestion. Update Purpose after archive.
## Requirements
### Requirement: Ingest cleanup-advanced suggestions
The system SHALL optionally ingest `/cleanup-advanced` suggestions into findings when requested.

#### Scenario: Valid suggestions are ingested
- **WHEN** the user runs `ai-clean ingest --plan-id <id> --artifact <path> --update-findings` with an artifact containing a JSON array of suggestions (`description`, `path`, `start_line`, `end_line`, `change_type`, `model`, `prompt_hash`)
- **AND** each suggestion path and line range falls within the provided payload/selected files and respects configured limits
- **THEN** the command converts suggestions into `Finding` objects tagged with analyzer metadata and writes them to findings JSON without dropping existing findings

#### Scenario: Invalid suggestions are rejected
- **WHEN** a suggestion is malformed (missing fields, extra fields, invalid types), exceeds limits, or references a path/lines outside the allowed payload
- **THEN** ingest aborts with a clear error, does NOT write any suggestions, and leaves existing findings unchanged

#### Scenario: Flag not set skips suggestions
- **WHEN** the artifact includes a suggestions array but the user does not pass `--update-findings`
- **THEN** ingest processes only the execution result and ignores suggestions without error
